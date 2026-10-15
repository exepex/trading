"""Story G6 revision 5 (judge 98 addendum 4): Brier thresholds by event-count band, each held within tolerance on its
own conditioned nulls."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from fno.forecast_v4.confirmatory import EVENT_BANDS, event_band

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import v4_brier_bands as bands  # noqa: E402

DATA = json.loads((ROOT / "research/forecasts/v4_brier_bands.json").read_text(encoding="utf-8"))


def test_bands_cover_every_count_from_the_gate_without_overlap():
    assert event_band(4) is None
    assert [event_band(k) for k in (5, 7, 8, 12, 13, 60)] == [(5, 7), (5, 7), (8, 12), (8, 12), (13, None), (13, None)]
    assert tuple(bands.BANDS) == EVENT_BANDS


def test_in_band_and_the_conditional_threshold_use_only_the_band_series():
    events = np.array([4, 5, 7, 8, 13, 20])
    assert bands.in_band(events, (5, 7)).tolist() == [False, True, True, False, False, False]
    p = np.linspace(0.001, 1.0, 1000)
    tau = bands.band_threshold([(p, np.full(1000, 6)), (p, np.full(1000, 30))], (5, 7), 0.05)
    assert tau == float(np.sort(p)[bands.claims.conservative_rank(0.05, 1000)])


def test_every_band_holds_claims_and_futility_at_both_sizes_and_looks():
    rows = DATA["rows"]
    assert DATA["series"] == 200_000 and len(rows) == 2 * 2 * len(EVENT_BANDS)
    assert all(bands.within(r) for r in rows)


def test_committed_markdown_matches_the_data():
    assert (ROOT / "research/forecasts/v4_brier_bands.md").read_text(encoding="utf-8") == bands.markdown(DATA["rows"])
