"""GR1 protocol section 12 (a) end to end: run 1 (`study.run_select`) on synthetic inputs, with and without a planted
2025 record whose outcome is extreme. Run 1 never looks that outcome up and its output is identical either way
(only the input hash differs). Run 2 can then read it."""

from datetime import date, timedelta

import pytest
import study

from tests.research_gr1.gr1_fakes import Z, context, weekdays

PLANTED = date(2025, 6, 2)


def records(with_planted: bool) -> list[dict]:
    found = []
    for i, day in enumerate(weekdays(date(2023, 1, 2), date(2024, 12, 31))):
        for horizon, steps in (("N1", 1), ("N3", 3)):
            for underlying in ("NIFTY", "BANKNIFTY"):
                row = {"forecaster": "implied", "horizon": horizon, "status": "ok", "s_ref": 100.0 + i % 7,
                       "target_day": (day + timedelta(days=steps)).isoformat()}  # fmt: skip
                row.update({f"lq{n:02d}": z * 0.01 * steps**0.5 for n, z in zip((5, 25, 50, 75, 95), Z, strict=True)})
                found.append({"underlying": underlying, "day": day.isoformat(), "rows": [row]})
    if with_planted:
        row = {"forecaster": "implied", "horizon": "N1", "status": "ok", "s_ref": 100.0,
               "target_day": (PLANTED + timedelta(days=1)).isoformat()}  # fmt: skip
        row.update({f"lq{n:02d}": z * 0.01 for n, z in zip((5, 25, 50, 75, 95), Z, strict=True)})
        found.append({"underlying": "NIFTY", "day": PLANTED.isoformat(), "rows": [row]})
    return found


@pytest.fixture
def fake_inputs(monkeypatch):
    asked = []

    def close(underlying, day):
        asked.append(day)
        return 1000.0 if day == PLANTED + timedelta(days=1) else 100.5 + (day.toordinal() % 5) / 10

    monkeypatch.setattr(study.inputs, "closes", lambda: close)
    monkeypatch.setattr(study.inputs, "context", lambda rows, calendar, stats=None: context())
    monkeypatch.setattr(study.inputs, "opens", lambda first, last: {})
    monkeypatch.setattr("fno.storage.wiring.build_session_calendar", lambda: None)
    return asked


def run(monkeypatch, with_planted):
    monkeypatch.setattr(study.inputs, "back_fill_records", lambda: records(with_planted))
    out = study.run_select()
    return {k: v for k, v in out.items() if k != "records_sha256"}


def test_a_planted_2025_record_never_reaches_run_1(monkeypatch, fake_inputs):
    clean = run(monkeypatch, False)
    planted = run(monkeypatch, True)
    assert planted == clean and PLANTED + timedelta(days=1) not in fake_inputs
    assert set(clean["cells"]) == {"NIFTY/N1", "NIFTY/N3", "BANKNIFTY/N1", "BANKNIFTY/N3"}
