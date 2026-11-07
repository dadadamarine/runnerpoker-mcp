import pytest

from runnerpoker_mcp import stats
from runnerpoker_mcp.auth import RunnerPokerError


async def test_position_date_channel_mapping_and_filter(monkeypatch):
    async def request(path, params):
        assert path == "/api/v1/craft/holdem/positions"
        assert params == {
            "Period": "custom",
            "From": "2026-11-01",
            "To": "2026-11-07",
            "ChannelIds": [3, 4],
        }
        return {
            "items": [
                {"position": "BB", "hands": 200, "bb100": -20},
                {"position": "BTN", "hands": 150, "bb100": 10},
            ]
        }

    monkeypatch.setattr(stats.client, "get_json", request)
    result = await stats.positions("custom", "2026-11-01", "2026-11-07", [3, 4, 3], ["bb"])
    assert result["items"] == [{"position": "BB", "hands": 200, "bb100": -20}]
    assert "net_bb" not in result["items"][0]
    assert not result["unavailable_positions"]


async def test_missing_position_is_not_zero_profit(monkeypatch):
    async def request(*args):
        return {"items": [{"position": "BB", "hands": 0, "bb100": None}]}

    monkeypatch.setattr(stats.client, "get_json", request)
    result = await stats.positions(selected_positions=["UTG"])
    assert result["items"] == []
    assert result["unavailable_positions"] == ["UTG"]


async def test_session_hud_repeated_array_contract(monkeypatch):
    async def request(path, params):
        assert path == "/api/v1/craft/hud"
        assert params == {"GameType": "holdem", "ParticipantIds": [123456]}
        return {"stats": {"vpip": 25}}

    monkeypatch.setattr(stats.client, "get_json", request)
    assert (await stats.hud(session_id=123456))["stats"]["vpip"] == 25


async def test_session_performance_path_and_recent_order(monkeypatch):
    calls = []

    async def request(path, params=None):
        calls.append((path, params))
        return {"items": []}

    monkeypatch.setattr(stats.client, "get_json", request)
    await stats.session_performance(123456)
    await stats.sessions(page=2, page_size=10)
    assert calls[0] == ("/api/v1/craft/holdem/sessions/123456/performance", None)
    assert calls[1][1]["Sort"] == "startedAt"
    assert calls[1][1]["Order"] == "desc"
    assert calls[1][1]["Page"] == 2


@pytest.mark.parametrize(
    "kwargs",
    [
        {"game_type": "wrong"},
        {"session_id": 1, "period": "today"},
        {"game_type": "tournament", "channel_ids": [1]},
    ],
)
async def test_invalid_hud_scopes(kwargs):
    with pytest.raises(RunnerPokerError):
        await stats.hud(**kwargs)


@pytest.mark.parametrize("ids", [[], [0], [True], list(range(1, 102))])
def test_channel_ids_validated(ids):
    with pytest.raises(RunnerPokerError):
        stats.scope_params("all", None, None, ids)


async def test_batch_deduplicates_and_preserves_partial_failures(monkeypatch):
    calls = []

    async def request(hand_id):
        calls.append(hand_id)
        if hand_id == 2:
            raise RunnerPokerError("Session expired or access denied.")
        return {"handId": hand_id, "streets": []}

    monkeypatch.setattr(stats.hands, "get_hand", request)
    result = await stats.batch_histories([1, 1, 2])
    assert calls == [1, 2]
    assert result["requested_count"] == 2 and result["returned_count"] == 1
    assert not result["complete"]
    assert result["errors"][0]["hand_id"] == 2


def sample():
    def hand(hand_id, combo, position, net):
        return {
            "hand_id": hand_id,
            "hand_class": combo,
            "net_bb": net,
            "spot": {"pot_type": "three_bet", "hero_reached_river": True},
            "summary": {"hero": {"position": position}},
        }

    return {
        "hands": [
            hand(1, "AA", "BB", -50),
            hand(2, "AA", "BB", 100),
            hand(3, "AKs", "BTN", -20),
            hand(4, None, None, None),
        ],
        "history_exhausted": False,
        "classification_complete": False,
    }


def test_class_aggregate_includes_wins_losses_and_unknowns():
    result = stats.aggregate(sample(), "hand_class", 20)
    groups = {g["group"]: g for g in result["groups"]}
    assert groups["AA"]["net_bb"] == 50
    assert groups["AA"]["sample_bb_per_100"] == 2500
    assert groups["AA"]["wins"] == 1 and groups["AA"]["losses"] == 1
    assert groups["AA"]["below_min_samples"] is True
    assert groups["AA"]["largest_loss_hand_ids"] == [1]
    assert groups["AA"]["largest_win_hand_ids"] == [2]
    assert groups["unknown"]["net_bb"] is None
    assert groups["unknown"]["missing_bb_results"] == 1
    assert result["coverage"]["classification_complete"] is False
    assert "hands" not in result["coverage"]


def test_position_aggregation_has_correct_denominator():
    groups = {g["group"]: g for g in stats.aggregate(sample(), "position", 2)["groups"]}
    assert groups["BB"]["hands"] == 2
    assert groups["BB"]["below_min_samples"] is False
    assert groups["BTN"]["sample_bb_per_100"] == -2000


