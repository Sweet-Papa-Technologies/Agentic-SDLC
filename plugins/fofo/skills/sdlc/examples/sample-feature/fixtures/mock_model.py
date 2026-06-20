#!/usr/bin/env python3
"""Tiny stand-in for an Anthropic-compatible /v1/messages endpoint.

Used only by the smoke test so semantic-test-judge can exercise the FULL model
path (real HTTP POST -> parse -> contract verdict) without a real API key. Returns
a canned reply that marks the weak test as not asserting intent.

Usage: mock_model.py <port>
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

VERDICT = {
    "tests": [
        {"name": "REQ-001 builds a slug", "asserts_intent": False, "confidence": 0.9,
         "reason": "calls slugify() but never checks the returned value"},
        {"name": "REQ-002 sanity", "asserts_intent": False, "confidence": 0.88,
         "reason": "asserts 1===1, a tautology unrelated to the requirement"},
    ],
    "overall_confidence": 0.89,
    "summary": "2 tests touch lines without asserting requirement intent",
}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        self.rfile.read(length)
        body = json.dumps({"content": [{"type": "text", "text": json.dumps(VERDICT)}]}).encode()
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):  # noqa: A002
        pass


if __name__ == "__main__":
    port = int(sys.argv[1])
    srv = HTTPServer(("127.0.0.1", port), Handler)
    print("READY", flush=True)
    srv.serve_forever()
