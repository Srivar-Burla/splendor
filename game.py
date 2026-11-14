"""Splendor rules engine (base game, 2-4 players)."""

import random

from data import CARD_BY_ID, CARDS, COLORS, NOBLE_BY_ID, NOBLES


class GameError(Exception):
    """Raised when a player attempts an illegal action."""


def token_total(player):
    return sum(player["tokens"].values())


class Game:
    def __init__(self, players, rng=None):
        if not (2 <= len(players) <= 4):
            raise GameError("Splendor needs 2 to 4 players.")
        self.rng = rng or random.Random()
        self.n = len(players)
        self.player_ids = [p["id"] for p in players]
        self.index_by_id = {p["id"]: i for i, p in enumerate(players)}
        self.players = [
            {
                "id": p["id"],
                "name": p["name"],
                "tokens": {c: 0 for c in COLORS} | {"gold": 0},
                "bonuses": {c: 0 for c in COLORS},
                "cards": [],
                "reserved": [],
                "nobles": [],
            }
            for p in players
        ]

        per_color = {2: 4, 3: 5, 4: 7}[self.n]
        self.bank = {c: per_color for c in COLORS}
        self.bank["gold"] = 5

        self.decks = {1: [], 2: [], 3: []}
        for card in CARDS:
            self.decks[card["tier"]].append(card["id"])
        for tier in self.decks:
            self.rng.shuffle(self.decks[tier])

        self.board = {t: [self._draw(t) for _ in range(4)] for t in (1, 2, 3)}

        noble_ids = [n["id"] for n in NOBLES]
        self.rng.shuffle(noble_ids)
        self.nobles = noble_ids[: self.n + 1]

        self.turn = self.rng.randrange(self.n)
        self.first_player = self.turn
        self.final_round = False
        self.pending_noble = None
        self.finished = False
        self.winner = None
        self.scores = None
        self.log = []
        self._log(f"Game started. {self.players[self.turn]['name']} goes first.")

    # ------------------------------------------------------------------ utils
    def _draw(self, tier):
        return self.decks[tier].pop() if self.decks[tier] else None

    def _log(self, message):
        self.log.append(message)
        if len(self.log) > 240:
            del self.log[:120]

    def index_of(self, player_id):
        return self.index_by_id[player_id]

    def points(self, index):
        p = self.players[index]
        return sum(CARD_BY_ID[cid]["points"] for cid in p["cards"]) + 3 * len(p["nobles"])

    # --------------------------------------------------------------- actions
    def act(self, player_index, action):
        if self.finished:
            raise GameError("The game is over.")
        if self.pending_noble is not None:
            if action.get("type") != "choose_noble":
                raise GameError("Choose a noble before doing anything else.")
            self._choose_noble(player_index, action)
            self._end_turn()
            return
        if player_index != self.turn:
            raise GameError("It's not your turn.")

        kind = action.get("type")
        if kind == "take3":
            self._take3(player_index, action)
        elif kind == "take2":
            self._take2(player_index, action)
        elif kind == "reserve":
            self._reserve(player_index, action)
        elif kind == "buy":
            self._buy(player_index, action)
        elif kind == "pass":
            self._pass(player_index)
        else:
            raise GameError("Unknown action.")

        self._resolve_nobles(player_index)
        if self.pending_noble is None:
            self._end_turn()

    def skip_turn(self):
        if self.finished:
            raise GameError("The game is over.")
        if self.pending_noble is not None:
            self._award_noble(self.pending_noble["player"], self.pending_noble["options"][0])
            self.pending_noble = None
        self._log(f"{self.players[self.turn]['name']}'s turn was skipped.")
        self._end_turn()

    # ------------------------------------------------------------ take gems
    def _take3(self, index, action):
        p = self.players[index]
        colors = action.get("colors") or []
        if not isinstance(colors, list) or not (1 <= len(colors) <= 3):
            raise GameError("Choose 1 to 3 different colors.")
        if len(set(colors)) != len(colors):
            raise GameError("The colors must all be different.")
        for c in colors:
            if c not in COLORS:
                raise GameError("Unknown gem color.")
            if self.bank[c] < 1:
                raise GameError(f"No {c} tokens left in the bank.")
        if token_total(p) + len(colors) > 10:
            raise GameError("You can only hold 10 tokens. Buy a card or take fewer.")
        for c in colors:
            self.bank[c] -= 1
            p["tokens"][c] += 1
        self._log(f"{p['name']} took {', '.join(colors)}.")

    def _take2(self, index, action):
        p = self.players[index]
        c = action.get("color")
        if c not in COLORS:
            raise GameError("Unknown gem color.")
        if self.bank[c] < 4:
            raise GameError(f"You can only take 2 {c} if at least 4 are in the bank.")
        if token_total(p) + 2 > 10:
            raise GameError("You can only hold 10 tokens. Buy a card or take fewer.")
        self.bank[c] -= 2
        p["tokens"][c] += 2
        self._log(f"{p['name']} took 2 {c}.")

    # --------------------------------------------------------------- reserve
    def _reserve(self, index, action):
        p = self.players[index]
        if len(p["reserved"]) >= 3:
            raise GameError("You can only reserve 3 cards.")

        cid = action.get("card")
        tier = action.get("tier")
        if cid is not None:
            found = None
            for t in (1, 2, 3):
                if cid in self.board[t]:
                    found = t
                    break
            if found is None:
                raise GameError("That card is not on the table.")
            slot = self.board[found].index(cid)
            self.board[found][slot] = self._draw(found)
        else:
            if tier not in (1, 2, 3):
                raise GameError("Choose a deck to reserve from.")
            if not self.decks[tier]:
                raise GameError("That deck is empty.")
            cid = self.decks[tier].pop()

        p["reserved"].append(cid)
        got_gold = False
        if self.bank["gold"] > 0 and token_total(p) < 10:
            self.bank["gold"] -= 1
            p["tokens"]["gold"] += 1
            got_gold = True

        card = CARD_BY_ID[cid]
        self._log(
            f"{p['name']} reserved a tier-{card['tier']} {card['bonus']} card"
            + (" and took a gold." if got_gold else ".")
        )

    # ------------------------------------------------------------------ buy
    def _buy(self, index, action):
        p = self.players[index]
        cid = action.get("card")
        if cid not in CARD_BY_ID:
            raise GameError("Unknown card.")

        source = None
        if cid in p["reserved"]:
            source = "reserved"
        else:
            for t in (1, 2, 3):
                if cid in self.board[t]:
                    source = t
                    break
        if source is None:
            raise GameError("That card is not available to you.")

        card = CARD_BY_ID[cid]
        payment = self._payment(p, card["cost"])
        if payment is None:
            raise GameError("You don't have enough gems to buy that card.")

        for c, amount in payment["tokens"].items():
            p["tokens"][c] -= amount
            self.bank[c] += amount
        p["tokens"]["gold"] -= payment["gold"]
        self.bank["gold"] += payment["gold"]

        if source == "reserved":
            p["reserved"].remove(cid)
        else:
            slot = self.board[source].index(cid)
            self.board[source][slot] = self._draw(source)

        p["cards"].append(cid)
        p["bonuses"][card["bonus"]] += 1
        if source == "reserved":
            self._log(
                f"{p['name']} bought a reserved tier-{card['tier']} {card['bonus']} card"
                f" (+{card['points']} prestige)."
            )
        else:
            self._log(
                f"{p['name']} bought a tier-{card['tier']} {card['bonus']} card"
                f" from the board (+{card['points']} prestige)."
            )

    def _payment(self, p, cost):
        tokens = {}
        gold_needed = 0
        for c in COLORS:
            need = max(0, cost.get(c, 0) - p["bonuses"][c])
            use = min(need, p["tokens"][c])
            tokens[c] = use
            gold_needed += need - use
        if gold_needed > p["tokens"]["gold"]:
            return None
        return {"tokens": tokens, "gold": gold_needed}

    def has_legal_move(self, index):
        p = self.players[index]
        total = token_total(p)

        if total < 10 and any(self.bank[c] > 0 for c in COLORS):
            return True
        if total <= 8 and any(self.bank[c] >= 4 for c in COLORS):
            return True

        if len(p["reserved"]) < 3:
            if any(cid is not None for t in (1, 2, 3) for cid in self.board[t]):
                return True
            if any(self.decks[t] for t in (1, 2, 3)):
                return True

        for t in (1, 2, 3):
            for cid in self.board[t]:
                if cid is not None and self._payment(p, CARD_BY_ID[cid]["cost"]):
                    return True
        for cid in p["reserved"]:
            if self._payment(p, CARD_BY_ID[cid]["cost"]):
                return True
        return False

    def _pass(self, index):
        if self.has_legal_move(index):
            raise GameError("You still have a legal move.")
        self._log(f"{self.players[index]['name']} passed.")

    # --------------------------------------------------------------- nobles
    def _resolve_nobles(self, index):
        p = self.players[index]
        eligible = [nid for nid in self.nobles if self._meets(p, NOBLE_BY_ID[nid])]
        if not eligible:
            return
        if len(eligible) == 1:
            self._award_noble(index, eligible[0])
        else:
            self.pending_noble = {"player": index, "options": eligible}
            self._log(f"{p['name']} may choose a noble.")

    def _meets(self, p, noble):
        return all(p["bonuses"][c] >= noble["requirement"][c] for c in COLORS)

    def _award_noble(self, index, noble_id):
        if noble_id not in self.nobles:
            raise GameError("That noble is no longer available.")
        self.nobles.remove(noble_id)
        self.players[index]["nobles"].append(noble_id)
        self._log(
            f"{self.players[index]['name']} was visited by "
            f"{NOBLE_BY_ID[noble_id]['name']} (+3 prestige)."
        )

    def _choose_noble(self, index, action):
        pending = self.pending_noble
        if pending is None or pending["player"] != index:
            raise GameError("You don't have a noble choice pending.")
        noble_id = action.get("noble")
        if noble_id not in pending["options"]:
            raise GameError("That noble is not one of your options.")
        self._award_noble(index, noble_id)
        self.pending_noble = None

    # ------------------------------------------------------------ turn flow
    def _end_turn(self):
        if not self.final_round and any(self.points(i) >= 15 for i in range(self.n)):
            self.final_round = True
            self._log("Final round! The game ends when everyone has had the same number of turns.")

        nxt = (self.turn + 1) % self.n
        if self.final_round and nxt == self.first_player:
            self._finish()
            return
        self.turn = nxt

    def _finish(self):
        self.finished = True
        rows = []
        for i, p in enumerate(self.players):
            rows.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "points": self.points(i),
                    "cards": len(p["cards"]),
                    "reserved": len(p["reserved"]),
                    "nobles": len(p["nobles"]),
                }
            )
        rows.sort(key=lambda r: (-r["points"], r["cards"], r["reserved"]))
        best = rows[0]
        winners = [
            r
            for r in rows
            if (r["points"], r["cards"], r["reserved"])
            == (best["points"], best["cards"], best["reserved"])
        ]
        self.scores = rows
        self.winner = {
            "ids": [w["id"] for w in winners],
            "names": [w["name"] for w in winners],
        }
        names = ", ".join(w["name"] for w in winners)
        self._log(f"Game over! Winner: {names} with {best['points']} prestige.")

    # ------------------------------------------------------------ serialize
    def to_state(self, viewer_index):
        players = []
        for i, p in enumerate(self.players):
            players.append(
                {
                    "id": p["id"],
                    "name": p["name"],
                    "points": self.points(i),
                    "tokens": dict(p["tokens"]),
                    "bonuses": dict(p["bonuses"]),
                    "cardCount": len(p["cards"]),
                    "reservedCount": len(p["reserved"]),
                    "nobles": [NOBLE_BY_ID[nid] for nid in p["nobles"]],
                    "isYou": i == viewer_index,
                }
            )

        me = self.players[viewer_index]
        return {
            "bank": dict(self.bank),
            "board": {
                str(t): [CARD_BY_ID[cid] if cid is not None else None for cid in self.board[t]]
                for t in (1, 2, 3)
            },
            "decks": {str(t): len(self.decks[t]) for t in (1, 2, 3)},
            "nobles": [NOBLE_BY_ID[nid] for nid in self.nobles],
            "players": players,
            "turn": self.turn,
            "firstPlayer": self.first_player,
            "finalRound": self.final_round,
            "pendingNoble": (
                {
                    "player": self.pending_noble["player"],
                    "options": [NOBLE_BY_ID[nid] for nid in self.pending_noble["options"]],
                }
                if self.pending_noble
                else None
            ),
            "you": {
                "tokens": dict(me["tokens"]),
                "bonuses": dict(me["bonuses"]),
                "cards": [CARD_BY_ID[cid] for cid in me["cards"]],
                "reserved": [CARD_BY_ID[cid] for cid in me["reserved"]],
                "points": self.points(viewer_index),
                "nobles": [NOBLE_BY_ID[nid] for nid in me["nobles"]],
                "canPass": not self.has_legal_move(viewer_index),
            },
            "log": self.log[-80:],
            "finished": self.finished,
            "winner": self.winner,
            "scores": self.scores,
        }
