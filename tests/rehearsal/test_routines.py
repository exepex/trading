"""REH1c: the four routines a rehearsal replays are CLAUDE.md's own (each command held to its section); their
commands run in the rehearsal's checkout in the routine's order, a background one first, one failure never stopping
the next; the routine's receipts are committed as its session commits them, through the hooks, to the rehearsal's
origin."""

import os
import re
import subprocess
from datetime import date
from pathlib import Path

from fno.rehearsal.rehearse import commit_receipts, run_routine
from fno.rehearsal.routines import ROUTINES, Command, Routine

REPOSITORY = Path(__file__).resolve().parents[2]
DAY = date(2026, 10, 23)


COMMAND = re.compile(r"python\s+-m\s+fno\s+((?:[a-z][a-z0-9-]*\s+)*[a-z][a-z0-9-]*)")
NOT_REHEARSED: dict[str, set[str]] = {}  # a routine's command a rehearsal leaves out, with its reason (none today)


def section(title: str) -> str:
    text = (REPOSITORY / "CLAUDE.md").read_text(encoding="utf-8")
    start = text.index(f"## {title}")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else None]


def steps(text: str) -> dict[str, str]:
    """The section's numbered steps (`1.`, `1b.`, `2.`), before any `###` subsection (the daily one's 3 pm parts are
    the run's own children, not the routine's commands)."""
    text = text.split("\n### ", 1)[0]
    found = re.split(r"^(\d+[a-z]?)\. ", text, flags=re.M)
    return dict(zip(found[1::2], found[2::2], strict=True))


def names(text: str) -> set[str]:
    return {" ".join(m.group(1).split()) for m in COMMAND.finditer(text)}


def documented(routine) -> set[str]:
    """Every `python -m fno` command the routine's own steps name: the morning and the evening share their section,
    split by its own markers (1b and "The morning:", 1c and "The evening:")."""
    parts = steps(section(routine.section))
    if routine.name not in ("morning", "evening"):
        return set().union(*(names(t) for t in parts.values()))
    morning_2, evening_2 = re.split(r"The\s+evening:", parts["2"], maxsplit=1)  # the doc wraps its lines
    return names(parts["1b"] + morning_2) if routine.name == "morning" else names(parts["1c"] + evening_2)


def rehearsed(routine) -> set[str]:
    return {" ".join(a for a in c.args[: next((i for i, a in enumerate(c.args) if a.startswith("--")), None)])
            for c in routine.commands}  # fmt: skip


def test_every_routine_command_in_claude_md_is_rehearsed_and_nothing_else():
    """Judge 563 SF2: both ways. A command the routine's steps name is in its list (or named as not rehearsed), and
    the list holds nothing its steps do not name."""
    for routine in ROUTINES.values():
        expected = documented(routine) - NOT_REHEARSED.get(routine.name, set())
        assert rehearsed(routine) == expected, routine.name
        for path in routine.receipts:
            assert path.rstrip("/") in section(routine.section).replace("<morning|evening>", routine.name), path


def test_the_two_way_check_catches_a_missing_and_an_extra_command():
    evening = ROUTINES["evening"]
    short = Routine("evening", evening.section, evening.start, evening.commands[:-1])
    extra = Routine("evening", evening.section, evening.start, (*evening.commands, Command(("weather", "capture"))))
    assert rehearsed(short) != documented(evening) and rehearsed(extra) != documented(evening)


FAKE_FNO = """import sys
args = sys.argv[1:]
print("ran " + " ".join(args), flush=True)
raise SystemExit(3 if args[0] == "fails" else 0)
"""


def test_the_commands_run_in_order_a_background_one_first_and_a_failure_never_stops_the_next(tmp_path):
    (tmp_path / "fno").mkdir()
    (tmp_path / "fno" / "__init__.py").write_text("")
    (tmp_path / "fno" / "__main__.py").write_text(FAKE_FNO)
    routine = Routine("test", "-", None, (Command(("bg", "{day}"), background=True), Command(("fails",)),
                                         Command(("after", "{week_ago}"))))  # fmt: skip
    lines = []
    code, line = run_routine(tmp_path, routine, DAY, dict(os.environ), lines.append)
    assert (code, line) == (1, "failed: fails")
    assert (
        lines[:2] == ["ran fails", "ran after 2026-10-16"] and lines[2] == "ran bg 2026-10-23"
    )  # bg relayed at its end


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def test_the_receipts_are_committed_through_the_hooks_and_pushed_to_the_rehearsal_s_origin(tmp_path):
    origin, clone = tmp_path / "origin.git", tmp_path / "clone"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(clone))
    for key, value in (("user.email", "t@example.com"), ("user.name", "t"), ("commit.gpgsign", "false")):
        git(clone, "config", key, value)
    git(clone, "checkout", "-q", "-b", "main")
    hooks = clone / ".githooks"
    hooks.mkdir()
    (hooks / "pre-commit").write_text("#!/bin/sh\ntouch ../hook-ran\n")
    (hooks / "pre-commit").chmod(0o755)
    git(clone, "config", "core.hooksPath", ".githooks")
    (clone / "receipts/data/forecast_lab/v1/evening").mkdir(parents=True)
    (clone / "receipts/data/forecast_lab/v1/evening/a.sha256").write_text("x")
    (clone / "other.txt").write_text("not the routine's")
    commit_receipts(clone, ("receipts/data/forecast_lab/v1/evening/", "research/missing/"), "Rehearsal evening",
                    dict(os.environ))  # fmt: skip
    assert (
        git(origin, "log", "--format=%s", "main").strip() == "Rehearsal evening" and (tmp_path / "hook-ran").is_file()
    )
    assert git(origin, "ls-tree", "-r", "--name-only", "main").split() == [
        "receipts/data/forecast_lab/v1/evening/a.sha256"
    ]
