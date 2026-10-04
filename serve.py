#!/usr/bin/env python3
"""Serve this directory over loopback as the browser's new tab page."""

import os
import socket
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Both loopback addresses: "localhost" resolves to ::1 as well as 127.0.0.1,
# and a browser that picks the IPv6 one gets a refusal rather than falling back
# the way curl does. Neither address is reachable from the network.
HOSTS = ("127.0.0.1", "::1")
PORT = 8777
ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(SimpleHTTPRequestHandler):
    # The new tab must reflect the file on disk the instant it is saved, so the
    # browser is told to keep no copy at all. Re-reading 40KB over loopback is
    # cheaper than the revalidation round trip a remote host would need, so
    # there is nothing to win by letting it cache.
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    # launchd would otherwise accumulate a request log for every tab opened.
    def log_message(self, format, *args):
        pass


class V6Server(ThreadingHTTPServer):
    address_family = socket.AF_INET6

    def server_bind(self):
        # Pin this socket to IPv6 so it cannot collide with the IPv4 listener
        # holding the same port.
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        super().server_bind()


def listener(host):
    cls = V6Server if ":" in host else ThreadingHTTPServer
    return cls((host, PORT), partial(Handler, directory=ROOT))


if __name__ == "__main__":
    servers = []
    for host in HOSTS:
        try:
            servers.append(listener(host))
        except OSError as err:
            # A host without IPv6 still gets a working server on the other one.
            print(f"skipping {host}: {err}")

    if not servers:
        raise SystemExit(f"could not bind port {PORT} on any loopback address")

    for server in servers[1:]:
        threading.Thread(target=server.serve_forever, daemon=True).start()
    servers[0].serve_forever()
