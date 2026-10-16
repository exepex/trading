"""An AI book's decision answer (story F1t). The routine writes only `model_reported` and `decision`; `seal` adds the
labels its pointer fixes (book, day, version, both pack hashes, the cards item's hash), so the model cannot mislabel
them. The same checks run when sealing (the model can fix a refused answer before the deadline) and when collecting
(nothing unchecked reaches a decider): the labels, the model rule, F1t's base shape (an object with a one-line
`reason`; what it decides is the book's own, checked by F5's or F6's `check_decision`) and the private-figure rule."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass

from ..desk.pack_items import canonical_json, sha256_hex
from .figures import figure_problems
from .pointer import DecisionPointer

DRAFT_FIELDS = ("decision", "model_reported")
LABELS = ("book", "cards_sha256", "common_pack_sha256", "day", "private_pack_sha256", "version")
ANSWER_FIELDS = tuple(sorted(LABELS + DRAFT_FIELDS))
UNKNOWN_MODEL = "unknown"
MODEL_ID = re.compile(r"[a-z][a-z0-9.-]{2,80}(\[[a-z0-9]{1,8}\])?")
MAX_REASON_CHARS = 600
MODEL_RULE = (
    "MODEL RULE (story F1t): set model_reported to the exact model ID your own instructions state (your identity "
    "line). If you also have the session-description tool (get_session), use its session_context.model. Write "
    '"unknown" only when you have neither. An unknown or different model means no trade today.'
)


class AnswerRefused(ValueError):
    """The answer cannot be used; the message lists every problem, so the model can fix them all at once."""


@dataclass(frozen=True)
class CheckedAnswer:
    decision: dict
    model_reported: str


def labels_of(pointer: DecisionPointer) -> dict:
    return {"book": pointer.book, "cards_sha256": sha256_hex(canonical_json(pointer.analyst_cards)),
            "common_pack_sha256": pointer.common_pack_sha256, "day": pointer.day.isoformat(),
            "private_pack_sha256": pointer.private_pack_sha256, "version": pointer.version}  # fmt: skip


def complete_answer(draft, labels: dict) -> dict:
    if not isinstance(draft, dict) or sorted(draft) != list(DRAFT_FIELDS):
        raise AnswerRefused(f"the answer must have exactly the fields {', '.join(DRAFT_FIELDS)}")
    return {**labels, **draft}


def check_answer(answer, labels: dict, shape_check: Callable[[dict], list[str]], private: set[str]) -> CheckedAnswer:
    if not isinstance(answer, dict) or sorted(answer) != list(ANSWER_FIELDS):
        raise AnswerRefused(f"the answer must have exactly the fields {', '.join(ANSWER_FIELDS)}")
    wrong = [name for name in LABELS if answer[name] != labels[name]]
    if wrong:
        raise AnswerRefused(f"the answer is not for this input: {', '.join(wrong)} differ")
    model, decision = answer["model_reported"], answer["decision"]
    problems = _model_problems(model) + base_problems(decision)
    if not problems:
        problems = list(shape_check(decision)) + figure_problems(decision, private)
    if problems:
        raise AnswerRefused("; ".join(problems))
    return CheckedAnswer(decision, model)


def _model_problems(model) -> list[str]:
    if isinstance(model, str) and (model == UNKNOWN_MODEL or MODEL_ID.fullmatch(model)):
        return []
    return [f'model_reported must be the exact model ID (for example "claude-opus-5-5") or "{UNKNOWN_MODEL}"']


def base_problems(decision) -> list[str]:
    if not isinstance(decision, dict):
        return ["decision must be an object"]
    reason = decision.get("reason")
    if not isinstance(reason, str) or not reason.strip() or "\n" in reason or len(reason) > MAX_REASON_CHARS:
        return [f"decision.reason must be one line of 1 to {MAX_REASON_CHARS} characters"]
    return []
