from datetime import date

import pytest

from fno.filings.day_lists import EveryDayCalendar, check_day_list
from fno.filings.sources import NseAnnouncementsSource, NseBoardMeetingsSource, NseFilingFileSource
from fno.http_pacing import HOST_SPACING_SECONDS, PacedSession, RequestPacer
from fno.providers.public import PublicData
from fno.storage.wiring import build_nse_source


def test_day_list_paths_and_urls():
    path = NseAnnouncementsSource.path_for(date(2025, 3, 7))
    assert path == "nse/equities/filings/announcements/2025/03/announcements_20250307.json"
    assert NseAnnouncementsSource.url_for(path).endswith("from_date=07-03-2025&to_date=07-03-2025")
    assert NseBoardMeetingsSource.day_for_path(NseBoardMeetingsSource.path_for(date(2024, 1, 2))) == date(2024, 1, 2)
    assert EveryDayCalendar().is_session(date(2025, 3, 9))  # a Sunday: companies announce on any day


def test_filing_file_url_is_nse_xbrl_folder_and_name():
    path = "nse/equities/filings/results-xbrl/TCS/INDAS_1.xml"
    assert NseFilingFileSource.url_for(path) == "https://nsearchives.nseindia.com/corporate/xbrl/INDAS_1.xml"


def test_day_list_check():
    check_day_list("a.json", b"[]")
    check_day_list("a.json", b'[{"symbol": "TCS"}]')
    for bad in (b"<html>", b'{"data": []}'):
        with pytest.raises(ValueError):
            check_day_list("a.json", bad)


def test_every_nse_request_of_the_archive_goes_through_the_paced_session():
    assert isinstance(build_nse_source(NseFilingFileSource).session, PacedSession)
    assert isinstance(PublicData().session, PacedSession)
    assert HOST_SPACING_SECONDS["www.nseindia.com"] >= 1.0 and HOST_SPACING_SECONDS["nsearchives.nseindia.com"] >= 1.0


def test_a_planted_burst_is_spread_to_one_request_per_second_per_host():
    now = [0.0]
    pacer = RequestPacer(clock=lambda: now[0])
    pacer.sleep = lambda seconds: now.__setitem__(0, now[0] + seconds)
    starts = {"www.nseindia.com": [], "nsearchives.nseindia.com": []}
    for _ in range(10):
        for host, times in starts.items():
            pacer.wait_turn(host)
            times.append(now[0])
    for times in starts.values():
        assert all(later - earlier >= 1.0 for earlier, later in zip(times, times[1:], strict=False))


def test_day_lists_resume_at_the_first_day_without_a_manifest_row(tmp_path):
    from fno.filings.runs_cli import first_unarchived_day
    from fno.storage.manifest_folder import Fingerprint, ManifestFolder

    manifests, source = ManifestFolder(tmp_path), NseAnnouncementsSource
    first = date(2023, 10, 13)
    assert first_unarchived_day(source, date(2026, 10, 12), manifests, first) == first
    days = [first, date(2023, 10, 14), date(2023, 10, 16)]
    for day in days:
        manifests.record(source, Fingerprint.of(source, source.path_for(day), b"[]"))
    assert first_unarchived_day(source, date(2026, 10, 12), manifests, first) == date(2023, 10, 15)
    assert first_unarchived_day(source, date(2023, 10, 14), manifests, first) == date(2023, 10, 15)  # all done: end + 1


def test_nse_not_found_web_page_served_with_200_is_not_published():
    class Answer:
        status_code, headers = 200, {}
        content = b'<!DOCTYPE html>\n<html lang="en"><head></head><body>doesn\'t appear to exist</body></html>'

        def raise_for_status(self):
            return None

    class Session:
        def get(self, url, timeout):
            return Answer()

    source = NseFilingFileSource(Session())
    assert source.fetch("nse/equities/filings/results-xbrl/LT/INTEGRATED_FILING_INDAS_1477033.xml") is None
    Answer.content = b'<?xml version="1.0"?><xbrli:xbrl/>'
    assert source.fetch("nse/equities/filings/results-xbrl/LT/X.xml") == Answer.content
