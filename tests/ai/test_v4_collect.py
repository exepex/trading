"""Story G11 (round 2b step 4; completion C9, C11, C13, C19): a v4 day from fire to rows. The test publishes each
book's two files the way the routine's `seal` and `reveal` do; collect judges them under v4's terms (15:10 on
GitHub's receipt) against the labels and envelope the fire logged (the input is never rebuilt), writes each audit once
with the release record's SHA, and the settled days become one row per question; pending days are counted, never
written. The fire log's edits, a lost log, the late go-live and judge 586's F2 are in `test_v4_collect_log.py`."""

import json
import shutil
from datetime import timedelta

import pytest

from fno.ai.draw_seed import WeekSeed
from fno.ai.history import RepoHistory
from fno.ai.paths import CLOSES_FILE
from fno.ai.run_terms import V4_TERMS
from fno.ai.seal import Commitment, new_salt, reveal_text
from fno.ai.transcript_audit import TranscriptAudits, new_audit
from fno.ai.v4_book_inputs import V4BookInputs
from fno.ai.v4_collect import V4BookCollector
from fno.ai.v4_fire import V4BookFirer
from fno.ai.v4_pointer import parse_v4_pointer, v4_labels
from fno.ai.v4_settle import V4RowSettler
from fno.constants import BOOK2_HYBRID, BOOK3_AI, V3_RV_20S, V4_SLOT_AI, V6_BIG_MOVE_1S, V6_BIG_MOVE_5S
from fno.forecast_scoring.v4.inputs import ForecastFiles
from fno.forecast_v4_rules import records
from tests.ai.fakes import ROOT, FakeReceipts, git
from tests.ai.test_v4_fire import DAY, Ledger, NoBudgetStop, Released, Series, at, write_rules
from tests.pipeline.fakes import FakeTrigger, RecordingAlerts

SETTLED = {DAY.isocalendar()[:2]: WeekSeed("2026-W44", "2026-10-30", "25000.0", "e" * 64)}  # the week is drawn


class V4Desk:
    def __init__(self, root, ledger=None):
        self.root, self.receipts, self.alerts = root, FakeReceipts(), RecordingAlerts()
        (root / CLOSES_FILE).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / CLOSES_FILE, root / CLOSES_FILE)
        git(root, "init", "-q", "-b", "main")
        git(root, "config", "user.email", "desk@example.invalid")
        git(root, "config", "user.name", "desk")
        git(root, "add", ".")
        git(root, "commit", "-q", "-m", "closes")
        self.sessions = [DAY]  # the v4 sessions since go-live the collect may revisit (a test adds earlier ones)
        self.triggers = {BOOK2_HYBRID: FakeTrigger(BOOK2_HYBRID), BOOK3_AI: FakeTrigger(BOOK3_AI)}
        self.v4 = write_rules(root / "research/forecasts/v4")
        self.inputs = V4BookInputs(root, ledger or Ledger(), ForecastFiles(self.v4), Series())

    def fire(self, now=None):
        firer = V4BookFirer(self.root, self.triggers, lambda: Released(), self.inputs, self.alerts,
                            lambda: now or at(14, 33), DAY, lambda day: [], NoBudgetStop(),
                            lambda first, last: [])  # fmt: skip
        return firer.fire(DAY)

    def answer(self, book, sealed=None, revealed=None, values=(0.05, 0.18), model="claude-opus-5-5"):
        built = parse_v4_pointer(self.triggers[book].fired[-1].to_text()).input
        forecasts = {q: {"probability": p, "reason": f"reason for {q}"} for q, p in zip(built["questions"], values)}
        answer = {**v4_labels(built), "model_reported": model, "forecasts": forecasts}
        salt = new_salt()
        commit_sealed = self._publish(V4_TERMS.commitment_path(DAY, book), Commitment.of(answer, salt).to_text())
        commit_revealed = self._publish(V4_TERMS.reveal_path(DAY, book), reveal_text(answer, salt))
        self.receipts.times |= {commit_sealed: sealed or at(15, 4), commit_revealed: revealed or at(15, 10, 12)}

    def _publish(self, path, text):
        (self.root / path).parent.mkdir(parents=True, exist_ok=True)
        (self.root / path).write_text(text, encoding="utf-8")
        git(self.root, "add", path)
        git(self.root, "commit", "-q", "-m", path)
        return git(self.root, "rev-parse", "HEAD").strip()

    def collect(self, released=None, day=DAY, now=None, live_from=None):
        collector = V4BookCollector(self.root, RepoHistory(self.root), self.receipts, self.inputs,
                                    lambda: released or Released(), lambda: now or at(15, 31),
                                    live_from or min(self.sessions),
                                    lambda first, last: [d for d in self.sessions if first <= d <= last])  # fmt: skip
        return collector.collect(day)

    def settle(self, seeds=SETTLED, audited=(BOOK2_HYBRID, BOOK3_AI)):
        """Records a clean transcript audit for each fired book in `audited` (v4's first 10 days are all audited,
        round 2c), then settles."""
        for book in audited:
            self.audit_transcript(book)
        return V4RowSettler(self.root, self.v4, lambda: seeds).settle()

    def audit_transcript(self, book, breaches=()):
        log_file = self.root / V4_TERMS.fired_path(DAY)
        fired = V4_TERMS.fired_books(json.loads(log_file.read_text())).get(book, {}) if log_file.is_file() else {}
        audits = TranscriptAudits(self.root, V4_TERMS)
        if not fired.get("fired") or audits.get(DAY, book) is not None:
            return None
        return audits.record(DAY, new_audit(DAY, book, fired, list(breaches), "tool calls read", "judge", at(16, 0)))

    def audit(self, book):
        return self.audit_of(DAY, book)

    def audit_of(self, day, book):
        return json.loads((self.root / V4_TERMS.audit_path(day, book)).read_text())

    def row(self, book, question):
        return records.read(records.path(self.v4, f"{book}_v2", question)).get(DAY.isoformat())


