"""REH1c: A17e's Yahoo reads in a rehearsal are the copies the day archived, at their own fetch times, checked
against their snapshot-log rows; a URL the day never fetched near then is a request never sent."""

import hashlib
from datetime import datetime, timedelta

import pytest
import requests

from fno.models import IST
from fno.rehearsal.recorded_cues import RecordedCueSession

URL = "https://query1.finance.yahoo.com/v8/finance/chart/%5EAXJO?range=1d&interval=5m"
PATH = "yahoo/preopen/2026/10/23/085039_asx200_5m.json"
DATA = b'{"chart": {}}'


class Clock:
    def __init__(self, at):
        self.at = at

    def __call__(self):
        return self.at

    def sleep(self, seconds):
        self.at += timedelta(seconds=seconds)


@pytest.fixture
def logs(tmp_path):
    row = f"2026-10-23T08:50:39.952721+05:30,{PATH},{URL},,{hashlib.sha256(DATA).hexdigest()},{len(DATA)}\n"
    (tmp_path / "asx200_preopen.csv").write_text("fetched_at,path,url,form,sha256,size_bytes\n" + row)
    return tmp_path


def test_a_read_gets_the_day_s_archived_copy_at_its_own_time(logs):
    clock = Clock(datetime(2026, 10, 23, 8, 50, 35, tzinfo=IST))
    answer = RecordedCueSession(logs, {PATH: DATA}.get, clock, clock.sleep).get(URL, timeout=5, allow_redirects=False)
    assert (answer.status_code, answer.is_redirect, answer.content) == (200, False, DATA)
    assert clock() >= datetime(2026, 10, 23, 8, 50, 39, tzinfo=IST)


def test_an_unrecorded_url_or_a_changed_copy_is_a_request_never_sent(logs):
    clock = Clock(datetime(2026, 10, 23, 8, 50, 35, tzinfo=IST))
    with pytest.raises(requests.RequestException, match="rehearsal:NOT_RECORDED"):
        RecordedCueSession(logs, {PATH: DATA}.get, clock, clock.sleep).get(URL.replace("AXJO", "N225"))
    with pytest.raises(requests.RequestException, match="differs from its snapshot-log row"):
        RecordedCueSession(logs, {PATH: b"changed"}.get, clock, clock.sleep).get(URL)
