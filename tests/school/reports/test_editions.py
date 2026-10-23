"""Criterion 1 and the wiring (story MS-P1g): with the flag off both editions are byte-identical to today (golden
files made from the unwrapped maker before this part existed); with it on the sections join the message text only."""

import hashlib
import sys
from datetime import date, datetime
from pathlib import Path

import pytest

from fno.forecast_lab.design.renderer import DesignRenderer
from fno.forecast_lab.maker import ReportMaker
from fno.school.report_entry import school_report_inputs
from fno.school.reports.guard import with_school_sections
from fno.school.reports.maker import SchoolReportMaker
from fno.school.reports.wiring import UNWIRED
from tests.forecast_lab.design_builders import page
from tests.forecast_lab.test_maker_and_render import Camera, Pages
from tests.school.reports import fakes as f

GOLDEN = Path(__file__).parent / "golden"
DAY, NOW = date(2026, 10, 23), datetime(2026, 10, 23, 8, 50)
OFF = {"school": {"enabled": False, "reports": False, "first_counted": None, "account_rs": 1, "max_loss_rs": 1,
                  "daily_stop_rs": 1, "brake_rs": 1, "max_new_trades_per_slot": 1, "bucket_rs": 1, "open_risk_rs": 1,
                  "new_risk_day_rs": 1}}  # fmt: skip
ON = {"school": {**OFF["school"], "reports": True}}


def lab_maker(edition: str) -> ReportMaker:
    return ReportMaker(Pages(page(edition)), DesignRenderer(), Camera())


def make(maker, edition: str):
    return maker.make(DAY, NOW, edition, ("an alert",), "a\n\nb")


def files_of(made) -> dict[str, str]:
    return {a.name: hashlib.sha256(a.data).hexdigest() for a in made.files}


def plain(edition: str):
    """The edition made by the unwrapped lab maker in this same run: whatever the page design is today, the school's
    wrapper must change nothing of it (so no frozen hash of another story's design is kept here)."""
    return make(lab_maker(edition), edition)


@pytest.mark.parametrize("edition", ["morning", "evening"])
def test_with_the_flag_off_the_edition_is_byte_identical_to_the_unwrapped_maker_and_the_text_golden(edition):
    made, unwrapped = make(with_school_sections(lab_maker(edition), OFF), edition), plain(edition)
    assert made.text == (GOLDEN / f"{edition}.txt").read_text(), "the text golden pins the wrapper's own output"
    assert made.text == unwrapped.text and files_of(made) == files_of(unwrapped)
    assert made.alerts == unwrapped.alerts and made.verdicts == unwrapped.verdicts
    assert files_of(made), "the page files exist, so the comparison above is not vacuous"


def test_with_the_flag_off_the_maker_itself_is_returned_unwrapped():
    maker = lab_maker("morning")
    assert with_school_sections(maker, OFF) is maker


@pytest.mark.parametrize("edition,title", [("morning", "Today"), ("evening", "How did today go")])
def test_with_the_flag_on_the_edition_text_gains_its_section_and_the_page_files_stay_identical(edition, title):
    inner = lab_maker(edition)
    maker = with_school_sections(inner, ON, f.Today(), f.Day((f.refused_record(),), (f.counts(),)))
    made = make(maker, edition)
    assert made.text.startswith((GOLDEN / f"{edition}.txt").read_text() + "\n\n")
    assert f"School pilot, {title} (Paper" in made.text
    assert files_of(made) == files_of(plain(edition)), "the page is untouched"
    assert made.alerts == ()


def test_a_school_section_that_fails_never_stops_the_edition_and_alerts_once():
    class Broken:
        def roads(self, session):
            raise KeyError("capture gone")

        def plan(self, session):
            return ()

    made = make(with_school_sections(lab_maker("morning"), ON, Broken(), f.Day()), "morning")
    assert made.text == (GOLDEN / "morning.txt").read_text() and len(made.files) == 2
    assert made.alerts == ("school morning section not made (KeyError); the edition was posted without it",)


def test_a_flag_turned_on_before_the_inputs_are_wired_alerts_and_posts_the_plain_edition():
    made = make(with_school_sections(lab_maker("evening"), ON), "evening")
    assert made.text == (GOLDEN / "evening.txt").read_text()
    assert made.alerts == ("school evening section not made (SchoolInputsNotWired); the edition was posted without it",)
    assert UNWIRED not in made.alerts[0], "the exception's message is never repeated"


