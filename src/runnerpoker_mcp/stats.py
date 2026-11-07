"""Verified Craft analytics endpoints and sample-scoped review aggregates."""

import re
from collections import defaultdict
from typing import Any, Literal

from . import client, hands
from .auth import RunnerPokerError

GroupBy = Literal["position", "hand_class", "pot_type", "river_participation"]

SITE_TERMS = {
    "vpip": "VPIP",
    "pfr": "PFR",
    "threeBet": "3Bet",
    "flopCb": "플랍 C-bet",
    "riverWtsd": "WTSD",
    "riverWsd": "WSD",
    "bb100": "BB/100",
    "evBb100": "EV BB/100",
    "profit": "손익",
    "hands": "핸드",
    "position": "포지션",
    "hand_class": "핸드 레인지 분석",
    "unknown": "미확인",
    "net_bb": "손익 (BB)",
    "sample_bb_per_100": "BB/100",
    "below_min_samples": "표본 부족",
}


async def holdem_summary(
    period: client.Period = "thisMonth",
    start_date: str | None = None,
    end_date: str | None = None,
    channel_ids: list[int] | None = None,
) -> dict[str, Any]:
    params = scope_params(period, start_date, end_date, channel_ids)
    summary = await client.get_json("/api/v1/craft/holdem/summary", params)
    hud_params = {**params, "GameType": "holdem"}
    hud_data = await client.get_json("/api/v1/craft/hud", hud_params)
    return {
        "scope": params,
        "summary": summary,
        "hud": hud_data,
        "site_terms": SITE_TERMS,
        "metric_note": "Use the site's labels. HUD values are returned unchanged; "
        "the site displays 0–1 ratios as percentages. Do not rescale twice. "
        "EV BB/100 is the upstream metric, not a solver evaluation. "
        "When ChannelIds is absent no explicit channel selection is sent; "
        "the site's current channel selection may differ.",
    }


def scope_params(
    period: client.Period,
    start_date: str | None,
    end_date: str | None,
    channel_ids: list[int] | None = None,
) -> dict[str, Any]:
    params = client.timeline_params(period, start_date, end_date, 1, 10)
    del params["Page"], params["PageSize"]
    if channel_ids is not None:
        if not 1 <= len(channel_ids) <= 100:
            raise RunnerPokerError("channel_ids must contain between 1 and 100 IDs.")
        params["ChannelIds"] = list(dict.fromkeys(hands.positive_id(i) for i in channel_ids))
    return params


async def session_performance(session_id: int) -> dict[str, Any]:
    return await client.get_json(
        f"/api/v1/craft/holdem/sessions/{hands.positive_id(session_id)}/performance"
    )


