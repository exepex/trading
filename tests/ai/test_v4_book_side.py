"""Story G11 criteria C5 and C6 (step 7, the book side of v4): `brief` takes a v4 pointer and prints prompt v2 and the
input the pointer carries; `seal` checks the answer against the input's labels and questions and publishes the v4
commitment; `reveal` never publishes before 15:10:10 and waits at most 9 minutes per call, saying when to run it
again, so the prompt's 10-minute Bash timeout never cuts a reveal. v2's path is unchanged (`test_book_session.py`)."""

import json
from datetime import datetime, time

import pytest

from fno.ai.book import REVEAL_WAIT_CAP, BookStepRefused
from fno.ai.paths import timing_path
from fno.ai.run_terms import V2_TERMS, V4_TERMS
from fno.ai.seal import Commitment, open_reveal
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.models import IST
from tests.ai.fakes import Clock, FakeRoutine, make_desk_repo
from tests.ai.test_v4_input import DAY, QUESTIONS
from tests.ai.test_v4_pointer import pointer


def at(hh, mm, ss=0):
    return datetime.combine(DAY, time(hh, mm, ss), IST)


def draft(values=(9.5e-05, 4.5e-04, 0.05, 0.4, 0.47)):
    keys = ("value", "value", "probability", "probability", "probability")
    forecasts = {q: {k: v, "reason": f"why {q}"} for q, k, v in zip(QUESTIONS, keys, values, strict=True)}
    return {"model_reported": "claude-opus-5-5", "forecasts": forecasts}


@pytest.fixture
def desk(tmp_path):
    return make_desk_repo(tmp_path)


def sealed_routine(desk, book=BOOK3_AI, sealed_at=None):
    routine = FakeRoutine(desk, Clock(at(14, 41)))
    routine.run(pointer(book).to_text(), draft(), sealed_at or at(14, 45), reveal=False)
    return routine


def test_brief_prints_prompt_v2_then_the_pointers_own_input(desk):
    routine = FakeRoutine(desk, Clock(at(14, 41)))
    routine.session().brief(pointer(BOOK2_HYBRID).to_text())
    prompt, header, body = routine.printed
    assert prompt.startswith("# Book 2 (Hybrid)") and "version 2" in prompt.splitlines()[0]
    assert header.startswith("INPUT (export_sha256 ") and "WARNING" not in header
    assert json.loads(body) == pointer(BOOK2_HYBRID).input


def test_a_brief_after_1510_warns_with_v4s_deadline(desk):
    routine = FakeRoutine(desk, Clock(at(15, 10, 1)))
    routine.session().brief(pointer().to_text())
    assert "WARNING: already past 15:10:00 IST" in routine.printed[1]


def test_seal_publishes_the_v4_commitment_and_nothing_at_v2s_path(desk):
    routine = sealed_routine(desk)
    assert (desk / V4_TERMS.commitment_path(DAY, BOOK3_AI)).is_file()
    assert not (desk / V2_TERMS.commitment_path(DAY, BOOK3_AI)).exists()
    assert "pushed before 15:10:00 IST" in routine.printed[-1]


def test_seal_refuses_an_answer_that_misses_a_question_of_the_day(desk):
    routine = FakeRoutine(desk, Clock(at(14, 41)))
    wrong = draft() | {"forecasts": {QUESTIONS[0]: {"probability": 0.1, "reason": "one only"}}}
    with pytest.raises(ValueError, match="forecasts must name exactly"):
        routine.run(pointer().to_text(), wrong, at(14, 45), reveal=False)
    assert routine.transport.commits == []


def test_reveal_before_its_time_without_a_seal_is_refused(desk):
    routine = FakeRoutine(desk, Clock(at(14, 41)))
    routine.session().brief(pointer().to_text())
    with pytest.raises(BookStepRefused, match="sealed.json missing"):
        routine.session().reveal()


def test_one_early_reveal_waits_at_most_nine_minutes_and_says_to_run_it_again(desk):
    routine = sealed_routine(desk)
    routine.session().reveal()  # 14:45: 25 min 10 s to go
    assert routine.clock.now == at(14, 54) and routine.printed[-1] == "waiting until 15:10:10 IST: run reveal again"
    assert not (desk / V4_TERMS.reveal_path(DAY, BOOK3_AI)).exists()
    routine.session().reveal()  # 14:54 -> 15:03
    routine.session().reveal()  # 15:03 -> 15:10:10, inside the cap: publishes
    assert routine.clock.now == at(15, 10, 10)
    revealed = (desk / V4_TERMS.reveal_path(DAY, BOOK3_AI)).read_text(encoding="utf-8")
    commitment = Commitment.from_text((desk / V4_TERMS.commitment_path(DAY, BOOK3_AI)).read_text(encoding="utf-8"))
    assert open_reveal(revealed, commitment)["forecasts"][QUESTIONS[1]]["value"] == 4.5e-04
    timed = json.loads((desk / timing_path(DAY, BOOK3_AI)).read_text(encoding="utf-8"))  # C17: work and wait apart
    assert (timed["sealed_at"], timed["reveal_calls"]) == (at(14, 45).isoformat(), 3)


@pytest.mark.parametrize(("now", "published"), [(at(15, 1, 10), True), (at(15, 1, 9), False)])
def test_exactly_nine_minutes_before_the_reveal_time_it_publishes_in_that_call(desk, now, published):
    routine = sealed_routine(desk)
    routine.clock.now = now
    routine.session().reveal()
    assert (desk / V4_TERMS.reveal_path(DAY, BOOK3_AI)).exists() is published
    assert REVEAL_WAIT_CAP == 540


def test_a_reveal_after_its_time_publishes_at_once(desk):
    routine = sealed_routine(desk)
    routine.clock.now = at(15, 40)
    routine.session().reveal()
    assert routine.clock.now == at(15, 40) and (desk / V4_TERMS.reveal_path(DAY, BOOK3_AI)).exists()


def test_hybrids_seal_keeps_v4s_envelope(desk):
    routine = FakeRoutine(desk, Clock(at(14, 41)))
    with pytest.raises(BookStepRefused, match="outside the envelope"):
        routine.run(pointer(BOOK2_HYBRID).to_text(), draft((9.5e-05, 4.5e-04, 0.95, 0.4, 0.47)), at(14, 45),
                    reveal=False)  # fmt: skip


def test_reveal_refuses_a_sealed_answer_of_another_day(desk):
    """Review of dfb26381: in a reused container, yesterday's sealed answer is never revealed at today's path."""
    routine = sealed_routine(desk)
    sealed_file = desk / ".ai_book" / "sealed.json"
    sealed = json.loads(sealed_file.read_text(encoding="utf-8"))
    sealed["answer"]["day"] = "2026-10-23"
    sealed_file.write_text(json.dumps(sealed), encoding="utf-8")
    routine.clock.now = at(15, 10, 10)
    with pytest.raises(BookStepRefused, match="not this run's"):
        routine.session().reveal()
    assert not (desk / V4_TERMS.reveal_path(DAY, BOOK3_AI)).exists()
