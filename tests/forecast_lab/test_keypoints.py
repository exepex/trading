"""FL1-1d-2: the 2-4 key points in their stated order. The morning: what the forecast is built from (the one `used`
point), the day's flags, then context by the size of its move. The evening: on a miss, its after-the-fact reasons,
the US equity cues that moved the same way, then other context; a right day: the largest context moves. A Section
that fails is `failed` and said in the system line, never a crash."""

from fno.forecast_lab.page.cues import AVAILABLE, FAILED, NOT_OUT_YET, Cue, Section, SectionView
from fno.forecast_lab.page.keypoints import evening_points, morning_points
from fno.forecast_lab.page.model import Band, Outcome

from .test_page_editions import FRI, MON, build, implied

BAND = Band(25000.0, 25200.0, 25300.0, 25400.0, 25600.0)
FLAG = SectionView("Today's flags", AVAILABLE, MON, (Cue("RBI policy decision", text="RBI policy decision"),))
CUES = (
    SectionView("S&P 500", AVAILABLE, FRI, (Cue("S&P 500", 6000.0, -1.2, "%", FRI, size=1.5),)),
    SectionView("Brent", AVAILABLE, FRI, (Cue("Brent", 80.0, 2.0, "%", FRI, size=2.5),)),
    SectionView("Nasdaq-100", NOT_OUT_YET),
    SectionView("India VIX", AVAILABLE, FRI, (Cue("India VIX", 15.0, 3.0, "%", FRI, size=0.5),)),
)


def test_the_morning_says_what_the_forecast_is_built_from_then_flags_then_the_biggest_moves():
    points = morning_points("implied", (*CUES, FLAG))
    assert [(p.name, p.role) for p in points] == [("Built from", "used"), ("RBI policy decision", "context"),
                                                  ("Brent", "context"), ("S&P 500", "context")]  # fmt: skip
    assert points[0].text == "option prices (the range the options imply)"


def test_a_miss_leads_with_its_reasons_then_us_equities_that_moved_its_way():
    below = Outcome(MON, 24900.0, BAND, False, False, True, provisional=True)
    points = evening_points(below, ("India VIX up 12% on the day",), CUES)
    assert [p.name for p in points] == ["Reason (after the fact)", "S&P 500", "Brent", "India VIX"]
    above = Outcome(MON, 25700.0, BAND, False, False, True, provisional=True)
    assert [p.name for p in evening_points(above, (), CUES)] == [
        "Brent",
        "S&P 500",
        "India VIX",
    ]  # S&P fell: not its way


def test_a_right_day_or_an_unchecked_one_gives_the_two_largest_context_moves():
    inside = Outcome(MON, 25350.0, BAND, True, True, True, provisional=True)
    assert [p.name for p in evening_points(inside, (), CUES)] == ["Brent", "S&P 500"]
    assert [p.name for p in evening_points(None, (), CUES)] == ["Brent", "S&P 500"]
    quiet = evening_points(inside, (), CUES[2:3])  # nothing shown: said, never padded
    assert [p.text for p in quiet] == ["no notable moves in our data"]
    one = evening_points(inside, (), CUES[3:])
    assert [p.name for p in one] == ["India VIX", "no notable moves in our data"]


class Broken(Section):
    name = "S&P 500"

    def read(self, day, edition):
        raise KeyError("sp500: no table loaded")


def test_a_failing_section_is_failed_and_said_and_the_page_still_builds():
    from fno.forecast_lab.page.builder import PageBuilder

    from .builders import SESSIONS, Forecasts, at
    from .test_page_builder import History, NoFacts

    pages = PageBuilder(Forecasts((implied(FRI),)), History(), NoFacts(), SESSIONS, underlyings=("NIFTY",),
                        sections=(Broken(),))  # fmt: skip
    view = pages.build(MON, at(MON, 8, 50), "morning")
    assert [(s.name, s.status) for s in view.cues] == [("S&P 500", FAILED)]
    assert "S&P 500: the read failed (KeyError)" in view.system
    assert view.indices[0].why[0].role == "used"


def test_the_page_carries_the_why_of_each_index():
    view = build("evening", (implied(FRI), implied(MON)), read=25700.0, at_time=(20, 5))
    assert view.indices[0].why[0].name == "Reason (after the fact)"
    assert view.indices[0].why[0].text == "no clear reason in our data"


def test_gift_nifty_s_gap_follows_the_flags_in_the_morning():
    gift = SectionView("GIFT Nifty", AVAILABLE, MON, (Cue("GIFT Nifty", 25125.5, 0.5, "%", MON),))
    points = morning_points("rv20", (*CUES, gift, FLAG))
    assert [p.name for p in points] == ["Built from", "RBI policy decision", "GIFT Nifty", "Brent"]
