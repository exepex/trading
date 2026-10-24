"""REH1h (DRY2's gap G2b): a file the day's own routine archived is served from the record near its row's commit,
never before it (H1, H2); a copy that differs from its row or is missing is refused (H3); one copy or a refusal (H4);
everything else is today's "not recorded" (H5)."""

import hashlib
import re
from datetime import UTC, date, datetime, timedelta

import pytest

from fno.models import IST
from fno.rehearsal.manifest_rows import A9Row
from fno.rehearsal.nse_wiring import NOT_RECORDED, NotRecorded
from fno.rehearsal.recorded_archive import RecordedArchiveSession, path_of
from fno.storage.raw_source import NseDailyFoSource, ParticipantOiSource
from fno.storage.snapshot_source import (
    CorporateActionsBySymbolSource,
    FiiDiiCashBySessionSource,
    FiiDiiCashSource,
    FoBanListSource,
)

DAY = date(2026, 10, 23)
FO_PATH = NseDailyFoSource.path_for(DAY)
FO_URL = NseDailyFoSource.url_for(FO_PATH)
OI_URL = ParticipantOiSource.url_for(ParticipantOiSource.path_for(DAY))
FLOWS_URL = FiiDiiCashBySessionSource.url_for(FiiDiiCashBySessionSource.path_for(DAY))
BAN_URL = FoBanListSource.url_for(FoBanListSource.path_for(DAY))


def ist(hour, minute, second=0, microsecond=0, day=DAY):
    return datetime(day.year, day.month, day.day, hour, minute, second, microsecond, tzinfo=IST)


def a9(dataset, day, url, committed, data):
    return A9Row(committed.astimezone(UTC), dataset, day, url, hashlib.sha256(data).hexdigest())


FO = a9("fo-bhavcopy", DAY, FO_URL, ist(19, 55, 20), b"fo 23")
OI = a9("participant-oi", DAY, OI_URL, ist(19, 55, 29), b"oi 23")
FLOWS = a9("fii-dii-cash-by-session", DAY, FLOWS_URL, ist(19, 55, 39), b"flows 23")


class Rows:
    def __init__(self, *rows):
        self.rows = rows

    def archived(self, url):
        return sorted(row for row in self.rows if row.url == url)


class Clock:
    """The replay clock and its real wait: a sleep moves it on by the same amount."""

    def __init__(self, at):
        self.at, self.slept = at, []

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.at += timedelta(seconds=seconds)


def session(at, *rows, files=None, day=DAY):
    clock = Clock(at)
    drive = {
        FO_PATH: b"fo 23",
        ParticipantOiSource.path_for(DAY): b"oi 23",
        FiiDiiCashBySessionSource.path_for(DAY): b"flows 23",
    }
    drive = drive if files is None else files
    reads = []

    def read(path):
        reads.append(path)
        return drive.get(path)

    served = RecordedArchiveSession(Rows(*rows), day, read, clock, clock.sleep)
    return served, clock, reads


def not_recorded(url):
    return re.escape(NOT_RECORDED.format(url=url))


# H1: served at the row's commit with the day's bytes


@pytest.mark.parametrize(("row", "data"), [(FO, b"fo 23"), (OI, b"oi 23"), (FLOWS, b"flows 23")])
def test_a_file_archived_in_the_evening_s_own_run_is_served_at_its_row_s_commit(row, data):
    served, clock, _ = session(ist(19, 53, 30), FO, OI, FLOWS)
    answer = served.get(row.url)
    assert (answer.status_code, answer.content, answer.headers) == (200, data, {})
    assert clock() == row.committed  # waited exactly until the commit, never served earlier


def test_the_real_source_gets_the_day_s_bytes_and_no_last_written_time():
    served, _, _ = session(ist(19, 53, 30), FO)
    published = NseDailyFoSource(served, sleep=lambda s: pytest.fail("no retry")).fetch_published(FO_PATH)
    assert (published.data, published.last_modified) == (b"fo 23", None)


# H2: never before the record held it; a fetch-first read after the commit is still served


