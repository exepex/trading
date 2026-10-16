"""One rates run end to end on a local folder for Drive (story A21, criteria 3, 5, 6 and 13)."""

import re
from datetime import timedelta

from fno.rates.constants import RBI_RELEASE, RBI_RELEASES
from fno.rates.fetch import RateFetchError

from .helpers import HOME, LIST, RELEASE, T0, Clock, capture, pages


def test_a_first_run_adds_the_release_and_the_repo_rate_and_stores_every_page(tmp_path):
    run, failures, alerts, _ = capture(tmp_path, pages())
    result = run.run()
    assert sorted((r.rate, r.value_pct) for r in result.added) == [
        ("policy_repo", "5.50"), ("tbill_182d_cutoff", "6.2896"), ("tbill_364d_cutoff", "6.4891"),
        ("tbill_91d_cutoff", "5.7281")]  # fmt: skip
    assert (failures.rows, alerts.sent) == ([], [])
    stored = sorted(p.name for p in (tmp_path / "drive" / "data" / "rates").rglob("*.*"))
    assert [name.split("_", 1)[1] for name in stored if name.endswith(".html")] == ["home.html", "list.html",
                                                                                     "release_63803.html"]  # fmt: skip
    assert len(list((tmp_path / "receipts").rglob("*.sha256"))) == 4  # three pages and one table part


def test_a_second_run_adds_nothing_and_a_changed_repo_rate_adds_one_row_and_an_information_line(tmp_path):
    capture(tmp_path, pages())[0].run()
    again = capture(tmp_path, pages(), clock=Clock(T0 + timedelta(minutes=5)), run="20261016T131500Z-bbbbbb")[0].run()
    assert again.added == [] and again.problems == []
    changed = re.sub(rb"(Policy Repo Rate.*?)5\.50%", rb"\g<1>5.25%", HOME, count=1, flags=re.S)
    later = Clock(T0 + timedelta(minutes=10))
    run, failures, alerts, _ = capture(tmp_path, pages(home=changed), clock=later, run="20261016T132000Z-cccccc")
    result = run.run()
    assert [(r.rate, r.value_pct) for r in result.added] == [("policy_repo", "5.25")]
    assert failures.rows == [] and "changed from 5.50% to 5.25%" in alerts.sent[0]


def test_a_refused_page_and_a_changed_layout_are_one_row_each_and_one_alert(tmp_path):
    home = RateFetchError("refused", "https://www.rbi.org.in/: HTTP 403")
    release = b"<html>Date : Oct 14, 2026 nothing else</html>"
    run, failures, alerts, _ = capture(tmp_path, pages(home=home, release=release))
    result = run.run()
    assert result.added == []
    assert [(step, kind) for _, step, kind, _ in failures.rows] == [("home", "refused"), ("release 63803", "layout")]
    assert len(alerts.sent) == 1 and "HTTP 403" in alerts.sent[0] and "'title'" in alerts.sent[0]


def test_an_unreadable_history_stops_before_fetching_anything(tmp_path):
    class Broken:
        def rows(self):
            raise RuntimeError("rates table not readable from Drive")

        def last_home_read(self):
            return None

    run, failures, alerts, fetch = capture(tmp_path, pages(), history=Broken())
    result = run.run()
    assert fetch.asked == [] and result.added == []
    assert [kind for _, _, kind, _ in failures.rows] == ["history_unreadable"] and len(alerts.sent) == 1


def test_a_week_later_with_no_new_release_is_stale_and_a_down_home_page_too(tmp_path):
    capture(tmp_path, pages())[0].run()
    later = Clock(T0 + timedelta(days=9))
    down = RateFetchError("unreachable", "https://www.rbi.org.in/: ConnectionError")
    run, failures, alerts, _ = capture(tmp_path, pages(home=down), clock=later, run="20261025T131000Z-dddddd")
    run.run()
    kinds = [kind for _, _, kind, _ in failures.rows]
    assert kinds == ["unreachable", "stale", "stale"]  # one O10 row per failure: the auction and the home page
    assert alerts.sent[0].count("stale:") == 2


def test_a_table_that_cannot_be_written_claims_no_rows(tmp_path):
    run, failures, _, _ = capture(tmp_path, pages())

    class DownTable:
        def write(self, day, rows):
            raise OSError("Drive is down")

    run.table = DownTable()
    result = run.run()
    assert result.added == [] and [kind for _, _, kind, _ in failures.rows] == ["store_failed"]


