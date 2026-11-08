"""Randomized full-game playthroughs to stress the rules engine."""

import itertools
import random

from data import CARD_BY_ID, COLORS
from game import Game


def legal_moves(g, idx):
    p = g.players[idx]
    total = sum(p["tokens"].values())
    moves = []

    available = [c for c in COLORS if g.bank[c] > 0]
    for k in range(1, min(3, len(available)) + 1):
        for combo in itertools.combinations(available, k):
            if total + k <= 10:
                moves.append({"type": "take3", "colors": list(combo)})

    for c in COLORS:
        if g.bank[c] >= 4 and total + 2 <= 10:
            moves.append({"type": "take2", "color": c})

    if len(p["reserved"]) < 3:
        for t in (1, 2, 3):
            for cid in g.board[t]:
                if cid is not None:
                    moves.append({"type": "reserve", "card": cid})
            if g.decks[t]:
                moves.append({"type": "reserve", "tier": t})

    for t in (1, 2, 3):
        for cid in g.board[t]:
            if cid is not None and g._payment(p, CARD_BY_ID[cid]["cost"]):
                moves.append({"type": "buy", "card": cid})
    for cid in p["reserved"]:
        if g._payment(p, CARD_BY_ID[cid]["cost"]):
            moves.append({"type": "buy", "card": cid})

    return moves


def play(seed, n):
    g = Game([{"id": i, "name": f"P{i}"} for i in range(n)], rng=random.Random(seed))
    rng = random.Random(seed * 31 + n)
    steps = 0
    while not g.finished and steps < 8000:
        if g.pending_noble:
            g.act(
                g.pending_noble["player"],
                {"type": "choose_noble", "noble": g.pending_noble["options"][0]},
            )
        else:
            idx = g.turn
            moves = legal_moves(g, idx)
            if not moves:
                g.skip_turn()
            else:
                g.act(idx, rng.choice(moves))
        steps += 1
    assert g.finished, f"seed {seed} n={n} did not finish"
    assert g.winner is not None
    assert g.scores is not None
    return g


def main():
    for n in (2, 3, 4):
        for seed in range(15):
            g = play(seed, n)
            assert g.scores[0]["points"] >= 15, (seed, n, g.scores)
    print("45 randomized playthroughs passed")


if __name__ == "__main__":
    main()
