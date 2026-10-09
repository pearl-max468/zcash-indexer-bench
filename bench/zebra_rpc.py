"""Minimal JSON-RPC client for Zebra (and other zcashd-style RPC servers), used as the reference oracle."""

from __future__ import annotations

import base64
import itertools
import json
import pathlib
import urllib.error
import urllib.request


class RpcError(Exception):
    def __init__(self, code, message):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message


class JsonRpc:
    def __init__(self, url: str, cookie: str | None = None, userpass: str | None = None, timeout: float = 60):
        self.url = url
        self.timeout = timeout
        self._ids = itertools.count(1)
        self.auth = None
        if cookie:
            userpass = pathlib.Path(cookie).read_text().strip()
        if userpass:
            self.auth = "Basic " + base64.b64encode(userpass.encode()).decode()

    def call(self, method: str, *params):
        body = json.dumps({"jsonrpc": "2.0", "id": next(self._ids), "method": method, "params": list(params)})
        request = urllib.request.Request(self.url, data=body.encode(), method="POST")
        request.add_header("content-type", "application/json")
        if self.auth:
            request.add_header("authorization", self.auth)
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as e:
            # zcashd-style servers return JSON-RPC errors with HTTP 4xx/5xx bodies.
            try:
                payload = json.load(e)
            except (json.JSONDecodeError, ValueError):
                raise RpcError(e.code, f"HTTP {e.code}") from None
        if payload.get("error"):
            err = payload["error"]
            raise RpcError(err.get("code"), err.get("message"))
        return payload.get("result")
