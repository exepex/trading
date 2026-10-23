"""G13 criterion 4's committed fixture: the real 16 Oct 2026 NSE chain (committed CSV) through the committed code
reproduces the probe's numbers (story text; judge 304's recomputation). The fixture was written by `summary` below
from this code; rerun `python -m fno pricedist value --day 2026-10-16 --source nse --dry-run` to see the record."""

import json
from datetime import date
from pathlib import Path

import pytest

from fno.config import load_app_config
from fno.price_distribution.build import DayBuilder
from fno.price_distribution.sources import SnapshotChains
from fno.price_distribution.wiring import build_day_builder
from fno.storage.raw_store import LocalFolderStore

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = Path(__file__).parent / "fixtures" / "nse_20261016_expected.json"
DAY = date(2026, 10, 16)


def record() -> dict:
    chain = SnapshotChains(LocalFolderStore(ROOT / "research" / "data" / "quotes"), ("nse",)).chain("NIFTY", DAY)
    builder: DayBuilder = build_day_builder(load_app_config())
    return builder.build(chain, "backfill_3pm", None)


def summary(found: dict) -> dict:
    out = {}
    for e in found["valuation"]["expiries"]:
        d = e["distribution"]
        out[e["expiry"]] = {"forward": e["forward"], "strikes": len(d["cdf"]) + 1, "cdf_low": d["lower_tail"]["cdf"],
                            "cdf_high": d["upper_tail"]["cdf"], "raw_decreases": d["raw_decreases"],
                            "quantiles": d["quantiles"]}  # fmt: skip
    return out


def test_the_16_october_nse_chain_reproduces_the_committed_fixture():
    assert summary(record()) == json.loads(FIXTURE.read_text())


def test_the_fixture_holds_the_story_s_numbers():
    near, far = (json.loads(FIXTURE.read_text())[e] for e in ("2026-10-27", "2026-11-23"))
    assert near["forward"] == pytest.approx(23_122.0, abs=0.1) and near["strikes"] == 47
    assert (round(near["cdf_low"], 4), round(near["cdf_high"], 4), near["raw_decreases"]) == (0.0217, 0.9895, 3)
    levels = [near["quantiles"][k]["level"] for k in ("q05", "q50", "q95")]
    assert levels == pytest.approx([22_263, 23_147, 23_822], abs=1)
    logs = [round(near["quantiles"][k]["log_return"] * 100, 2) for k in ("q05", "q50", "q95")]
    assert logs == [-3.79, 0.11, 2.98]
    assert (round(far["cdf_low"], 4), round(far["cdf_high"], 4), far["raw_decreases"]) == (0.1034, 0.8742, 10)
    assert [far["quantiles"][k]["source"] for k in ("q05", "q10", "q25", "q75", "q90", "q95")] == [
        "tail", "tail", "body", "body", "tail", "tail"]  # fmt: skip


def test_the_value_command_prints_the_record_and_writes_nothing(capsys, tmp_path, monkeypatch):
    from argparse import Namespace

    from fno.price_distribution.cli import cmd_pricedist

    monkeypatch.setattr("fno.price_distribution.wiring.build_store", lambda *a: (_ for _ in ()).throw(AssertionError))
    args = Namespace(action="value", day=DAY, source="nse", underlying=None, start=None, end=None, dry_run=True)
    assert cmd_pricedist(args) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["day"] == "2026-10-16" and printed["source"] == "nse" and len(printed["forecasts"]) == 12
    assert cmd_pricedist(Namespace(**{**vars(args), "source": "drive"})) == 2
