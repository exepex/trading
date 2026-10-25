"""REC1d's wrapper (items 1-4; criteria a and d): its own switch, `daily.live_from.recommend`, never the school's; all
four switch pairs against golden files of both editions; the school's section and the inner maker's alerts kept when
the recommender's section fails, and the recommender's block kept when the school's fails; set-up failures isolated."""

from datetime import timedelta
from pathlib import Path

import pytest

from fno.forecast_lab.maker import Made
from fno.recommend import report_words as w
from fno.recommend.report_guard import with_recommend_section
from fno.recommend.report_maker import RecommendReportMaker
from fno.recommend.report_section import EveningSection
from fno.school.reports.guard import with_school_sections
from tests.recommend.builders import DAY
from tests.recommend.report_fakes import Store
from tests.school.reports import fakes as f
from tests.school.reports.test_editions import GOLDEN as SCHOOL_GOLDEN
from tests.school.reports.test_editions import NOW, OFF, ON, files_of, lab_maker

GOLDEN = Path(__file__).parent / "golden"
LIVE = {"daily": {"live_from": {"recommend": DAY.isoformat()}}}
CONFIGS = {(False, False): OFF, (True, False): ON, (False, True): {**OFF, **LIVE}, (True, True): {**ON, **LIVE}}
EDITIONS = ("morning", "evening")


@pytest.fixture
def store(tmp_path):
    store = Store(tmp_path)
    store.record(day=DAY - timedelta(days=3))  # Friday: the morning's standing answer
    store.record(day=DAY)
    return store


def edition(store, school: bool, recommender: bool, name: str, school_day=None):
    config = CONFIGS[(school, recommender)]
    inner = with_school_sections(lab_maker(name), config, f.Today(), school_day or f.Day((f.refused_record(),),
                                                                                          (f.counts(),)))  # fmt: skip
    return with_recommend_section(inner, config, store.ports()).make(DAY, NOW, name, ("an alert",), "a\n\nb")


@pytest.mark.parametrize("name", EDITIONS)
@pytest.mark.parametrize("school,recommender", list(CONFIGS))
def test_each_switch_pair_matches_its_golden_and_leaves_the_page_files_alone(store, name, school, recommender):
    made = edition(store, school, recommender, name)
    golden = GOLDEN / f"{name}_school_{'on' if school else 'off'}_recommender_{'on' if recommender else 'off'}.txt"
    assert made.text == golden.read_text()
    plain = lab_maker(name).make(DAY, NOW, name, ("an alert",), "a\n\nb")
    assert files_of(made) == files_of(plain) and made.alerts == plain.alerts == (), "nothing failed"


@pytest.mark.parametrize("name", EDITIONS)
def test_with_both_switches_off_the_text_is_the_school_s_flag_off_golden(store, name):
    assert edition(store, False, False, name).text == (SCHOOL_GOLDEN / f"{name}.txt").read_text()


@pytest.mark.parametrize("name", EDITIONS)
def test_school_on_recommender_off_is_the_school_s_edition_exactly(store, name):
    school_only = with_school_sections(lab_maker(name), ON, f.Today(), f.Day((f.refused_record(),), (f.counts(),)))
    assert edition(store, True, False, name).text == school_only.make(DAY, NOW, name, ("an alert",), "a\n\nb").text
    assert w.TITLE not in edition(store, True, False, name).text


@pytest.mark.parametrize("name", EDITIONS)
def test_school_off_recommender_on_shows_the_block_without_the_school_s(store, name):
    text = edition(store, False, True, name).text
    assert text.startswith((SCHOOL_GOLDEN / f"{name}.txt").read_text() + f"\n\n{w.TITLE}\n")
    assert "School pilot" not in text


@pytest.mark.parametrize("name", EDITIONS)
def test_with_both_on_the_school_s_sections_come_first(store, name):
    text = edition(store, True, True, name).text
    assert text.index("School pilot") < text.index(w.TITLE)


