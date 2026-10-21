"""A20b criteria 7 and 8: new circulars are listed in the run that first sees them, with first-seen time and file
status; a failed file is retried (a link failing twice then working ends `saved` with the first first-seen time;
still failing after 3 days ends `abandoned`); a second run with the same list writes nothing; the NSE window is 14
days; a feed that is stale by its rule or that skipped items is a problem, never "nothing new"."""

from datetime import UTC, date, datetime, timedelta

from fno.circulars.capture import LIST_TABLE, WINDOW, CircularCapture, file_path
from fno.circulars.model import ABANDONED, COLUMNS, FAILED, NOT_KEPT, NSE, SAVED, SEBI, Circular, FeedFailed, Problem
from fno.storage.data_store import DataStore
from fno.storage.part_table import read_parts
from fno.storage.raw_store import LocalFolderStore
from fno.storage.receipts import ReceiptFolder

D16 = date(2026, 10, 16)
NOW = datetime(2026, 10, 16, 11, 5, tzinfo=UTC)
FNO = Circular(NSE, "NSE/FAOP/76921", D16, "Futures & Options", "Trading", "Mock trading", "https://x/FAOP76921.pdf")
MF = Circular(NSE, "NSE/NMF/76970", D16, "Mutual Fund", "Trading", "Suspension", "https://x/NMF76970.zip")
SEBI_C = Circular(SEBI, "105293", D16, "", "", "derivatives", "https://www.sebi.gov.in/legal/circulars/a_105293.html")


class Feed:
    def __init__(self, listed=(), error=None, latest_page_only=False, broken=()):
        self.listed, self.error, self.broken, self.asked = list(listed), error, set(broken), []
        self.LATEST_PAGE_ONLY = latest_page_only

    def fetch(self, since, until):
        self.asked.append((since, until))
        if self.error:
            raise self.error
        return self.listed

    def download(self, circular):
        if circular.link in self.broken:
            raise FeedFailed(f"{circular.link}: HTTP 403")
        return f"file of {circular.number}".encode()


def fresh(source, listed, today):
    return None


class Clock:
    def __init__(self, now=NOW):
        self.now = now

    def __call__(self):
        return self.now


def capture(tmp_path, feeds, clock=None, freshness=None, run="20261016T110500Z-aaaaaa"):
    drive = LocalFolderStore(tmp_path / "drive")
    store = DataStore(drive, "data", ReceiptFolder(tmp_path / "receipts"), "circulars", run)
    checks = freshness or dict.fromkeys(feeds, fresh)
    return drive, CircularCapture(feeds, checks, lambda c: c.number in {FNO.number, SEBI_C.number}, store,
                                  clock or Clock(), out=[].append)  # fmt: skip


def rows(tmp_path):
    folder = tmp_path / "drive" / "data" / LIST_TABLE
    return read_parts(folder, COLUMNS) if folder.exists() else []


def test_new_circulars_are_listed_at_first_sight_with_time_and_file_status(tmp_path):
    drive, cap = capture(tmp_path, {NSE: Feed([FNO, MF])})
    assert cap.run(D16, []) == []
    assert [(r["number"], r["fno_relevant"], r["file"], r["first_seen_at"]) for r in rows(tmp_path)] == [
        ("NSE/FAOP/76921", "yes", SAVED, "2026-10-16T11:05:00+00:00"),
        ("NSE/NMF/76970", "no", NOT_KEPT, "2026-10-16T11:05:00+00:00"),
    ]
    assert (
        drive.get(f"data/{file_path(FNO)}") == b"file of NSE/FAOP/76921" and drive.get(f"data/{file_path(MF)}") is None
    )
    assert file_path(FNO) == "circulars/files/nse/2026/10/FAOP76921.pdf"


def test_an_empty_list_and_a_second_run_with_the_same_list_write_no_part(tmp_path):
    _, cap = capture(tmp_path, {NSE: Feed([])})
    assert cap.run(D16, []) == [] and rows(tmp_path) == []
    _, cap = capture(tmp_path, {NSE: Feed([FNO, MF])})
    seen = [FNO.row(True, "t0", SAVED), MF.row(False, "t0", NOT_KEPT)]
    assert cap.run(D16, seen) == [] and rows(tmp_path) == []


def test_every_run_asks_nse_for_14_days():
    assert timedelta(days=14) == WINDOW


def test_the_feed_is_asked_from_14_days_back(tmp_path):
    feed = Feed([])
    capture(tmp_path, {NSE: feed})[1].run(D16, [])
    assert feed.asked == [(date(2026, 10, 2), D16)]


