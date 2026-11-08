"""Quick self-tests for the Splendor rules engine."""

import random

from data import CARD_BY_ID, CARDS, COLORS, NOBLES
from game import Game, GameError


def new_game(n=2, seed=7):
    players = [{"id": i, "name": f"P{i}"} for i in range(n)]
    return Game(players, rng=random.Random(seed))


def expect_error(fn, needle=""):
    try:
        fn()
    except GameError as exc:
        assert needle.lower() in str(exc).lower(), f"unexpected message: {exc}"
        return
    raise AssertionError("expected a GameError")


def test_data():
    assert len(CARDS) == 90
    assert sum(1 for c in CARDS if c["tier"] == 1) == 40
    assert sum(1 for c in CARDS if c["tier"] == 2) == 30
    assert sum(1 for c in CARDS if c["tier"] == 3) == 20
    assert len(NOBLES) == 10
    assert all(n["points"] == 3 for n in NOBLES)


def test_setup():
    for n, per_color in ((2, 4), (3, 5), (4, 7)):
        g = new_game(n)
        assert g.bank["gold"] == 5
        assert g.bank["diamond"] == per_color
        assert len(g.nobles) == n + 1
        assert len(g.decks[1]) == 36
        assert len(g.decks[2]) == 26
        assert len(g.decks[3]) == 16
        assert all(len(g.board[t]) == 4 for t in (1, 2, 3))


def test_take3_and_turn_order():
    g = new_game(2)
    g.turn = 0
    g.act(0, {"type": "take3", "colors": ["diamond", "sapphire", "emerald"]})
    assert g.players[0]["tokens"]["diamond"] == 1
    assert g.players[0]["tokens"]["sapphire"] == 1
    assert g.players[0]["tokens"]["emerald"] == 1
    assert g.turn == 1


def test_take3_rejects_duplicates():
    g = new_game(2)
    g.turn = 0
    expect_error(
        lambda: g.act(0, {"type": "take3", "colors": ["diamond", "diamond"]}),
        "different",
    )


def test_take2_needs_four():
    g = new_game(2)
    g.turn = 0
    g.bank["diamond"] = 3
    expect_error(lambda: g.act(0, {"type": "take2", "color": "diamond"}), "at least 4")
    g.bank["diamond"] = 4
    g.act(0, {"type": "take2", "color": "diamond"})
    assert g.players[0]["tokens"]["diamond"] == 2


def test_token_limit():
    g = new_game(2)
    g.turn = 0
    g.players[0]["tokens"]["diamond"] = 9
    expect_error(
        lambda: g.act(0, {"type": "take3", "colors": ["sapphire", "emerald"]}),
        "10 tokens",
    )


def test_reserve_from_board_and_gold():
    g = new_game(2)
    g.turn = 0
    card_id = next(c for c in g.board[1] if c is not None)
    g.act(0, {"type": "reserve", "card": card_id})
    assert card_id in g.players[0]["reserved"]
    assert g.players[0]["tokens"]["gold"] == 1
    assert g.bank["gold"] == 4
    assert card_id not in g.board[1]


def test_reserve_blind_and_limit():
    g = new_game(2)
    for _ in range(3):
        g.turn = 0
        g.act(0, {"type": "reserve", "tier": 1})
    assert len(g.players[0]["reserved"]) == 3
    g.turn = 0
    expect_error(lambda: g.act(0, {"type": "reserve", "tier": 1}), "3 cards")


def test_buy_with_bonus_and_gold():
    g = new_game(2)
    g.turn = 0
    # Find a tier-1 card and give the player exactly enough to buy it.
    card = CARD_BY_ID[g.board[1][0]]
    p = g.players[0]
    for color, amount in card["cost"].items():
        p["tokens"][color] = amount
    g.act(0, {"type": "buy", "card": card["id"]})
    assert card["id"] in p["cards"]
    assert p["bonuses"][card["bonus"]] == 1
    assert g.points(0) == card["points"]


def test_buy_uses_gold_as_wild():
    g = new_game(2)
    g.turn = 0
    card = CARD_BY_ID[g.board[1][0]]
    p = g.players[0]
    # Give one gold for every gem the card needs, and nothing else.
    total = sum(card["cost"].values())
    p["tokens"]["gold"] = total
    g.act(0, {"type": "buy", "card": card["id"]})
    assert card["id"] in p["cards"]
    assert p["tokens"]["gold"] == 0


def test_buy_rejects_unaffordable():
    g = new_game(2)
    g.turn = 0
    card = CARD_BY_ID[g.board[3][0]]
    expect_error(lambda: g.act(0, {"type": "buy", "card": card["id"]}), "enough gems")


def test_noble_award():
    g = new_game(2)
    g.turn = 0
    noble = next(n for n in NOBLES if n["id"] in g.nobles)
    for color, amount in noble["requirement"].items():
        g.players[0]["bonuses"][color] = amount
    g._resolve_nobles(0)
    assert noble["id"] in g.players[0]["nobles"]
    assert noble["id"] not in g.nobles
    assert g.points(0) == 3


def test_final_round_and_finish():
    g = new_game(2)
    g.turn = 0
    g.first_player = 0
    # Give player 0 enough points to trigger the final round.
    g.players[0]["cards"] = [c["id"] for c in CARDS if c["points"] == 5][:3]
    g._end_turn()
    assert g.final_round is True
    assert g.turn == 1
    g._end_turn()
    assert g.finished is True
    assert g.winner is not None


def test_tiebreak_fewest_cards():
    g = new_game(2)
    g.players[0]["cards"] = [c["id"] for c in CARDS if c["points"] == 5][:3]
    g.players[1]["cards"] = [c["id"] for c in CARDS if c["points"] == 5][:3]
    # Same points; player 1 has more cards, so player 0 should win.
    g.players[1]["cards"] += [c["id"] for c in CARDS if c["points"] == 0][:1]
    g._finish()
    assert g.winner["ids"] == [0]


def test_skip_turn():
    g = new_game(2)
    g.turn = 0
    g.skip_turn()
    assert g.turn == 1


def test_pass_only_when_stuck():
    g = new_game(2)
    g.turn = 0
    assert g.has_legal_move(0)
    expect_error(lambda: g.act(0, {"type": "pass"}), "legal move")

    p = g.players[0]
    p["tokens"] = {c: 0 for c in COLORS} | {"gold": 0}
    p["tokens"]["diamond"] = 10
    p["bonuses"] = {c: 0 for c in COLORS}
    p["reserved"] = [72, 80, 84]  # cost 7 of a color the player does not have
    g.bank = {c: 0 for c in COLORS} | {"gold": 0}
    g.board = {1: [None] * 4, 2: [None] * 4, 3: [None] * 4}
    g.decks = {1: [], 2: [], 3: []}

    assert not g.has_legal_move(0)
    g.act(0, {"type": "pass"})
    assert g.turn == 1


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
        print(f"  ok  {test.__name__}")
    print(f"\n{len(tests)} tests passed.")
