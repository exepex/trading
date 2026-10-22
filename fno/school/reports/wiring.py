"""Composition root of `fno/school/reports/` (story MS-P1g): the school's sections for the 08:50 and 20:05 editions.

`with_school_sections` is the one call `fno/forecast_lab/page_wiring.py` makes. With `school.reports` off it returns the
maker it was given, so both editions stay byte-identical. The day's inputs (roads, dashcam records, counts, driver
roles) are wired by the join-up (MS-P1j); until then a flag turned on gives an alert, never a section."""

from ...config import load_app_config
from ..settings import school_settings
from .evening import HowDidTodayGoSection
from .inputs import DayInputs, TodayInputs
from .maker import SchoolReportMaker
from .today import TodaySection

MORNING, EVENING = "morning", "evening"
UNWIRED = "the school's day inputs are wired by MS-P1j"


class SchoolInputsNotWired(RuntimeError):
    def __init__(self):
        super().__init__(UNWIRED)


class _NotWired:
    def __getattr__(self, name):
        raise SchoolInputsNotWired


def school_sections(today: TodayInputs, day: DayInputs) -> dict:
    return {MORNING: TodaySection(today), EVENING: HowDidTodayGoSection(day)}


def with_school_sections(maker, config: dict | None = None, today: TodayInputs | None = None,
                         day: DayInputs | None = None):  # fmt: skip
    settings = school_settings(config if config is not None else load_app_config())
    if not settings.reports:
        return maker
    return SchoolReportMaker(maker, school_sections(today or _NotWired(), day or _NotWired()))