def test_with_no_live_date_the_maker_itself_is_returned(store):
    maker = lab_maker("morning")
    assert with_recommend_section(maker, ON, store.ports()) is maker
    assert with_recommend_section(maker, OFF, store.ports()) is maker


def test_before_its_live_date_the_edition_is_unchanged(store):
    late = {**OFF, "daily": {"live_from": {"recommend": (DAY + timedelta(days=1)).isoformat()}}}
    made = with_recommend_section(lab_maker("evening"), late, store.ports()).make(DAY, NOW, "evening")
    assert made.text == (SCHOOL_GOLDEN / "evening.txt").read_text()


class Broken:
    def render(self, day):
        raise KeyError("a strike 51200 in a message")


class Alerting:
    """An inner maker that made one alert of its own."""

    def make(self, day, now, edition, alerts=(), checks="", confirmation=()):
        return Made("the inner edition", (), ("the inner alert",), ())


def test_a_failing_recommender_section_keeps_the_inner_text_and_alerts():
    made = RecommendReportMaker(Alerting(), {"evening": Broken()}, DAY).make(DAY, NOW, "evening")
    assert made.text == "the inner edition"
    assert made.alerts == ("the inner alert", w.SECTION_FAILED.format(edition="evening", failure="KeyError"))
    assert "51200" not in " ".join(made.alerts), "the class only, never the message"


def test_a_failing_recommender_section_keeps_the_school_s_section():
    inner = with_school_sections(lab_maker("evening"), ON, f.Today(), f.Day((f.refused_record(),), (f.counts(),)))
    made = RecommendReportMaker(inner, {"evening": Broken()}, DAY).make(DAY, NOW, "evening")
    assert made.text == inner.make(DAY, NOW, "evening").text and "School pilot" in made.text


def test_the_block_keeps_the_inner_alerts(store):
    made = RecommendReportMaker(Alerting(), {"evening": EveningSection(store.ports())}, DAY).make(DAY, NOW, "evening")
    assert made.alerts == ("the inner alert",) and made.text.startswith(f"the inner edition\n\n{w.TITLE}\n")


def test_a_failing_school_section_keeps_the_recommender_s_block(store):
    class BrokenDay(f.Day):
        def records(self, session):
            raise OSError("drive down")

    made = edition(store, True, True, "evening", BrokenDay())
    assert (
        w.TITLE in made.text and len(made.alerts) == 1 and "school evening section not made (OSError)" in made.alerts[0]
    )


def test_a_set_up_failure_gives_the_inner_edition_and_one_alert(store):
    made = with_recommend_section(lab_maker("morning"), {"daily": {"live_from": {"recommend": "not a date"}}},
                                  store.ports()).make(DAY, NOW, "morning")  # fmt: skip
    assert made.text == (SCHOOL_GOLDEN / "morning.txt").read_text()
    assert made.alerts == (w.SECTION_FAILED.format(edition="morning", failure="ValueError"),)


def test_the_lab_wraps_the_school_s_maker_in_the_recommender_s(monkeypatch):
    from fno.forecast_lab import page_wiring
    from fno.storage import data_wiring

    class Stub:
        def __init__(self, *args, **kwargs):
            pass

    for name in ("PageBuilder", "ReportMaker", "RepositoryFacts", "A4hTodayCloses", "G13bHistory", "RegularSessions",
                 "DesignRenderer", "ChromiumCamera"):  # fmt: skip
        monkeypatch.setattr(page_wiring, name, Stub)
    monkeypatch.setattr(page_wiring, "flows_reader", lambda calendar: None)
    monkeypatch.setattr(page_wiring, "build_sections", lambda *a: ())
    monkeypatch.setattr(page_wiring, "build_levels", lambda *a: None)
    monkeypatch.setattr(data_wiring, "build_drive_cache", lambda *a, **k: None)
    monkeypatch.setattr(page_wiring, "with_school_sections", lambda maker, inputs=None: "school")
    monkeypatch.setattr(page_wiring, "with_recommend_section", lambda maker: ("recommender", maker))
    assert page_wiring.build_report_maker(None, None, None, None, None) == ("recommender", "school")
