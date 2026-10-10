// Diagnostic only (`--tcp-nodelay` in bench/run_serving.py): sets TCP_NODELAY on every socket the
// server process accepts, as tonic's own `Server::serve` path does. Loaded with LD_PRELOAD, so the
// binary under test is unchanged. Non-TCP sockets reject the option harmlessly.
// build: cc -O2 -shared -fPIC -o nodelay.so nodelay.c -ldl
#define _GNU_SOURCE
#include <dlfcn.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <stdio.h>
#include <sys/socket.h>

static void set_nodelay(int fd) {
    static int reported;
    int one = 1;
    if (fd >= 0 && setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof one) == 0 && !reported) {
        reported = 1;
        fprintf(stderr, "zbench nodelay shim: TCP_NODELAY set on accepted socket\n");
    }
}

int accept(int s, struct sockaddr *addr, socklen_t *len) {
    static int (*next)(int, struct sockaddr *, socklen_t *);
    if (!next) next = dlsym(RTLD_NEXT, "accept");
    int fd = next(s, addr, len);
    set_nodelay(fd);
    return fd;
}

int accept4(int s, struct sockaddr *addr, socklen_t *len, int flags) {
    static int (*next)(int, struct sockaddr *, socklen_t *, int);
    if (!next) next = dlsym(RTLD_NEXT, "accept4");
    int fd = next(s, addr, len, flags);
    set_nodelay(fd);
    return fd;
}
