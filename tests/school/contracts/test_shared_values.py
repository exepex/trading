"""The school writes three values the repository also defines, so its contracts load nothing outside the standard
library (judge 479 finding 1). Each copy must equal its source."""

from fno import constants
from fno.quotes import recorder, weekly
from fno.school import constants as school


def test_the_order_sides_are_the_ledgers_sides():
    assert (school.SIDE_BUY, school.SIDE_SELL, school.SIDES) == (constants.SIDE_BUY, constants.SIDE_SELL,
                                                                 constants.SIDES)  # fmt: skip


def test_the_quote_datasets_are_the_recorders():
    assert (school.MONTHLY_DATASET, school.WEEKLY_DATASET) == (recorder.DATASET, weekly.WEEKLY_DATASET)
