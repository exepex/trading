"""Stories G2 and G3: the committed history back-fill equals a fresh recomputation, every record follows the frozen
schema and names its method, version, the close proxy and the day's IV30 state, and Book 1 is the mean of its
baselines on every day."""

import gzip
from collections import defaultdict

import pytest

from fno.config import ROOT, load_app_config
from fno.forecast.backfill import BACKFILL_FILE, backfill_records
from fno.forecast.baseline_wiring import build_baselines, build_forecast_history, panel_pack_sha256
from fno.forecast.book1_method import method_label
from fno.forecast.comparisons import baselines_for
from fno.forecast.golden import GOLDEN_FILE, read_golden
from fno.forecast.record_files import read_records, records_gzip


@pytest.fixture(scope="module")
def committed():
    return read_records(gzip.decompress((ROOT / BACKFILL_FILE).read_bytes()).decode("utf-8"))


def test_the_committed_backfill_equals_a_fresh_recomputation():
    history = build_forecast_history(load_app_config())
    fresh = records_gzip(backfill_records(history, build_baselines(history), panel_pack_sha256()))
    assert fresh == (ROOT / BACKFILL_FILE).read_bytes()


def test_every_record_names_its_method_version_proxy_and_iv30_state(committed):
    golden = {r["date"]: r["iv30_flagged"] for r in read_golden((ROOT / GOLDEN_FILE).read_text(encoding="utf-8"))}
    state = {"true": "iv30:flagged", "false": "iv30:interpolated", "": "iv30:none"}
    for r in committed:
        assert "/close-proxy/" in r.method_or_version and r.pack_sha256 == panel_pack_sha256()
        assert r.method_or_version.endswith(state[golden[r.date.isoformat()]])
        if r.book == "book1_rules":
            assert r.method_or_version.startswith(method_label())
        else:
            assert r.method_or_version.startswith(f"{r.book}/v1/")
    assert len(committed) == 5 * 4 * len(golden)


def test_book1_is_the_mean_of_its_baselines_on_every_record(committed):
    by = defaultdict(dict)
    for r in committed:
        by[(r.date, r.question)][r.book] = r.probability
    for (_, question), values in by.items():
        available = [values[b] for b in baselines_for(question) if values[b] is not None]
        expected = sum(available) / len(available) if available else None
        assert (
            values["book1_rules"] == pytest.approx(expected) if expected is not None else values["book1_rules"] is None
        )
