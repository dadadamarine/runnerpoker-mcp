from copy import deepcopy

import pytest

from runnerpoker_mcp import hands
from runnerpoker_mcp.auth import Credentials, RunnerPokerError


def detail(hand_id=1, raises=2, river=True, fold_stage=None):
    streets = [
        {
            "stage": "Preflop",
            "actions": [
                {"seq": 1, "userId": 7, "action": "SmallBlind", "totalBet": 1},
                {"seq": 2, "userId": 42, "action": "BigBlind", "totalBet": 2},
                *[
                    {
                        "seq": i + 3,
                        "userId": 7 if i % 2 == 0 else 42,
                        "action": "Raise",
                        "totalBet": [6, 20, 50][i],
                    }
                    for i in range(raises)
                ],
            ],
        }
    ]
    folded = False
    for stage in ["Flop", "Turn", "River"] if river else ["Flop"]:
        streets.append(
            {
                "stage": stage,
                "actions": [
                    {
                        "seq": 1,
                        "userId": 7 if folded else 42,
                        "action": "Fold" if stage == fold_stage else "Check",
                    }
                ],
            }
        )
        folded = folded or stage == fold_stage
    return {
        "handId": hand_id,
        "players": [{"userId": 42}, {"userId": 7}],
        "table": {"board": [3, 4, 5, 6, 7] if river else [3, 4, 5], "blinds": {"bigBlind": 2}},
        "streets": streets,
    }


def summary(hand_id=1, cards=None, delta=-100):
    return {
        "handId": hand_id,
        "gameType": "Cash",
        "endAt": "2026-11-07T09:00:00Z",
        "hero": {"holeCards": cards or [1, 14], "netDelta": delta, "position": "BB"},
        "table": {"blinds": {"bigBlind": 2}},
    }


@pytest.mark.parametrize(
    "cards,expected",
    [
        ([1, 14], "AA"),
        ([13, 26], "KK"),
        ([2, 15], "22"),
        ([1, 13], "AKs"),
        ([1, 26], "AKo"),
        ([0, 14], None),
        ([1, 1], None),
        ([True, 14], None),
        ([1], None),
    ],
)
def test_card_encoding(cards, expected):
    assert hands.hand_class(cards) == expected


@pytest.mark.parametrize(
    "raises,pot", [(0, "unraised"), (1, "single_raised"), (2, "three_bet"), (3, "four_bet_plus")]
)
def test_pot_classification(raises, pot):
    assert hands.classify(detail(raises=raises), 42)["pot_type"] == pot


def test_unknown_raise_sizing_straddle_and_short_allin():
    for replacement in [
        {"action": "Straddle"},
        {"totalBet": None},
        {"action": "AllIn", "totalBet": 7},
    ]:
        record = detail()
        record["streets"][0]["actions"][-1].update(replacement)
        assert hands.classify(record, 42)["pot_type"] is None


def test_hero_river_is_not_just_five_board_cards():
    assert hands.classify(detail(), 42)["hero_reached_river"] is True
    assert hands.classify(detail(fold_stage="Turn"), 42)["hero_reached_river"] is False
    assert hands.classify(detail(river=False), 42)["hero_reached_river"] is False
    assert hands.classify(detail(), 999)["hero_reached_river"] is None
    assert hands.classify({"table": {"board": [1, 2, 3, 4, 5]}}, 42)["hero_reached_river"] is None


def test_prior_allin_runout_is_separate_from_river_action():
    record = detail()
    record["streets"][0]["actions"] = [
        {"seq": 1, "userId": 42, "action": "AllIn", "totalBet": 100},
        {"seq": 2, "userId": 7, "action": "Call", "totalBet": 100},
    ]
    for street in record["streets"][1:]:
        street["actions"] = []
    result = hands.classify(record, 42)
    assert result["hero_reached_river"] is True
    assert result["hero_has_river_action"] is False


def test_other_players_actions_cannot_prove_hero_reached_river():
    record = detail()
    for street in record["streets"]:
        street["actions"] = [{"seq": 1, "userId": 7, "action": "Check"}]
    result = hands.classify(record, 42)
    assert result["hero_reached_river"] is None
    assert result["hero_has_river_action"] is None


def test_hero_turn_check_does_not_prove_survival_of_missing_turn_actions():
    record = detail()
    record["streets"][-1]["actions"] = []
    assert hands.classify(record, 42)["hero_reached_river"] is None


def test_contradictory_fold_then_river_action_stays_unknown():
    record = detail(fold_stage="Turn")
    record["streets"][-1]["actions"] = [{"seq": 1, "userId": 42, "action": "Check"}]
    result = hands.classify(record, 42)
    assert result["hero_reached_river"] is None
    assert result["reasons"]["river"] == "contradictory_actions_after_fold_or_allin"


@pytest.mark.parametrize("allin_stage", ["Preflop", "Flop", "Turn"])
def test_allin_runout_from_each_street(allin_stage):
    record = detail()
    after_allin = False
    for street in record["streets"]:
        if after_allin:
            street["actions"] = []
        if street["stage"] == allin_stage:
            street["actions"] = [
                {"seq": 1, "userId": 42, "action": "AllIn"},
                {"seq": 2, "userId": 7, "action": "Call"},
            ]
            after_allin = True
    result = hands.classify(record, 42)
    assert result["hero_reached_river"] is True
    assert result["hero_has_river_action"] is False
    assert result["reasons"]["river"] == "explicit_hero_allin_with_river_runout"


