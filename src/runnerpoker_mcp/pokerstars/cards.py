"""Craft card ids (1-52) to PokerStars card text."""

from .errors import ConversionError

SUITS = "sdhc"
RANKS = "A23456789TJQK"


def card_text(card: object) -> str:
    if isinstance(card, bool) or not isinstance(card, int) or not 1 <= card <= 52:
        raise ConversionError("Card id must be an integer between 1 and 52.")
    return RANKS[(card - 1) % 13] + SUITS[(card - 1) // 13]


def cards_text(cards: list[int]) -> str:
    return " ".join(card_text(card) for card in cards)


def has_known_cards(cards: object) -> bool:
    """Craft hides unseen hole cards as [0, 0]."""
    return isinstance(cards, list) and len(cards) == 2 and all(c not in (0, None) for c in cards)
