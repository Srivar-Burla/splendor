"""Static game data for Splendor (base game, 2014).

Card costs and noble requirements are functional game rules, transcribed from
the published base game and cross-checked against two open-source datasets
(bouk/splendimax and boardgamers/splendor).
"""

COLORS = ["diamond", "sapphire", "emerald", "ruby", "onyx"]

COLOR_LABELS = {
    "diamond": "Diamond",
    "sapphire": "Sapphire",
    "emerald": "Emerald",
    "ruby": "Ruby",
    "onyx": "Onyx",
    "gold": "Gold",
}

# (tier, bonus, points, diamond, sapphire, emerald, ruby, onyx)
CARD_ROWS = [
    # ---- Tier 1 (40 cards) ----
    (1, "onyx", 0, 1, 1, 1, 1, 0),
    (1, "onyx", 0, 1, 1, 1, 2, 0),
    (1, "onyx", 0, 2, 0, 1, 2, 0),
    (1, "onyx", 0, 0, 1, 0, 3, 1),
    (1, "onyx", 0, 0, 0, 2, 1, 0),
    (1, "onyx", 0, 2, 0, 2, 0, 0),
    (1, "onyx", 0, 0, 0, 3, 0, 0),
    (1, "onyx", 1, 0, 4, 0, 0, 0),
    (1, "sapphire", 0, 1, 0, 1, 1, 1),
    (1, "sapphire", 0, 1, 0, 1, 2, 1),
    (1, "sapphire", 0, 1, 0, 2, 2, 0),
    (1, "sapphire", 0, 0, 1, 3, 1, 0),
    (1, "sapphire", 0, 1, 2, 0, 0, 0),
    (1, "sapphire", 0, 2, 0, 2, 0, 0),
    (1, "sapphire", 0, 0, 3, 0, 0, 0),
    (1, "sapphire", 1, 0, 0, 0, 4, 0),
    (1, "diamond", 0, 0, 1, 1, 1, 1),
    (1, "diamond", 0, 0, 1, 2, 1, 1),
    (1, "diamond", 0, 0, 2, 2, 0, 1),
    (1, "diamond", 0, 1, 1, 0, 0, 3),
    (1, "diamond", 0, 0, 1, 0, 2, 0),
    (1, "diamond", 0, 2, 2, 0, 0, 0),
    (1, "diamond", 0, 0, 0, 3, 0, 0),
    (1, "diamond", 1, 0, 0, 4, 0, 0),
    (1, "emerald", 0, 1, 1, 0, 1, 1),
    (1, "emerald", 0, 1, 1, 0, 1, 2),
    (1, "emerald", 0, 2, 1, 0, 2, 0),
    (1, "emerald", 0, 1, 0, 3, 1, 0),
    (1, "emerald", 0, 0, 0, 1, 0, 2),
    (1, "emerald", 0, 0, 2, 0, 2, 0),
    (1, "emerald", 0, 0, 0, 0, 3, 0),
    (1, "emerald", 1, 0, 0, 0, 0, 4),
    (1, "ruby", 0, 1, 1, 1, 0, 1),
    (1, "ruby", 0, 2, 1, 1, 0, 1),
    (1, "ruby", 0, 2, 0, 1, 0, 2),
    (1, "ruby", 0, 1, 3, 0, 0, 1),
    (1, "ruby", 0, 0, 0, 2, 1, 0),
    (1, "ruby", 0, 0, 2, 0, 0, 2),
    (1, "ruby", 0, 0, 0, 0, 0, 3),
    (1, "ruby", 1, 0, 0, 0, 0, 4),
    # ---- Tier 2 (30 cards) ----
    (2, "onyx", 1, 3, 2, 2, 0, 0),
    (2, "onyx", 1, 3, 2, 0, 0, 2),
    (2, "onyx", 2, 0, 1, 4, 2, 0),
    (2, "onyx", 2, 0, 0, 5, 3, 0),
    (2, "onyx", 2, 5, 0, 0, 0, 0),
    (2, "onyx", 3, 0, 0, 0, 0, 6),
    (2, "sapphire", 1, 0, 2, 2, 3, 0),
    (2, "sapphire", 1, 0, 3, 2, 0, 3),
    (2, "sapphire", 2, 5, 0, 3, 0, 0),
    (2, "sapphire", 2, 2, 4, 0, 1, 0),
    (2, "sapphire", 2, 0, 0, 5, 0, 0),
    (2, "sapphire", 3, 0, 0, 0, 6, 0),
    (2, "diamond", 1, 0, 0, 3, 2, 2),
    (2, "diamond", 1, 2, 0, 0, 3, 3),
    (2, "diamond", 2, 0, 0, 1, 4, 2),
    (2, "diamond", 2, 0, 3, 0, 5, 0),
    (2, "diamond", 2, 0, 0, 0, 0, 5),
    (2, "diamond", 3, 0, 0, 0, 0, 6),
    (2, "emerald", 1, 3, 0, 0, 3, 2),
    (2, "emerald", 1, 2, 3, 0, 0, 2),
    (2, "emerald", 2, 0, 2, 0, 0, 4),
    (2, "emerald", 2, 0, 0, 5, 3, 0),
    (2, "emerald", 2, 0, 5, 0, 0, 0),
    (2, "emerald", 3, 0, 0, 6, 0, 0),
    (2, "ruby", 1, 2, 0, 0, 2, 3),
    (2, "ruby", 1, 2, 0, 3, 0, 3),
    (2, "ruby", 2, 1, 0, 0, 4, 2),
    (2, "ruby", 2, 0, 0, 0, 3, 5),
    (2, "ruby", 2, 0, 0, 0, 0, 5),
    (2, "ruby", 3, 0, 0, 0, 6, 0),
    # ---- Tier 3 (20 cards) ----
    (3, "onyx", 3, 3, 3, 5, 3, 0),
    (3, "onyx", 4, 0, 0, 0, 7, 0),
    (3, "onyx", 4, 3, 0, 0, 6, 3),
    (3, "onyx", 5, 3, 0, 0, 7, 0),
    (3, "sapphire", 3, 3, 0, 3, 3, 5),
    (3, "sapphire", 4, 7, 0, 0, 0, 0),
    (3, "sapphire", 4, 6, 3, 0, 0, 3),
    (3, "sapphire", 5, 7, 0, 0, 0, 3),
    (3, "diamond", 3, 0, 3, 3, 3, 5),
    (3, "diamond", 4, 0, 0, 0, 0, 7),
    (3, "diamond", 4, 3, 6, 0, 0, 3),
    (3, "diamond", 5, 0, 7, 0, 0, 3),
    (3, "emerald", 3, 5, 3, 0, 3, 3),
    (3, "emerald", 4, 0, 7, 0, 0, 0),
    (3, "emerald", 4, 3, 3, 6, 0, 0),
    (3, "emerald", 5, 0, 0, 7, 3, 0),
    (3, "ruby", 3, 3, 3, 3, 0, 5),
    (3, "ruby", 4, 0, 0, 7, 0, 0),
    (3, "ruby", 4, 3, 0, 3, 6, 0),
    (3, "ruby", 5, 0, 3, 7, 0, 0),
]