def test_a_row_exactly_ten_minutes_ahead_is_served_after_the_wait_and_a_microsecond_more_is_not_recorded():
    at = FO.committed - timedelta(minutes=10)
    served, clock, _ = session(at, FO)
    assert served.get(FO_URL).content == b"fo 23"
    assert clock.slept == [600.0]
    late, clock, reads = session(at - timedelta(microseconds=1), FO)
    with pytest.raises(NotRecorded, match=f"^{not_recorded(FO_URL)}$"):
        late.get(FO_URL)
    assert (clock.slept, reads) == ([], [])


@pytest.mark.parametrize("after", [timedelta(seconds=61), timedelta(hours=1)])
def test_a_fetch_first_read_after_the_commit_is_served_the_day_s_copy_with_no_wait(after):
    served, clock, _ = session(FLOWS.committed + after, FLOWS)
    assert served.get(FLOWS_URL).content == b"flows 23"
    assert clock.slept == []


def test_a_row_committed_on_the_day_before_is_never_a_candidate():
    """The replay day is IST's: 23:59:59 on 22 Oct is the day before, 00:00:00 on 23 Oct is the day."""
    before = a9("fo-bhavcopy", DAY, FO_URL, ist(23, 59, 59, day=date(2026, 10, 22)), b"fo 23")
    served, _, _ = session(ist(0, 5), before)
    with pytest.raises(NotRecorded, match=f"^{not_recorded(FO_URL)}$"):
        served.get(FO_URL)
    midnight = a9("fo-bhavcopy", DAY, FO_URL, ist(0, 0), b"fo 23")
    assert session(ist(0, 5), midnight)[0].get(FO_URL).content == b"fo 23"


def test_a_read_the_day_saw_as_not_published_is_served_when_the_row_comes_within_ten_minutes():
    """Judge 573 m2's boundary: the day's 19:50 read found nothing yet; the row reached main at 19:55:20, so the
    rehearsal serves it after the wait, and the routine's line differs from the day's (a stated difference)."""
    served, clock, _ = session(ist(19, 50), FO)
    assert served.get(FO_URL).content == b"fo 23"
    assert clock() == FO.committed


def test_a_row_ahead_is_preferred_to_one_already_on_main():
    """The day's own read in this run: the copy committed after now, not the earlier one the record held."""
    earlier = a9("fii-dii-cash-by-session", date(2026, 10, 22), FLOWS_URL, ist(9, 0), b"flows 22")
    files = {path_of(earlier): b"flows 22", path_of(FLOWS): b"flows 23"}
    served, clock, reads = session(ist(19, 53, 30), earlier, FLOWS, files=files)
    assert served.get(FLOWS_URL).content == b"flows 23"
    assert (clock(), reads) == (FLOWS.committed, [path_of(FLOWS)])


def test_of_two_rows_ahead_the_earliest_is_served():
    later = a9("fii-dii-cash", DAY, FLOWS_URL, ist(19, 58), b"run-dated")
    files = {path_of(FLOWS): b"flows 23", path_of(later): b"run-dated"}
    served, clock, _ = session(ist(19, 53, 30), later, FLOWS, files=files)
    assert served.get(FLOWS_URL).content == b"flows 23"
    assert clock() == FLOWS.committed


def test_of_two_rows_already_on_main_the_latest_is_served():
    morning = a9("fii-dii-cash-by-session", date(2026, 10, 22), FLOWS_URL, ist(9, 0), b"flows 22")
    files = {path_of(morning): b"flows 22", path_of(FLOWS): b"flows 23"}
    served, _, _ = session(ist(21, 0), morning, FLOWS, files=files)
    assert served.get(FLOWS_URL).content == b"flows 23"


# H3: a copy that differs from its row, or is missing from Drive, is refused


@pytest.mark.parametrize("files", [{}, {FiiDiiCashBySessionSource.path_for(DAY): b"changed"}])
def test_a_missing_or_changed_copy_is_refused_naming_its_path(files):
    served, _, _ = session(ist(20, 0), FLOWS, files=files)
    with pytest.raises(NotRecorded, match=f"recorded copy {FiiDiiCashBySessionSource.path_for(DAY)} is missing"):
        served.get(FLOWS_URL)
    assert served.served == {}  # never remembered as served


