"""Story A4h-2: each index's day high, low and previous close in A4h's record, the range check (DR1's sanity check 5,
judge 541 SF1), their confirmation against the official files, the recheck's field differences, and older records."""

import json
from datetime import date

import pytest

from fno.close_read.answer import Refused, read_answer
from fno.close_read.confirm import Confirmer
from fno.close_read.constants import RECHECK
from fno.close_read.records import confirm_path, encode, overdue_path, recheck_path, record_path
from tests.close_read.fakes import (
    CALENDAR,
    DAY,
    LEVELS,
    OFFICIAL,
    RANGES,
    Alerts,
    Answers,
    Clock,
    MemoryStore,
    Official,
    answer,
    at,
    reader,
)

NEXT, SECOND = date(2026, 10, 22), date(2026, 10, 23)
PLANTED = {"NIFTY 50": (23121.37, 22650.13, 22889.17), "NIFTY BANK": (55868.33, 54697.29, 55488.43),
           "INDIA VIX": (16.21, 14.53, 14.83)}  # fmt: skip
CHECKED = ("NIFTY 50", "NIFTY BANK")


def _ranges(name, high=None, low=None):
    found_high, found_low, previous = RANGES[name]
    return {**RANGES, name: (found_high if high is None else high, found_low if low is None else low, previous)}


def test_the_record_holds_each_index_s_high_low_and_previous_close():
    store = MemoryStore()
    reader(store, Answers(answer(ranges=PLANTED)), Clock(at(15, 40))).run()
    indices = json.loads(store.files[record_path(DAY)])["indices"]
    for name, (high, low, previous) in PLANTED.items():
        assert (indices[name]["high"], indices[name]["low"], indices[name]["previous_close"]) == (high, low, previous)


@pytest.mark.parametrize("name", CHECKED)
@pytest.mark.parametrize("field", ["high", "low", "previousClose"])
@pytest.mark.parametrize("bad", [None, "", "-"])  # missing, empty, unreadable
def test_a_checked_index_without_a_readable_field_is_refused(name, field, bad):
    broken = answer()
    row = next(row for row in broken["data"] if row["index"] == name)
    row.pop(field) if bad is None else row.update({field: bad})
    with pytest.raises(Refused, match=f"^{name} has no readable {field}$"):
        read_answer(broken, DAY)


def test_india_vix_without_its_range_is_kept_with_null_fields():
    broken = answer()
    row = next(row for row in broken["data"] if row["index"] == "INDIA VIX")
    del row["high"], row["low"]
    row["previousClose"] = "-"
    got = read_answer(broken, DAY)
    assert got.values["INDIA VIX"] == {"last": 15.7, "open": 14.77, "high": None, "low": None, "previous_close": None}
    assert got.problems == {}


@pytest.mark.parametrize("name", CHECKED)
@pytest.mark.parametrize("which", ["last", "open"])
def test_the_range_check_refuses_a_paisa_beyond_the_edge_and_accepts_the_edge(name, which):
    """`last` at the day's high, `open` at its low: the edge is inside, 0.01 beyond it is refused."""
    last, _ = LEVELS[name]
    levels = {**LEVELS, name: (last, last - 100.0)}
    _, _, previous = RANGES[name]
    edges = {"last": ((last, last - 150.0), (last - 0.01, last - 150.0)),
             "open": ((last + 50.0, last - 100.0), (last + 50.0, round(last - 99.99, 2)))}  # fmt: skip
    (high, low), (beyond_high, beyond_low) = edges[which]
    got = read_answer(answer(levels=levels, ranges={**RANGES, name: (high, low, previous)}), DAY)
    assert got.values[name]["high"] == high and got.values[name]["low"] == low
    with pytest.raises(Refused, match=f"^{name}: {which} outside the day's high-low$"):
        read_answer(answer(levels=levels, ranges={**RANGES, name: (beyond_high, beyond_low, previous)}), DAY)


@pytest.mark.parametrize("name", CHECKED)
def test_a_low_above_the_high_is_refused(name):
    high, low, _ = RANGES[name]
    with pytest.raises(Refused, match=f"^{name}: low above high$"):
        read_answer(answer(ranges=_ranges(name, high=low, low=high)), DAY)


def test_india_vix_outside_its_range_is_recorded_as_a_problem_and_the_read_is_kept():
    store, lines = MemoryStore(), []
    reader(store, Answers(answer(ranges=_ranges("INDIA VIX", high=15.69))), Clock(at(15, 40)), lines=lines).run()
    record = json.loads(store.files[record_path(DAY)])
    assert record["problems"] == {"INDIA VIX": ["last outside the day's high-low"]}
    assert lines[0].startswith("close read 2026-10-21: ")


def test_a_refused_range_prints_its_reason_and_no_level():
    lines = []
    source = Answers(answer(ranges=_ranges("NIFTY 50", high=22811.34)))
    assert reader(MemoryStore(), source, Clock(at(15, 40)), lines=lines).run() == 1
    assert lines == ["close not read: NIFTY 50: last outside the day's high-low"]