@pytest.fixture
def desk(tmp_path):
    return V4Desk(tmp_path)


def test_two_on_time_books_become_ok_rows_for_both_questions(desk):
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.answer(BOOK2_HYBRID, values=(0.05, None))  # V6a inside base rate 0.04 +- 0.10; V6b has no envelope: null
    assert all(" on_time: collected" in line for line in desk.collect())
    assert desk.audit(BOOK3_AI)["released_sha256"] == "d" * 64
    assert desk.settle()[0].endswith("4 v4 row(s) added; 0 day(s) awaiting audit")
    row = desk.row(BOOK3_AI, V6_BIG_MOVE_5S)
    assert (row.status, row.value, row.slot, row.kind) == ("ok", "0.18", "ai_team", "ai")
    hybrid = [desk.row(BOOK2_HYBRID, q) for q in (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S)]
    assert [(r.status, r.value, r.slot) for r in hybrid] == [("ok", "0.05", "hybrid"), ("invalid", "", "hybrid")]
    assert desk.settle()[0].startswith("Omenix F&O AI forecasts v4: 0 v4 row(s) added")  # written once


@pytest.mark.parametrize(("sealed", "status"), [(at(15, 10), "ok"), (at(15, 10) + timedelta(seconds=1), "late")])
def test_the_deadline_is_1510_on_githubs_receipt(desk, sealed, status):
    desk.fire()
    desk.answer(BOOK3_AI, sealed=sealed)
    desk.collect()
    desk.settle()
    assert desk.row(BOOK3_AI, V6_BIG_MOVE_1S).status == status


def test_a_book_that_never_answered_is_a_no_submission_miss(desk):
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.collect()
    desk.settle()
    assert {desk.row(BOOK2_HYBRID, q).status for q in (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S)} == {"no_submission"}


def test_a_session_the_fire_never_ran_is_a_not_fired_miss_for_every_question(desk):
    desk.collect()  # no fire log, a released pack
    desk.settle()
    assert desk.row(BOOK3_AI, V6_BIG_MOVE_5S).status == "not_fired"
    assert "never ran" in desk.audit(BOOK2_HYBRID)["fire"]["reason"]


def test_no_released_pack_collects_nothing(desk):
    lines = desk.collect(released=Released(late=True))  # the real class returns a system_late record
    assert "nothing collected (no row)" in lines[0] and not (desk.root / V4_TERMS.folder).exists()


def test_a_first_ten_days_session_waits_for_its_transcript_audit_and_gets_no_row(desk):
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.collect()
    lines = desk.settle(audited=())
    # Hybrid never answered: a settled miss (2 rows); Book 3 was on time but its audit is due: it waits
    assert lines[0].endswith("2 v4 row(s) added; 1 day(s) awaiting audit") and "transcript audit due" in lines[1]
    assert desk.row(BOOK3_AI, V6_BIG_MOVE_1S) is None  # on time but unaudited: no row yet
    desk.settle()  # the audit lands: the row follows
    assert desk.row(BOOK3_AI, V6_BIG_MOVE_1S).status == "ok"


def test_after_ten_fired_days_a_day_whose_week_is_not_drawn_waits(desk):
    for back in range(1, 11):  # ten earlier v4 days with both books fired: DAY is the eleventh
        earlier = DAY - timedelta(days=back)
        log = {"released": True, "books": {b: {"fired": True, "version": "x"} for b in (BOOK2_HYBRID, BOOK3_AI)}}
        (desk.root / V4_TERMS.fired_path(earlier)).parent.mkdir(parents=True, exist_ok=True)
        (desk.root / V4_TERMS.fired_path(earlier)).write_text(json.dumps(log))
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.collect()
    lines = desk.settle(seeds={}, audited=())
    assert lines[0].endswith("2 v4 row(s) added; 1 day(s) awaiting audit") and "weekly audit draw" in lines[1]


def test_the_verdict_comes_from_the_fire_log_so_a_file_changed_after_the_fire_changes_nothing(desk):
    """Review of dfb26381: a late close or A16 row after the fire must not turn an on-time answer invalid."""
    desk.fire()
    desk.answer(BOOK3_AI)
    with (desk.root / CLOSES_FILE).open("a", encoding="utf-8") as closes:
        closes.write("2026-10-23,regular,25100.0,12.1,late.csv," + "f" * 64 + "\n")  # O6's late evening extension
    desk.collect()
    assert desk.audit(BOOK3_AI)["status"] == "on_time"


