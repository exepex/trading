"""Stories F1 (criteria 3, 4, 5 and 7) and G5 (criteria 1 and 2), end to end with a fake trigger and fake routines:
the fire sends Hybrid the rules and the AI team none; on-time sealed answers become five records each; a late, missing,
unrevealed, broken, exposed or wrong-model answer records "no forecast" (never imputed) with the reason in the audit;
the records carry the committed pack's hash; and the first collection stands."""

import hashlib
import json
from datetime import timedelta

import pytest

from fno.ai.answer import complete_answer
from fno.ai.book_run import answer_labels
from fno.ai.collect import AiForecastCollector
from fno.ai.export import build_export
from fno.ai.fire import AiBookFirer
from fno.ai.history import RepoHistory
from fno.ai.paths import audit_path, commitment_path, fired_path, pack_path, records_path, reveal_path
from fno.ai.pointer import parse_pointer
from fno.ai.record_writer import AiRecordWriter
from fno.ai.seal import Commitment, new_salt, reveal_text
from fno.ai.versions import current_version
from fno.constants import BOOK2_HYBRID, BOOK3_AI, FORECAST_QUESTIONS
from fno.forecast.record_files import read_records_v2
from tests.ai.fakes import DAY, Clock, FakeReceipts, FakeRoutine, at, draft, git, make_desk_repo
from tests.pipeline.fakes import FakeTrigger, RecordingAlerts

# Book 1's values of the golden day, rounded: inside Hybrid's envelope on every question
INSIDE_ENVELOPE = dict(zip(FORECAST_QUESTIONS, (0.55, 0.42, 0.41, 0.42, 0.7)))


class Desk:
    def __init__(self, root):
        self.root, self.receipts, self.alerts = make_desk_repo(root), FakeReceipts(), RecordingAlerts()
        self.triggers = {BOOK2_HYBRID: FakeTrigger(BOOK2_HYBRID), BOOK3_AI: FakeTrigger(BOOK3_AI)}

    def fire(self):
        return AiBookFirer(self.root, self.triggers, self.alerts, Clock(at(15, 10, 30))).fire(DAY)

    def answer(self, book, values=None, sealed=None, revealed=None, model="claude-opus-5-5"):
        """The book's routine answers from the text it was fired with; GitHub logs its two pushes at these times."""
        sealed, revealed = sealed or at(15, 13), revealed or at(15, 15, 12)
        values = values or (INSIDE_ENVELOPE if book == BOOK2_HYBRID else None)
        text = self.triggers[book].fired[-1].to_text()
        commits = FakeRoutine(self.root, Clock(at(15, 11))).run(text, draft(values, model), sealed)
        self.receipts.times |= {commits[0]: sealed, commits[1]: revealed}
        return commits

    def collect(self):
        writer = AiRecordWriter(self.root)
        return AiForecastCollector(self.root, RepoHistory(self.root), self.receipts, writer, Clock(at(15, 16))).collect(
            DAY
        )

    def records(self, book):
        return {r.record.question: r for r in read_records_v2((self.root / records_path(DAY, book)).read_text())}

    def audit(self, book):
        return json.loads((self.root / audit_path(DAY, book)).read_text())


@pytest.fixture
def desk(tmp_path):
    return Desk(tmp_path)


def test_the_fire_gives_hybrid_the_rules_and_the_ai_team_none(desk):
    assert desk.fire() == ["Omenix F&O AI forecasts (GitHub Actions): 2026-10-13: fired book2_hybrid, book3_ai of "
                           "book2_hybrid, book3_ai"]  # fmt: skip
    hybrid, team = (parse_pointer(desk.triggers[b].fired[0].to_text()) for b in (BOOK2_HYBRID, BOOK3_AI))
    assert hybrid.rules["q5_rv20_below_atm_iv30"]["book1_rules"] == pytest.approx(0.708) and team.rules is None
    log = json.loads((desk.root / fired_path(DAY)).read_text())
    assert log[BOOK3_AI]["fired"] and log[BOOK3_AI]["session"].startswith("https://claude.ai/code/session_")
    assert desk.fire()[0].endswith("already fired (fired once per day)")
    assert sum(len(t.fired) for t in desk.triggers.values()) == 2


def test_on_time_sealed_answers_become_five_records_each_with_the_packs_hash(desk):
    desk.fire()
    desk.answer(BOOK2_HYBRID, INSIDE_ENVELOPE | {"q2_nifty_move_3pct_20d": 0.4})
    desk.answer(BOOK3_AI)
    lines = desk.collect()
    assert "book2_hybrid on_time: 5 of 5 probabilities; recorded" in lines[0]
    assert (
        lines[1]
        == "ai receipt: 2026-10-13 book2_hybrid status on_time commitment_received_at 2026-10-13T15:13:00+05:30"
    )
    pack_sha = hashlib.sha256((desk.root / pack_path(DAY)).read_bytes()).hexdigest()
    for book, value in ((BOOK2_HYBRID, 0.4), (BOOK3_AI, 0.5)):
        records = desk.records(book)
        assert records["q2_nifty_move_3pct_20d"].record.probability == value
        assert {r.record.pack_sha256 for r in records.values()} == {pack_sha}
        assert all(r.on_time and r.input_mode == "live_1500_proxy" for r in records.values())
        assert records["q1_nifty_up_20d"].record.method_or_version.startswith(f"{book}/v1/sha256:")
    audit = desk.audit(BOOK3_AI)
    assert audit["status"] == "on_time" and audit["model_check"] == "match" and audit["isolation"] == "sealed_same_day"
    assert audit["attempted"]["q1_nifty_up_20d"]["reason"] == "reason for q1_nifty_up_20d"
    assert audit["fire"]["session"].startswith("https://claude.ai/code/session_")