# H4: one copy, or a refusal


@pytest.mark.parametrize(("dataset", "url", "source"), [("fo-ban-list", BAN_URL, FoBanListSource),
                                                         ("fii-dii-cash-by-session", FLOWS_URL,
                                                          FiiDiiCashBySessionSource)])  # fmt: skip
def test_the_same_url_with_rows_on_two_days_is_served_only_the_replay_day_s(dataset, url, source):
    old = a9(dataset, date(2026, 10, 22), url, ist(19, 55, day=date(2026, 10, 22)), b"22")
    new = a9(dataset, DAY, url, ist(19, 55), b"23")
    files = {source.path_for(date(2026, 10, 22)): b"22", source.path_for(DAY): b"23"}
    assert session(ist(21, 0), old, new, files=files)[0].get(url).content == b"23"


def test_two_rows_at_one_commit_time_with_different_copies_are_refused_as_ambiguous():
    run_dated = a9("fii-dii-cash", DAY, FLOWS_URL, FLOWS.committed, b"other")
    files = {path_of(FLOWS): b"flows 23", path_of(run_dated): b"other"}
    served, _, reads = session(ist(20, 0), FLOWS, run_dated, files=files)
    with pytest.raises(NotRecorded, match="two recorded copies reached main at 2026-10-23T19:55:39"):
        served.get(FLOWS_URL)
    assert reads == []


def test_two_rows_at_one_commit_time_with_the_same_copy_are_served():
    run_dated = a9("fii-dii-cash", DAY, FLOWS_URL, FLOWS.committed, b"flows 23")
    files = {path_of(FLOWS): b"flows 23", FiiDiiCashSource.path_for(DAY): b"flows 23"}
    assert session(ist(20, 0), FLOWS, run_dated, files=files)[0].get(FLOWS_URL).content == b"flows 23"


def test_a_repeat_request_gets_the_same_copy_even_after_a_later_row():
    rows = Rows(FLOWS)
    clock = Clock(ist(20, 0))
    files = {path_of(FLOWS): b"flows 23", FiiDiiCashSource.path_for(DAY): b"later"}
    served = RecordedArchiveSession(rows, DAY, files.get, clock, clock.sleep)
    assert served.get(FLOWS_URL).content == b"flows 23"
    rows.rows += (a9("fii-dii-cash", DAY, FLOWS_URL, ist(20, 30), b"later"),)
    clock.at = ist(21, 0)
    assert served.get(FLOWS_URL).content == b"flows 23"


# H5: empty, with today's exact message


@pytest.mark.parametrize("url", [FO_URL, "https://www.nseindia.com/", "https://www.nseindia.com/api/unknown"])
def test_a_url_with_no_candidate_is_not_recorded_with_today_s_message(url):
    served, clock, reads = session(ist(19, 53, 30))  # a holiday, a warm-up page, a dataset with no manifest
    with pytest.raises(NotRecorded, match=f"^{not_recorded(url)}$"):
        served.get(url)
    assert (clock.slept, reads) == ([], [])


def test_every_head_request_is_not_recorded_even_with_a_candidate():
    served, _, reads = session(ist(20, 0), FO)
    with pytest.raises(NotRecorded, match=f"^{not_recorded(FO_URL)}$"):
        served.head(FO_URL)
    assert reads == []


def test_a_morning_ban_list_read_is_not_recorded_only_when_its_list_reached_main_the_evening_before():
    """Judges 582 m1 and 583 m2, the record's two cases: 22 Oct's list reached main on 21 Oct at 20:00:23, so an
    08:40 read on 22 Oct has no row that day and stays "not recorded"; 23 Oct's list reached main at 00:04:12 on
    23 Oct, so an 08:40 read on 23 Oct is served it (the session's own list, committed before the read)."""
    d22 = date(2026, 10, 22)
    evening = a9("fo-ban-list", d22, BAN_URL, ist(20, 0, 23, day=date(2026, 10, 21)), b"ban 22")
    served, _, _ = session(ist(8, 40, day=d22), evening, files={FoBanListSource.path_for(d22): b"ban 22"}, day=d22)
    with pytest.raises(NotRecorded, match=f"^{not_recorded(BAN_URL)}$"):
        served.get(BAN_URL)
    after_midnight = a9("fo-ban-list", DAY, BAN_URL, ist(0, 4, 12), b"ban 23")
    files = {FoBanListSource.path_for(DAY): b"ban 23"}
    assert session(ist(8, 40), after_midnight, files=files)[0].get(BAN_URL).content == b"ban 23"