CARDS = []
for _i, _row in enumerate(CARD_ROWS):
    _tier, _bonus, _points, *_costs = _row
    CARDS.append(
        {
            "id": _i,
            "tier": _tier,
            "bonus": _bonus,
            "points": _points,
            "cost": {_c: _costs[_j] for _j, _c in enumerate(COLORS)},
        }
    )

CARD_BY_ID = {_c["id"]: _c for _c in CARDS}

# (name, diamond, sapphire, emerald, ruby, onyx)
NOBLE_ROWS = [
    ("Mary Stuart", 0, 0, 4, 4, 0),
    ("Charles V", 0, 4, 4, 0, 0),
    ("Machiavelli", 4, 4, 0, 0, 0),
    ("Isabella of Castile", 4, 0, 0, 0, 4),
    ("Suleiman the Magnificent", 0, 0, 0, 4, 4),
    ("Catherine de' Medici", 0, 3, 3, 3, 0),
    ("Anne of Brittany", 3, 0, 3, 3, 0),
    ("Henry VIII", 3, 3, 0, 0, 3),
    ("Elisabeth of Austria", 0, 0, 3, 3, 3),
    ("Francis I of France", 3, 3, 3, 0, 0),
]

NOBLES = []
for _i, _row in enumerate(NOBLE_ROWS):
    _name, *_req = _row
    NOBLES.append(
        {
            "id": _i,
            "name": _name,
            "points": 3,
            "requirement": {_c: _req[_j] for _j, _c in enumerate(COLORS)},
        }
    )

NOBLE_BY_ID = {_n["id"]: _n for _n in NOBLES}
