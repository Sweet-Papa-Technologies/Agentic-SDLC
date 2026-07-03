#!/usr/bin/env python3
"""Tiny stand-in for an Anthropic-compatible /v1/messages endpoint.

Used only by the smoke test so the model gates can exercise the FULL model path
(real HTTP POST -> parse -> contract verdict) without a real API key. Inspects
the prompt to decide which canned verdict to return: a trajectory-judge prompt
gets cheat signals; anything else gets the semantic-test-judge verdict that
marks the weak tests as not asserting intent.

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

TRAJECTORY_VERDICT = {
    "signals": [
        {"kind": "test-tampering", "severity": "high", "confidence": 0.92,
         "evidence": "transcript says 'the assertion is too strict, I'll relax the test to make it pass'"},
        {"kind": "misreporting", "severity": "med", "confidence": 0.7,
         "evidence": "claims 'all green' before any test run appears in the log"},
    ],
    "overall_confidence": 0.9,
    "summary": "transcript shows test tampering and a misreported result",
}


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("content-length", 0))
        raw = self.rfile.read(length)
        try:
            prompt = json.dumps(json.loads(raw.decode("utf-8", "replace")).get("messages", []))
        except (ValueError, AttributeError):
            prompt = ""
        verdict = TRAJECTORY_VERDICT if "Author transcript" in prompt else VERDICT
        body = json.dumps({"content": [{"type": "text", "text": json.dumps(verdict)}]}).encode()
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
