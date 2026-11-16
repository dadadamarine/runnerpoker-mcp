"""Convert a RunnerPoker v2 hand record into PokerStars hand-history text.

Output follows the locktree PokerStars projection (frontend/src/api/pokerstars-text) so the
text can be pasted into locktree or uploaded to GTO Wizard: hero is named "Hero", the header
time is CET, cards use T for ten, and `shows` lines carry no hand description.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from .cards import cards_text, has_known_cards
from .errors import ConversionError
from .validation import validate_cards

STREET_BOARD_SIZES = (("Flop", 3), ("Turn", 4), ("River", 5))
CET_OFFSET = timedelta(hours=1)
BLIND_ACTIONS = {"SmallBlind", "BigBlind", "PlayableBlind"}
KNOWN_ACTIONS = {"Fold", "Check", "Call", "Bet", "Raise", "AllIn", "Allin", *BLIND_ACTIONS}
SEAT_ROLES = {"BTN": " (button)", "SB": " (small blind)", "BB": " (big blind)"}


def clean_text(value: object, fallback: str) -> str:
    text = "".join(ch if ch.isprintable() else " " for ch in str(value))
    return " ".join(text.split()) or fallback


def player_names(players: list[dict[str, Any]], hero_id: int | None) -> dict[str, str]:
    """Hero becomes "Hero"; other duplicate or "Hero" nicknames get a `_seat` suffix."""
    base = {
        str(p["userId"]): clean_text(p.get("nickname"), f"Seat{p['seat'] + 1}") for p in players
    }
    counts: dict[str, int] = {}
    for name in base.values():
        counts[name] = counts.get(name, 0) + 1
    names = {}
    for player in sorted(players, key=lambda p: p["seat"]):
        uid = str(player["userId"])
        if hero_id is not None and uid == str(hero_id):
            names[uid] = "Hero"
        elif base[uid] == "Hero" or counts[base[uid]] > 1:
            names[uid] = f"{base[uid]}_{player['seat'] + 1}"
        else:
            names[uid] = base[uid]
    return names


def header_time(start_at: object) -> str:
    if not isinstance(start_at, str):
        raise ConversionError("Hand record has no startAt.")
    try:
        utc = datetime.fromisoformat(start_at.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        raise ConversionError("Hand record startAt is not an ISO timestamp.") from None
    return (utc + CET_OFFSET).strftime("%Y/%m/%d %H:%M:%S")


def require(record: dict[str, Any], key: str, kind: type) -> Any:
    value = record.get(key)
    if not isinstance(value, kind):
        raise ConversionError(f"Hand record is missing {key}.")
    return value


class Renderer:
    def __init__(self, record: dict[str, Any], hero_id: int | None, bb_units: bool) -> None:
        self.record = record
        self.table = require(record, "table", dict)
        self.players: list[dict[str, Any]] = require(record, "players", list)
        self.streets: list[dict[str, Any]] = require(record, "streets", list)
        blinds = require(self.table, "blinds", dict)
        self.small_blind, self.big_blind = blinds["smallBlind"], blinds["bigBlind"]
        self.divisor = self.big_blind if bb_units else 1
        self.board: list[int] = self.table.get("board") or []
        self.names = player_names(self.players, hero_id)
        self.hero_id = hero_id
        self.by_id = {str(p["userId"]): p for p in self.players}
        self.starting = {uid: p["finalStack"] - p["netDelta"] for uid, p in self.by_id.items()}
        self.committed = {uid: 0 for uid in self.by_id}
        self.uncalled: tuple[str, int] | None = None
        self.pot_trim = 0
        self.folded_on: dict[str, str] = {}
        self.lines: list[str] = []

    def amount(self, chips: float) -> str:
        if self.divisor == 1:
            return str(chips)
        text = f"{round(chips / self.divisor, 2):.2f}"
        return text.rstrip("0").rstrip(".")

    def action_line(self, action: dict[str, Any], street_max: int) -> tuple[str, int]:
        """Render one action; returns the line and the street's new highest total bet."""
        kind, added, total = action["action"], action["betMoney"], action["totalBet"]
        uid = str(action["userId"])
        name = self.names[uid]
        if kind == "SmallBlind":
            return f"{name}: posts small blind {self.amount(added)}", max(street_max, total)
        if kind in ("BigBlind", "PlayableBlind"):
            return f"{name}: posts big blind {self.amount(added)}", max(street_max, total)
        if kind in ("Fold", "Check"):
            return f"{name}: {kind.lower()}s", street_max
        if total <= street_max and kind != "Bet":
            line, new_max = f"{name}: calls {self.amount(added)}", street_max
        elif street_max == 0:
            line, new_max = f"{name}: bets {self.amount(added)}", total
        else:
            line = f"{name}: raises {self.amount(total - street_max)} to {self.amount(total)}"
            new_max = total
        if self.committed[uid] + added >= self.starting[uid]:
            line += " and is all-in"
        return line, new_max

    def play(self, actions: list[dict[str, Any]], stage: str, street_max: int) -> int:
        for action in actions:
            if action.get("action") not in KNOWN_ACTIONS:
                raise ConversionError(f"Unknown action {action.get('action')!r}.")
            uid = str(action["userId"])
            line, street_max = self.action_line(action, street_max)
            self.committed[uid] += action["betMoney"]
            self.lines.append(line)
            if action["action"] == "Fold":
                self.folded_on[uid] = "before Flop" if stage == "Preflop" else f"on the {stage}"
        return street_max

    def find_uncalled(self) -> tuple[str, int] | None:
        """Player and chips of an unmatched bet, from the action totals."""
        ranked = sorted(self.committed.items(), key=lambda item: item[1], reverse=True)
        if len(ranked) < 2 or ranked[0][1] <= ranked[1][1]:
            return None
        return ranked[0][0], ranked[0][1] - ranked[1][1]

    def pot_still_holds_uncalled(self) -> bool:
        """Craft leaves the unmatched chips in the pot when everyone folds, but removes them
        after an all-in call; only the first case needs the pot trimmed."""
        return self.uncalled is not None and sum(self.committed.values()) == self.table.get(
            "totalPot"
        )

    def pot_labels(self) -> list[tuple[str, dict[str, Any]]]:
        pots = self.record.get("pots") or {}
        sides = pots.get("side") or []
        labels = []
        if isinstance(pots.get("main"), dict):
            labels.append(("main pot" if sides else "pot", pots["main"]))
        labels += [(f"side pot-{i}", pot) for i, pot in enumerate(sides, 1)]
        return labels

    def append_header(self) -> None:
        game_name = clean_text(self.record.get("gameName"), "table").replace("'", " ")
        room = (self.record.get("game") or {}).get("roomId", 0)
        blinds = f"{self.amount(self.small_blind)}/{self.amount(self.big_blind)}"
        self.lines += [
            f"PokerStars Hand #{self.record['handId']}: Hold'em No Limit ({blinds}) - "
            f"{header_time(self.record.get('startAt'))} CET",
            f"Table 'RunnerPoker {game_name} {room}' {self.table.get('maxPlayers', 6)}-max "
            f"Seat #{self.table['buttonSeat'] + 1} is the button",
        ]
        for player in sorted(self.players, key=lambda p: p["seat"]):
            uid = str(player["userId"])
            stack = self.amount(self.starting[uid])
            self.lines.append(f"Seat {player['seat'] + 1}: {self.names[uid]} ({stack} in chips)")

    def append_streets(self) -> None:
        stages = {s["stage"]: s for s in self.streets}
        preflop = (stages.get("Preflop") or {}).get("actions", [])
        blind_count = 0
        while blind_count < len(preflop) and preflop[blind_count].get("action") in BLIND_ACTIONS:
            blind_count += 1
        street_max = self.play(preflop[:blind_count], "Preflop", 0)
        self.lines.append("*** HOLE CARDS ***")
        hero = self.by_id.get(str(self.hero_id)) if self.hero_id is not None else None
        if hero is not None:
            cards = hero.get("holeCards")
            known = has_known_cards(cards)
            self.lines.append(f"Dealt to Hero [{cards_text(cards)}]" if known else "Dealt to Hero ")
        self.play(preflop[blind_count:], "Preflop", street_max)
        uncalled_slot = len(self.lines)

        revealed: list[int] = []
        for stage, count in STREET_BOARD_SIZES:
            if len(self.board) < count:
                break
            new_cards = cards_text(self.board[len(revealed) : count])
            before = f"[{cards_text(revealed)}] " if revealed else ""
            self.lines.append(f"*** {stage.upper()} *** {before}[{new_cards}]")
            revealed = self.board[:count]
            actions = (stages.get(stage) or {}).get("actions", [])
            self.play(actions, stage, 0)
            if actions:
                uncalled_slot = len(self.lines)
        self.uncalled = self.find_uncalled()
        if self.uncalled is not None:
            uid, chips = self.uncalled
            returned = f"Uncalled bet ({self.amount(chips)}) returned to {self.names[uid]}"
            self.lines.insert(uncalled_slot, returned)
            self.pot_trim = chips if self.pot_still_holds_uncalled() else 0

    def append_showdown(self) -> tuple[bool, dict[str, int]]:
        in_hand = [
            p for p in self.players if str(p["userId"]) not in self.folded_on and p["handBet"] > 0
        ]
        is_showdown = len(in_hand) >= 2
        if is_showdown:
            self.lines.append("*** SHOW DOWN ***")
            for player in in_hand:
                if has_known_cards(player.get("holeCards")):
                    cards = cards_text(player["holeCards"])
                    self.lines.append(f"{self.names[str(player['userId'])]}: shows [{cards}]")
        won = {uid: 0 for uid in self.by_id}
        trim = self.pot_trim
        for label, pot in self.pot_labels():
            for winner in pot.get("winners") or []:
                uid = str(winner["userId"])
                is_bettor = self.uncalled is not None and uid == self.uncalled[0]
                collected = winner["potMoney"] - (trim if is_bettor else 0)
                trim = 0 if is_bettor else trim
                won[uid] += collected
                self.lines.append(
                    f"{self.names[uid]} collected {self.amount(collected)} from {label}"
                )
        return is_showdown, won

    def append_summary(self, won: dict[str, int], is_showdown: bool) -> None:
        rake = (self.record.get("game") or {}).get("rakeMoney", 0)
        total_pot = self.amount(self.table.get("totalPot", 0) - self.pot_trim)
        self.lines += ["*** SUMMARY ***", f"Total pot {total_pot} | Rake {self.amount(rake)}"]
        if self.board:
            self.lines.append(f"Board [{cards_text(self.board)}]")
        reached_flop = len(self.board) >= 3
        for player in sorted(self.players, key=lambda p: p["seat"]):
            uid = str(player["userId"])
            role = SEAT_ROLES.get(player.get("position"), "")
            head = f"Seat {player['seat'] + 1}: {self.names[uid]}{role}"
            collected, cards = won[uid], player.get("holeCards")
            if is_showdown and uid not in self.folded_on and has_known_cards(cards):
                outcome = f"and won ({self.amount(collected)})" if collected else "and lost"
                result = f"showed [{cards_text(cards)}] {outcome}"
            elif collected:
                result = f"{'won' if reached_flop else 'collected'} ({self.amount(collected)})"
            elif uid in self.folded_on:
                folded = self.folded_on[uid]
                untouched = folded == "before Flop" and not player["handBet"]
                result = f"folded {folded}" + (" (didn't bet)" if untouched else "")
            else:
                result = "mucked"
            self.lines.append(f"{head} {result}")

    def render(self) -> str:
        validate_cards(self.board, self.players, self.hero_id)
        self.append_header()
        self.append_streets()
        is_showdown, won = self.append_showdown()
        rake = (self.record.get("game") or {}).get("rakeMoney", 0)
        if sum(won.values()) + rake != self.table.get("totalPot", 0) - self.pot_trim:
            raise ConversionError("Hand record pot does not match its actions and winners.")
        self.append_summary(won, is_showdown)
        return "\n".join(self.lines) + "\n"


def to_pokerstars(
    record: dict[str, Any], hero_id: int | None = None, bb_units: bool = False
) -> str:
    """PokerStars text for one v2 record; `bb_units` divides amounts by the big blind."""
    try:
        return Renderer(record, hero_id, bb_units).render()
    except (KeyError, TypeError, IndexError) as error:
        raise ConversionError(f"Hand record is incomplete or malformed: {error!r}.") from None
