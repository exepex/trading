"""Story G10 completion, criteria 1-2: protocol v4's 14:30-14:40 capture is a quote part of the daily run, live from
`daily.live_from.v4_pack`, with A4e's window times (never copied); it commits as soon as it ends, never after NIFTY;
and NIFTY's 14:55 pathspec no longer takes the v4 dataset's files."""

import shutil
import subprocess
from datetime import date, datetime, time

from fno.config import ROOT, load_app_config
from fno.constants import STEP_FAILED, STEP_NOT_LIVE, STEP_OK
from fno.daily.earlier_run import PartMarkers
from fno.daily.part_locks import PART_LOCKS, PartLocks
from fno.daily.quote_parts import NIFTY_QUOTES, NOT_IN_THIS_RUN, QUOTE_PARTS, QuoteParts
from fno.daily.quote_steps import FinishQuoteParts, ServicingWaiter, StartQuoteParts
from fno.daily.v4_part import v4_part, v4_quotes
from fno.models import IST
from fno.quotes.window import named_window
from tests.timetable.fakes import Clock

from .fakes import FakeProcesses, RecordingCommitter, part_files

DAY = date(2026, 10, 26)
WINDOW = named_window(load_app_config(), "v4")
V4 = v4_part(WINDOW)
PARTS = (*QUOTE_PARTS, V4)
NIFTY, NSE, INDICES = (part.arguments for part in QUOTE_PARTS)
GROWW = "research/data/quotes/groww/derivatives/quote-snapshots/2026/10"
V4_FOLDER = "research/data/quotes/groww/derivatives/quote-snapshots-v4/2026/10"
WEEKLY = "research/data/quotes/groww/derivatives/quote-snapshots-weekly/2026/10"


def at(hour, minute):
    return datetime(2026, 10, 26, hour, minute, tzinfo=IST)


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "alert sent"


class Markers(PartMarkers):
    def __init__(self, recorded=None):
        self.by = recorded or {}

    def recorded(self, day, canonicals):
        return self.by.get(canonicals)

    def missing(self, day, canonicals):
        return [] if canonicals in self.by else [f"{stem}.canonical" for _, stem in canonicals]

    def ended_none(self, day, canonicals):
        return []


def run(tmp_path, clock, live, ends=(14, 34), recorded=None, files=None):
    script = {NIFTY: (at(14, 58), 0, ["recorded"]), NSE: (at(14, 58), 0, ["recorded"]),
              INDICES: (at(15, 12), 0, ["recorded"]), V4.arguments: (at(*ends), 0, ["recorded"])}  # fmt: skip
    processes, commits, alerts = FakeProcesses(clock, script), [], Alerts()
    parts = QuoteParts(PARTS, processes, RecordingCommitter(clock, commits), part_files(files or {}), alerts, clock,
                       PartLocks(tmp_path / PART_LOCKS), Markers(recorded), live={"v4_pack": live})  # fmt: skip
    return parts, processes, commits, alerts


def test_the_part_is_a4e_s_window_with_its_own_times_and_dataset():
    assert V4.arguments == ("quotes", "record", "--window", "v4")
    assert (WINDOW.start, WINDOW.end) == (time(14, 30), time(14, 40))
    assert V4.not_before == time(14, 3) and V4.window_end == time(14, 40)  # 14:30 - 30 min + O1's 3 min margin
    assert V4.pathspecs == (":(glob)research/data/quotes/groww/derivatives/quote-snapshots-v4/**",)
    assert V4.canonicals == (("groww/derivatives/quote-snapshots-v4", "nifty"),)
    assert V4.live_key == "v4_pack" and V4.apart and V4.starts_after is None


def test_live_today_it_starts_at_the_run_s_start_and_commits_alone_before_nifty_starts(tmp_path):
    clock = Clock()
    clock.now = at(14, 7)
    files = {V4.pathspecs[0]: [f"{V4_FOLDER}/nifty_20261026.canonical"]}
    parts, processes, commits, alerts = run(tmp_path, clock, live=DAY, files=files)
    parts.start(DAY)
    assert [a for _, a in processes.started] == [V4.arguments]  # NIFTY and NSE wait for 14:38
    clock.now = at(14, 35)
    parts.service()
    assert [m for _, m, _ in commits] == ["3 pm quotes 2026-10-26 v4"] and "nifty" not in parts.results
    assert parts.results["v4"]["status"] == STEP_OK and alerts.sent == []


def test_not_live_it_never_starts_is_not_live_and_is_no_problem_of_the_day(tmp_path):
    for live in (None, date(2026, 10, 27)):
        clock = Clock()
        clock.now = at(14, 7)
        parts, processes, commits, alerts = run(tmp_path / str(live), clock, live=live)
        step = StartQuoteParts(parts).run(DAY)
        assert "v4 not live" in step.result["reason"]
        clock.now = at(15, 20)
        done = FinishQuoteParts(parts, ServicingWaiter(parts, clock, sleep=clock.advance)).run(DAY)
        assert V4.arguments not in [a for _, a in processes.started]
        assert done.result["parts"]["v4"]["status"] == STEP_NOT_LIVE and done.result["status"] == STEP_OK
        assert not any("v4" in text for text in alerts.sent)


def test_a_rerun_after_14_40_takes_an_earlier_run_s_capture_or_fails_it_once(tmp_path):
    clock = Clock()
    clock.now = at(14, 50)
    parts, processes, _, alerts = run(tmp_path / "none", clock, live=DAY)
    parts.resume(DAY)
    assert parts.results["v4"]["status"] == STEP_FAILED and parts.results["v4"]["reason"] == NOT_IN_THIS_RUN
    assert sum("v4" in text for text in alerts.sent) == 1 and V4.arguments not in [a for _, a in processes.started]
    parts, processes, _, alerts = run(tmp_path / "marker", clock, live=DAY, recorded={V4.canonicals: "c1"})
    parts.resume(DAY)
    assert V4.arguments not in [a for _, a in processes.started] and not any("v4" in t for t in alerts.sent)


def _git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True).stdout


def test_each_spec_stages_only_its_own_files_with_real_git(tmp_path):
    _git(tmp_path, "init", "-q")
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")
    own = {
        "nifty": [f"{GROWW}/nifty_20261026.canonical", f"{GROWW}/nifty_20261026_145500.meta.json"],
        "v4": [f"{V4_FOLDER}/nifty_20261026.canonical", f"{V4_FOLDER}/nifty_20261026_143000.meta.json"],
        "weekly": [f"{WEEKLY}/niftyweekly_20261026.canonical"],
    }
    raw = [f"{V4_FOLDER}/nifty_20261026_143000.csv", f"{GROWW}/nifty_20261026_145500.csv"]
    for path in [*sum(own.values(), []), *raw]:
        (tmp_path / path).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / path).write_text("x")

    def staged(spec):
        lines = _git(tmp_path, "add", "--dry-run", spec).splitlines()
        return sorted(line.removeprefix("add '").removesuffix("'") for line in lines if line)

    assert staged(NIFTY_QUOTES) == sorted(own["nifty"])  # never a v4 file, never the weekly
    assert staged(v4_quotes(WINDOW)) == sorted(own["v4"])  # never a raw quote file (`.gitignore`)
    assert staged(":(glob)research/data/quotes/groww/**/niftyweekly_*") == own["weekly"]


def test_claude_md_gives_the_code_s_paths():
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").replace("\n   ", " ")
    assert f"'{NIFTY_QUOTES}'" in text and f"'{v4_quotes(WINDOW)}'" in text
    assert "':(glob)research/data/quotes/groww/**/nifty_*'" not in text
