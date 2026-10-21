"""A4h criterion 4: each earlier day confirmed once against NSE's official file (21 Oct's real values), within 0.01;
a difference alerts once; a day with no official file waits, then alerts once at the second session after it."""

import json
from datetime import date

import pytest

from fno.close_read.confirm import Confirmer
from fno.close_read.records import confirm_path, encode, overdue_path, record_path
from fno.fo_bhavcopy import BadFile
from tests.close_read.fakes import CALENDAR, DAY, OFFICIAL, Alerts, MemoryStore, Official

NEXT, SECOND = date(2026, 10, 22), date(2026, 10, 23)  # the two sessions after 21 Oct


def _recorded(nifty=22811.35, vix=15.7) -> MemoryStore:
    store = MemoryStore()
    values = {"NIFTY 50": nifty, "NIFTY BANK": 54976.9, "INDIA VIX": vix}
    store.put(record_path(DAY), encode({"indices": {k: {"last": v, "open": 1.0} for k, v in values.items()}}))
    return store


def _confirm(store, today=NEXT, official=None):
    alerts, lines = Alerts(), []
    Confirmer(store, official or Official({DAY: OFFICIAL}), CALENDAR, alerts, lines.append).run(today)
    return lines, alerts.sent


@pytest.mark.parametrize("nifty", [22811.35, 22811.34, 22811.36])
def test_within_0_01_point_is_confirmed_with_no_alert(nifty):
    store = _recorded(nifty)
    lines, sent = _confirm(store)
    assert lines == ["close confirm 2026-10-21: NIFTY 50 confirmed, NIFTY BANK confirmed, INDIA VIX differs by 0.02 "
                     "(list value)"] and sent == []  # fmt: skip
    assert json.loads(store.files[confirm_path(DAY)])["official_file"] == "ind_close_all_21102026.csv"


def test_a_difference_of_0_02_is_recorded_and_alerted_once_and_never_rewritten():
    store = _recorded(22811.33)
    lines, sent = _confirm(store)
    assert "NIFTY 50 differs by 0.02" in lines[0] and len(sent) == 1 and "NIFTY 50 differs by 0.02" in sent[0]
    before = dict(store.files)
    assert _confirm(store, SECOND, Official({DAY: {**OFFICIAL, "Nifty 50": 1.0}})) == ([], [])
    assert store.files == before


def test_vix_alone_differing_is_recorded_without_an_alert():
    lines, sent = _confirm(_recorded(vix=16.0))
    assert "INDIA VIX differs by 0.32 (list value)" in lines[0] and sent == []


def test_no_official_file_waits_then_alerts_once_at_the_second_session_after():
    store = _recorded()
    assert _confirm(store, NEXT, Official()) == (
        ["close confirm 2026-10-21: no official index-close file in Drive yet"],
        [],
    )
    lines, sent = _confirm(store, SECOND, Official())
    assert lines == ["close confirm 2026-10-21: still not confirmed on 2026-10-23 (no official index-close file); one "
                     "alert"] and len(sent) == 1 and overdue_path(DAY) in store.files  # fmt: skip
    assert _confirm(store, date(2026, 10, 26), Official()) == ([], [])  # never again
    assert _confirm(store, date(2026, 10, 26))[0][0].startswith("close confirm 2026-10-21: NIFTY 50 confirmed")


def test_today_is_never_confirmed_and_a_damaged_file_says_so():
    assert _confirm(_recorded(), DAY) == ([], [])
    lines, sent = _confirm(_recorded(), NEXT, Official(raises=BadFile("x")))
    assert lines == ["close confirm 2026-10-21: the official file cannot be read; not confirmed"] and sent == []
