"""Lightwallet-protocol client helpers shared by the compatibility and serving tools.

Stubs are generated on first import from the vendored lightwallet-protocol v0.5.0 protos
(proto/lightwallet-protocol) into proto/gen, so no generated code is committed.
"""

from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import urllib.parse

import grpc

ROOT = pathlib.Path(__file__).resolve().parent.parent
PROTO_DIR = ROOT / "proto" / "lightwallet-protocol"
GEN_DIR = ROOT / "proto" / "gen"


def _generate_stubs() -> None:
    from grpc_tools import protoc

    GEN_DIR.mkdir(parents=True, exist_ok=True)
    args = [
        "protoc",
        f"-I{PROTO_DIR}",
        f"-I{pathlib.Path(protoc.__file__).parent / '_proto'}",
        f"--python_out={GEN_DIR}",
        f"--grpc_python_out={GEN_DIR}",
        str(PROTO_DIR / "compact_formats.proto"),
        str(PROTO_DIR / "service.proto"),
    ]
    if protoc.main(args) != 0:
        raise RuntimeError("protoc failed to generate lightwallet-protocol stubs")


if not (GEN_DIR / "service_pb2_grpc.py").exists():
    _generate_stubs()
sys.path.insert(0, str(GEN_DIR))

import compact_formats_pb2 as cf  # noqa: E402
import service_pb2 as pb  # noqa: E402
import service_pb2_grpc as pb_grpc  # noqa: E402

from google.protobuf import json_format  # noqa: E402

# Responses up to a full 100,000-block range must fit; both servers stream, so this bounds one message.
MAX_MESSAGE_BYTES = 256 * 1024 * 1024


def connect(url: str, ready_timeout: float = 15) -> pb_grpc.CompactTxStreamerStub:
    """Open a channel to http://host:port (plaintext) or https://host:port (TLS)."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or not parsed.port:
        raise ValueError(f"expected http://host:port or https://host:port, got {url!r}")
    target = f"{parsed.hostname}:{parsed.port}"
    options = [
        ("grpc.max_receive_message_length", MAX_MESSAGE_BYTES),
        ("grpc.max_send_message_length", MAX_MESSAGE_BYTES),
    ]
    if parsed.scheme == "https":
        channel = grpc.secure_channel(target, grpc.ssl_channel_credentials(), options=options)
    else:
        channel = grpc.insecure_channel(target, options=options)
    try:
        grpc.channel_ready_future(channel).result(timeout=ready_timeout)
    except grpc.FutureTimeoutError:
        channel.close()
        raise ConnectionError(f"{url} not accepting connections within {ready_timeout}s") from None
    return pb_grpc.CompactTxStreamerStub(channel)


def canonical(message) -> dict:
    """Stable JSON form of a protobuf message: field names as in the .proto, defaults included."""
    return json_format.MessageToDict(
        message,
        preserving_proto_field_name=True,
        always_print_fields_with_no_presence=True,
    )


def digest(messages) -> str:
    """SHA-256 over the deterministic serialization of a sequence of messages."""
    h = hashlib.sha256()
    for m in messages:
        body = m.SerializeToString(deterministic=True)
        h.update(len(body).to_bytes(8, "big"))
        h.update(body)
    return h.hexdigest()


def display_hex(internal: bytes) -> str:
    """Block hashes and txids travel in internal byte order; RPCs and explorers show them reversed."""
    return internal[::-1].hex()


def internal_bytes(display: str) -> bytes:
    return bytes.fromhex(display)[::-1]


def diff(a, b, path: str = "", out: list | None = None, limit: int = 20) -> list[str]:
    """Field-level differences between two canonical() dicts, capped at `limit` entries."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if key not in a:
                out.append(f"{path}.{key}: only in second")
            elif key not in b:
                out.append(f"{path}.{key}: only in first")
            else:
                diff(a[key], b[key], f"{path}.{key}", out, limit)
            if len(out) >= limit:
                break
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            out.append(f"{path}: length {len(a)} != {len(b)}")
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, f"{path}[{i}]", out, limit)
            if len(out) >= limit:
                break
    elif a != b:
        out.append(f"{path}: {json.dumps(a)[:80]} != {json.dumps(b)[:80]}")
    return out


class SplitMix64:
    """Deterministic, dependency-free PRNG so request sequences are identical across runs and servers."""

    def __init__(self, seed: int):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def next(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        return z ^ (z >> 31)

    def below(self, n: int) -> int:
        return self.next() % n
