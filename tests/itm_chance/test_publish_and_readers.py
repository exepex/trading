"""Criterion 5 (write-once, nothing written without a new settled expiry) and the reader ports FL1 and the dashboard
use (section 3)."""

import json
from datetime import date

import pytest

from fno.itm_chance.constants import MEASURE
from fno.itm_chance.folders import CALIBRATION
from fno.itm_chance.publish import ALREADY, NONE_SETTLED, encode, publish
from fno.itm_chance.reader import ItmCalibration, ItmChances
from fno.price_distribution.folders import BACKFILL, LIVE

from .builders import expiry, record

METHOD = "m" * 64
DAY, EXPIRY = date(2026, 10, 1), date(2026, 10, 27)


class FakeStore:
    def __init__(self):
        self.files = {}

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        self.files[path] = data


def report(last="2026-09-29", as_of="2026-10-22") -> dict:
    return {"underlying": "NIFTY", "last_settled_expiry": last, "as_of": as_of, "measure": MEASURE, "notes": [],
            "settled_expiries": [last] if last else [], "left_out": [], "slices": {"all": {"expiries": 1}}}  # fmt: skip


def test_a_report_is_written_once_under_its_last_expiry_and_content(tmp_path):
    store = FakeStore()
    line = publish(report(), tmp_path, store)
    ((path, data),) = store.files.items()
    assert path.startswith(f"{CALIBRATION}/nifty_2026-09-29_") and data == encode(report()) and path in line


def test_nothing_is_written_without_a_settled_expiry_or_when_drive_has_one_for_it(tmp_path):
    store = FakeStore()
    assert publish(report(last=None), tmp_path, store) == NONE_SETTLED.format(underlying="NIFTY")
    (tmp_path / CALIBRATION).mkdir(parents=True)
    (tmp_path / CALIBRATION / "nifty_2026-09-29_abc.json").write_text("{}")
    assert publish(report(as_of="2026-10-23"), tmp_path, store) == ALREADY.format(underlying="NIFTY",
                                                                                   expiry="2026-09-29")  # fmt: skip
    assert store.files == {}


def write_records(root, records, folder=LIVE, name="nifty_2026-10-01.json"):
    target = root / folder / "2026" / "10"
    target.mkdir(parents=True, exist_ok=True)
    (target / name).write_text(json.dumps(records))


def test_itm_chances_reads_the_current_method_only_and_each_source_apart(tmp_path):
    write_records(tmp_path, record(DAY, [expiry(EXPIRY, 26)], label="live", method=METHOD))
    old_day = date(2026, 10, 2)
    write_records(tmp_path, record(old_day, [expiry(EXPIRY, 25)], label="live", method="o" * 64), name="old.json")
    chances = ItmChances(tmp_path, METHOD)
    found = chances.for_day("NIFTY", DAY)
    assert len(found) == 4 and {c.source for c in found} == {"3pm"} and {c.measure for c in found} == {MEASURE}
    assert chances.for_contract("NIFTY", DAY, EXPIRY, 23000.0, "CE").itm_chance == pytest.approx(0.45)
    assert chances.for_contract("NIFTY", DAY, EXPIRY, 99.0, "CE") is None and chances.for_day("NIFTY", old_day) == []


def test_for_contract_prefers_the_3pm_chain_unless_a_source_is_asked(tmp_path):
    write_records(tmp_path, record(DAY, [expiry(EXPIRY, 26)], label="live", method=METHOD))
    eod = {"schema": "g13_backfill_v1", "records": [record(DAY, [expiry(EXPIRY, 26)], method=METHOD)]}
    write_records(tmp_path, eod, folder=BACKFILL, name="eod.json")
    chances = ItmChances(tmp_path, METHOD)
    assert chances.for_contract("NIFTY", DAY, EXPIRY, 23000.0, "PE").source == "3pm"
    assert chances.for_contract("NIFTY", DAY, EXPIRY, 23000.0, "PE", source="backfill_eod").source == "backfill_eod"


def test_latest_calibration_is_the_latest_settled_expiry(tmp_path):
    folder = tmp_path / CALIBRATION
    folder.mkdir(parents=True)
    runs = (("2026-08-25", "2026-10-09"), ("2026-09-29", "2026-10-01"), ("2026-09-29", "2026-10-05"))
    for last, as_of in runs:  # an older expiry's report rerun later never wins
        (folder / f"nifty_{last}_{as_of}.json").write_text(json.dumps(report(last, as_of)))
    latest = ItmCalibration(tmp_path).latest("NIFTY")
    assert (latest.last_settled_expiry, latest.as_of, latest.measure) == ("2026-09-29", "2026-10-05", MEASURE)
    assert ItmCalibration(tmp_path).latest("BANKNIFTY") is None