def test_a_by_session_copy_of_the_session_before_committed_on_the_replay_day_is_served():
    """Judges 582 SF1 and 583 m1, the text's own case: a 22 Oct by-session read at 19:40 gets the 21 Oct session's
    copy, which reached main at 01:07:09 on 22 Oct. A session-filed list is never held to the replay day's row."""
    d22 = date(2026, 10, 22)
    row = a9("fii-dii-cash-by-session", date(2026, 10, 21), FLOWS_URL, ist(1, 7, 9, day=d22), b"flows 21")
    files = {FiiDiiCashBySessionSource.path_for(date(2026, 10, 21)): b"flows 21"}
    served, clock, _ = session(ist(19, 40, day=d22), row, files=files, day=d22)
    assert served.get(FLOWS_URL).content == b"flows 21"
    assert clock.slept == []


def test_an_evening_ban_list_for_the_next_session_is_served():
    """Judge 582 SF1: on 21 Oct the 22 Oct list reached main at 20:00:23; a 21:00 read that evening is served it."""
    d21, d22 = date(2026, 10, 21), date(2026, 10, 22)
    row = a9("fo-ban-list", d22, BAN_URL, ist(20, 0, 23, day=d21), b"ban 22")
    files = {FoBanListSource.path_for(d22): b"ban 22"}
    assert session(ist(21, 0, day=d21), row, files=files, day=d21)[0].get(BAN_URL).content == b"ban 22"


def test_a_row_whose_path_does_not_map_back_to_its_url_is_never_served():
    """A symbol's own corporate-action list: its dataset path for the day names no symbol, so it is not the URL."""
    url = CorporateActionsBySymbolSource.SYMBOL_API.format(symbol="BANKNIFTY1")
    row = a9("corporate-actions-by-symbol", DAY, url, ist(19, 55), b"list")
    unknown = a9("no-such-dataset", DAY, url, ist(19, 55), b"list")
    served, _, reads = session(ist(20, 0), row, unknown, files={})
    with pytest.raises(NotRecorded, match="^rehearsal:NOT_RECORDED"):
        served.get(url)
    assert reads == []


def test_a_list_filed_by_the_run_s_day_is_served_only_the_replayed_day_s_own_copy():
    """Self-review 1: EQUITY_L.csv has one URL every day; 22 Oct's copy reaching main late on 23 Oct is never
    served (and so never filed) as 23 Oct's, while 23 Oct's own row is."""
    from fno.storage.snapshot_source import EquityListSource

    url = EquityListSource.url_for(EquityListSource.path_for(DAY))
    late = a9("equity-list", date(2026, 10, 22), url, ist(9, 0), b"list 22")
    served, _, reads = session(ist(9, 5), late, files={EquityListSource.path_for(date(2026, 10, 22)): b"list 22"})
    with pytest.raises(NotRecorded, match=f"^{not_recorded(url)}$"):
        served.get(url)
    assert reads == []
    own = a9("equity-list", DAY, url, ist(9, 1), b"list 23")
    files = {EquityListSource.path_for(DAY): b"list 23"}
    assert session(ist(9, 5), late, own, files=files)[0].get(url).content == b"list 23"


def test_a_drive_read_that_fails_is_a_refused_line_never_a_crash():
    def broken(path):
        raise RuntimeError("set the four FNO_GDRIVE_* settings")

    clock = Clock(ist(20, 0))
    served = RecordedArchiveSession(Rows(FO), DAY, broken, clock, clock.sleep)
    with pytest.raises(NotRecorded, match=f"recorded copy {re.escape(FO_PATH)} could not be read from Drive: set"):
        served.get(FO_URL)