def test_a_commitment_received_after_1515_is_late_and_records_no_forecast(desk):
    desk.fire()
    desk.answer(BOOK3_AI, sealed=at(15, 15, 1), revealed=at(15, 15, 20))
    desk.collect()
    assert all(r.record.probability is None for r in desk.records(BOOK3_AI).values())
    audit = desk.audit(BOOK3_AI)
    assert audit["status"] == "late" and audit["attempted"]["q1_nifty_up_20d"]["probability"] == 0.5


def test_a_routine_that_never_answers_or_was_never_fired_records_no_forecast(desk):
    desk.triggers[BOOK3_AI] = FakeTrigger(BOOK3_AI, failure="HTTP 401: the routine's token was refused")
    desk.fire()
    assert "book3_ai not fired: HTTP 401" in desk.alerts.lines[0]
    desk.collect()
    assert desk.audit(BOOK2_HYBRID)["status"] == "no_submission"  # fired, but the AI was unavailable
    assert desk.audit(BOOK3_AI)["status"] == "not_fired"
    for book in (BOOK2_HYBRID, BOOK3_AI):
        records = desk.records(book)
        assert len(records) == 5 and all(r.record.probability is None for r in records.values())


def test_a_reveal_that_never_came_or_does_not_match_records_no_forecast(desk):
    desk.fire()
    commits = desk.answer(BOOK3_AI)
    del desk.receipts.times[commits[1]]  # GitHub's log does not show the reveal: unknown fails closed
    desk.answer(BOOK2_HYBRID)
    reveal = desk.root / reveal_path(DAY, BOOK2_HYBRID)
    reveal.write_text(reveal.read_text().replace('"probability": 0.55', '"probability": 0.6', 1))
    git(desk.root, "commit", "-qam", "a reveal rewritten after the fact")
    desk.collect()
    assert desk.audit(BOOK3_AI)["status"] == "not_revealed"
    assert desk.audit(BOOK2_HYBRID)["status"] == "on_time"  # the first published reveal counts, not the rewrite
    assert any("changed after it was first published" in n for n in desk.audit(BOOK2_HYBRID)["notes"])


def test_a_book_committing_after_the_other_books_answer_was_public_is_exposed(desk):
    desk.fire()
    desk.answer(BOOK2_HYBRID, sealed=at(15, 12), revealed=at(15, 12, 30))  # revealed early, before 15:15
    desk.answer(BOOK3_AI, sealed=at(15, 14))
    desk.collect()
    assert desk.audit(BOOK3_AI)["status"] == "exposed"
    assert all(r.record.probability is None for r in desk.records(BOOK3_AI).values())
    assert desk.audit(BOOK2_HYBRID)["status"] == "on_time"


def test_a_different_served_model_leaves_the_day_unscored_and_unknown_is_flagged(desk):
    desk.fire()
    desk.answer(BOOK2_HYBRID, model="claude-sonnet-5-5")
    desk.answer(BOOK3_AI, model="unknown")
    desk.collect()
    assert desk.audit(BOOK2_HYBRID)["status"] == "model_mismatch"
    assert all(r.record.probability is None for r in desk.records(BOOK2_HYBRID).values())
    assert desk.audit(BOOK3_AI)["model_check"] == "unverified" and desk.audit(BOOK3_AI)["status"] == "on_time"


def test_a_hybrid_answer_outside_its_envelope_loses_that_question_only(desk):
    desk.fire()
    pointer = parse_pointer(desk.triggers[BOOK2_HYBRID].fired[0].to_text())
    labels = answer_labels(pointer, build_export(desk.root, pointer, current_version(BOOK2_HYBRID)))
    answer = complete_answer(draft(dict.fromkeys(FORECAST_QUESTIONS, 0.45) | {"q4_vix_up_10d": 0.9}), labels)
    salt, transport = new_salt(), FakeRoutine(desk.root, Clock(at(15, 12))).transport
    sealed = transport.publish(commitment_path(DAY, BOOK2_HYBRID), Commitment.of(answer, salt).to_text(), "seal")
    revealed = transport.publish(reveal_path(DAY, BOOK2_HYBRID), reveal_text(answer, salt), "reveal")
    desk.receipts.times |= {sealed: at(15, 12), revealed: at(15, 15, 12)}  # a routine that skipped seal's checks
    desk.collect()
    records, audit = desk.records(BOOK2_HYBRID), desk.audit(BOOK2_HYBRID)
    assert records["q4_vix_up_10d"].record.probability is None and records["q1_nifty_up_20d"].record.probability == 0.45
    assert audit["problems"]["q4_vix_up_10d"].startswith("outside the envelope")
    assert audit["attempted"]["q4_vix_up_10d"]["probability"] == 0.9


def test_the_first_collection_stands(desk):
    desk.fire()
    desk.answer(BOOK3_AI)
    first = desk.collect()
    desk.receipts.times = {c: t + timedelta(minutes=30) for c, t in desk.receipts.times.items()}
    again = desk.collect()
    assert "recorded" in first[2] and again[2].endswith("already recorded; this collection differs, the first stands")
    assert desk.audit(BOOK3_AI)["status"] == "on_time"


def test_a_day_without_a_pack_fires_and_records_nothing(desk):
    (desk.root / pack_path(DAY)).unlink()
    assert desk.fire()[0].endswith("no v2 pack for the day; nothing fired")
    assert desk.collect()[0].endswith("no v2 pack for the day; nothing recorded")
