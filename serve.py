#!/usr/bin/env python3
"""Serve this directory over loopback as the browser's new tab page."""

import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

HOST = "127.0.0.1"
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
    def log_message(self, *args):
        pass


if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), partial(Handler, directory=ROOT))
    server.serve_forever()
