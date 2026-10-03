import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest

from sdk_py import GXRagClient
from sdk_py.client import GXRagError

SEEN: list[dict] = []


class Handler(BaseHTTPRequestHandler):
    def _reply(self, status, body):
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        SEEN.append({"path": self.path, "auth": self.headers.get("Authorization"),
                     "ws": self.headers.get("X-Workspace-Id"), "body": json.loads(self.rfile.read(length))})
        if self.headers.get("Authorization") == "Bearer bad":
            return self._reply(401, {"detail": "Invalid API key."})
        self._reply(200, {"ok": True})

    def do_GET(self):
        self._reply(200, {"status": "ok"})

    def log_message(self, *args):
        pass


@pytest.fixture
def server():
    SEEN.clear()
    httpd = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_port}"
    httpd.shutdown()


def test_sends_key_workspace_and_payload(server):
    client = GXRagClient(server, workspace_id="ws_1", api_key="gxk_abc_def")
    assert client.hybrid("zarnotide", limit=3) == {"ok": True}
    assert SEEN[-1] == {"path": "/v1/query/hybrid", "auth": "Bearer gxk_abc_def", "ws": "ws_1",
                        "body": {"query": "zarnotide", "limit": 3}}


def test_no_auth_headers_when_unset(server):
    GXRagClient(server).vector("x")
    assert SEEN[-1]["auth"] is None and SEEN[-1]["ws"] is None


def test_http_errors_become_typed_exceptions(server):
    with pytest.raises(GXRagError) as caught:
        GXRagClient(server, api_key="bad").graph("x")
    assert caught.value.status == 401 and caught.value.detail == "Invalid API key."


def test_health(server):
    assert GXRagClient(server).health() == {"status": "ok"}
