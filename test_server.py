"""End-to-end HTTP tests for the LAN server."""

import json
import threading
import urllib.error
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
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def get(url):
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def main():
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
    httpd.daemon_threads = True
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    status, alice = post(base + "/api/join", {"name": "Alice"})
    assert status == 200, (status, alice)
    status, bob = post(base + "/api/join", {"name": "Bob"})
    assert status == 200, (status, bob)
    assert alice["player"]["isHost"] is True
    assert bob["player"]["isHost"] is False

    status, _ = post(base + "/api/join", {"name": "Alice"})
    assert status == 403, "duplicate names must be rejected"

    status, _ = post(base + "/api/start", {"token": bob["token"]})
    assert status == 400, "non-host must not start"

    status, _ = post(base + "/api/start", {"token": alice["token"]})
    assert status == 200, "host should start"

    status, _ = post(base + "/api/join", {"name": "Carol"})
    assert status == 403, "joins must be locked after start"

    status, state = get(base + f"/api/state?token={alice['token']}")
    assert status == 200
    assert state["state"]["phase"] == "playing"
    game = state["state"]["game"]
    assert len(game["players"]) == 2
    assert game["bank"]["gold"] == 5

    turn = game["turn"]
    token = alice["token"] if game["players"][turn]["isYou"] else bob["token"]
    status, result = post(
        base + "/api/action",
        {
            "token": token,
            "action": {"type": "take3", "colors": ["diamond", "sapphire", "emerald"]},
        },
    )
    assert status == 200, (status, result)

    status, state = get(base + f"/api/state?token={alice['token']}")
    assert state["state"]["game"]["turn"] != turn, "turn should advance"

    status, rejoin = post(base + "/api/join", {"token": alice["token"]})
    assert status == 200
    assert rejoin["token"] == alice["token"], "token rejoin should keep the seat"

    status, _ = get(base + "/api/state?token=nope")
    assert status == 403, "unknown token must be rejected"

    print("server tests passed")
    httpd.shutdown()


if __name__ == "__main__":
    main()
