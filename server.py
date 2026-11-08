"""Local-network Splendor server. Python standard library only.

Run:  python server.py
Then share the printed http://<lan-ip>:8000 link with your group.
"""

import argparse
import json
import mimetypes
import os
import queue
import socket
import threading
import time
import uuid
from collections import defaultdict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from game import Game, GameError

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
MAX_PLAYERS = 4


def lan_ip():
    """Best-effort LAN address of this machine."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


class Hub:
    """Holds lobby + game state and fans updates out to SSE clients."""

    def __init__(self):
        self.lock = threading.RLock()
        self.players = []          # join order == seat order
        self.by_token = {}
        self.phase = "lobby"       # lobby | playing | finished
        self.join_locked = False
        self.game = None
        self.clients = defaultdict(set)  # token -> set[queue.Queue]
        self.next_id = 0

    # ------------------------------------------------------------- helpers
    def _find(self, token):
        return self.by_token.get(token) if token else None

    def _host_connected(self):
        return any(p["is_host"] and p["connected"] for p in self.players)

    def _is_connected(self, player_id):
        return any(p["id"] == player_id and p["connected"] for p in self.players)

    def _public_players(self):
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "isHost": p["is_host"],
                "connected": p["connected"],
            }
            for p in self.players
        ]

    def state_for(self, player):
        with self.lock:
            state = {
                "phase": self.phase,
                "you": {
                    "id": player["id"],
                    "name": player["name"],
                    "isHost": player["is_host"],
                    "connected": player["connected"],
                },
                "players": self._public_players(),
                "joinLocked": self.join_locked,
                "canStart": (
                    self.phase == "lobby"
                    and len(self.players) >= 2
                    and (player["is_host"] or not self._host_connected())
                ),
                "serverTime": time.time(),
            }
            if self.game is not None:
                state["game"] = self.game.to_state(self.game.index_of(player["id"]))
            return state

    # ------------------------------------------------------------ fan-out
    def broadcast(self):
        with self.lock:
            for token, queues in list(self.clients.items()):
                player = self._find(token)
                if not player:
                    continue
                payload = json.dumps({"type": "state", "state": self.state_for(player)})
                for q in list(queues):
                    try:
                        q.put_nowait(payload)
                    except queue.Full:
                        try:
                            q.get_nowait()
                            q.put_nowait(payload)
                        except queue.Empty:
                            pass

    def subscribe(self, token):
        q = queue.Queue(maxsize=64)
        with self.lock:
            self.clients[token].add(q)
            player = self._find(token)
            if player:
                player["connected"] = True
                q.put_nowait(
                    json.dumps({"type": "state", "state": self.state_for(player)})
                )
        self.broadcast()
        return q

    def unsubscribe(self, token, q):
        with self.lock:
            queues = self.clients.get(token)
            if queues:
                queues.discard(q)
                if not queues:
                    self.clients.pop(token, None)
                    player = self._find(token)
                    if player:
                        player["connected"] = False
        self.broadcast()

    # ------------------------------------------------------------ actions
    def join(self, name, token=None):
        with self.lock:
            if token:
                player = self._find(token)
                if player:
                    player["connected"] = True
                    self.broadcast()
                    return player, None
            if self.join_locked or self.phase != "lobby":
                return None, "The game has already started."
            if len(self.players) >= MAX_PLAYERS:
                return None, "The game is full (4 players max)."
            name = (name or "").strip()[:20]
            if not name:
                return None, "Please enter a name."
            if any(p["name"].lower() == name.lower() for p in self.players):
                return None, "That name is already taken."
            token = uuid.uuid4().hex
            player = {
                "id": self.next_id,
                "name": name,
                "token": token,
                "connected": True,
                "is_host": len(self.players) == 0,
            }
            self.next_id += 1
            self.players.append(player)
            self.by_token[token] = player
            self.broadcast()
            return player, None

    def start(self, token):
        with self.lock:
            player = self._find(token)
            if not player:
                return "You are not in this game."
            if self.phase != "lobby":
                return "The game has already started."
            if not (player["is_host"] or not self._host_connected()):
                return "Only the host can start the game."
            if len(self.players) < 2:
                return "You need at least 2 players to start."
            self.game = Game([{"id": p["id"], "name": p["name"]} for p in self.players])
            self.phase = "playing"
            self.join_locked = True
            self.broadcast()
            return None

    def act(self, token, action):
        with self.lock:
            player = self._find(token)
            if not player:
                return "You are not in this game."
            if self.phase != "playing" or self.game is None:
                return "The game is not running."
            try:
                self.game.act(self.game.index_of(player["id"]), action)
            except GameError as exc:
                return str(exc)
            if self.game.finished:
                self.phase = "finished"
            self.broadcast()
            return None

    def skip(self, token):
        with self.lock:
            player = self._find(token)
            if not player:
                return "You are not in this game."
            if self.phase != "playing" or self.game is None:
                return "The game is not running."
            if not player["is_host"]:
                return "Only the host can skip a turn."
            current = self.game.players[self.game.turn]
            if current["id"] != player["id"] and self._is_connected(current["id"]):
                return "You can only skip a disconnected player's turn."
            try:
                self.game.skip_turn()
            except GameError as exc:
                return str(exc)
            if self.game.finished:
                self.phase = "finished"
            self.broadcast()
            return None

    def play_again(self, token):
        with self.lock:
            player = self._find(token)
            if not player:
                return "You are not in this game."
            if not player["is_host"]:
                return "Only the host can start a new game."
            if self.phase != "finished":
                return "The game is still running."
            self.game = Game([{"id": p["id"], "name": p["name"]} for p in self.players])
            self.phase = "playing"
            self.broadcast()
            return None

    def open_lobby(self, token):
        with self.lock:
            player = self._find(token)
            if not player:
                return "You are not in this game."
            if not player["is_host"]:
                return "Only the host can reopen the lobby."
            self.game = None
            self.phase = "lobby"
            self.join_locked = False
            self.broadcast()
            return None

    def shutdown(self, token):
        with self.lock:
            player = self._find(token)
            if not player:
                return "You are not in this game."
            if not player["is_host"]:
                return "Only the host can stop the server."
        threading.Thread(target=self._stop_process, daemon=True).start()
        return None

    @staticmethod
    def _stop_process():
        time.sleep(0.4)
        os._exit(0)

    def leave(self, token):
        with self.lock:
            player = self._find(token)
            if not player or self.phase != "lobby":
                return
            self.players.remove(player)
            self.by_token.pop(token, None)
            self.clients.pop(token, None)
            if player["is_host"] and self.players:
                self.players[0]["is_host"] = True
            self.broadcast()


HUB = Hub()


class QuietServer(ThreadingHTTPServer):
    """Threading server that ignores clients dropping mid-request."""

    daemon_threads = True

    def handle_error(self, request, client_address):
        import sys

        exc = sys.exc_info()[1]
        if isinstance(exc, (ConnectionAbortedError, ConnectionResetError, BrokenPipeError)):
            return
        super().handle_error(request, client_address)


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "SplendorLAN/1.0"

    def log_message(self, fmt, *args):
        pass

    # ------------------------------------------------------------ helpers
    def _send_json(self, obj, status=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return {}
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return {}

    def _serve_file(self, rel_path):
        full = os.path.normpath(os.path.join(STATIC_DIR, rel_path))
        if full != STATIC_DIR and not full.startswith(STATIC_DIR + os.sep):
            self._send_json({"error": "Not found"}, 404)
            return
        if not os.path.isfile(full):
            self._send_json({"error": "Not found"}, 404)
            return
        ctype = mimetypes.guess_type(full)[0] or "application/octet-stream"
        with open(full, "rb") as fh:
            body = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    # ---------------------------------------------------------------- GET
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/config":
            self._send_json({"lanUrl": f"http://{lan_ip()}:{self.server.server_port}"})
            return

        if path == "/api/state":
            token = (parse_qs(parsed.query).get("token") or [""])[0]
            with HUB.lock:
                player = HUB._find(token)
                if not player:
                    self._send_json({"error": "Unknown player"}, 403)
                    return
                state = HUB.state_for(player)
            self._send_json({"state": state})
            return

        if path == "/api/events":
            token = (parse_qs(parsed.query).get("token") or [""])[0]
            with HUB.lock:
                player = HUB._find(token)
            if not player:
                self._send_json({"error": "Unknown player"}, 403)
                return
            self._stream(token)
            return

        if path in ("/", "/index.html"):
            self._serve_file("index.html")
            return
        if path.startswith("/static/"):
            self._serve_file(path[len("/static/"):])
            return
        if path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        self._send_json({"error": "Not found"}, 404)

    def _stream(self, token):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        q = HUB.subscribe(token)
        try:
            while True:
                try:
                    payload = q.get(timeout=20)
                    self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            HUB.unsubscribe(token, q)

    # --------------------------------------------------------------- POST
    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read_json()

        if path == "/api/join":
            player, error = HUB.join(body.get("name"), body.get("token"))
            if error:
                self._send_json({"error": error}, 403)
                return
            with HUB.lock:
                state = HUB.state_for(player)
            self._send_json(
                {
                    "token": player["token"],
                    "player": {
                        "id": player["id"],
                        "name": player["name"],
                        "isHost": player["is_host"],
                    },
                    "state": state,
                }
            )
            return

        routes = {
            "/api/start": HUB.start,
            "/api/skip": HUB.skip,
            "/api/play-again": HUB.play_again,
            "/api/open-lobby": HUB.open_lobby,
            "/api/shutdown": HUB.shutdown,
        }
        if path in routes:
            error = routes[path](body.get("token"))
            if error:
                self._send_json({"error": error}, 400)
                return
            self._send_json({"ok": True})
            return

        if path == "/api/action":
            error = HUB.act(body.get("token"), body.get("action") or {})
            if error:
                self._send_json({"error": error}, 400)
                return
            self._send_json({"ok": True})
            return

        if path == "/api/leave":
            HUB.leave(body.get("token"))
            self._send_json({"ok": True})
            return

        self._send_json({"error": "Not found"}, 404)


def main():
    parser = argparse.ArgumentParser(description="Run a local-network Splendor game.")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    server = QuietServer((args.host, args.port), Handler)
    server.daemon_threads = True
    ip = lan_ip()

    print()
    print("  SPLENDOR  -  local network game")
    print("  " + "-" * 46)
    print(f"  This laptop:        http://127.0.0.1:{args.port}")
    print(f"  Share this link:    http://{ip}:{args.port}")
    print("  " + "-" * 46)
    print("  Everyone must be on the same Wi-Fi network.")
    print("  Press Ctrl+C to stop.")
    print(flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Server stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
