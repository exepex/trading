"""Judge 598 (story G7b completion, round 2) through `pack_wiring.build_pack_capture` with every outside source
replaced: SF1, a refit day stores both measures' ratios whatever the release (a `system_late` day and a day with no
release record too), the next day reads them and writes none, a non-refit day writes none; m1, a V5 outcome settled
in the run reaches V5's base rate the same run."""

import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta

import pytest

from fno.constants import V5_INSIDE_STRADDLE
from fno.forecast_v4.settlement import V5Outcome
from fno.forecast_v4_rules import pack_wiring
from fno.forecast_v4_rules.implied import IvPoint
from fno.forecast_v4_rules.intraday_series import RATIO_CLOSE_PROXY, RATIO_INTRADAY
from fno.forecast_v4_rules.option_history import OptionHistory
from fno.forecast_v4_rules.ratio_store import RATIOS_FOLDER
from fno.forecast_v4_rules.series import DayValue
from fno.v4_pack.release import NotReleased, ReleaseRecord
from tests.forecast_v4_rules.test_v4rules_pack_live import TERMS

START = date(2024, 1, 1)
SESSIONS = [START + timedelta(n) for n in range(1100) if (START + timedelta(n)).weekday() < 5]
REFIT = date(2026, 10, 1)  # Thursday: the first session of October
NEXT = date(2026, 10, 2)
V5_DAY = date(2026, 9, 24)
SEEN = datetime(2026, 9, 30, 13, 0, tzinfo=UTC)  # first seen before REFIT


class Drive:
    def __init__(self):
        self.files = {}

    def put(self, path, data):
        self.files[path] = data

    def ratios(self):
        return {p: json.loads(d) for p, d in self.files.items() if p.startswith(RATIOS_FOLDER)}


class Released:
    def __init__(self, label):
        self.label = label

    def release(self, day):
        if self.label is None:
            raise NotReleased(f"no release record for {day}")
        return ReleaseRecord(day, self.label, "", "", None)


class Resolver:
    def resolve(self, terms):
        return V5Outcome(terms.expiry, True, 26000.0, "x", "f" * 64, SEEN)


def capture(monkeypatch, day, label, drive=None):
    drive = drive or Drive()
    closes = [DayValue(d, 25000.0 + 50 * (i % 2)) for i, d in enumerate(SESSIONS) if d < day]
    eod = {d: IvPoint(0.15, False) for d in SESSIONS if d < day}
    v5_terms = {V5_DAY: replace(TERMS, day=V5_DAY)}
    monkeypatch.setattr(pack_wiring, "implied_history", lambda: (eod, closes, SESSIONS))
    monkeypatch.setattr(pack_wiring, "build_data_store", lambda writer, env: drive)
    monkeypatch.setattr(pack_wiring, "drive_get", drive.files.get)
    monkeypatch.setattr(pack_wiring, "intraday_rv", lambda: ({d: 2e-5 for d in SESSIONS if d < day}, set()))
    monkeypatch.setattr(pack_wiring, "option_history", lambda s: OptionHistory({}, v5_terms, {}, [], s))
    monkeypatch.setattr(pack_wiring, "v5_resolver", lambda env: Resolver())
    monkeypatch.setattr(pack_wiring, "build_session_calendar", lambda: None)
    monkeypatch.setattr(pack_wiring, "build_released_packs", lambda env: Released(label))
    return pack_wiring.build_pack_capture(day, env={}), drive


@pytest.mark.parametrize("label", ["system_late", None])
def test_a_refit_day_stores_both_measures_ratios_whatever_the_release(monkeypatch, label):
    built, drive = capture(monkeypatch, REFIT, label)
    stored = drive.ratios()
    assert {(r["measure"], r["question"]) for r in stored.values()} == {
        (m, q) for m in (RATIO_CLOSE_PROXY, RATIO_INTRADAY) for q in pack_wiring.QUESTIONS
    }
    assert all(r["refit_day"] == REFIT.isoformat() and r["ratio"] is not None for r in stored.values())
    assert sum(line.startswith("premium ratio") for line in built.settled) == 6
    assert (built.refused is None) is (label is not None)  # no release record: refused, the ratios stored anyway


def test_the_next_day_reads_the_stored_ratios_and_a_non_refit_day_writes_none(monkeypatch):
    _, drive = capture(monkeypatch, REFIT, "system_late")
    before = dict(drive.files)
    built, drive = capture(monkeypatch, NEXT, "system_late", drive)
    assert drive.ratios() == {p: json.loads(d) for p, d in before.items() if p.startswith(RATIOS_FOLDER)}
    assert not any(line.startswith("premium ratio") for line in built.settled)
    ratio = built.forecasts.implied[RATIO_CLOSE_PROXY][pack_wiring.QUESTIONS[1]].ratio
    assert (
        ratio.at(REFIT)
        == json.loads(before[f"{RATIOS_FOLDER}/{RATIO_CLOSE_PROXY}/{ratio.question}/2026-10.json"])["ratio"]
    )
    _, fresh = capture(monkeypatch, NEXT, "system_late")  # a missed refit day: the next day never computes it late
    assert fresh.ratios() == {}


def test_a_v5_outcome_settled_in_the_run_reaches_v5s_base_rate_the_same_run(monkeypatch):
    built, drive = capture(monkeypatch, NEXT, "system_late")
    assert any(line.startswith(f"V5 {V5_DAY}: outcome written") for line in built.settled)
    assert [(o.day, o.value) for o in built.forecasts.base_outcomes[V5_INSIDE_STRADDLE]] == [(V5_DAY, True)]
