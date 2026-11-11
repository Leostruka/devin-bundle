"""One-shot internal-protocol capture server.

Run: python recon/capture.py --port 8642
Then: WINDSURF_API_SERVER_URL=http://127.0.0.1:8642 devin -p "hi"

Logs method/path/headers/body per request to capture-YYYYMMDD-HHMMSS.jsonl.
Responds 200 with an empty body so the CLI reveals its full request sequence.
"""

import base64
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

OUT = Path(__file__).resolve().parent / f"capture-{time.strftime('%Y%m%d-%H%M%S')}.jsonl"
PORT = 8642

REDACT = {"authorization", "x-api-key", "cookie"}


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _dump(self, method: str) -> None:
        n = int(self.headers.get("content-length") or 0)
        body = self.rfile.read(n) if n else b""
        rec = {
            "ts": time.time(),
            "method": method,
            "path": self.path,
            "headers": {
                k: ("<REDACTED>" if k.lower() in REDACT else v)
                for k, v in self.headers.items()
            },
            "body_b64": base64.b64encode(body).decode(),
            "body_len": n,
        }
        with OUT.open("a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"[capture] {method} {self.path} ct={self.headers.get('content-type')} len={n}", flush=True)
        payload = b"{}"
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    do_GET = lambda s: H._dump(s, "GET")
    do_POST = lambda s: H._dump(s, "POST")
    do_PUT = lambda s: H._dump(s, "PUT")

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(sys.argv[sys.argv.index("--port") + 1]) if "--port" in sys.argv else PORT
    print(f"[capture] :{port} -> {OUT}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
