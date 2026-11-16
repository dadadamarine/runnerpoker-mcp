import json
import re
from copy import deepcopy
from pathlib import Path

import pytest

from runnerpoker_mcp.pokerstars import ConversionError, export_warnings, to_pokerstars
from runnerpoker_mcp.pokerstars.cards import card_text
from runnerpoker_mcp.pokerstars.converter import player_names

HERO_ID = 9396
FIXTURES = Path(__file__).parent / "fixtures"
HAND = json.loads((FIXTURES / "hand_2986858.json").read_text("utf-8"))

EXPECTED_CHIPS = """\
PokerStars Hand #2986858: Hold'em No Limit (5000000/10000000) - 2026/11/16 03:19:08 CET
Table 'RunnerPoker 마스터 2006 5' 6-max Seat #3 is the button
Seat 1: 런하니 (1000000000 in chips)
Seat 2: 김정진 (1000000000 in chips)
Seat 3: Hero (815376555 in chips)
Seat 4: 비질게 (1000000000 in chips)
Seat 5: 네이든 (1000000000 in chips)
Seat 6: 물고기 (1000000000 in chips)
비질게: posts small blind 5000000
네이든: posts big blind 10000000
*** HOLE CARDS ***
Dealt to Hero [5d 5c]
물고기: folds
런하니: folds
김정진: folds
Hero: raises 15000000 to 25000000
비질게: folds
네이든: calls 15000000
*** FLOP *** [Js 5s 7h]
네이든: checks
Hero: checks
*** TURN *** [Js 5s 7h] [9h]
네이든: checks
Hero: bets 27500000
네이든: calls 27500000
*** RIVER *** [Js 5s 7h 9h] [6s]
네이든: checks
Hero: bets 60000000
네이든: raises 290000000 to 350000000
Hero: calls 290000000
*** SHOW DOWN ***
Hero: shows [5d 5c]
네이든: shows [As 4s]
네이든 collected 810000000 from pot
*** SUMMARY ***
Total pot 810000000 | Rake 0
Board [Js 5s 7h 9h 6s]
Seat 1: 런하니 folded before Flop (didn't bet)
Seat 2: 김정진 folded before Flop (didn't bet)
Seat 3: Hero (button) showed [5d 5c] and lost
Seat 4: 비질게 (small blind) folded before Flop
Seat 5: 네이든 (big blind) showed [As 4s] and won (810000000)
Seat 6: 물고기 folded before Flop (didn't bet)
"""


def short_stack_all_in_record():
    """Hero (BB) shoves 20 over a flop bet; the opponent calls only part, so 10 is returned."""
    record = deepcopy(HAND)
    record["table"]["board"] = [11, 5, 33]
    record["table"]["totalPot"] = 40000000
    for player in record["players"]:
        player.update(handBet=0, netDelta=0, finalStack=1000000000, winMoney=0)
    hero = next(p for p in record["players"] if p["userId"] == HERO_ID)
    villain = next(p for p in record["players"] if p["userId"] == 35101)
    hero.update(handBet=20000000, netDelta=-20000000, finalStack=10000000)
    villain.update(handBet=20000000, netDelta=20000000, finalStack=1020000000, winMoney=40000000)
    record["streets"] = [
        {"stage": "Preflop", "actions": [
            {"userId": 35101, "action": "BigBlind", "betMoney": 10000000, "totalBet": 10000000},
            {"userId": 9396, "action": "Call", "betMoney": 10000000, "totalBet": 10000000},
        ]},
        {"stage": "Flop", "actions": [
            {"userId": 35101, "action": "Check", "betMoney": 0, "totalBet": 0},
            {"userId": 9396, "action": "AllIn", "betMoney": 20000000, "totalBet": 20000000},
            {"userId": 35101, "action": "Call", "betMoney": 10000000, "totalBet": 10000000},
        ]},
    ]  # fmt: skip
    record["pots"] = {
        "main": {"amount": 40000000, "winners": [{"userId": 35101, "potMoney": 40000000}]},
        "side": [],
    }
    return record


def test_matches_locktree_projection_for_real_hand():
    assert to_pokerstars(HAND, HERO_ID) == EXPECTED_CHIPS


def test_bb_units_divides_every_amount_by_the_big_blind():
    text = to_pokerstars(HAND, HERO_ID, bb_units=True)
    assert "Hold'em No Limit (0.5/1)" in text
    assert "Seat 3: Hero (81.54 in chips)" in text
    assert "네이든: raises 29 to 35" in text
    assert "Total pot 81 | Rake 0" in text


def test_hero_is_omitted_when_unknown():
    text = to_pokerstars(HAND, None)
    assert "Dealt to" not in text
    assert "Seat 3: GTO대로칩니다 (815376555 in chips)" in text


def test_all_in_marks_short_stack_and_returns_uncalled_bet_before_the_summary():
    record = short_stack_all_in_record()
    text = to_pokerstars(record, HERO_ID)
    lines = text.splitlines()
    assert "Hero: bets 20000000 and is all-in" in lines
    returned = lines.index("Uncalled bet (10000000) returned to Hero")
    assert lines[returned - 1] == "네이든: calls 10000000"
    assert lines[returned + 1] == "*** SHOW DOWN ***"


def test_unknown_action_is_rejected_instead_of_guessed():
    record = deepcopy(HAND)
    record["streets"][1]["actions"][0]["action"] = "Straddle"
    with pytest.raises(ConversionError, match="Unknown action"):
        to_pokerstars(record, HERO_ID)