def _recorded(fields=None) -> MemoryStore:
    store = MemoryStore()
    reader(store, Answers(answer()), Clock(at(15, 40))).run()
    record = json.loads(store.files[record_path(DAY)])
    for (name, key), value in (fields or {}).items():
        record["indices"][name][key] = value
    store.files[record_path(DAY)] = encode(record)
    return store


def _confirm(store, today=NEXT, official=None):
    alerts, lines = Alerts(), []
    Confirmer(store, official or Official({DAY: OFFICIAL}), CALENDAR, alerts, lines.append).run(today)
    return lines, alerts.sent


@pytest.mark.parametrize("gap", [0.0, 0.01, -0.01])
@pytest.mark.parametrize("key", ["high", "low"])
def test_a_high_or_low_within_0_01_of_the_official_file_confirms(key, gap):
    high, low, _ = RANGES["NIFTY 50"]
    store = _recorded({("NIFTY 50", key): round((high if key == "high" else low) + gap, 2)})
    lines, sent = _confirm(store)
    fields = json.loads(store.files[confirm_path(DAY)])["fields"]
    assert fields["NIFTY 50"] == {"high": "confirmed", "low": "confirmed", "previous_close": "confirmed"}
    assert lines[0].startswith("close confirm 2026-10-21: NIFTY 50 confirmed, NIFTY BANK confirmed,") and sent == []


@pytest.mark.parametrize("key", ["high", "low"])
def test_a_high_or_low_0_02_off_is_recorded_and_alerted_once(key):
    high, low, _ = RANGES["NIFTY BANK"]
    store = _recorded({("NIFTY BANK", key): round((high if key == "high" else low) + 0.02, 2)})
    lines, sent = _confirm(store)
    assert f"NIFTY BANK confirmed ({key} differs by 0.02)" in lines[0] and len(sent) == 1
    assert _confirm(store, SECOND) == ([], [])  # never confirmed twice


def test_a_previous_close_that_differs_from_the_previous_session_s_official_close_is_recorded():
    store = _recorded({("NIFTY 50", "previous_close"): 22888.85})
    lines, sent = _confirm(store)
    assert "NIFTY 50 confirmed (previous_close differs by 0.10)" in lines[0] and len(sent) == 1


def test_india_vix_s_range_differences_are_recorded_never_alerted():
    store = _recorded({("INDIA VIX", "high"): 16.5})
    lines, sent = _confirm(store)
    assert "INDIA VIX differs by 0.02 (list value) (high differs by 0.33 (list value))" in lines[0] and sent == []


def test_with_the_previous_session_s_file_missing_the_day_waits_then_alerts_once():
    store, missing = _recorded(), Official({DAY: OFFICIAL}, previous=False)
    assert _confirm(store, NEXT, missing) == (
        ["close confirm 2026-10-21: the previous session's official index-close file not in Drive yet"],
        [],
    )
    lines, sent = _confirm(store, SECOND, missing)
    assert confirm_path(DAY) not in store.files and overdue_path(DAY) in store.files and len(sent) == 1
    assert _confirm(store, date(2026, 10, 26), missing) == ([], [])  # never again


def test_the_recheck_names_a_change_in_high():
    store = MemoryStore()
    reader(store, Answers(answer()), Clock(at(15, 40))).run()
    moved = _ranges("NIFTY 50", high=round(RANGES["NIFTY 50"][0] + 0.05, 2))
    lines = []
    reader(store, Answers(answer(ranges=moved)), Clock(at(16, 0)), lines=lines).run(RECHECK)
    recheck = json.loads(store.files[recheck_path(DAY)])
    assert recheck["fields_against_first"]["NIFTY 50"] == {"high": "differs by 0.05", "low": "same",
                                                           "previous_close": "same"}  # fmt: skip
    assert lines[0].startswith("close recheck 2026-10-21: NIFTY 50 same (high differs by 0.05), NIFTY BANK same,")


def test_an_older_record_without_the_fields_is_rechecked_and_confirmed_on_last_alone():
    """22 Oct's record shape (A4h before A4h-2): `last` and `open` only."""
    store = MemoryStore()
    old = {name: {"last": last, "open": opened, "official_close": True} for name, (last, opened) in LEVELS.items()}
    store.put(record_path(DAY), encode({"day": DAY.isoformat(), "indices": old}))
    store.put(f"closes/2026/10/{DAY}.first.raw.json", b"{}")
    lines = []
    reader(store, Answers(answer()), Clock(at(16, 0)), lines=lines).run(RECHECK)
    assert lines[0].startswith("close recheck 2026-10-21: NIFTY 50 same, NIFTY BANK same, INDIA VIX same, NSE stamp")
    lines, sent = _confirm(store, NEXT, Official({DAY: OFFICIAL}, previous=False))  # no previous file needed
    assert json.loads(store.files[confirm_path(DAY)])["fields"] == {name: {} for name in LEVELS} and sent == []
