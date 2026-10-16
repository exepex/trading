"""Story G11 round 2b, step 6: prompt v2 is each book's protocol v4 version, registered beside v1 without changing the
v2 run (v1 stays its version until the freeze, owner's choice A); a version names the questions its prompt defines
and the forecaster it registers as."""

import pytest

from fno.ai.versions import VERSIONS, VersionRefused, current_version
from fno.config import ROOT
from fno.constants import (
    AI_BOOKS,
    BOOK3_AI,
    FORECAST_PROTOCOL_V2,
    FORECAST_PROTOCOL_V4,
    FORECAST_QUESTIONS,
    V6_BIG_MOVE_1S,
    V6_BIG_MOVE_5S,
)


@pytest.mark.parametrize("book", AI_BOOKS)
def test_the_v2_run_keeps_prompt_v1_and_v4_gets_prompt_v2(book):
    assert current_version(book).number == 1 and current_version(book, FORECAST_PROTOCOL_V2).number == 1
    v4 = current_version(book, FORECAST_PROTOCOL_V4)
    assert (v4.number, v4.questions, v4.forecaster) == (2, (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S), f"{book}_v2")
    assert current_version(book).questions == FORECAST_QUESTIONS


def test_every_registered_prompt_matches_its_hash():
    for version in VERSIONS:
        assert version.prompt_text(ROOT).startswith("# Book ")


def test_a_protocol_without_a_version_is_refused():
    with pytest.raises(VersionRefused, match="no registered v9 version"):
        current_version(BOOK3_AI, "v9")
