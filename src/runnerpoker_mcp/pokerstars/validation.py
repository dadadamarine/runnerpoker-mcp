"""Record checks that mirror locktree's PokerStars export validation."""

from typing import Any

from .cards import card_text
from .errors import ConversionError


def validate_cards(board: list[int], players: list[dict[str, Any]], hero_id: int | None) -> None:
    """Hero shows 0 or 2 hole cards, and no card appears twice among everything revealed."""
    known_cards = [card_text(card) for card in board]
    for player in players:
        revealed = [card for card in player.get("holeCards") or [] if card not in (0, None)]
        is_hero = hero_id is not None and str(player["userId"]) == str(hero_id)
        if is_hero and len(revealed) not in (0, 2):
            raise ConversionError(f"Hero must have 0 or 2 hole cards, got {len(revealed)}.")
        if len(revealed) == 2:
            known_cards += [card_text(card) for card in revealed]
    duplicates = sorted({card for card in known_cards if known_cards.count(card) > 1})
    if duplicates:
        raise ConversionError(f"Duplicate cards in hand record: {' '.join(duplicates)}.")


def export_warnings(record: dict[str, Any]) -> list[str]:
    """Non-blocking findings. locktree rejects a button that is not the seat before the small
    blind, but Craft hands with an empty button seat (dead button) are real, so only warn."""
    try:
        small_blind = next(
            a
            for street in record["streets"]
            for a in street["actions"]
            if a["action"] == "SmallBlind"
        )
        seats = sorted(p["seat"] for p in record["players"])
        small_blind_seat = next(
            p["seat"] for p in record["players"] if p["userId"] == small_blind["userId"]
        )
        index = seats.index(small_blind_seat)
        expected = small_blind_seat if len(seats) == 2 else seats[index - 1]
        button = record["table"]["buttonSeat"]
    except (KeyError, TypeError, StopIteration):
        return []
    if expected == button:
        return []
    return [
        f"button-blind-mismatch: button is seat {button + 1}, but the seat before the small "
        f"blind is seat {expected + 1}."
    ]