@pytest.mark.parametrize("group_by", ["position", "hand_class", "pot_type", "river_participation"])
def test_unknown_group_cannot_report_classification_complete(group_by):
    record = {
        "hand_id": 1,
        "hand_class": None,
        "net_bb": -20,
        "spot": {"pot_type": None, "hero_reached_river": None},
        "summary": {"hero": {}},
    }
    result = stats.aggregate(
        {
            "hands": [record],
            "history_exhausted": True,
            "classification_complete": True,
            "unclassified_count": 0,
        },
        group_by,
        20,
    )
    assert result["coverage"]["classification_complete"] is False
    assert result["coverage"]["group_unknown_count"] == 1
    assert result["coverage"]["unclassified_count"] == 1


def test_metric_completeness_is_independent_from_group_completeness():
    record = {
        "hand_id": 1,
        "hand_class": "AA",
        "net_bb": None,
        "spot": {},
        "summary": {"hero": {"position": "BB"}},
    }
    result = stats.aggregate(
        {"hands": [record], "history_exhausted": True, "classification_complete": True},
        "hand_class",
        20,
    )
    assert result["coverage"]["classification_complete"] is True
    assert result["coverage"]["profit_complete"] is False
    assert result["coverage"]["analysis_complete"] is False


@pytest.mark.parametrize("position", ["", "Unknown", "unknown", "—", "-", "미확인"])
def test_upstream_unknown_position_labels_stay_unclassified(position):
    record = {
        "hand_id": 1,
        "hand_class": "AA",
        "net_bb": 5,
        "summary": {"hero": {"position": position}},
        "spot": {},
    }
    result = stats.aggregate({"hands": [record], "history_exhausted": True}, "position", 1)
    assert result["groups"][0]["group"] == "unknown"
    assert not result["coverage"]["classification_complete"]


async def test_aggregate_never_selects_only_losing_hands(monkeypatch):
    async def search(**kwargs):
        assert "result" not in kwargs
        assert kwargs["limit"] == 100
        assert kwargs["pocket_pairs_only"] is True
        return sample()

    monkeypatch.setattr(stats.hands, "search_hands", search)
    result = await stats.summarize_spots(group_by="hand_class", pocket_pairs_only=True)
    assert result["groups"]


@pytest.mark.parametrize("kwargs", [{"group_by": "wrong"}, {"min_samples": 0}])
async def test_invalid_aggregate_before_fetch(kwargs):
    with pytest.raises(RunnerPokerError):
        await stats.summarize_spots(**kwargs)


async def test_summary_and_hud_share_period_and_site_labels(monkeypatch):
    calls = []

    async def request(path, params):
        calls.append((path, params.copy()))
        return {"stats": {"vpip": 0.25}}

    monkeypatch.setattr(stats.client, "get_json", request)
    result = await stats.holdem_summary("today", channel_ids=[3])
    assert calls[0] == ("/api/v1/craft/holdem/summary", {"Period": "today", "ChannelIds": [3]})
    assert calls[1][1] == {"Period": "today", "ChannelIds": [3], "GameType": "holdem"}
    assert result["hud"]["stats"]["vpip"] == 0.25
    assert result["site_terms"]["threeBet"] == "3Bet"
    assert result["site_terms"]["flopCb"] == "플랍 C-bet"


async def test_handrange_uses_no_detail_calls_and_returns_review_ids(monkeypatch):
    async def listing(*args):
        return {
            "items": [
                {
                    "handId": 1,
                    "gameType": "Cash",
                    "hero": {"holeCards": [1, 14], "netDelta": -100},
                    "table": {"blinds": {"bigBlind": 2}},
                },
                {
                    "handId": 2,
                    "gameType": "Cash",
                    "hero": {"holeCards": [1, 27], "netDelta": 200},
                    "table": {"blinds": {"bigBlind": 2}},
                },
            ],
            "hasNext": False,
        }

    async def no_detail(*args):
        pytest.fail("Range aggregates must not call the detail API")

    monkeypatch.setattr(stats.hands, "list_hands", listing)
    monkeypatch.setattr(stats.hands, "get_hand", no_detail)
    result = await stats.hand_range_stats(selected_hands=["AA", "KK"])
    assert result["groups"][0]["group"] == "AA"
    assert result["groups"][0]["net_bb"] == 50
    assert result["matching_hand_ids"] == {"AA": [1, 2], "KK": []}
    assert result["unobserved_hands"] == ["KK"]
    assert result["coverage"]["details_fetched"] == 0
    assert result["coverage"]["classification_complete"] is True


async def test_handrange_cursor_dedup_partial_scope(monkeypatch):
    calls = []

    async def listing(*args):
        calls.append(args[-1])
        return {
            "items": [
                {
                    "handId": 1,
                    "gameType": "Cash",
                    "hero": {"holeCards": [1, 14]},
                    "table": {"blinds": {"bigBlind": 2}},
                }
            ],
            "hasNext": True,
            "nextCursor": "same",
        }

    monkeypatch.setattr(stats.hands, "list_hands", listing)
    result = await stats.hand_range_stats()
    assert calls == [None, "same"]
    assert result["coverage"]["scanned_hands"] == 1
    assert result["coverage"]["stop_reason"] == "invalid_cursor"
    assert result["coverage"]["history_exhausted"] is False
    assert result["coverage"]["classification_complete"] is True
    assert result["coverage"]["profit_complete"] is False
    assert result["coverage"]["analysis_complete"] is False
    assert result["groups"][0]["net_bb"] is None


@pytest.mark.parametrize("selected", [[], ["AK"], ["AAs"], ["KAs"], ["private"], [12]])
async def test_invalid_hand_class_never_fetches(selected):
    with pytest.raises(RunnerPokerError):
        await stats.hand_range_stats(selected_hands=selected)
