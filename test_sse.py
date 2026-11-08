"""Verify the SSE stream sends an initial state frame."""

import json
import threading
import urllib.request
from http.server import ThreadingHTTPServer

import server


def post(url, payload):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def main():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    httpd.daemon_threads = True
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    joined = post(base + "/api/join", {"name": "SseTester"})
    token = joined["token"]

    req = urllib.request.Request(base + f"/api/events?token={token}")
    with urllib.request.urlopen(req, timeout=5) as r:
        line = r.readline().decode("utf-8").strip()
        assert line.startswith("data: "), line
        payload = json.loads(line[len("data: "):])
        assert payload["type"] == "state"
        assert payload["state"]["you"]["name"] == "SseTester"

    print("sse test passed")
    httpd.shutdown()


if __name__ == "__main__":
    main()
