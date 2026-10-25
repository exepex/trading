"""Story F1t criterion 6: every status of the judging table from a constructed day (fake receipts and submissions),
first rule that applies wins."""

import pytest

from fno.ai.fire_once import FIRE_UNKNOWN, FIRED, NOT_FIRED
from fno.ai.outcome import EXPOSED, INVALID, LATE, MODEL_MISMATCH, NO_SUBMISSION, NOT_REVEALED
from fno.ai.seal import Commitment, commitment_hash, reveal_text
from fno.ai.submissions import Published, Submission
from fno.ai_trading.answer import complete_answer, labels_of
from fno.ai_trading.outcome import ACCEPTED, MODEL_UNVERIFIED, Deadlines, Judged, judge
from tests.ai.fakes import FakeReceipts

from .builders import MODEL, at, canonical, draft, pointer, shape_check

SALT = "a" * 32
DEADLINES = Deadlines(at(15, 10), at(15, 11))


def submitted(tmp_path, committed=DEADLINES.receipt, revealed=DEADLINES.reveal, reveal=True, **kwargs):
    labels = labels_of(pointer(tmp_path))
    answer = complete_answer(draft(**kwargs), labels)
    commitment = Commitment("book2_hybrid", labels["day"], labels["version"], canonical(labels),
                            commitment_hash(SALT, answer))  # fmt: skip
    receipts = FakeReceipts()
    if committed:
        receipts.times["c1"] = committed
    if revealed:
        receipts.times["c2"] = revealed
    shown = Published(reveal_text(answer, SALT), "c2", None) if reveal else None
    return labels, Submission(Published(commitment.to_text(), "c1", None), shown), receipts


def judged(tmp_path, state=FIRED, others=(), **kwargs):
    labels, submission, receipts = submitted(tmp_path, **kwargs)
    facts = Judged({"state": state, "reason": "budget stop"}, labels, submission, shape_check, set(), MODEL)
    return judge("book2_hybrid", facts, receipts, DEADLINES, list(others))


def test_an_on_time_revealed_valid_answer_from_the_registered_model_is_accepted(tmp_path):
    outcome = judged(tmp_path)
    assert (outcome.status, outcome.model_check) == (ACCEPTED, "match") and outcome.answer.decision["action"] == "trade"


def test_a_fire_unknown_book_is_judged_on_its_submission(tmp_path):
    assert judged(tmp_path, state=FIRE_UNKNOWN).status == ACCEPTED


def test_not_fired(tmp_path):
    outcome = judged(tmp_path, state=NOT_FIRED)
    assert (outcome.status, outcome.reason) == ("not_fired", "budget stop")


def test_no_submission(tmp_path):
    labels, _, receipts = submitted(tmp_path)
    facts = Judged({"state": FIRED}, labels, Submission(None, None), shape_check, set(), MODEL)
    assert judge("book2_hybrid", facts, receipts, DEADLINES, []).status == NO_SUBMISSION


@pytest.mark.parametrize("committed", [DEADLINES.reveal, None])
def test_a_commitment_not_seen_at_the_receipt_deadline_is_late(tmp_path, committed):
    assert judged(tmp_path, committed=committed).status == LATE


def test_another_book_s_early_reveal_exposes_this_one(tmp_path):
    outcome = judged(tmp_path, others=["book3_ai"])
    assert outcome.status == EXPOSED and "book3_ai revealed before 15:10:00" in outcome.reason


def test_its_own_early_reveal_is_invalid(tmp_path):
    outcome = judged(tmp_path, revealed=DEADLINES.receipt)
    assert outcome.status == INVALID and "revealed before" in outcome.reason


@pytest.mark.parametrize("revealed, reveal", [(None, True), (DEADLINES.reveal, False)])
def test_no_reveal_by_the_reveal_deadline(tmp_path, revealed, reveal):
    assert judged(tmp_path, revealed=revealed, reveal=reveal).status == NOT_REVEALED


def test_a_reveal_that_does_not_open_the_commitment_is_invalid(tmp_path):
    labels, submission, receipts = submitted(tmp_path)
    broken = Submission(
        submission.commitment, Published(submission.reveal.text.replace("trade", "no_trade"), "c2", None)
    )
    facts = Judged({"state": FIRED}, labels, broken, shape_check, set(), MODEL)
    assert judge("book2_hybrid", facts, receipts, DEADLINES, []).status == INVALID


def test_an_answer_failing_its_checks_is_invalid(tmp_path):
    outcome = judged(tmp_path, action="sell_naked")
    assert outcome.status == INVALID and "not allowed" in outcome.reason


def test_another_model_is_a_mismatch_and_unknown_is_unverified(tmp_path):
    assert judged(tmp_path, model="claude-sonnet-5-5").status == MODEL_MISMATCH
    outcome = judged(tmp_path, model="unknown")
    assert outcome.status == MODEL_UNVERIFIED and outcome.answer is None
