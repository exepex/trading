"""Fakes for the AI books' forecast tests (stories F1 and G5): a desk repository in a temporary folder (the golden v2
pack of 13 Oct 2026 with its baselines and Book 1, the official closes and the versioned prompts), a transport that
commits locally instead of pushing, GitHub receipts from a table, a settable clock, and a fake routine that answers."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date, datetime, timedelta
from pathlib import Path

from fno.ai.book import BookSession
from fno.ai.paths import CLOSES_FILE, pack_path, rules_path
from fno.ai.receipts import PushReceipts, ReceiptUnknown
from fno.ai.run_timing import RunTiming
from fno.ai.transport import SubmissionTransport
from fno.ai.versions import VERSIONS
from fno.constants import FORECAST_QUESTIONS
from fno.models import IST

ROOT = Path(__file__).resolve().parents[2]
GOLDEN = ROOT / "research/forecasts/v2/golden/case_a"
DAY = date(2026, 10, 13)


def at(hour: int, minute: int, second: int = 0) -> datetime:
    return datetime(DAY.year, DAY.month, DAY.day, hour, minute, second, tzinfo=IST)


def git(root: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, text=True).stdout


def make_desk_repo(root: Path) -> Path:
    """A git repository holding what the forecast-capture job has committed by 15:10 on DAY, plus Book 1's records."""
    files = {pack_path(DAY): GOLDEN / "pack.json", rules_path(DAY): GOLDEN / "forecasts.csv",
             CLOSES_FILE: ROOT / CLOSES_FILE} | {v.prompt_file: ROOT / v.prompt_file for v in VERSIONS}  # fmt: skip
    for target, source in files.items():
        (root / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, root / target)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "user.email", "desk@example.invalid")
    git(root, "config", "user.name", "desk")
    git(root, "add", ".")
    git(root, "commit", "-q", "-m", "the day's pack")
    return root


class LocalCommitTransport(SubmissionTransport):
    """Commits the file in the test repository (no remote, no hooks): what a push would leave on main."""

    def __init__(self, root: Path):
        self.root, self.commits = root, []

    def existing(self, path: str) -> str | None:
        file = self.root / path
        return file.read_text(encoding="utf-8") if file.is_file() else None

    def publish(self, path: str, text: str, message: str) -> str:
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text, encoding="utf-8")
        git(self.root, "add", path)
        git(self.root, "commit", "-q", "-m", message)
        self.commits.append(git(self.root, "rev-parse", "HEAD").strip())
        return self.commits[-1]


class FakeReceipts(PushReceipts):
    """GitHub's push times, set by the test per commit; an unknown commit is an unreadable log."""

    def __init__(self):
        self.times: dict[str, datetime] = {}

    def received_at(self, commit: str) -> datetime:
        if commit not in self.times:
            raise ReceiptUnknown(f"no push of {commit[:10]} in the test log")
        return self.times[commit]


class Clock:
    def __init__(self, now: datetime):
        self.now = now

    def __call__(self) -> datetime:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


def draft(values: dict[str, float | None] | None = None, model: str = "claude-opus-5-5") -> dict:
    values = values or dict.fromkeys(FORECAST_QUESTIONS, 0.5)
    forecasts = {q: {"probability": values[q], "reason": f"reason for {q}"} for q in FORECAST_QUESTIONS}
    return {"model_reported": model, "forecasts": forecasts}


class FakeRoutine:
    """A book's routine: brief with the fired text, write the answer, seal, then reveal (each step's time settable)."""

    def __init__(self, root: Path, clock: Clock):
        self.root, self.clock = root, clock
        self.transport = LocalCommitTransport(root)
        self.printed: list[str] = []

    def session(self, session_id: str = "session_01AbCdEf") -> BookSession:
        timing = RunTiming(self.root, self.transport, self.clock, session_id)
        return BookSession(self.root, self.transport, self.clock, self.clock.sleep, timing, self.printed.append)

    def run(self, text: str, answer: dict, sealed_at: datetime, reveal: bool = True) -> list[str]:
        session = self.session()
        session.brief(text)
        self.clock.now = sealed_at
        answer_file = self.root / ".ai_book" / "answer.json"
        answer_file.write_text(json.dumps(answer), encoding="utf-8")
        session.seal(answer_file)
        if reveal:
            session.reveal()
        return self.transport.commits
