"""LLM-facing tools exercised over real MCP messages and mocked HTTP responses."""

import httpx
import pytest


async def call(session, name, arguments=None):
    result = await session.call_tool(name, arguments or {})
    assert not result.isError, result.content
    assert isinstance(result.structuredContent, dict)
    return result.structuredContent


@pytest.mark.parametrize(
    "tool,args,key",
    [
        ("auth_status", {}, "configured"),
        ("get_timeline", {}, "performance"),
        ("get_timeline_day", {"day": "2026-11-07"}, "items"),
        ("list_hand_histories", {"session_id": 123456}, "items"),
        ("get_hand_history", {"hand_id": 101}, "streets"),
        ("search_review_hands", {}, "hands"),
        ("get_hand_histories", {"hand_ids": [101, 102]}, "hands"),
        ("list_holdem_sessions", {}, "items"),
        ("get_session_performance", {"session_id": 123456}, "stackTrend"),
        ("get_position_stats", {}, "items"),
        ("get_holdem_summary", {}, "hud"),
        ("get_hand_range_stats", {}, "groups"),
        ("get_hud_stats", {}, "stats"),
        ("summarize_review_spots", {}, "groups"),
    ],
)
async def test_every_tool_through_mcp_http_and_serialization(mcp_session, tool, args, key):
    assert key in await call(mcp_session, tool, args)


async def test_pocket_three_bet_losses_exclude_four_bet_and_nonpairs(mcp_session, fixture_api):
    result = await call(
        mcp_session,
        "search_review_hands",
        {
            "session_id": 123456,
            "pocket_pairs_only": True,
            "pot_type": "three_bet",
            "result": "lost",
            "reached_river": True,
        },
    )
    assert [hand["hand_id"] for hand in result["hands"]] == [101]
    hand = result["hands"][0]
    assert hand["hand_class"] == "AA" and hand["net_bb"] == -16
    assert hand["spot"]["reasons"]["river"] == "explicit_hero_river_action"
    assert hand["detail"]["streets"][-1]["actions"][-1]["action"] == "Fold"
    assert result["scanned_hands"] == 5  # Cross-page duplicate 103 removed.
    assert result["history_exhausted"] is True
    assert result["filter_unknown_count"] == 1  # Hidden hole cards cannot be guessed.
    listings = [r for r in fixture_api.requests if r.url.path == "/hand-histories"]
    assert len(listings) == 2
    assert all(r.url.params["ParticipantId"] == "123456" for r in listings)
    assert listings[1].url.params["Cursor"] == "fixture-page-2"


async def test_river_search_includes_allin_runout_and_not_early_fold(mcp_session):
    result = await call(mcp_session, "search_review_hands", {"reached_river": True})
    records = {hand["hand_id"]: hand for hand in result["hands"]}
    assert set(records) == {101, 102, 104}
    assert records[104]["spot"]["hero_has_river_action"] is False
    assert records[104]["spot"]["reasons"]["river"] == "explicit_hero_allin_with_river_runout"
    assert records[102]["spot"]["hero_has_river_action"] is True


@pytest.mark.parametrize(
    "filters,expected",
    [
        ({"result": "won", "sort": "biggest_win", "min_abs_net_bb": 20}, [104, 102]),
        ({"result": "lost", "sort": "biggest_loss", "min_abs_net_bb": 15}, [103, 101]),
        ({"sort": "largest_swing", "limit": 2}, [103, 104]),
    ],
)
async def test_profit_search_and_sort(mcp_session, filters, expected):
    result = await call(mcp_session, "search_review_hands", filters)
    assert [hand["hand_id"] for hand in result["hands"]] == expected


async def test_handrange_totals_include_both_outcomes_and_fetch_review_records(
    mcp_session,
    fixture_api,
):
    result = await call(mcp_session, "get_hand_range_stats", {"selected_hands": ["AA", "KK"]})
    groups = {g["group"]: g for g in result["groups"]}
    assert groups["AA"]["net_bb"] == 6
    assert groups["AA"]["hands"] == 2
    assert groups["AA"]["sample_bb_per_100"] == 300
    assert groups["KK"]["net_bb"] == -25
    assert result["matching_hand_ids"] == {"AA": [101, 102], "KK": [103]}
    assert all(r.url.path == "/hand-histories" for r in fixture_api.requests)
    records = await call(
        mcp_session, "get_hand_histories", {"hand_ids": result["matching_hand_ids"]["AA"]}
    )
    assert records["complete"] is True
    assert [h["handId"] for h in records["hands"]] == [101, 102]
    assert records["hands"][0]["players"][1]["holeCards"] == []


