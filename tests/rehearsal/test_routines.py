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


def section(title: str) -> str:
    text = (REPOSITORY / "CLAUDE.md").read_text(encoding="utf-8")
    start = text.index(f"## {title}")
    end = text.find("\n## ", start + 1)
    return text[start : end if end != -1 else None]


def test_every_routine_command_is_its_claude_md_section_s_own():
    for routine in ROUTINES.values():
        text = section(routine.section)
        for command in routine.commands:
            first_option = next((i for i, a in enumerate(command.args) if a.startswith("--")), len(command.args))
            words = command.args[:first_option]  # the command's name; the rehearsal names the day itself
            pattern = r"python\s+-m\s+fno\s+" + r"\s+".join(map(re.escape, words))  # the doc wraps its lines
            assert re.search(pattern, text), (routine.name, words)
        for path in routine.receipts:
            assert path.rstrip("/") in text.replace("<morning|evening>", routine.name), (routine.name, path)


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
