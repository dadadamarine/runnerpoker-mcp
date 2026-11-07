"""Cursor-based history search and conservative local spot classification."""

import math
from datetime import datetime, time, timezone
from typing import Any, Literal
from zoneinfo import ZoneInfo

from . import client
from .auth import Credentials, RunnerPokerError

GameType = Literal["Cash", "Tournament"]
Result = Literal["any", "won", "lost"]
PotType = Literal["any", "three_bet"]
Sort = Literal["recent", "biggest_loss", "biggest_win", "largest_swing"]


def number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value) if math.isfinite(value) else None


def positive_id(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RunnerPokerError("ID must be a positive integer.")
    return value


def big_blind(table: object) -> float | None:
    if not isinstance(table, dict) or not isinstance(table.get("blinds"), dict):
        return None
    return number(table["blinds"].get("bigBlind"))


def hand_class(cards: object) -> str | None:
    # Same card encoding as Craft module 243: suits s,h,d,c; rank 1 is Ace.
    if not isinstance(cards, list) or len(cards) != 2:
        return None
    if any(isinstance(c, bool) or not isinstance(c, int) or not 1 <= c <= 52 for c in cards):
        return None
    if cards[0] == cards[1]:
        return None
    ranks = ["A23456789TJQK"[(c - 1) % 13] for c in cards]
    rank_order = "AKQJT98765432"
    ranks.sort(key=rank_order.index)
    if ranks[0] == ranks[1]:
        return "".join(ranks)
    return "".join(ranks) + ("s" if (cards[0] - 1) // 13 == (cards[1] - 1) // 13 else "o")


async def list_hands(
    game_type: GameType = "Cash",
    session_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    cursor: str | None = None,
    page_size: int = 100,
) -> dict[str, Any]:
    if game_type not in {"Cash", "Tournament"}:
        raise RunnerPokerError("game_type must be Cash or Tournament.")
    if isinstance(page_size, bool) or not isinstance(page_size, int) or not 1 <= page_size <= 100:
        raise RunnerPokerError("page_size must be between 1 and 100.")
    params: dict[str, Any] = {"GameType": game_type, "PageSize": page_size}
    if session_id is not None:
        params["ParticipantId"] = positive_id(session_id)
    if cursor is not None:
        if not isinstance(cursor, str) or not cursor or len(cursor) > 4096:
            raise RunnerPokerError("Invalid cursor.")
        params["Cursor"] = cursor
    if (
        start_date
        and end_date
        and client.validate_date(start_date) > client.validate_date(end_date)
    ):
        raise RunnerPokerError("start_date must not be after end_date.")
    for value, key, boundary in [(start_date, "From", time.min), (end_date, "To", time.max)]:
        if value is not None:
            day = client.validate_date(value)
            instant = datetime.combine(day, boundary, ZoneInfo("Asia/Seoul"))
            params[key] = (
                instant.astimezone(timezone.utc)
                .isoformat(timespec="milliseconds")
                .replace("+00:00", "Z")
            )
    return await client.get_json("/hand-histories", params)


async def get_hand(hand_id: int) -> dict[str, Any]:
    positive_id(hand_id)
    record = await client.get_json(f"/hand-histories/v2/{hand_id}")
    if record.get("handId") != hand_id:
        raise RunnerPokerError("Hand detail ID does not match the requested hand.")
    return record


def classify(detail: dict[str, Any], hero_id: int) -> dict[str, Any]:
    """Unknown/short raises/straddles stay unknown rather than inventing a pot label."""
    result: dict[str, Any] = {
        "pot_type": None,
        "hero_reached_river": None,
        "hero_has_river_action": None,
        "reasons": {"pot_type": "insufficient_preflop_trace", "river": "insufficient_trace"},
    }
    streets = detail.get("streets")
    table = detail.get("table", {})
    if not isinstance(streets, list) or not isinstance(table, dict):
        return result
    actions: dict[str, list[dict]] = {}
    for street in streets:
        if not isinstance(street, dict) or not isinstance(street.get("actions"), list):
            return result
        if any(not isinstance(a, dict) for a in street["actions"]):
            return result
        if any(
            not isinstance(a.get("action"), str)
            or isinstance(a.get("userId"), bool)
            or not isinstance(a.get("userId"), (int, str))
            or a.get("userId") == ""
            for a in street["actions"]
        ):
            result["reasons"]["river"] = "invalid_action_record"
            return result
        stage = street.get("stage")
        if not isinstance(stage, str) or stage not in {"Preflop", "Flop", "Turn", "River"}:
            return result
        if stage in actions:
            return result
        seqs = [a.get("seq") for a in street["actions"]]
        if any(isinstance(s, bool) or not isinstance(s, int) or s < 0 for s in seqs) or len(
            set(seqs)
        ) != len(seqs):
            result["reasons"]["river"] = "invalid_action_sequence"
            return result
        actions[stage] = sorted(street["actions"], key=lambda action: action["seq"])
    preflop = actions.get("Preflop", [])
    bb = big_blind(table)
    if preflop and bb is not None and bb > 0:
        highest, increment, raises = bb, bb, 0
        # A trace starting after the blind posts may omit earlier raises.
        known = any(a.get("action") == "BigBlind" for a in preflop)
        seqs = [a.get("seq") for a in preflop]
        if any(number(s) is None for s in seqs) or len(set(seqs)) != len(seqs):
            known = False
        for action in sorted(preflop, key=lambda a: number(a.get("seq")) or 0):
            name = action.get("action")
            if name in {"Straddle", "PlayableBlind"}:
                known = False
            elif name in {"Raise", "Bet", "AllIn", "Allin"}:
                total = number(action.get("totalBet"))
                if total is None:
                    known = False
                elif total > highest:
                    if total - highest < increment:
                        known = False  # Short all-in / reopening is not inferred.
                    increment, highest, raises = total - highest, total, raises + 1
                elif name in {"Raise", "Bet"}:
                    known = False
            elif name not in {"Fold", "Check", "Call", "SmallBlind", "BigBlind", "Ante"}:
                known = False
        if known:
            result["pot_type"] = (
                "three_bet"
                if raises == 2
                else "four_bet_plus"
                if raises >= 3
                else "single_raised"
                if raises == 1
                else "unraised"
            )
            result["reasons"]["pot_type"] = "counted_full_preflop_raises"
            result["preflop_full_raise_count"] = raises
        else:
            result["reasons"]["pot_type"] = "incomplete_or_unsupported_preflop_trace"
    players = detail.get("players", [])
    board = table.get("board")
    if (
        not isinstance(players, list)
        or not any(isinstance(p, dict) and str(p.get("userId")) == str(hero_id) for p in players)
        or not isinstance(board, list)
        or len(board) not in {0, 3, 4, 5}
        or any(isinstance(c, bool) or not isinstance(c, int) or not 1 <= c <= 52 for c in board)
        or len(set(board)) != len(board)
    ):
        result["reasons"]["river"] = "missing_hero_or_invalid_board"
        return result
    hero_actions = [
        (stage, action)
        for stage in ["Preflop", "Flop", "Turn", "River"]
        for action in actions.get(stage, [])
        if str(action.get("userId")) == str(hero_id)
    ]
    decisions = {"Fold", "Check", "Call", "Bet", "Raise", "AllIn", "Allin"}
    hero_river = [
        a for stage, a in hero_actions if stage == "River" and a.get("action") in decisions
    ]
    terminal_seen = False
    for _, action in hero_actions:
        if terminal_seen:
            result["reasons"]["river"] = "contradictory_actions_after_fold_or_allin"
            return result
        terminal_seen = action.get("action") in {"Fold", "AllIn", "Allin"}
    earlier = [(stage, a) for stage, a in hero_actions if stage != "River"]
    folded = any(a.get("action") == "Fold" for _, a in earlier)
    allin = any(a.get("action") in {"AllIn", "Allin"} for _, a in earlier)
    if hero_river and len(board) < 5:
        result["reasons"]["river"] = "river_action_without_river_board"
    elif folded or len(board) < 5:
        result.update(hero_reached_river=False, hero_has_river_action=False)
        result["reasons"]["river"] = (
            "hero_folded_before_river" if folded else "board_ended_before_river"
        )
    elif hero_river:
        result.update(hero_reached_river=True, hero_has_river_action=True)
        result["reasons"]["river"] = "explicit_hero_river_action"
    elif allin:
        result.update(hero_reached_river=True, hero_has_river_action=False)
        result["reasons"]["river"] = "explicit_hero_allin_with_river_runout"
    else:
        result["reasons"]["river"] = "no_positive_hero_river_evidence"
    return result


def net_bb(hand: dict) -> float | None:
    if hand.get("gameType") != "Cash":
        return None  # Tournament chips are not cash win-rate.
    hero, table = hand.get("hero"), hand.get("table")
    if not isinstance(hero, dict) or not isinstance(table, dict):
        return None
    delta = number(hero.get("netDelta"))
    bb = big_blind(table)
    return delta / bb if delta is not None and bb is not None and bb > 0 else None


async def search_hands(
    game_type: GameType = "Cash",
    session_id: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    pocket_pairs_only: bool = False,
    pot_type: PotType = "any",
    reached_river: bool | None = None,
    result: Result = "any",
    min_abs_net_bb: float = 0,
    sort: Sort = "recent",
    max_pages: int = 3,
    max_details: int = 30,
    limit: int = 20,
) -> dict[str, Any]:
    if pot_type not in {"any", "three_bet"} or result not in {"any", "won", "lost"}:
        raise RunnerPokerError("Unsupported pot_type or result filter.")
    if sort not in {"recent", "biggest_loss", "biggest_win", "largest_swing"}:
        raise RunnerPokerError("Unsupported sort.")
    for value, maximum in [(max_pages, 20), (max_details, 100), (limit, 100)]:
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= maximum:
            raise RunnerPokerError("Invalid search budget or result limit.")
    threshold = number(min_abs_net_bb)
    if threshold is None or threshold < 0:
        raise RunnerPokerError("min_abs_net_bb must be finite and nonnegative.")
    if game_type != "Cash" and (threshold > 0 or sort != "recent"):
        raise RunnerPokerError("BB profit thresholds and profit sorting require Cash.")
    hero_id = Credentials.load().user_seq
    seen: set[int] = set()
    matches, unknown = [], []
    cursor, exhausted, detail_count, scanned, eligible, pages = None, False, 0, 0, 0, 0
    stop_reason = "page_budget"
    for _ in range(max_pages):
        page = await list_hands(game_type, session_id, start_date, end_date, cursor)
        pages += 1
        items, has_next = page.get("items"), page.get("hasNext")
        if not isinstance(items, list) or not isinstance(has_next, bool):
            raise RunnerPokerError("Unexpected hand pagination response.")
        for hand in items:
            if not isinstance(hand, dict):
                raise RunnerPokerError("Unexpected hand record shape.")
            hand_id = positive_id(hand.get("handId"))
            if hand_id in seen:
                continue
            seen.add(hand_id)
            scanned += 1
            hero = hand.get("hero", {})
            if not isinstance(hero, dict):
                raise RunnerPokerError("Unexpected hero record shape.")
            combo = hand_class(hero.get("holeCards"))
            bb = net_bb(hand)
            delta = number(hero.get("netDelta"))
            if pocket_pairs_only and combo is None:
                unknown.append({"hand_id": hand_id, "reason": "unknown_hole_cards"})
                continue
            if pocket_pairs_only and len(combo) != 2:
                continue
            if (
                result == "lost"
                and delta is not None
                and delta >= 0
                or result == "won"
                and delta is not None
                and delta <= 0
            ):
                continue
            if result != "any" and delta is None or threshold > 0 and bb is None:
                unknown.append({"hand_id": hand_id, "reason": "unknown_profit"})
                continue
            if threshold > 0 and abs(bb) < threshold:
                continue
            eligible += 1
            if detail_count >= max_details:
                unknown.append({"hand_id": hand_id, "reason": "detail_budget"})
                continue
            detail_count += 1
            detail = await get_hand(hand_id)
            if detail.get("handId") != hand_id:
                raise RunnerPokerError("Hand detail ID does not match the requested hand.")
            spot = classify(detail, hero_id)
            if pot_type != "any" and spot["pot_type"] is None:
                unknown.append({"hand_id": hand_id, "reason": "unknown_pot_type"})
                continue
            if pot_type != "any" and spot["pot_type"] != pot_type:
                continue
            if reached_river is not None and spot["hero_reached_river"] is None:
                unknown.append({"hand_id": hand_id, "reason": "unknown_river_participation"})
                continue
            if reached_river is not None and spot["hero_reached_river"] != reached_river:
                continue
            matches.append(
                {
                    "hand_id": hand_id,
                    "hand_class": combo,
                    "net_bb": bb,
                    "spot": spot,
                    "summary": hand,
                    "detail": detail,
                }
            )
        if not has_next:
            exhausted, stop_reason = True, "history_exhausted"
            break
        next_cursor = page.get("nextCursor")
        if next_cursor is None or str(next_cursor) == cursor or str(next_cursor) == "":
            stop_reason = "invalid_cursor"
            break
        cursor = str(next_cursor)
        if detail_count >= max_details:
            stop_reason = "detail_budget"
            break
    # Sort only the reviewed sample; never call this a global worst-hands ranking.
    if sort != "recent":
        missing = [m for m in matches if m["net_bb"] is None]
        unknown.extend({"hand_id": m["hand_id"], "reason": "unknown_profit"} for m in missing)
        matches = [m for m in matches if m["net_bb"] is not None]
        matches.sort(
            key=lambda m: abs(m["net_bb"]) if sort == "largest_swing" else m["net_bb"],
            reverse=sort in {"biggest_win", "largest_swing"},
        )
    return {
        "hands": matches[:limit],
        "matches_in_reviewed_sample": len(matches),
        "scanned_hands": scanned,
        "candidate_hands": eligible,
        "pages_fetched": pages,
        "details_fetched": detail_count,
        "history_exhausted": exhausted,
        "classification_complete": exhausted and not unknown,
        "stop_reason": stop_reason,
        "unclassified_count": len(unknown),
        "filter_unknown_count": len(unknown),
        "unclassified_sample": unknown[:20],
        "results_truncated": len(matches) > limit,
        "scope_note": "Ranked within scanned/reviewed sample only. Recent order is upstream order; "
        "not independently verified. Increase date/session specificity or budgets. "
        "Do not infer strategic mistakes or EV loss from realized losses. "
        "River participation includes all-in runouts; see hero_has_river_action.",
    }
