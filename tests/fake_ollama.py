"""
tests/fake_ollama.py — a stand-in for Ollama, used only by the tests
====================================================================

A tiny web server on this computer that answers the two requests the app
makes: GET /api/tags (which models exist) and POST /api/chat (answer a
conversation). Tests choose what it says, and can make it misbehave, so we
can check the app copes when the real Ollama is missing or fails.
"""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class FakeOllama:
    """Start with `start()`, point the app at `.url`, stop with `stop()`."""

    def __init__(self):
        self.models = ["model-newest", "model-older"]
        self.mode = "ok"            # "ok", "error500", or "drop"
        self.stream_pieces = ["Hello ", "there."]   # streamed answer
        self.replies = []           # queued answers for non-streamed calls
        self.requests = []          # every chat request body received
        self.tag_requests = 0       # how many times the model list was asked for
        self._server = None

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self._server.server_address[1]}"

    def start(self):
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):     # keep test output quiet
                pass

            def _json(self, status, body):
                data = json.dumps(body).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def do_GET(self):
                fake.tag_requests += 1
                # A model may be a plain name, or a dict to add details
                # such as "remote_host" (a model that runs in the cloud).
                self._json(200, {"models": [
                    m if isinstance(m, dict) else {"name": m}
                    for m in fake.models]})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length) or b"{}")
                fake.requests.append(body)

                if fake.mode == "error500":
                    self._json(500, {"error": "this model does not support chat"})
                    return

                if not body.get("stream"):
                    text = fake.replies.pop(0) if fake.replies else ""
                    self._json(200, {"message": {"content": text}, "done": True})
                    return

                # Streamed answer: one JSON object per line, no length given,
                # so the connection closing marks the end.
                self.send_response(200)
                self.send_header("Content-Type", "application/x-ndjson")
                self.send_header("Connection", "close")
                self.end_headers()
                pieces = fake.stream_pieces[:1] if fake.mode == "drop" else fake.stream_pieces
                for piece in pieces:
                    line = {"message": {"content": piece}, "done": False}
                    self.wfile.write(json.dumps(line).encode() + b"\n")
                if fake.mode != "drop":     # "drop" hangs up before finishing
                    self.wfile.write(json.dumps({"done": True}).encode() + b"\n")
                self.close_connection = True

        self._server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=self._server.serve_forever, daemon=True).start()
        return self

    def stop(self):
        self._server.shutdown()
        self._server.server_close()