def test_an_answer_for_another_input_than_the_logged_one_is_invalid(desk):
    desk.fire()
    desk.answer(BOOK3_AI)
    log_file = desk.root / V4_TERMS.fired_path(DAY)
    log = json.loads(log_file.read_text())
    log["books"][BOOK3_AI]["labels"]["export_sha256"] = "0" * 64
    log_file.write_text(json.dumps(log))
    desk.collect()
    assert desk.audit(BOOK3_AI)["status"] == "invalid"


def test_a_missing_fire_log_while_a_commitment_exists_waits_never_not_fired(desk):
    """Review of dfb26381: the fire ran and its log's push was lost; the books' on-time answers must not be lost."""
    desk.fire()
    desk.answer(BOOK3_AI)
    (desk.root / V4_TERMS.fired_path(DAY)).unlink()
    lines = desk.collect()
    assert len(lines) == 1 and "awaiting the fire log: book3_ai's commitment exists" in lines[0]
    assert not (desk.root / V4_TERMS.audit_path(DAY, BOOK3_AI)).exists()


def test_today_waits_for_every_fired_books_reveal_before_1530(desk):
    desk.fire()
    desk.answer(BOOK3_AI)  # Book 2 fired but has not revealed
    early = desk.collect(now=at(15, 12))
    assert len(early) == 1 and "too early: not every fired book has revealed" in early[0]
    assert all("collected" in line or "no_submission" in line for line in desk.collect(now=at(15, 30)))


@pytest.mark.parametrize("received", [at(15, 10), at(15, 10, 1), at(15, 9, 59)])
def test_v4s_deadline_is_g10s_receipt_rule(received):
    """Criterion 4: the same rule as G10's check (fno/v4_pack/commitment.py), reused through its constant."""
    from fno.v4_pack.commitment import on_time

    assert (received <= V4_TERMS.receipt_deadline(DAY)) == on_time(received, DAY)


def test_an_unknown_github_receipt_writes_no_verdict_and_the_next_collect_retries_it(desk):
    """G11 C19: never a guessed time; the whole day waits (exposure needs both books' receipt times)."""
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.answer(BOOK2_HYBRID, values=(0.05, None))
    known, desk.receipts.times = desk.receipts.times, {}  # GitHub's log cannot answer yet
    lines = desk.collect()
    assert len(lines) == 1 and "awaiting GitHub's receipt (no push of" in lines[0]
    assert not any((desk.root / V4_TERMS.audit_path(DAY, b)).exists() for b in (BOOK2_HYBRID, BOOK3_AI))
    desk.receipts.times = known  # the next collect finds them
    assert all(" on_time: collected" in line for line in desk.collect())


def test_a_past_session_the_collect_never_ran_is_caught_up_as_not_fired(desk):
    earlier = DAY - timedelta(days=3)
    desk.sessions = [earlier, DAY]
    desk.fire()
    desk.answer(BOOK3_AI)
    lines = desk.collect()
    assert any(line.startswith(f"Omenix F&O AI forecasts v4 (GitHub Actions): {earlier}: book3_ai not_fired")
               for line in lines)  # fmt: skip
    assert desk.audit(BOOK3_AI)["status"] == "on_time"  # today's day collected as before
    assert json.loads((desk.root / V4_TERMS.audit_path(earlier, BOOK3_AI)).read_text())["status"] == "not_fired"
    assert all(earlier.isoformat() not in line for line in desk.collect())  # collected once: never revisited


def test_nothing_pending_says_zero_days_awaiting(desk):
    desk.collect()
    assert desk.settle()[0].endswith("0 day(s) awaiting audit")


def test_a_question_the_prompt_does_not_define_is_a_not_fired_row_for_every_question_never_a_gap(tmp_path):
    """Review of dfb26381: the refused book keeps its registered questions, so each gets its not_fired miss."""
    desk = V4Desk(tmp_path, Ledger(extra=[(V3_RV_20S, V4_SLOT_AI)]))
    desk.fire()
    desk.answer(BOOK2_HYBRID, values=(0.05, None))
    desk.collect()
    lines = desk.settle()
    assert "NOT settled" not in " ".join(lines)
    statuses = {q: desk.row(BOOK3_AI, q).status for q in (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S, V3_RV_20S)}
    assert statuses == dict.fromkeys(statuses, "not_fired")


def test_one_broken_audit_is_said_and_never_stops_the_other_days(desk):
    desk.fire()
    desk.answer(BOOK3_AI)
    desk.collect()
    broken = desk.root / V4_TERMS.audit_path(DAY, BOOK2_HYBRID)
    audit = json.loads(broken.read_text())
    del audit["fire"]["questions"]
    broken.write_text(json.dumps(audit))
    lines = desk.settle()
    assert lines[0].endswith("2 v4 row(s) added; 0 day(s) awaiting audit")  # Book 3's day still lands
    assert any("NOT settled, fix and rerun" in line and "KeyError" in line for line in lines)