def test_missing_board_card_id_is_rejected():
    record = deepcopy(HAND)
    record["table"]["board"][0] = 53
    with pytest.raises(ConversionError, match="Card id"):
        to_pokerstars(record, HERO_ID)


def test_side_pots_use_main_and_side_labels():
    text = to_pokerstars(json.loads((FIXTURES / "hand_2964123.json").read_text("utf-8")), HERO_ID)
    assert "익플PQUM collected 24169672 from main pot" in text
    assert "익플PQUM collected 60560740 from side pot-1" in text
    assert "Total pot 84730412 | Rake 0" in text


def test_names_disambiguate_duplicates_and_hero_lookalikes():
    players = [
        {"userId": 1, "nickname": "Hero", "seat": 0},
        {"userId": 2, "nickname": "dup", "seat": 1},
        {"userId": 3, "nickname": "dup", "seat": 2},
        {"userId": 4, "nickname": "me", "seat": 3},
    ]
    assert player_names(players, 4) == {"1": "Hero_1", "2": "dup_2", "3": "dup_3", "4": "Hero"}


@pytest.mark.parametrize(
    ("card", "text"), [(1, "As"), (14, "Ad"), (27, "Ah"), (52, "Kc"), (10, "Ts")]
)
def test_card_ids_decode_to_rank_and_suit(card, text):
    assert card_text(card) == text


def load_fixture(name):
    return (FIXTURES / name).read_text("utf-8")


# Real Craft records. Each golden text was reviewed by hand against its actions.
GOLDEN_HANDS = {
    "2982926": "all-in call; the short call leaves 5000000 uncalled and already out of the pot",
    "2984660": "hero folds a 4-bet pot; turn raise and call; showdown between two others",
    "2987773": "PlayableBlind post; fold-win keeps the uncalled turn bet inside Craft's pot",
    "2987985": "Allin action as a raise; all-in call; run-out streets without actions",
    "2964123": "side pot: main pot and side pot-1 both won by the same player",
    "2987595": "preflop 5-bet shove; hero wins the run-out",
    "2988134": "everyone folds to the big blind; blinds only",
    "2988238": "river all-in fold; uncalled bet is already out of Craft's pot",
    "2980455": "PlayableBlind plus an Allin flop bet and call",
}


@pytest.mark.parametrize("hand_id", GOLDEN_HANDS)
def test_real_hand_matches_reviewed_pokerstars_text(hand_id):
    record = json.loads(load_fixture(f"hand_{hand_id}.json"))
    assert to_pokerstars(record, HERO_ID) == load_fixture(f"hand_{hand_id}.ps.txt")


@pytest.mark.parametrize("hand_id", GOLDEN_HANDS)
def test_real_hand_collected_chips_equal_the_total_pot(hand_id):
    text = to_pokerstars(json.loads(load_fixture(f"hand_{hand_id}.json")), HERO_ID)
    collected = sum(int(chips) for chips in re.findall(r" collected (\d+) from ", text))
    assert f"Total pot {collected} | Rake 0" in text


def test_playable_blind_is_posted_as_a_big_blind_and_checks_its_option():
    text = to_pokerstars(json.loads(load_fixture("hand_2987773.json")), HERO_ID)
    lines = text.splitlines()
    assert "sy: posts big blind 10000000" in lines
    assert lines.index("sy: posts big blind 10000000") < lines.index("*** HOLE CARDS ***")
    assert "sy: checks" in lines[lines.index("*** HOLE CARDS ***") :]


def test_unmatched_bet_still_inside_the_pot_is_trimmed_from_the_winner():
    text = to_pokerstars(json.loads(load_fixture("hand_2987773.json")), HERO_ID, bb_units=True)
    assert "Uncalled bet (19.5) returned to sy" in text
    assert "sy collected 19.5 from pot" in text
    assert "Total pot 19.5 | Rake 0" in text


def test_duplicate_cards_are_rejected():
    record = deepcopy(HAND)
    record["table"]["board"][0] = record["players"][3]["holeCards"][0]
    with pytest.raises(ConversionError, match="Duplicate cards"):
        to_pokerstars(record, HERO_ID)


def test_hero_with_one_known_hole_card_is_rejected():
    record = deepcopy(HAND)
    record["players"][3]["holeCards"] = [18, 0]
    with pytest.raises(ConversionError, match="0 or 2 hole cards"):
        to_pokerstars(record, HERO_ID)


def test_hero_without_visible_cards_is_dealt_an_empty_hand():
    record = deepcopy(HAND)
    record["players"][3]["holeCards"] = [0, 0]
    assert "Dealt to Hero \n" in to_pokerstars(record, HERO_ID)


def test_button_that_is_not_the_seat_before_the_small_blind_only_warns():
    assert export_warnings(HAND) == []
    dead_button = json.loads(load_fixture("hand_2988134.json"))
    assert export_warnings(dead_button) == [
        "button-blind-mismatch: button is seat 4, but the seat before the small blind is seat 3."
    ]
    assert to_pokerstars(dead_button, HERO_ID).startswith("PokerStars Hand #2988134")


def test_record_whose_pot_contradicts_its_actions_is_rejected():
    record = json.loads(load_fixture("hand_2960876.json"))
    with pytest.raises(ConversionError, match="pot does not match"):
        to_pokerstars(record, HERO_ID)