@pytest.mark.parametrize("invalid", [[1, 1, 2, 3, 4], [0, 1, 2, 3, 4], [1, 2]])
def test_invalid_board_never_proves_river(invalid):
    record = detail()
    record["table"]["board"] = invalid
    assert hands.classify(record, 42)["hero_reached_river"] is None


def test_duplicate_action_sequence_is_unknown():
    record = detail()
    record["streets"][0]["actions"][0]["seq"] = 2
    assert hands.classify(record, 42)["hero_reached_river"] is None


def test_all_1326_hole_card_combinations_map_to_169_classes():
    from collections import Counter
    from itertools import combinations

    counts = Counter(hands.hand_class(list(cards)) for cards in combinations(range(1, 53), 2))
    assert len(counts) == 169 and None not in counts
    for label, count in counts.items():
        assert count == (6 if len(label) == 2 else 4 if label.endswith("s") else 12)


def test_string_user_ids_match_account_identity_and_missing_blinds_stay_unknown():
    record = detail()
    record["players"][0]["userId"] = "42"
    for street in record["streets"]:
        for action in street["actions"]:
            action["userId"] = str(action["userId"])
    assert hands.classify(record, 42)["hero_reached_river"] is True
    record["table"]["blinds"] = None
    assert hands.classify(record, 42)["pot_type"] is None
    brief = summary()
    brief["table"]["blinds"] = None
    assert hands.net_bb(brief) is None


async def test_verified_session_mapping_cursor_dates(monkeypatch):
    async def get(path, params):
        assert path == "/hand-histories"
        assert params == {
            "GameType": "Cash",
            "ParticipantId": 123456,
            "PageSize": 100,
            "Cursor": "abc",
            "From": "2026-10-31T15:00:00.000Z",
            "To": "2026-11-07T14:59:59.999Z",
        }
        return {"items": [], "hasNext": False}

    monkeypatch.setattr(hands.client, "get_json", get)
    await hands.list_hands(
        session_id=123456, start_date="2026-11-01", end_date="2026-11-07", cursor="abc"
    )


@pytest.fixture
def auth(monkeypatch):
    monkeypatch.setattr(hands.Credentials, "load", lambda: Credentials("fake", 42))


async def test_combined_spot_search_and_big_loss_sort(auth, monkeypatch):
    async def listing(*args):
        return {
            "items": [
                summary(1),
                summary(2, delta=-200),
                summary(3, cards=[1, 26]),
                summary(4, delta=100),
            ],
            "hasNext": False,
        }

    async def fetch(hand_id):
        return detail(hand_id)

    monkeypatch.setattr(hands, "list_hands", listing)
    monkeypatch.setattr(hands, "get_hand", fetch)
    result = await hands.search_hands(
        pocket_pairs_only=True,
        pot_type="three_bet",
        reached_river=True,
        result="lost",
        min_abs_net_bb=50,
        sort="biggest_loss",
    )
    assert [h["hand_id"] for h in result["hands"]] == [2, 1]
    assert result["classification_complete"] is True
    assert result["details_fetched"] == 2
    assert result["hands"][0]["detail"]["streets"]


async def test_cursor_pages_dedup_and_unknown_coverage(auth, monkeypatch):
    async def listing(*args):
        if args[-1] is None:
            return {"items": [summary(1)], "hasNext": True, "nextCursor": "next"}
        return {"items": [summary(1), summary(2)], "hasNext": False}

    async def fetch(hand_id):
        return detail(hand_id, raises=3) if hand_id == 1 else {"handId": hand_id}

    monkeypatch.setattr(hands, "list_hands", listing)
    monkeypatch.setattr(hands, "get_hand", fetch)
    result = await hands.search_hands(pot_type="three_bet")
    assert result["hands"] == []
    assert result["scanned_hands"] == 2
    assert result["history_exhausted"] is True
    assert result["classification_complete"] is False
    assert result["unclassified_count"] == 1


async def test_detail_budget_is_explicit(auth, monkeypatch):
    async def listing(*args):
        return {"items": [summary(1), summary(2)], "hasNext": True, "nextCursor": "next"}

    async def fetch(hand_id):
        return detail(hand_id)

    monkeypatch.setattr(hands, "list_hands", listing)
    monkeypatch.setattr(hands, "get_hand", fetch)
    result = await hands.search_hands(max_details=1)
    assert result["details_fetched"] == 1
    assert result["stop_reason"] == "detail_budget"
    assert result["classification_complete"] is False
    assert result["unclassified_sample"][0]["reason"] == "detail_budget"


async def test_repeated_cursor_stops(auth, monkeypatch):
    async def listing(*args):
        return {"items": [], "hasNext": True, "nextCursor": "same"}

    monkeypatch.setattr(hands, "list_hands", listing)
    result = await hands.search_hands()
    assert result["stop_reason"] == "invalid_cursor"
    assert result["history_exhausted"] is False


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_abs_net_bb": float("nan")},
        {"max_pages": 0},
        {"game_type": "Tournament", "sort": "biggest_win"},
        {"limit": 101},
    ],
)
async def test_search_validates_before_network(kwargs):
    with pytest.raises(RunnerPokerError):
        await hands.search_hands(**kwargs)


async def test_detail_id_is_validated_before_network():
    with pytest.raises(RunnerPokerError):
        await hands.get_hand(-1)


def test_tournament_has_no_cash_bb_metric():
    record = deepcopy(summary())
    record["gameType"] = "Tournament"
    assert hands.net_bb(record) is None