async def test_position_scope_dates_channels_and_unchanged_rates(mcp_session, fixture_api):
    result = await call(
        mcp_session,
        "get_position_stats",
        {
            "period": "custom",
            "start_date": "2026-11-01",
            "end_date": "2026-11-07",
            "channel_ids": [3, 4],
            "selected_positions": ["bb", "BTN"],
        },
    )
    assert [r["position"] for r in result["items"]] == ["BB", "BTN"]
    assert result["items"][0]["bb100"] == -1600
    assert result["items"][0]["evBb100"] is None
    query = fixture_api.requests[0].url.params
    assert query["Period"] == "custom" and query["From"] == "2026-11-01"
    assert query.get_list("ChannelIds") == ["3", "4"]


async def test_summary_hud_site_terms_and_denominators(mcp_session):
    result = await call(mcp_session, "get_holdem_summary", {"period": "today"})
    assert result["hud"]["stats"]["vpip"] == 0.6
    assert result["hud"]["handCount"] == 5
    assert result["site_terms"]["threeBet"] == "3Bet"
    assert result["site_terms"]["flopCb"] == "플랍 C-bet"
    assert result["summary"]["evBb100"] is None


async def test_session_to_hands_and_exact_date_conversion(mcp_session, fixture_api):
    sessions = await call(mcp_session, "list_holdem_sessions", {"period": "today"})
    session_id = sessions["items"][0]["sessionId"]
    await call(mcp_session, "get_session_performance", {"session_id": session_id})
    await call(mcp_session, "get_hud_stats", {"session_id": session_id})
    await call(
        mcp_session,
        "list_hand_histories",
        {"session_id": session_id, "start_date": "2026-11-07", "end_date": "2026-11-07"},
    )
    hud = next(r for r in fixture_api.requests if r.url.path.endswith("/hud"))
    assert hud.url.params.get_list("ParticipantIds") == [str(session_id)]
    query = fixture_api.requests[-1].url.params
    assert query["From"] == "2026-11-06T15:00:00.000Z"
    assert query["To"] == "2026-11-07T14:59:59.999Z"


async def test_unknown_group_never_reports_complete_analysis(mcp_session):
    result = await call(mcp_session, "summarize_review_spots", {"group_by": "pot_type"})
    groups = {g["group"]: g for g in result["groups"]}
    assert groups["three_bet"]["hands"] == 1
    assert groups["unknown"]["hands"] == 1
    assert result["coverage"]["history_exhausted"] is True
    assert result["coverage"]["group_unknown_count"] == 1
    assert result["coverage"]["classification_complete"] is False
    assert result["coverage"]["profit_complete"] is False
    assert result["coverage"]["analysis_complete"] is False


async def test_budget_limit_and_output_truncation_are_explicit(mcp_session):
    limited = await call(mcp_session, "search_review_hands", {"max_details": 1})
    assert limited["details_fetched"] == 1 and not limited["history_exhausted"]
    assert limited["stop_reason"] == "detail_budget"
    truncated = await call(mcp_session, "search_review_hands", {"limit": 1})
    assert len(truncated["hands"]) == 1 and truncated["results_truncated"] is True


@pytest.mark.parametrize("status", [302, 401, 403, 404, 429, 500])
async def test_http_error_becomes_safe_mcp_error(mcp_session, fixture_api, status):
    fixture_api.overrides["/api/v1/craft/timeline"] = httpx.Response(
        status, text="DO_NOT_ECHO_fixture-token", headers={"Location": "https://example.com"}
    )
    result = await mcp_session.call_tool("get_timeline", {})
    assert result.isError
    assert "DO_NOT_ECHO" not in result.content[0].text
    assert "fixture-token" not in result.content[0].text
    assert len(fixture_api.requests) == 1  # No redirects or hidden retries.


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="invalid JSON"),
        httpx.Response(200, json=[1, 2]),
        httpx.Response(200, json={"code": 4001, "message": "DO_NOT_ECHO"}),
    ],
)
async def test_invalid_json_root_and_application_error(mcp_session, fixture_api, response):
    fixture_api.overrides["/api/v1/craft/timeline"] = response
    result = await mcp_session.call_tool("get_timeline", {})
    assert result.isError
    assert "DO_NOT_ECHO" not in result.content[0].text


