"""Where the AI books' trading records live (story F1t). None of them is inside a book's own folder, so none enters a
private pack: each day's fire log, each book's submissions (commitment and reveal) and its outcome record are under
`journal/ai_decisions/`. The routine's working files and the remote observer's readings are git-ignored."""

from __future__ import annotations

from datetime import date

DECISIONS_FOLDER = "journal/ai_decisions"
WORK_FOLDER = ".ai_decision"  # the routine's private working files (salt, pointer); never committed
OBSERVATIONS_FOLDER = ".ai_decision_observations"  # the remote observer's readings (daily run side); never committed


def fired_path(day: date) -> str:
    return f"{DECISIONS_FOLDER}/{day:%Y}/{day.isoformat()}_fired.json"


def outcome_path(day: date, book: str) -> str:
    return f"{DECISIONS_FOLDER}/{day:%Y}/{day.isoformat()}_{book}_outcome.json"


def commitment_path(day: date, book: str) -> str:
    return f"{DECISIONS_FOLDER}/submissions/{day:%Y}/{day.isoformat()}_{book}.commitment.json"


def reveal_path(day: date, book: str) -> str:
    return f"{DECISIONS_FOLDER}/submissions/{day:%Y}/{day.isoformat()}_{book}.reveal.json"


def transcript_audit_path(day: date, book: str) -> str:
    return f"{DECISIONS_FOLDER}/{day:%Y}/{day.isoformat()}_{book}_transcript_audit.json"


def observations_path(day: date) -> str:
    return f"{OBSERVATIONS_FOLDER}/{day.isoformat()}.json"


def common_pack_path(day: date) -> str:
    """E2's committed common pack (`fno/desk/pack_store.py`), repeated here because the routine side cannot import the
    desk's pack code; `tests/ai_trading/test_paths.py` keeps them equal."""
    return f"journal/packs/{day.isoformat()}/common.json"