def test_an_edition_with_no_section_is_passed_through():
    made = make(SchoolReportMaker(lab_maker("morning"), {}), "morning")
    assert made.text == (GOLDEN / "morning.txt").read_text()


def test_the_real_config_has_the_flag_off(monkeypatch):
    maker = lab_maker("morning")
    assert with_school_sections(maker) is maker


def test_a_failure_alert_never_repeats_the_exceptions_message():
    class Leaky:
        def roads(self, session):
            raise KeyError("ContractKey(expiry=2026-11-23, strike=51200.0, kind=CE)")

        def plan(self, session):
            return ()

    made = make(with_school_sections(lab_maker("morning"), ON, Leaky(), f.Day()), "morning")
    assert "51200" not in made.alerts[0] and "ContractKey" not in made.alerts[0] and "KeyError" in made.alerts[0]


def bad_blocks():
    school = OFF["school"]
    return {
        "a first_counted that is not a date": {"school": {**school, "first_counted": "2026-13-01"}},
        "an unknown key": {"school": {**school, "surprise": 1}},
        "a missing key": {"school": {k: v for k, v in school.items() if k != "brake_rs"}},
        "no school block": {},
        "a wrong kind": {"school": {**school, "reports": "yes"}},
    }


@pytest.mark.parametrize("case", list(bad_blocks()))
@pytest.mark.parametrize("edition", ["morning", "evening"])
def test_a_bad_school_block_gives_the_plain_edition_and_one_alert_naming_the_class(case, edition):
    made = make(with_school_sections(lab_maker(edition), bad_blocks()[case]), edition)
    assert made.text == (GOLDEN / f"{edition}.txt").read_text()
    assert files_of(made) == files_of(plain(edition))
    assert made.alerts == (
        f"school {edition} section not made (SchoolSettingsError); the edition was posted without it",
    )


def test_an_import_failure_of_the_school_wiring_gives_the_plain_edition_and_one_alert(monkeypatch):
    monkeypatch.setitem(sys.modules, "fno.school.reports.wiring", None)  # `import` then raises ImportError
    made = make(with_school_sections(lab_maker("morning"), ON), "morning")
    assert made.text == (GOLDEN / "morning.txt").read_text()
    assert made.alerts == ("school morning section not made (ModuleNotFoundError); the edition was posted without it",)


def test_a_bad_real_config_never_stops_the_edition(monkeypatch):
    from fno.school.reports import wiring

    def broken():
        raise OSError("config.yaml unreadable")

    monkeypatch.setattr(wiring, "load_app_config", broken)
    made = make(with_school_sections(lab_maker("evening")), "evening")
    assert made.text == (GOLDEN / "evening.txt").read_text() and len(made.alerts) == 1 and "OSError" in made.alerts[0]


def test_the_real_report_maker_is_built_through_the_school_guard(monkeypatch):
    from fno.forecast_lab import page_wiring
    from fno.storage import data_wiring

    class Stub:
        def __init__(self, *args, **kwargs):
            self.args = args

    built = {}

    def spy(maker, inputs=None):
        built["inner"], built["inputs"] = maker, inputs
        return "wrapped"

    for name in ("PageBuilder", "ReportMaker", "RepositoryFacts", "A4hTodayCloses", "G13bHistory", "RegularSessions",
                 "DesignRenderer", "ChromiumCamera"):  # fmt: skip
        monkeypatch.setattr(page_wiring, name, Stub)
    monkeypatch.setattr(page_wiring, "flows_reader", lambda calendar: None)
    monkeypatch.setattr(page_wiring, "build_sections", lambda *a: ())
    monkeypatch.setattr(page_wiring, "build_levels", lambda *a: None)
    monkeypatch.setattr(data_wiring, "build_drive_cache", lambda *a, **k: None)
    monkeypatch.setattr(page_wiring, "with_school_sections", spy)
    assert page_wiring.build_report_maker(None, None, None, None, None) == "wrapped"
    assert isinstance(built["inner"], Stub), "the report maker goes through the school guard"
    assert built["inputs"] is school_report_inputs, "the lab passes the school's own inputs (MS-P1j)"
