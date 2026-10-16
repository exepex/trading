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
from tests.ai.test_v4_input import DAY, QUESTIONS, RULES, a_pack, closes


def pointer(book=BOOK3_AI):
    who = V4InputFor(book, current_version(book, FORECAST_PROTOCOL_V4).label, DAY, QUESTIONS, "d" * 64)
    rules, width = (RULES, 0.10) if book == BOOK2_HYBRID else (None, None)
    return V4Pointer(build_v4_input(who, a_pack(), closes(), rules, width))


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
     (lambda f: f["input"]["rules"]["by_question"].popitem(), BOOK2_HYBRID, "the day's questions")],
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
    """Prompt v2 defines V6a and V6b only; V1 needs a new version first."""
    with pytest.raises(PointerRefused, match="does not define"):
        parse_v4_pointer(_edited(lambda f: f["input"].update(questions=["v1_rv_next_session"])))
