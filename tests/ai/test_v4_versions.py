"""Story G11 round 2b, step 6: prompt v2 is each book's protocol v4 version, registered beside v1 without changing the
v2 run (v1 stays its version until the freeze, owner's choice A); a version names the questions its prompt defines
and the forecaster it registers as."""

import pytest

from fno.ai.run_terms import FORECAST_PROTOCOL_V2, FORECAST_PROTOCOL_V4
from fno.ai.versions import VERSIONS, VersionRefused, current_version
from fno.config import ROOT
from fno.constants import AI_BOOKS, BOOK3_AI, FORECAST_QUESTIONS
from fno.forecast_v4.terms import FAMILY_QUESTIONS


@pytest.mark.parametrize("book", AI_BOOKS)
def test_the_v2_run_keeps_prompt_v1_and_v4_gets_prompt_v2(book):
    assert current_version(book).number == 1 and current_version(book, FORECAST_PROTOCOL_V2).number == 1
    v4 = current_version(book, FORECAST_PROTOCOL_V4)
    assert (v4.number, v4.questions, v4.forecaster) == (2, FAMILY_QUESTIONS, f"{book}_v2")  # all five (G11 C1)
    assert current_version(book).questions == FORECAST_QUESTIONS


def test_every_registered_prompt_matches_its_hash():
    for version in VERSIONS:
        assert version.prompt_text(ROOT).startswith("# Book ")


def test_a_protocol_without_a_version_is_refused():
    with pytest.raises(VersionRefused, match="no registered v9 version"):
        current_version(BOOK3_AI, "v9")


def test_hybrid_v2_widens_a_probability_by_010_and_a_variance_by_25_percent():
    hybrid = current_version(AI_BOOKS[0], FORECAST_PROTOCOL_V4)
    assert (hybrid.book, hybrid.envelope_width, hybrid.point_envelope_width) == ("book2_hybrid", 0.10, 0.25)
    assert current_version(BOOK3_AI, FORECAST_PROTOCOL_V4).envelope_width is None


@pytest.mark.parametrize("book", AI_BOOKS)
def test_prompt_v2_names_every_question_its_measure_and_the_reveal_loop(book):
    text = current_version(book, FORECAST_PROTOCOL_V4).prompt_text(ROOT)
    assert all(f"`{q}`" in text for q in FAMILY_QUESTIONS)
    assert "close-proxy `RV_s`" in text and "intraday `RV_s`" in text and "squared log returns" in text
    assert "waiting until 15:10:10 IST: run reveal again" in text and "15:10:00 IST" in text
    assert "at most 0.01, V2's at most 0.05" in text  # the caps `answer.VARIANCE_CAP` applies
