"""FL1-1c: the message's content from one page model (text, picture, details file); a picture that cannot be made
never stops the report (the file and the text go, and one alert says why); both pages are self-contained."""

from datetime import date, datetime
from pathlib import Path

from fno.forecast_lab.maker import ReportMaker
from fno.forecast_lab.page.camera import ChromiumCamera, PageCamera, PictureFailed
from fno.forecast_lab.page.render import InterimRenderer

from .page_builders import days, index, outcome, page


class Pages:
    def __init__(self, view):
        self.view, self.calls = view, []

    def build(self, day, now, edition, alerts, checks, confirmation):
        self.calls.append((edition, alerts, checks, confirmation))
        return self.view


class Camera(PageCamera):
    def __init__(self, fail=False):
        self.fail = fail

    def picture(self, html, out):
        if self.fail:
            raise PictureFailed("no Chromium at /nowhere")
        out.write_bytes(b"PNG" + html[:15].encode())
        return out


def view_with_history():
    from dataclasses import replace

    from fno.forecast_lab.page.model import Horizon, Timeline

    points = tuple(outcome(d, 1000.0 + (30 if i == 3 else 0)) for i, d in enumerate(days(30)))
    return page(indices=(replace(index(), horizons=(Horizon(Timeline("N1", "implied", points), ()),)),))


def test_the_text_picture_and_details_come_from_one_page_model():
    pages = Pages(view_with_history())
    made = ReportMaker(pages, InterimRenderer(), Camera()).make(date(2026, 10, 23), datetime.now(), "evening",
                                                                ("an alert",), "a\n\nb")  # fmt: skip
    assert made.text.endswith("Research only. Not a trade tip.") and made.alerts == ()
    assert [f.name for f in made.files] == ["forecast-evening-2026-10-23.png", "forecast-evening-2026-10-23.html"]
    assert made.files[0].data.startswith(b"PNG<!doctype")
    assert pages.calls == [("evening", ("an alert",), ("a", "b"), ())]


def test_a_picture_that_cannot_be_made_sends_the_file_and_the_text_with_one_alert():
    maker = ReportMaker(Pages(view_with_history()), InterimRenderer(), Camera(fail=True))
    made = maker.make(date(2026, 10, 23), datetime.now(), "morning")
    assert [f.name for f in made.files] == ["forecast-morning-2026-10-23.html"] and made.text
    assert made.alerts == ("the morning picture was not made (no Chromium at /nowhere); the text and the details file "
                           "were posted without it",)  # fmt: skip


def test_both_pages_are_self_contained_and_carry_the_research_line():
    renderer, view = InterimRenderer(), view_with_history()
    for html in (renderer.picture(view), renderer.details(view)):
        assert "http://" not in html and "https://" not in html and "<link" not in html
        assert "Research only. Not a trade tip." in html or "Paper research only" in html
    assert "<script>" in renderer.details(view) and "<script>" not in renderer.picture(view)


def test_the_camera_says_why_when_chromium_is_missing(tmp_path):
    try:
        ChromiumCamera(executable=Path("/nowhere/chromium")).picture("<p>", tmp_path / "x.png")
    except PictureFailed as failed:
        assert str(failed) == "no Chromium at /nowhere/chromium"
    else:
        raise AssertionError("no picture without Chromium")


def test_the_real_camera_draws_the_picture_page_at_its_width_and_trims_the_bottom(tmp_path):
    camera = ChromiumCamera(width=600)
    if not camera.executable.exists():  # the routine's environment has it (/opt/pw-browsers); a laptop may not
        return
    from PIL import Image

    out = camera.picture(InterimRenderer().picture(view_with_history()), tmp_path / "p.png")
    with Image.open(out) as image:
        assert image.format == "PNG" and image.size[0] == 1200 and image.size[1] < 4000 * 2


def test_a_verdict_is_kept_only_for_today_s_own_provisional_check():
    from dataclasses import replace

    from fno.forecast_lab.maker import verdicts
    from fno.forecast_lab.page.model import Band, Horizon, Outcome, Timeline

    band = Band(980.0, 995.0, 1000.0, 1005.0, 1020.0)
    other = Outcome(date(2026, 10, 22), 1001.0, band, True, True, True, provisional=True)
    view = page(indices=(replace(index(), horizons=(Horizon(Timeline("N1", "implied", (other,)), ()),)),))
    assert verdicts(view) == ()
    today = replace(other, day=view.day)
    view = page(indices=(replace(index(), horizons=(Horizon(Timeline("N1", "implied", (today,)), ()),)),))
    assert [(v.day, v.close, v.band) for v in verdicts(view)] == [(view.day, 1001.0, (980.0, 995.0, 1005.0, 1020.0))]


def test_a_failed_section_is_alerted_once_with_the_report():
    from dataclasses import replace

    from fno.forecast_lab.page.cues import FAILED, SectionView

    view = replace(view_with_history(), cues=(SectionView("S&P 500", FAILED, why="S&P 500: the read failed (X)"),))
    made = ReportMaker(Pages(view), InterimRenderer(), Camera()).make(date(2026, 10, 23), datetime.now(), "morning")
    assert made.alerts == ("S&P 500: the read failed (X)",)
