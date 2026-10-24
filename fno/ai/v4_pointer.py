"""Story G11, what the AI books are fired with under protocol v4 (response 272): one line of JSON holding the book's
whole v4 input (`v4_input.py`), because a routine session has no Drive credentials and cannot read the pack. The
routine receives it as untrusted text, so reading it back checks every field before anything is shown to the model.
Capped at `ROUTINE_POINTER_MAX_BYTES` (the same cap as F1t's pointer); a longer one is never sent, so the book is
`not_fired`. Standard library only: `brief` reads it in the routine."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date

from ..constants import AI_BOOKS, BOOK2_HYBRID, FORECAST_PROTOCOL_V4, V4_QUESTIONS
from ..constants_operations import ROUTINE_POINTER_MAX_BYTES
from ..forecast_v4.terms import POINT_QUESTIONS
from .envelope import Envelope
from .pointer import SHA256, PointerRefused, is_number, is_probability
from .v4_input import input_sha256
from .versions import VersionRefused, current_version

KIND = "forecast_v4"
POINTER_FIELDS = ("input", "kind")
INPUT_FIELDS = ("book", "closes_before_day", "day", "derived", "history", "pack", "pack_sha256", "questions", "version")
HISTORY_FIELDS = ["date", "rv_s"]
TOO_LONG = "the pointer is {size} bytes, over the {cap}-byte cap: not fired, never truncated"


@dataclass(frozen=True)
class V4Pointer:
    input: dict

    @property
    def book(self) -> str:
        return self.input["book"]

    @property
    def day(self) -> date:
        return date.fromisoformat(self.input["day"])

    @property
    def input_sha256(self) -> str:
        return input_sha256(self.input)

    def to_text(self) -> str:
        """The fired text; ValueError when it would pass the cap (the caller records `not_fired`)."""
        text = json.dumps({"input": self.input, "kind": KIND}, sort_keys=True, separators=(",", ":"))
        size = len(text.encode("utf-8"))
        if size > ROUTINE_POINTER_MAX_BYTES:
            raise ValueError(TOO_LONG.format(size=size, cap=ROUTINE_POINTER_MAX_BYTES))
        return text


def v4_labels(built: dict) -> dict:
    """What a v4 input fixes in every answer (the book cannot mislabel them); `export_sha256` holds the input's hash, so
    the answer and commitment formats stay F1's."""
    return {"book": built["book"], "day": built["day"], "export_sha256": input_sha256(built),
            "pack_sha256": built["pack_sha256"], "version": built["version"]}  # fmt: skip


def v4_envelope(built: dict) -> Envelope | None:
    """Hybrid's envelope as its input states it; None for Book 3."""
    rules = built.get("rules")
    return Envelope.from_json(rules["envelope"]) if rules else None


def parse_v4_pointer(text: str) -> V4Pointer:
    if len(text.encode("utf-8")) > ROUTINE_POINTER_MAX_BYTES:
        raise PointerRefused("longer than any pointer")
    try:
        fields = json.loads(text)
    except ValueError as error:
        raise PointerRefused(f"not JSON ({error.msg})") from None
    if not isinstance(fields, dict) or sorted(fields) != list(POINTER_FIELDS) or fields["kind"] != KIND:
        raise PointerRefused(f"fields must be exactly {', '.join(POINTER_FIELDS)}, kind {KIND}")
    built = fields["input"]
    _check_input(built)
    return V4Pointer(built)


def _check_input(built) -> None:
    if not isinstance(built, dict):
        raise PointerRefused("input must be an object")
    book = built.get("book")
    wanted = sorted(INPUT_FIELDS + (("rules",) if book == BOOK2_HYBRID else ()))
    if sorted(built) != wanted:
        raise PointerRefused(f"input fields must be exactly {', '.join(wanted)}")
    if book not in AI_BOOKS:
        raise PointerRefused(f"{book!r} is not an AI book")
    try:
        date.fromisoformat(built["day"])
        registered = current_version(book, FORECAST_PROTOCOL_V4)
    except (VersionRefused, TypeError, ValueError) as error:
        raise PointerRefused(str(error)) from None
    if built["version"] != registered.label:
        raise PointerRefused("version is not the book's registered version")
    if not isinstance(built["pack_sha256"], str) or not SHA256.fullmatch(built["pack_sha256"]):
        raise PointerRefused("pack_sha256 is not a SHA-256")
    questions = built["questions"]
    if not isinstance(questions, list) or not questions or not set(questions) <= set(V4_QUESTIONS):
        raise PointerRefused("questions must be a non-empty list of v4 questions")
    if not set(questions) <= set(registered.questions):
        raise PointerRefused(f"{registered.label} does not define {sorted(set(questions) - set(registered.questions))}")
    _check_history(built["history"], questions)
    if book == BOOK2_HYBRID:
        _check_rules(built["rules"], questions)


def _check_history(history, questions: list) -> None:
    """Each asked point question's history: rows of a date and an `RV_s` (a number >= 0, or null for a void session)."""
    if not isinstance(history, dict) or not set(history) <= set(questions) & POINT_QUESTIONS:
        raise PointerRefused("history must hold only the day's point questions")
    for rows in history.values():
        if not isinstance(rows, list):
            raise PointerRefused("a question's history must be a list")
        for row in rows:
            if not isinstance(row, dict) or sorted(row) != HISTORY_FIELDS or not _rv(row["rv_s"]):
                raise PointerRefused("a history row must be exactly date and rv_s (a number >= 0 or null)")
            try:
                date.fromisoformat(row["date"])
            except (TypeError, ValueError):
                raise PointerRefused("a history row's date must be YYYY-MM-DD") from None


def _rv(value) -> bool:
    return value is None or (is_number(value) and value >= 0)


def _check_rules(rules, questions: list) -> None:
    if not isinstance(rules, dict) or sorted(rules) != ["by_question", "envelope"]:
        raise PointerRefused("rules must hold exactly by_question and envelope")
    by_question = rules["by_question"]
    if not isinstance(by_question, dict) or sorted(by_question) != sorted(questions):
        raise PointerRefused("rules must name exactly the day's questions")
    for question, by_name in by_question.items():
        kind = (lambda v: is_number(v) and v > 0) if question in POINT_QUESTIONS else is_probability
        if not isinstance(by_name, dict) or not all(v is None or kind(v) for v in by_name.values()):
            raise PointerRefused(f"{question}: a rule's value must be a {_unit(question)} or null")


def _unit(question: str) -> str:
    return "variance above 0" if question in POINT_QUESTIONS else "probability in [0, 1]"
