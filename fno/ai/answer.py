"""A book's answer (stories F1 and G5): per question a probability (or null for "no forecast") and its reason, plus
the model the session reports. The routine writes only those parts; `seal` adds the book, day, hashes and version
from its own pointer and export, so the model cannot mislabel them. The same checks run when sealing (the model can
fix a refused answer before the deadline) and when collecting (nothing unchecked becomes a record)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from ..constants import FORECAST_QUESTIONS
from .envelope import Envelope
from .pointer import is_probability

MAX_REASON_CHARS = 600
MAX_MODEL_CHARS = 100
ANSWER_FIELDS = ("book", "day", "export_sha256", "forecasts", "model_reported", "pack_sha256", "version")


class AnswerRefused(ValueError):
    """The answer as a whole is unusable (wrong shape); the message says why."""


@dataclass(frozen=True)
class CheckedAnswer:
    probabilities: dict[str, float | None]  # question -> probability kept (None: no forecast)
    problems: dict[str, str]  # question -> why its value was refused ('' when kept)
    model_reported: str


def complete_answer(draft: dict, labels: dict) -> dict:
    """The full answer: the routine's draft (`model_reported`, `forecasts`) and the labels its pointer fixes."""
    if not isinstance(draft, dict) or sorted(draft) != ["forecasts", "model_reported"]:
        raise AnswerRefused("the answer must have exactly the fields forecasts and model_reported")
    return {**labels, **draft}


def check_answer(answer: dict, labels: dict, envelope: Envelope | None,
                 questions: Sequence[str] = FORECAST_QUESTIONS) -> CheckedAnswer:  # fmt: skip
    """Every question's outcome, or AnswerRefused when the labels or the shape are wrong. `questions`: the day's (v2's
    five, or a v4 pointer's list)."""
    if not isinstance(answer, dict) or sorted(answer) != list(ANSWER_FIELDS):
        raise AnswerRefused(f"the answer must have exactly the fields {', '.join(ANSWER_FIELDS)}")
    wrong = [name for name, value in labels.items() if answer[name] != value]
    if wrong:
        raise AnswerRefused(f"answer is not for this input: {', '.join(wrong)} differ")
    model = answer["model_reported"]
    if not isinstance(model, str) or not model.strip() or len(model) > MAX_MODEL_CHARS:
        raise AnswerRefused('model_reported must be short text ("unknown" when the session cannot tell)')
    forecasts = answer["forecasts"]
    if not isinstance(forecasts, dict) or sorted(forecasts) != sorted(questions):
        raise AnswerRefused(f"forecasts must name exactly {', '.join(questions)}")
    kept, problems = {}, {}
    for question in questions:
        value, problem = _question(forecasts[question])
        problem = problem or (envelope.problem(question, value) if envelope else "")
        kept[question], problems[question] = (None if problem else value), problem
    return CheckedAnswer(kept, problems, model.strip())


def _question(entry) -> tuple[float | None, str]:
    if not isinstance(entry, dict) or sorted(entry) != ["probability", "reason"]:
        return None, 'must be {"probability": ..., "reason": ...}'
    value, reason = entry["probability"], entry["reason"]
    if not isinstance(reason, str) or not reason.strip() or "\n" in reason or len(reason) > MAX_REASON_CHARS:
        return None, f"reason must be one line of 1 to {MAX_REASON_CHARS} characters"
    if value is not None and not is_probability(value):
        return None, "probability must be a number in [0, 1] or null"
    return (None if value is None else float(value)), ""