@pytest.mark.parametrize(
    "payload", [{}, {"items": None}, {"items": [1]}, {"items": [], "hasNext": "false"}]
)
async def test_bad_hand_page_shape_is_not_empty_success(mcp_session, fixture_api, payload):
    fixture_api.overrides["/hand-histories"] = payload
    result = await mcp_session.call_tool("search_review_hands", {})
    assert result.isError


@pytest.mark.parametrize("payload", [{}, {"items": None}, {"items": [1]}])
async def test_bad_position_response_shape(mcp_session, fixture_api, payload):
    fixture_api.overrides["/api/v1/craft/holdem/positions"] = payload
    assert (await mcp_session.call_tool("get_position_stats", {})).isError


async def test_partial_batch_failure_and_id_mismatch(mcp_session, fixture_api):
    fixture_api.overrides["/hand-histories/v2/102"] = {"handId": 999}
    result = await call(mcp_session, "get_hand_histories", {"hand_ids": [101, 102, 101]})
    assert result["requested_count"] == 2 and result["returned_count"] == 1
    assert result["complete"] is False and result["errors"][0]["hand_id"] == 102


async def test_other_players_cannot_create_hero_river_participation(mcp_session, fixture_api):
    detail = fixture_api.data["hand_details"]["101"]
    for street in detail["streets"]:
        street["actions"] = [{"seq": 1, "userId": 7, "action": "Check"}]
    result = await call(mcp_session, "search_review_hands", {"reached_river": True})
    assert 101 not in [hand["hand_id"] for hand in result["hands"]]
    assert any(
        r["hand_id"] == 101 and r["reason"] == "unknown_river_participation"
        for r in result["unclassified_sample"]
    )


@pytest.mark.parametrize(
    "bad_action",
    [
        None,
        {"seq": 1},
        {"seq": 1, "userId": 42, "action": {}},
        {"seq": 1, "userId": None, "action": "Check"},
    ],
)
async def test_bad_action_record_stays_unknown_not_positive_river(
    mcp_session,
    fixture_api,
    bad_action,
):
    fixture_api.data["hand_details"]["101"]["streets"][-1]["actions"] = [bad_action]
    result = await call(mcp_session, "search_review_hands", {"reached_river": True})
    assert 101 not in [h["hand_id"] for h in result["hands"]]
    assert any(r["hand_id"] == 101 for r in result["unclassified_sample"])


@pytest.mark.parametrize("payload", [{}, {"handId": 999}, {"handId": "101"}])
async def test_single_hand_id_mismatch_is_not_success(mcp_session, fixture_api, payload):
    fixture_api.overrides["/hand-histories/v2/101"] = payload
    assert (await mcp_session.call_tool("get_hand_history", {"hand_id": 101})).isError


async def test_network_timeout_is_safe_protocol_error(mcp_session, fixture_api):
    fixture_api.overrides["/api/v1/craft/timeline"] = httpx.ReadTimeout("DO_NOT_ECHO_fixture-token")
    result = await mcp_session.call_tool("get_timeline", {})
    assert result.isError
    assert "network request failed" in result.content[0].text
    assert "fixture-token" not in result.content[0].text


@pytest.mark.parametrize(
    "tool,args",
    [
        (
            "get_position_stats",
            {"period": "custom", "start_date": "2026-02-30", "end_date": "2026-11-07"},
        ),
        (
            "get_position_stats",
            {"period": "custom", "start_date": "2026-11-07", "end_date": "2026-11-01"},
        ),
        ("get_hand_histories", {"hand_ids": []}),
        ("get_hand_history", {"hand_id": -1}),
        ("search_review_hands", {"max_details": 0}),
        ("get_hand_range_stats", {"selected_hands": ["KAs"]}),
    ],
)
async def test_invalid_inputs_never_reach_http(mcp_session, fixture_api, tool, args):
    assert (await mcp_session.call_tool(tool, args)).isError
    assert fixture_api.requests == []


async def test_duplicate_cursor_is_reported_without_infinite_fetch(mcp_session, fixture_api):
    fixture_api.data["hand_pages"][1]["hasNext"] = True
    fixture_api.data["hand_pages"][1]["nextCursor"] = "fixture-page-2"
    result = await call(mcp_session, "get_hand_range_stats", {"max_pages": 20})
    assert result["coverage"]["stop_reason"] == "invalid_cursor"
    assert not result["coverage"]["history_exhausted"]
    assert not result["coverage"]["analysis_complete"]
    assert len(fixture_api.requests) == 2
