"""Story G11 C14, O11's check for the AI books on protocol v4: one real live day replayed end to end, 22 Oct 2026,
the first session v4's rule forecasts ran live (O11's 16 Oct has no live v4 rule row: the back-fill ends 15 Oct).
Real: the committed closes, the day's committed rule and baseline rows, A16's committed rv rows, G8's outcome series
and scoring, F1/G5's book side (brief, seal, reveal) and every G11 step (fire, collect, settle). Replaced at their
seams only: the released 14:30 pack (G10's capture is not built; a fixture pack of the day), the two routine triggers
(the test plays each routine: it briefs, answers from its printed input, seals at 14:45 and reveals), GitHub's push
receipts (each commitment received 14:46, each reveal 15:10:15) and the transcript audits (recorded clean)."""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import replace
from datetime import date, datetime, time
from pathlib import Path

from fno.ai.budget_stop import BudgetCheck, BudgetStop
from fno.ai.history import RepoHistory
from fno.ai.paths import CLOSES_FILE
from fno.ai.receipts import PushReceipts
from fno.ai.run_terms import V4_TERMS
from fno.ai.transcript_audit import TranscriptAudits, new_audit
from fno.ai.v4_book_inputs import V4BookInputs
from fno.ai.v4_collect import V4BookCollector
from fno.ai.v4_fire import V4BookFirer
from fno.ai.v4_settle import V4RowSettler
from fno.config import ROOT
from fno.constants import AI_BOOKS, BOOK2_HYBRID, V4_SLOT_AI, V4_SLOT_HYBRID, V4_SLOT_RULES
from fno.forecast_scoring.v4.g7_series import G7Series
from fno.forecast_scoring.v4.inputs import ForecastFiles
from fno.forecast_scoring.v4.outcomes import SeriesOutcomes
from fno.forecast_scoring.v4.records import Registration, SlotRegistry
from fno.forecast_scoring.v4.scoring import V4Scoring
from fno.forecast_v4.terms import FAMILY_QUESTIONS, POINT_QUESTIONS
from fno.intraday.rv_table import RvTable
from fno.models import IST
from fno.v4_pack.release import ReleaseRecord
from tests.ai.fakes import Clock, FakeRoutine
from tests.ai.test_v4_input import a_pack
from tests.pipeline.fakes import FakeTrigger, RecordingAlerts

DAY = date(2026, 10, 22)
PACK_SHA = "d" * 64
RULES = {"v1_rv_next_session": "v1_close_blend", "v2_rv_next_5_sessions": "v2_close_blend",
         "v6_abs_move_2pct_next_session": "weather_vix_v1", "v6_abs_move_2pct_within_5_sessions": "weather_vix_v1",
         "v7_vix_higher_in_5_sessions": "v7_vix_vs_mean20"}  # fmt: skip  # the rules slot's forecaster per question
REAL_FOLDERS = (*set(RULES.values()), "har_daily", "har_intraday", "base_rate")
SLOT_FORECASTER = {V4_SLOT_HYBRID: "book2_hybrid_v2", V4_SLOT_AI: "book3_ai_v2"}
BOOK3_ANSWER = {"v1_rv_next_session": 9e-05, "v2_rv_next_5_sessions": 4.2e-04, "v6_abs_move_2pct_next_session": 0.04,
                "v6_abs_move_2pct_within_5_sessions": 0.16, "v7_vix_higher_in_5_sessions": 0.45}  # fmt: skip


def at(hh, mm, ss=0):
    return datetime.combine(DAY, time(hh, mm, ss), IST)


class Slots(SlotRegistry):
    """All 15 family slots registered from the day (the freeze builder's rules rows and G11's ten)."""

    def registered(self):
        rules = {(q, V4_SLOT_RULES): Registration(RULES[q], DAY) for q in FAMILY_QUESTIONS}
        return rules | {(q, s): Registration(f, DAY) for q in FAMILY_QUESTIONS for s, f in SLOT_FORECASTER.items()}


class Released:
    def release(self, day):
        return ReleaseRecord(day, "A", f"v4/packs/{day.year}/{day}.json", PACK_SHA, at(14, 40))

    def pack(self, release):
        return replace(a_pack(), day=DAY)


