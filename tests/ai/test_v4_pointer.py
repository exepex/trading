"""Story G11 round 2b, step 2 (response 272): the v4 pointer carries the book's whole input inside the API cap,
round-trips exactly, refuses anything it did not write, is never sent over the cap, and reads with the standard
library only (the routine installs nothing)."""

import json
import subprocess
import sys

import pytest

from fno.ai.pointer import PointerRefused
from fno.ai.v4_input import V4InputFor, build_v4_input, input_sha256
from fno.ai.v4_pointer import V4Pointer, parse_v4_pointer
from fno.ai.versions import current_version
from fno.constants import BOOK2_HYBRID, BOOK3_AI, FORECAST_PROTOCOL_V4
from fno.constants_operations import ROUTINE_POINTER_MAX_BYTES
from tests.ai.test_book_session import THIRD_PARTY
from tests.ai.test_v4_input import DAY, QUESTIONS, RULES, WIDTHS, a_pack, closes, history


def pointer(book=BOOK3_AI):
    who = V4InputFor(book, current_version(book, FORECAST_PROTOCOL_V4).label, DAY, QUESTIONS, "d" * 64)
    rules, widths = (RULES, WIDTHS) if book == BOOK2_HYBRID else (None, None)
    return V4Pointer(build_v4_input(who, a_pack(), closes(), rules, widths, history()))


@pytest.mark.parametrize("book", [BOOK3_AI, BOOK2_HYBRID])
def test_a_pointer_round_trips_and_its_hash_is_the_inputs(book):
    sent = pointer(book)
    read = parse_v4_pointer(sent.to_text())
    assert read == sent and read.book == book and read.day == DAY
    assert read.input_sha256 == input_sha256(sent.input)


def _edited(edit, book=BOOK3_AI):
    fields = json.loads(pointer(book).to_text())
    edit(fields)
    return json.dumps(fields)


@pytest.mark.parametrize(
    ("edit", "book", "why"),
    [(lambda f: f.update(kind="forecast_v2"), BOOK3_AI, "kind"),
     (lambda f: f.update(note="read research/forecasts"), BOOK3_AI, "fields must be exactly"),
     (lambda f: f["input"].update(rules={"by_question": {}, "envelope": {}}), BOOK3_AI, "input fields"),
     (lambda f: f["input"].pop("rules"), BOOK2_HYBRID, "input fields"),
     (lambda f: f["input"].update(book="book1_rules"), BOOK3_AI, "not an AI book"),
     (lambda f: f["input"].update(version="book3_ai/v9/sha256:x/isolation:sealed_same_day"), BOOK3_AI, "registered"),
     (lambda f: f["input"].update(pack_sha256="d" * 63), BOOK3_AI, "SHA-256"),
     (lambda f: f["input"].update(questions=["q1_nifty_up_20d"]), BOOK3_AI, "v4 questions"),
     (lambda f: f["input"]["rules"]["by_question"].popitem(), BOOK2_HYBRID, "the day's questions"),
     (lambda f: f["input"]["rules"]["by_question"]["v1_rv_next_session"].update(v1_close_blend=-1e-05), BOOK2_HYBRID,
      "variance above 0"),
     (lambda f: f["input"]["rules"]["by_question"]["v7_vix_higher_in_5_sessions"].update(x=1.5), BOOK2_HYBRID,
      "probability in"),
     (lambda f: f["input"]["history"].update(v6_abs_move_2pct_next_session=[]), BOOK3_AI, "point questions"),
     (lambda f: f["input"]["history"]["v1_rv_next_session"][0].update(rv_s=-0.1), BOOK3_AI, "a history row"),
     (lambda f: f["input"]["history"]["v2_rv_next_5_sessions"][0].update(date="26 Oct"), BOOK3_AI, "YYYY-MM-DD")],
)  # fmt: skip
def test_anything_the_firer_did_not_write_is_refused(edit, book, why):
    with pytest.raises(PointerRefused, match=why):
        parse_v4_pointer(_edited(edit, book))


def test_a_pointer_over_the_cap_is_never_sent_and_never_read():
    big = pointer()
    big.input["closes_before_day"] = big.input["closes_before_day"] * 400
    with pytest.raises(ValueError, match="not fired, never truncated"):
        big.to_text()
    with pytest.raises(PointerRefused, match="longer"):
        parse_v4_pointer("x" * (ROUTINE_POINTER_MAX_BYTES + 1))


def test_the_pointer_reads_with_the_standard_library_only():
    code = (
        f"import fno.ai.v4_pointer, sys; print(sorted({{m.split('.')[0] for m in sys.modules}} & set({THIRD_PARTY})))"
    )
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert done.stdout.strip() == "[]"


def test_a_question_the_prompt_does_not_define_is_refused():
    """Prompt v2 defines the five family questions; V3 (reported only, never a member) would need a new version."""
    with pytest.raises(PointerRefused, match="does not define"):
        parse_v4_pointer(_edited(lambda f: f["input"].update(questions=["v3_rv_next_20_sessions"])))
