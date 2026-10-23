"""Story REH1: every clock read of the package goes through `fno.models`, so a rehearsal's replay clock, installed
once at process start, reaches every step. A direct `datetime.now`, `date.today` or `datetime.utcnow` anywhere else
fails here."""

import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

import fno.models as models

PACKAGE = Path(__file__).resolve().parents[2] / "fno"
DIRECT = re.compile(r"\bdatetime\.now\(|\bdate\.today\(|\bdatetime\.utcnow\(")


def test_no_module_but_the_clock_s_own_reads_the_wall_clock():
    found = []
    for path in sorted(PACKAGE.rglob("*.py")):
        if path == PACKAGE / "models.py":
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        found += [f"{path.relative_to(PACKAGE.parent)}:{n}" for n, line in enumerate(lines, 1) if DIRECT.search(line)]
    assert found == []


def test_an_installed_clock_is_what_every_reader_sees(monkeypatch):
    replay = datetime(2026, 10, 23, 8, 35, tzinfo=UTC)  # 14:05 IST
    monkeypatch.setattr(models, "_clock", lambda: replay)
    assert models.now_ist().isoformat() == "2026-10-23T14:05:00+05:30"
    assert models.now_utc() == replay and models.today_local() == replay.astimezone().date()


def test_the_default_clock_is_the_wall_clock():
    assert abs(models.now_utc() - datetime.now(UTC)) < timedelta(seconds=5)
