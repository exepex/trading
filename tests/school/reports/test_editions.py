"""Criterion 1 and the wiring (story MS-P1g): with the flag off both editions are byte-identical to today (golden
files made from the unwrapped maker before this part existed); with it on the sections join the message text only."""

import hashlib
import json
from datetime import date, datetime
from pathlib import Path

import pytest

from fno.forecast_lab.design.renderer import DesignRenderer
from fno.forecast_lab.maker import ReportMaker
from fno.school.reports.maker import SchoolReportMaker
from fno.school.reports.wiring import UNWIRED, with_school_sections
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


@pytest.mark.parametrize("edition", ["morning", "evening"])
def test_with_the_flag_off_the_edition_is_byte_identical_to_the_golden_files(edition):
    maker = with_school_sections(lab_maker(edition), OFF)
    made = make(maker, edition)
    golden = json.loads((GOLDEN / "files.json").read_text())[edition]
    assert made.text == (GOLDEN / f"{edition}.txt").read_text()
    assert {a.name: hashlib.sha256(a.data).hexdigest() for a in made.files} == golden["files"]
    assert list(made.alerts) == golden["alerts"] and len(made.verdicts) == golden["verdicts"]


def test_with_the_flag_off_the_maker_itself_is_returned_unwrapped():
    maker = lab_maker("morning")
    assert with_school_sections(maker, OFF) is maker


@pytest.mark.parametrize("edition,title", [("morning", "Today"), ("evening", "How did today go")])
def test_with_the_flag_on_the_edition_text_gains_its_section_and_the_page_files_stay_identical(edition, title):
    inner = lab_maker(edition)
    maker = with_school_sections(inner, ON, f.Today(), f.Day((f.refused_record(),), (f.counts(),)))
    made = make(maker, edition)
    golden = json.loads((GOLDEN / "files.json").read_text())[edition]
    assert made.text.startswith((GOLDEN / f"{edition}.txt").read_text() + "\n\n")
    assert f"School pilot, {title} (Paper" in made.text
    assert {a.name: hashlib.sha256(a.data).hexdigest() for a in made.files} == golden["files"], "the page is untouched"
    assert made.alerts == ()


def test_a_school_section_that_fails_never_stops_the_edition_and_alerts_once():
    class Broken:
        def roads(self, session):
            raise KeyError("capture gone")

        def plan(self, session):
            return ()

    made = make(with_school_sections(lab_maker("morning"), ON, Broken(), f.Day()), "morning")
    assert made.text == (GOLDEN / "morning.txt").read_text() and len(made.files) == 2
    assert made.alerts == (
        "school morning section not made (KeyError: 'capture gone'); the edition was posted without it",
    )


def test_a_flag_turned_on_before_the_inputs_are_wired_alerts_and_posts_the_plain_edition():
    made = make(with_school_sections(lab_maker("evening"), ON), "evening")
    assert made.text == (GOLDEN / "evening.txt").read_text()
    assert len(made.alerts) == 1 and UNWIRED in made.alerts[0] and "SchoolInputsNotWired" in made.alerts[0]


def test_an_edition_with_no_section_is_passed_through():
    made = make(SchoolReportMaker(lab_maker("morning"), {}), "morning")
    assert made.text == (GOLDEN / "morning.txt").read_text()


def test_the_real_config_has_the_flag_off(monkeypatch):
    maker = lab_maker("morning")
    assert with_school_sections(maker) is maker