class Open(BudgetStop):
    def check(self, day):
        return BudgetCheck("", "")


class MessageReceipts(PushReceipts):
    """GitHub's receipt of each push by what it carried: a commitment at 14:46, anything else (reveal) at 15:10:15."""

    def __init__(self, root: Path):
        self.root = root

    def received_at(self, commit: str) -> datetime:
        subject = subprocess.run(["git", "log", "-1", "--format=%s", commit], cwd=self.root, capture_output=True,
                                 text=True, check=True).stdout  # fmt: skip
        return at(14, 46) if "commitment" in subject else at(15, 10, 15)


def answer_of(book: str, printed_input: dict) -> dict:
    """What each scripted routine answers: Book 3 its own numbers; Hybrid the middle of its envelope (null outside)."""
    forecasts = {}
    for question in printed_input["questions"]:
        key = "value" if question in POINT_QUESTIONS else "probability"
        if book == BOOK2_HYBRID:
            bounds = printed_input["rules"]["envelope"][question]
            value = None if bounds is None else (bounds[0] + bounds[1]) / 2
        else:
            value = BOOK3_ANSWER[question]
        forecasts[question] = {key: value, "reason": f"scripted replay answer for {question}"}
    return {"model_reported": "claude-opus-5-5", "forecasts": forecasts}


def replay(root: Path) -> dict:
    """The day from fire to G8's report; the lines each step printed and G8's live V6a scores."""
    v4 = root / "research" / "forecasts" / "v4"
    for name in REAL_FOLDERS:
        shutil.copytree(ROOT / "research" / "forecasts" / "v4" / name, v4 / name)
    for path in (CLOSES_FILE, *(f"agents/forecast/{b}_v2.md" for b in AI_BOOKS)):
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, root / path)
    git = (["init", "-q", "-b", "main"], ["config", "user.email", "replay@example.invalid"],
           ["config", "user.name", "replay"], ["add", "."], ["commit", "-q", "-m", "the day's files"])  # fmt: skip
    for args in git:
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    closes = (root / CLOSES_FILE).read_text(encoding="utf-8")
    series = G7Series(closes, RvTable(ROOT / "research" / "data" / "intraday").rows)
    inputs = V4BookInputs(root, Slots(), ForecastFiles(v4), series)
    triggers = {book: FakeTrigger(book) for book in AI_BOOKS}
    lines = V4BookFirer(root, triggers, Released, inputs, RecordingAlerts(), lambda: at(14, 41), DAY,
                        lambda day: [], Open()).fire(DAY)  # fmt: skip
    for book in AI_BOOKS:
        routine = FakeRoutine(root, Clock(at(14, 41)))
        session = routine.session()
        session.brief(triggers[book].fired[-1].to_text())
        printed = json.loads(routine.printed[-1])
        answer_file = root / ".ai_book" / "answer.json"
        answer_file.write_text(json.dumps(answer_of(book, printed)), encoding="utf-8")
        routine.clock.now = at(14, 45)
        session.seal(answer_file)
        while not (root / V4_TERMS.reveal_path(DAY, book)).exists():
            session.reveal()
        lines += [f"{book}: {routine.printed[-2]}"]
    collector = V4BookCollector(root, RepoHistory(root), MessageReceipts(root), inputs, Released, lambda: at(15, 31),
                                DAY, lambda first, last: [DAY])  # fmt: skip
    lines += collector.collect(DAY)
    audits = TranscriptAudits(root, V4_TERMS)
    log = V4_TERMS.fired_books(json.loads((root / V4_TERMS.fired_path(DAY)).read_text(encoding="utf-8")))
    for book in AI_BOOKS:
        audits.record(DAY, new_audit(DAY, book, log[book], [], "replay: no session to read", "replay", at(16, 0)))
    lines += V4RowSettler(root, v4, lambda: {}).settle()
    scoring = V4Scoring(ForecastFiles(v4), SeriesOutcomes(series), Slots())
    return {"lines": lines, "folder": v4, "report": scoring.question_report("v6_abs_move_2pct_next_session")}