def test_the_list_unreachable_still_reads_the_repo_rate(tmp_path):
    down = RateFetchError("unreachable", f"{RBI_RELEASES}: Timeout")
    run, failures, _, _ = capture(tmp_path, pages(releases=down))
    result = run.run()
    assert [r.rate for r in result.added] == ["policy_repo"]
    assert [(step, kind) for _, step, kind, _ in failures.rows] == [("release list", "unreachable")]


class SlowPages:
    """Moves the clock forward while the request is in flight, so the arrival time differs from the request time."""

    def __init__(self, inner, clock, seconds):
        self.inner, self.clock, self.seconds = inner, clock, seconds

    def get(self, url):
        self.clock.now += timedelta(seconds=self.seconds)
        return self.inner.get(url)


def test_first_seen_is_the_arrival_of_the_response(tmp_path):
    clock = Clock()
    run, _, _, fetch = capture(tmp_path, pages(), clock=clock)
    run.pages = SlowPages(fetch, clock, 30)
    started = clock.now
    result = run.run()
    repo = next(r for r in result.added if r.rate == "policy_repo")
    assert repo.seen_at >= started + timedelta(seconds=30)  # never the time the request left


def test_a_disagreement_is_one_o10_row_and_one_alert(tmp_path):
    other = re.sub(rb"(91 day T-bills.*?)5\.7281%", rb"\g<1>5.9000%", HOME, count=1, flags=re.S)
    run, failures, alerts, _ = capture(tmp_path, pages(home=other))
    run.run()
    assert [kind for _, _, kind, _ in failures.rows] == ["disagreement"] and "5.9000%" in alerts.sent[0]


def test_a_release_that_failed_once_is_retried_while_a_newer_one_is_kept(tmp_path):
    capture(tmp_path, pages())[0].run()  # records 63803
    two = LIST.replace(
        b"prid=63803>",
        b"prid=63950>91-Day, 182-Day and 364-Day T-Bill Auction Result: Cut-off</a>"
        b"<a class='link2' href=BS_PressReleaseDisplay.aspx?prid=63900>",
        1,
    )
    found = pages(releases=two)
    found[RBI_RELEASE.format(prid=63950)] = RELEASE.replace(b"Oct 14, 2026", b"Oct 28, 2026")
    found[RBI_RELEASE.format(prid=63900)] = RateFetchError("unreachable", "timeout")
    later = Clock(T0 + timedelta(days=14))
    first = capture(tmp_path, found, clock=later, run="20261030T131000Z-eeeeee")[0].run()
    assert {r.note for r in first.added if r.rate == "tbill_91d_cutoff"} == {"prid=63950"}
    found[RBI_RELEASE.format(prid=63900)] = RELEASE.replace(b"Oct 14, 2026", b"Oct 21, 2026")
    retry = capture(tmp_path, found, clock=Clock(T0 + timedelta(days=15)), run="20261031T131000Z-ffffff")[0].run()
    assert {r.note for r in retry.added if r.rate == "tbill_91d_cutoff"} == {"prid=63900"}


def test_a_drive_conflict_is_a_named_store_failure(tmp_path):
    capture(tmp_path, pages())[0].run()
    changed = HOME.replace(b"Policy Repo Rate", b"Policy Repo Rate", 1) + b"<!-- other bytes -->"
    run, failures, _, _ = capture(tmp_path, pages(home=changed))  # same clock: same path, other bytes
    run.run()
    assert ("home", "store_failed") in [(step, kind) for _, step, kind, _ in failures.rows]


def test_an_unreadable_home_page_never_counts_as_a_read(tmp_path):
    capture(tmp_path, pages())[0].run()
    broken = HOME.replace(b"Policy Repo Rate", b"Policy rate")
    later = Clock(T0 + timedelta(hours=49))
    run, failures, _, _ = capture(tmp_path, pages(home=broken), clock=later, run="20261018T141000Z-gggggg")
    run.run()
    assert [kind for _, _, kind, _ in failures.rows] == ["layout", "stale"]  # the 48 h clock was not reset
    assert any(p.name.endswith("_home_unreadable.html") for p in (tmp_path / "drive").rglob("*.html"))


def test_no_change_notice_without_its_row(tmp_path):
    capture(tmp_path, pages())[0].run()
    changed = re.sub(rb"(Policy Repo Rate.*?)5\.50%", rb"\g<1>5.25%", HOME, count=1, flags=re.S)
    run, _, alerts, _ = capture(tmp_path, pages(home=changed), clock=Clock(T0 + timedelta(minutes=5)),
                                run="20261016T131500Z-hhhhhh")  # fmt: skip

    class DownTable:
        def write(self, day, rows):
            raise OSError("Drive is down")

    run.table = DownTable()
    run.run()
    assert "changed from" not in alerts.sent[0] and "table: OSError" in alerts.sent[0]
