"""Owner, 24 Oct (O1 R2 round 3): the fills' own refusals carry a public code, never "unlisted": the late rerun's
`desk:FILLS_LATE` and round 2's refused inputs (`desk:NEEDS_*`). A joined reason gets the last template's code."""

import pytest

from fno.daily.public_log import ReasonRegistry
from fno.daily.reason_codes import COMMON, STEP_TEMPLATES
from fno.desk.daily_run import FILLS_LATE
from tests.desk.builders import at
from tests.timetable.test_daily_run import NORMAL

LATE = FILLS_LATE.format(now=at(15, 21, day=NORMAL), by=at(15, 20, day=NORMAL))


@pytest.mark.parametrize(
    ("text", "code"),
    [
        (LATE, "desk:FILLS_LATE"),
        ("needs snapshot, which failed today", "desk:NEEDS_FAILED"),
        ("needs snapshot, decisions, which has not run today", "desk:NEEDS_MISSING"),
        ("needs decisions, which was refused today", "desk:NEEDS_REFUSED"),
        ("needs snapshot, which failed today; needs decisions, which was refused today", "desk:NEEDS_REFUSED"),
    ],
)
def test_the_fills_refusals_have_their_own_public_codes(text, code):
    assert ReasonRegistry(COMMON, STEP_TEMPLATES).code("fills", text) == code
