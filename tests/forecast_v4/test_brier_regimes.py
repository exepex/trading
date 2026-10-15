"""Story G6 revision 4 (judge 98 addendum 3): the Brier rules across 2019-26 and calm stretches, the 5-event gate, and
the corrected descriptive quantile."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from fno.forecast_v4.confirmatory import MIN_EVENT_DAYS, brier_judgeable

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import v4_brier_regimes as regimes  # noqa: E402
import v4_size_study as study  # noqa: E402

DATA = json.loads((ROOT / "research/forecasts/v4_brier_regimes.json").read_text(encoding="utf-8"))


def test_the_gate_is_five_two_percent_days():
    assert MIN_EVENT_DAYS == 5 and brier_judgeable(5) and not brier_judgeable(4)


def test_the_nulls_cover_every_exposed_session_with_a_valid_base_rate_and_the_calm_stretches_have_no_event():
    series = regimes.brier_series(1)
    assert series["day"][0] == "2019-01-15" and series["day"][-1] == "2026-10-14"
    for length, first in ((125, "2021-04-13"), (250, "2022-10-06")):
        start = regimes.calm_stretch(series["big"], length)
        assert series["day"][start] == first and series["big"][start : start + length].sum() == 0


def test_without_the_gate_the_brier_rules_fail_and_with_it_every_cell_holds():
    rows = DATA["rows"]
    assert len(rows) == 2 * 2 * len(regimes.EVENT_GATES)
    assert not any(regimes.within(r) for r in rows if r["gate"] == 0)
    assert all(regimes.within(r) for r in rows if r["gate"] >= MIN_EVENT_DAYS)


def test_calm_stretches_are_never_judgeable_under_the_gate():
    for r in DATA["rows"]:
        if r["gate"] >= MIN_EVENT_DAYS:
            assert all(v == 0.0 for k, v in r["judgeable"].items() if k.startswith("calm"))


def test_committed_markdown_matches_the_data():
    text = (ROOT / "research/forecasts/v4_brier_regimes.md").read_text(encoding="utf-8")
    assert text == regimes.markdown(DATA["rows"])


def test_descriptive_quantile_rejects_exactly_the_allowed_count():
    p = np.arange(1, 1001) / 1000.0  # 1,000 distinct p-values
    tau = study._quantile(p, 0.005)  # 5 may be rejected
    assert tau == 0.005 and int((p <= tau).sum()) == 5
    assert study._quantile(p, 0.0009) == 0.0
