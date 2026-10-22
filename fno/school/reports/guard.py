"""The one entry the forecast lab calls (story MS-P1g): the school can never stop an 08:50 or 20:05 edition. The
school's wiring is imported here, inside the guard, and so are the settings it reads: a bad `school` block, a missing
key or an import failure gives the plain signed-off edition and one alert naming only the exception class.

This module imports nothing of the school at load time (only the maker's own small classes), so nothing the school
does can fail the lab's own import."""

from .maker import FailedSchoolMaker


def with_school_sections(maker, config: dict | None = None, today=None, day=None):
    try:
        from .wiring import build_school_maker

        return build_school_maker(maker, config, today, day)
    except Exception as failed:  # isolation: nothing of the school may stop an edition
        return FailedSchoolMaker(maker, failed)
