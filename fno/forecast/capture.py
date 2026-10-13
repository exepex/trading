"""Book 1's daily forecast capture (story G3), run by a scheduled GitHub Actions job (no AI).

**Today it records "no forecast" on every trading day.** The frozen protocol (PROTOCOL.md section 1) allows live
inputs only from the common market pack of story E2, which does not exist yet: "Until E2 exists there are no live
forecasts". So each day's record has five empty probabilities, Book 1's method label, the reason, and the SHA-256 of
an empty pack (no input was read). A forecast is never imputed. Live forecasts start with a protocol version that
names their input pack (`reviews/claude/response_62_g2-g3.md`, proposal).

Records: `research/forecasts/live/<YYYY>/<YYYY-MM-DD>_book1_rules.csv`, written once (the same bytes again is a no-op,
different bytes are refused). **Deadline:** 15:30 IST on the forecast day, the session's close, after which the day's
close is known; a record whose file was first committed later is ignored by scoring (`on_time`).
"""

from __future__ import annotations

import hashlib
import subprocess
from datetime import date, datetime, time
from pathlib import Path

from ..constants import BOOK1_RULES, FORECAST_QUESTIONS, SESSION_MUHURAT
from ..models import IST
from ..research_data.calendar import SessionCalendar
from .book1_method import method_label
from .record_files import records_csv
from .schema import ForecastRecord

LIVE_FOLDER = "research/forecasts/live"
CUTOFF, DEADLINE = time(15, 0), time(15, 30)
EMPTY_PACK_SHA256 = hashlib.sha256(b"").hexdigest()
NO_LIVE_INPUTS = "no-live-inputs"
NO_LIVE_REASON = "protocol v1 section 1: no live forecasts until the E2 common market pack exists"
LINE = "Omenix F&O forecasts (GitHub Actions): Book 1 on {day}: {result}"


class CaptureRefused(RuntimeError):
    """The day's record already exists with different content."""


def live_path(root: Path, day: date) -> Path:
    return Path(root) / LIVE_FOLDER / f"{day:%Y}" / f"{day.isoformat()}_{BOOK1_RULES}.csv"


def no_forecast_records(day: date) -> list[ForecastRecord]:
    cutoff = datetime.combine(day, CUTOFF, tzinfo=IST)
    label = f"{method_label()}/{NO_LIVE_INPUTS}"
    return [ForecastRecord(BOOK1_RULES, day, cutoff, q, None, label, EMPTY_PACK_SHA256) for q in FORECAST_QUESTIONS]


def capture_book1(root: Path, day: date, calendar: SessionCalendar) -> str:
    """Write the day's Book 1 record; the line to post. Not a trading day (or a muhurat session): nothing written."""
    if calendar.session_kind(day) in (None, SESSION_MUHURAT):
        return LINE.format(day=day, result="not a trading day; nothing recorded")
    path, text = live_path(root, day), records_csv(no_forecast_records(day))
    if path.exists():
        if path.read_text(encoding="utf-8") != text:
            raise CaptureRefused(f"{path} already holds a different record; records are written once")
        return LINE.format(day=day, result="already recorded")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return LINE.format(day=day, result=f"no forecast recorded ({NO_LIVE_REASON})")


def first_commit_time(root: Path, path: Path) -> datetime | None:
    """When the file was first committed (the committer time of the commit that added it), or None if never."""
    relative = Path(path).resolve().relative_to(Path(root).resolve()).as_posix()
    done = subprocess.run(
        ["git", "log", "--diff-filter=A", "--format=%cI", "--", relative], cwd=root, capture_output=True, text=True
    )
    times = done.stdout.split()
    return datetime.fromisoformat(times[-1]) if times else None


def on_time(day: date, committed: datetime | None) -> bool:
    """A forecast counts only if its file was committed by 15:30 IST on its day."""
    return committed is not None and committed <= datetime.combine(day, DEADLINE, tzinfo=IST)