async def sessions(
    period: client.Period = "thisMonth",
    start_date: str | None = None,
    end_date: str | None = None,
    channel_ids: list[int] | None = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    # This key and order are Craft's own default session listing.
    params = client.timeline_params(period, start_date, end_date, page, page_size)
    params.update(scope_params(period, start_date, end_date, channel_ids))
    params.update(Sort="startedAt", Order="desc")
    return await client.get_json("/api/v1/craft/holdem/sessions", params)


async def positions(
    period: client.Period = "thisMonth",
    start_date: str | None = None,
    end_date: str | None = None,
    channel_ids: list[int] | None = None,
    selected_positions: list[str] | None = None,
) -> dict[str, Any]:
    if selected_positions is not None and (
        not selected_positions
        or len(selected_positions) > 20
        or any(not isinstance(p, str) or not p or len(p) > 20 for p in selected_positions)
    ):
        raise RunnerPokerError("selected_positions must contain 1–20 position labels.")
    params = scope_params(period, start_date, end_date, channel_ids)
    payload = await client.get_json("/api/v1/craft/holdem/positions", params)
    items = payload.get("items")
    if not isinstance(items, list) or any(not isinstance(row, dict) for row in items):
        raise RunnerPokerError("Unexpected position stats response.")
    wanted = {p.upper() for p in selected_positions} if selected_positions else None
    rows = [row for row in items if wanted is None or str(row.get("position")).upper() in wanted]
    available = {str(row.get("position")).upper() for row in items}
    return {
        "scope": params,
        "items": rows,
        "unavailable_positions": sorted(wanted - available) if wanted else [],
        "upstream": payload,
        "metric_note": "Keep upstream metric units and denominators. bb100 is a rate, "
        "not total profit. Missing fields are not zero; no total profit "
        "or solver EV is inferred from rounded rates.",
    }


async def hud(
    game_type: Literal["holdem", "tournament"] = "holdem",
    session_id: int | None = None,
    period: client.Period = "thisMonth",
    start_date: str | None = None,
    end_date: str | None = None,
    channel_ids: list[int] | None = None,
) -> dict[str, Any]:
    if game_type not in {"holdem", "tournament"}:
        raise RunnerPokerError("HUD game_type must be holdem or tournament.")
    if game_type == "tournament" and channel_ids is not None:
        raise RunnerPokerError("channel_ids are supported for holdem only.")
    if session_id is not None:
        if period != "thisMonth" or start_date is not None or end_date is not None or channel_ids:
            raise RunnerPokerError("Session HUD cannot be combined with period/channel filters.")
        params = {"GameType": game_type, "ParticipantIds": [hands.positive_id(session_id)]}
    else:
        params = scope_params(period, start_date, end_date, channel_ids)
        params["GameType"] = game_type
    return await client.get_json("/api/v1/craft/hud", params)


async def batch_histories(hand_ids: list[int]) -> dict[str, Any]:
    if not 1 <= len(hand_ids) <= 30:
        raise RunnerPokerError("Provide between 1 and 30 hand IDs.")
    ids = list(dict.fromkeys(hands.positive_id(i) for i in hand_ids))
    records, errors = [], []
    for hand_id in ids:
        try:
            record = await hands.get_hand(hand_id)
            if record.get("handId") != hand_id:
                raise RunnerPokerError("Hand detail ID mismatch.")
            records.append(record)
        except RunnerPokerError as error:
            errors.append({"hand_id": hand_id, "error": str(error)})
    return {
        "hands": records,
        "errors": errors,
        "complete": not errors,
        "requested_count": len(ids),
        "returned_count": len(records),
    }


def aggregate(sample: dict[str, Any], group_by: GroupBy, min_samples: int) -> dict[str, Any]:
    if group_by not in {"position", "hand_class", "pot_type", "river_participation"}:
        raise RunnerPokerError("Unsupported grouping.")
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 1:
        raise RunnerPokerError("min_samples must be a positive integer.")
    groups: dict[str, list[dict]] = defaultdict(list)
    for hand in sample["hands"]:
        if group_by == "position":
            key = hand["summary"].get("hero", {}).get("position")
        elif group_by == "hand_class":
            key = hand["hand_class"]
        elif group_by == "pot_type":
            key = hand["spot"]["pot_type"]
        else:
            key = hand["spot"]["hero_reached_river"]
        groups[str(key) if key is not None else "unknown"].append(hand)
    rows = []
    for label, records in groups.items():
        valid = [record for record in records if record["net_bb"] is not None]
        net = sum(record["net_bb"] for record in valid) if valid else None
        examples = sorted(valid, key=lambda record: record["net_bb"])
        rows.append(
            {
                "group": label,
                "hands": len(records),
                "hands_with_bb_result": len(valid),
                "missing_bb_results": len(records) - len(valid),
                "net_bb": net,
                "sample_bb_per_100": net / len(valid) * 100 if valid else None,
                "below_min_samples": len(valid) < min_samples,
                "wins": sum(r["net_bb"] > 0 for r in valid),
                "losses": sum(r["net_bb"] < 0 for r in valid),
                "breakeven": sum(r["net_bb"] == 0 for r in valid),
                "largest_loss_hand_ids": [r["hand_id"] for r in examples if r["net_bb"] < 0][:3],
                "largest_win_hand_ids": [
                    r["hand_id"] for r in reversed(examples) if r["net_bb"] > 0
                ][:3],
            }
        )
    rows.sort(
        key=lambda row: (row["net_bb"] is None, row["net_bb"] if row["net_bb"] is not None else 0)
    )
    coverage = {key: value for key, value in sample.items() if key != "hands"}
    return {
        "group_by": group_by,
        "groups": rows,
        "coverage": coverage,
        "site_terms": SITE_TERMS,
        "minimum_samples": min_samples,
        "analysis_note": "Realized results for the reviewed sample only, not proof of a leak "
        "or solver EV. Groups below minimum samples remain visible and flagged. "
        "Filtered-spot BB/100 is conditional, not overall win rate. Missing "
        "results are excluded from its denominator; unknown groups stay visible. "
        "Use get_hand_histories for the example hand IDs to review decisions.",
    }


async def summarize_spots(
    group_by: GroupBy = "position",
    session_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    pocket_pairs_only: bool = False,
    pot_type: hands.PotType = "any",
    reached_river: bool | None = None,
    max_pages: int = 3,
    max_details: int = 100,
    min_samples: int = 20,
) -> dict[str, Any]:
    # No win/loss filter: include both sides so aggregates are not loss-selected.
    if group_by not in {"position", "hand_class", "pot_type", "river_participation"}:
        raise RunnerPokerError("Unsupported grouping.")
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 1:
        raise RunnerPokerError("min_samples must be a positive integer.")
    sample = await hands.search_hands(
        session_id=session_id,
        start_date=start_date,
        end_date=end_date,
        pocket_pairs_only=pocket_pairs_only,
        pot_type=pot_type,
        reached_river=reached_river,
        max_pages=max_pages,
        max_details=max_details,
        limit=100,
    )
    return aggregate(sample, group_by, min_samples)


async def hand_range_stats(
    selected_hands: list[str] | None = None,
    session_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    max_pages: int = 3,
    min_samples: int = 20,
) -> dict[str, Any]:
    """Mirror handrange: classify and aggregate summaries without detail requests."""
    if isinstance(max_pages, bool) or not isinstance(max_pages, int) or not 1 <= max_pages <= 20:
        raise RunnerPokerError("max_pages must be between 1 and 20.")
    if isinstance(min_samples, bool) or not isinstance(min_samples, int) or min_samples < 1:
        raise RunnerPokerError("min_samples must be a positive integer.")
    if selected_hands is not None:
        if not selected_hands or len(selected_hands) > 169:
            raise RunnerPokerError("selected_hands must contain 1–169 canonical hands.")
        ranks = "AKQJT98765432"
        for label in selected_hands:
            valid = isinstance(label, str) and re.fullmatch(r"[AKQJT2-9]{2}[so]?", label)
            if (
                not valid
                or len(label) == 2
                and label[0] != label[1]
                or len(label) == 3
                and ranks.index(label[0]) >= ranks.index(label[1])
            ):
                raise RunnerPokerError("Use canonical hands such as AA, AKs, AKo, 22.")
    records, seen, cursors = [], set(), set()
    cursor, exhausted, pages = None, False, 0
    stop_reason = "page_budget"
    for _ in range(max_pages):
        page = await hands.list_hands("Cash", session_id, start_date, end_date, cursor)
        pages += 1
        if not isinstance(page.get("items"), list) or not isinstance(page.get("hasNext"), bool):
            raise RunnerPokerError("Unexpected hand pagination response.")
        for record in page["items"]:
            if not isinstance(record, dict) or not isinstance(record.get("hero"), dict):
                raise RunnerPokerError("Unexpected hand record shape.")
            hand_id = hands.positive_id(record.get("handId"))
            if hand_id in seen:
                continue
            seen.add(hand_id)
            records.append(
                {
                    "hand_id": hand_id,
                    "hand_class": hands.hand_class(record["hero"].get("holeCards")),
                    "net_bb": hands.net_bb(record),
                    "summary": record,
                    "spot": {"pot_type": None, "hero_reached_river": None},
                }
            )
        if not page["hasNext"]:
            exhausted, stop_reason = True, "history_exhausted"
            break
        next_cursor = page.get("nextCursor")
        if next_cursor is None or not str(next_cursor) or str(next_cursor) in cursors:
            stop_reason = "invalid_cursor"
            break
        cursor = str(next_cursor)
        cursors.add(cursor)
    unknown = sum(r["hand_class"] is None or r["net_bb"] is None for r in records)
    sample = {
        "hands": records,
        "scanned_hands": len(records),
        "pages_fetched": pages,
        "history_exhausted": exhausted,
        "classification_complete": exhausted and not unknown,
        "stop_reason": stop_reason,
        "unclassified_count": unknown,
        "details_fetched": 0,
    }
    result = aggregate(sample, "hand_class", min_samples)
    available = {row["group"] for row in result["groups"]}
    if selected_hands is not None:
        wanted = set(selected_hands)
        result["groups"] = [g for g in result["groups"] if g["group"] in wanted]
        result["unobserved_hands"] = sorted(wanted - available)
        result["matching_hand_ids"] = {
            label: [r["hand_id"] for r in records if r["hand_class"] == label]
            for label in sorted(wanted)
        }
    result["site_label"] = "핸드 레인지 분석"
    result["scope"] = {
        "session_id": session_id,
        "start_date": start_date,
        "end_date": end_date,
        "game_type": "Cash",
    }
    return result