def test_a_link_failing_twice_then_working_ends_saved_with_its_first_first_seen_time(tmp_path):
    feed, clock = Feed([FNO], broken=[FNO.link]), Clock()
    problems = capture(tmp_path, {NSE: feed}, clock, run="r1-aaaaaa")[1].run(D16, [])
    assert [p.key for p in problems] == ["file:nse:NSE/FAOP/76921"]
    assert [(r["file"], r["first_seen_at"]) for r in rows(tmp_path)] == [(FAILED, "2026-10-16T11:05:00+00:00")]
    clock.now = NOW + timedelta(hours=1)
    problems = capture(tmp_path, {NSE: feed}, clock, run="r2-aaaaaa")[1].run(D16, rows(tmp_path))
    assert [p.key for p in problems] == ["file:nse:NSE/FAOP/76921"] and len(rows(tmp_path)) == 1  # no new row
    feed.broken.clear()
    clock.now = NOW + timedelta(hours=2)
    assert capture(tmp_path, {NSE: feed}, clock, run="r3-aaaaaa")[1].run(D16, rows(tmp_path)) == []
    assert [(r["file"], r["first_seen_at"]) for r in rows(tmp_path)] == [
        (FAILED, "2026-10-16T11:05:00+00:00"), (SAVED, "2026-10-16T11:05:00+00:00"),
    ]  # fmt: skip


def test_a_file_still_failing_after_3_days_is_abandoned_once(tmp_path):
    feed, clock = Feed([FNO], broken=[FNO.link]), Clock()
    capture(tmp_path, {NSE: feed}, clock, run="r1-aaaaaa")[1].run(D16, [])
    clock.now = NOW + timedelta(days=3)  # exactly 3 days: still retried
    problems = capture(tmp_path, {NSE: feed}, clock, run="r2-aaaaaa")[1].run(D16, rows(tmp_path))
    assert [p.key for p in problems] == ["file:nse:NSE/FAOP/76921"] and len(rows(tmp_path)) == 1
    clock.now = NOW + timedelta(days=3, minutes=1)
    problems = capture(tmp_path, {NSE: feed}, clock, run="r3-aaaaaa")[1].run(D16, rows(tmp_path))
    assert [(p.key, p.episode) for p in problems] == [("file:nse:NSE/FAOP/76921:abandoned", False)]
    assert [r["file"] for r in rows(tmp_path)] == [FAILED, ABANDONED]
    assert capture(tmp_path, {NSE: feed}, clock, run="r4-aaaaaa")[1].run(D16, rows(tmp_path)) == []  # never again


def test_a_failed_feed_is_a_problem_and_the_other_feed_still_runs(tmp_path):
    feeds = {NSE: Feed(error=FeedFailed("HTTP 403")), SEBI: Feed([SEBI_C], latest_page_only=True)}
    problems = capture(tmp_path, feeds)[1].run(D16, [])
    assert [(p.key, p.text) for p in problems] == [("nse:list", "nse: list NOT read: HTTP 403")]
    assert [r["source"] for r in rows(tmp_path)] == [SEBI]


def test_a_stale_feed_is_a_problem_and_its_new_circulars_are_still_listed(tmp_path):
    def stale(source, listed, today):
        return Problem(f"{source}:stale", "stale")

    problems = capture(tmp_path, {NSE: Feed([MF])}, freshness={NSE: stale})[1].run(D16, [])
    assert [p.key for p in problems] == ["nse:stale"] and len(rows(tmp_path)) == 1


def test_a_latest_page_with_nothing_seen_before_is_a_possible_gap(tmp_path):
    feeds = {SEBI: Feed([SEBI_C], latest_page_only=True)}
    old = Circular(SEBI, "1", D16, "", "", "x", "https://old").row(False, "t0", NOT_KEPT)
    problems = capture(tmp_path, feeds)[1].run(D16, [old])
    assert [p.key for p in problems] == ["sebi:gap"] and [r["number"] for r in rows(tmp_path)] == ["105293"]
    assert capture(tmp_path, feeds, run="r2-aaaaaa")[1].run(D16, []) == []  # the first ever run: no gap check


def test_a_failed_list_part_keeps_the_run_s_other_problems(tmp_path):
    def stale(source, listed, today):
        return Problem(f"{source}:stale", "stale")

    drive, cap = capture(tmp_path, {NSE: Feed([MF])}, freshness={NSE: stale})
    cap.table.write = lambda day, rows: (_ for _ in ()).throw(OSError("drive 503"))
    assert [p.key for p in cap.run(D16, [])] == ["nse:stale", "list-part"]


def test_a_file_already_receipted_counts_as_saved_without_downloading(tmp_path):
    drive, cap = capture(tmp_path, {NSE: Feed([FNO])})
    cap.store.put(file_path(FNO), b"the first copy")  # saved by a run whose list part then failed
    feed = Feed([FNO], broken=[FNO.link])
    _, cap = capture(tmp_path, {NSE: feed}, run="r2-aaaaaa")
    assert cap.run(D16, []) == [] and [r["file"] for r in rows(tmp_path)] == [SAVED]
