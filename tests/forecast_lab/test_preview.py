"""FL1-1f: the owner's preview of an edition: today's code, posted once to #fno-forecast under a bold "DRY RUN" first
line; it writes nothing and alerts nobody; a morning preview is posted only when every range of its sealed record is
unchanged. Fakes only: nothing is posted."""

from datetime import date, datetime

from fno.forecast_lab.delivery import Attachment, Delivery, ReportPoster
from fno.forecast_lab.edition_run import Composer
from fno.forecast_lab.preview import Preview, same_ranges
from fno.forecast_lab.written import WrittenReport

DAY, NOW = date(2026, 10, 23), datetime(2026, 10, 23, 8, 50)
SEALED = "*NIFTY* · today: most likely 22,530–22,800 (almost certainly 22,280–23,020) · 🟢 right 25 of 30"
NEW = "*NIFTY* · today: most likely 22,530–22,800 (almost certainly 22,280–23,020) · 🟢 Live so far: none"
FILES = (Attachment("p.png", b"png", "Today's forecast"),)


class Composing(Composer):
    def __init__(self, text):
        self.text = text

    def compose(self, day, now):
        return WrittenReport(self.text, ("NIFTY N3: no forecast was sealed",), attachments=FILES)


class Poster(ReportPoster):
    def __init__(self):
        self.posts = []

    def post(self, text, attachments):
        self.posts.append((text, attachments))
        return Delivery("report to #fno-forecast: posted", sent=True)


def preview(text, sealed=SEALED):
    poster = Poster()
    return Preview(Composing(text), poster, lambda day: WrittenReport(sealed, ()) if sealed else None), poster


def test_a_preview_is_posted_once_under_its_dry_run_label_with_its_files_and_alerts_nobody():
    run, poster = preview(NEW)
    lines, posted = run.run("evening", DAY, NOW)
    ((text, files),) = poster.posts
    assert posted and files == list(FILES)
    assert text.splitlines()[0] == ("*DRY RUN (owner's preview, 23 Oct): not today's report; the official editions "
                                    "are above*") and text.endswith(NEW)  # fmt: skip
    assert lines == ["lab preview 2026-10-23 evening: report to #fno-forecast: posted",
                     "lab preview 2026-10-23: would alert: NIFTY N3: no forecast was sealed"]  # fmt: skip


def test_a_morning_preview_keeps_the_sealed_numbers_or_is_not_posted():
    run, poster = preview(NEW)
    assert run.run("morning", DAY, NOW)[1] and len(poster.posts) == 1
    changed, poster = preview(NEW.replace("22,800", "22,810"))
    lines, posted = changed.run("morning", DAY, NOW)
    assert not posted and not poster.posts and "differ from its sealed record" in lines[0]
    unsealed, poster = preview(NEW, sealed=None)
    assert not unsealed.run("morning", DAY, NOW)[1] and not poster.posts


def test_the_ranges_compared_are_every_most_likely_and_almost_certainly_pair():
    assert same_ranges(SEALED, NEW) == []
    assert same_ranges(SEALED, "nothing") == ["most likely 22,530–22,800 (almost certainly 22,280–23,020)"]


def test_the_preview_never_builds_a_run_that_writes():
    """Only `EditionRun` writes records, markers and receipts; the preview's wiring never makes one."""
    import inspect

    from fno.forecast_lab import wiring

    source = inspect.getsource(wiring.build_preview)
    assert "EditionRun" not in source and "build_alert_sender" not in source and "build_composer" in source


def test_the_command_needs_an_edition_and_runs_it_at_its_own_posting_time(monkeypatch):
    from argparse import Namespace

    from fno.forecast_lab import cli

    out, seen = [], {}

    class Run:
        def run(self, edition, day, now):
            seen.update(edition=edition, now=now)
            return ["posted"], True

    monkeypatch.setattr("fno.forecast_lab.wiring.build_preview", lambda edition: Run())
    assert cli.cmd_lab(Namespace(action="preview", edition=None, day=DAY), out.append) == 1 and "--edition" in out[0]
    assert cli.cmd_lab(Namespace(action="preview", edition="evening", day=DAY), out.append) == 0
    assert (seen["edition"], seen["now"].strftime("%Y-%m-%d %H:%M %z")) == ("evening", "2026-10-23 20:05 +0530")
