"""Protocol v3 (ChatGPT review 30 item 5, response 69): a live day is replayed from the inputs at the parent of the
commit that added its records, never from today's grown panel."""

from __future__ import annotations

import json
import shutil
import subprocess
from datetime import date, datetime

import pytest

from fno.config import ROOT
from fno.forecast.record_files import records_csv_v2
from fno.forecast.schema import ForecastRecord
from fno.forecast.schema_v2 import ForecastRecordV2
from fno.forecast_scoring.replay import LiveReplay
from fno.forecast_scoring.wiring import recompute_live_day
from fno.models import IST

DAY = date(2026, 10, 14)
GENERATED = datetime(2026, 10, 14, 15, 5, tzinfo=IST)
MANIFEST = "research/data/nifty-panel/manifest.json"
RECORDS = "research/forecasts/live_v2/2026/2026-10-14_forecasts.csv"
PACK = RECORDS.replace("forecasts.csv", "pack.json")


def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


def _commit(root, message):
    _git(root, "add", "-A")
    _git(root, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", message)
    return _git(root, "rev-parse", "HEAD")


def _fake_recompute(seen):
    """Outputs that depend on the panel manifest it is given (and the generation time it is told)."""

    def recompute(inputs, day, generated_at):
        manifest = (inputs / MANIFEST).read_bytes()
        seen.append(manifest)
        cutoff = datetime(2026, 10, 14, 15, 0, tzinfo=IST)
        base = ForecastRecord("book1_rules", day, cutoff, "q1_nifty_up_20d", 0.5, "book1/v1", "a" * 64)
        text = records_csv_v2([ForecastRecordV2(base, "live_1500_proxy", "interpolated", generated_at)])
        return {"pack.json": manifest, "forecasts.csv": text.encode()}

    return recompute


def _write(root, path, data: bytes):
    (root / path).parent.mkdir(parents=True, exist_ok=True)
    (root / path).write_bytes(data)


def test_a_live_day_replays_from_the_checkout_its_pack_was_computed_from(tmp_path):
    """The capture's real commit order (forecast-capture.yml, judge 64): the pack is committed alone on the checkout it
    was computed from; `git pull` then merges another job's commit (the panel grew); the records come last."""
    _git(tmp_path, "init", "-q", "-b", "main")
    _write(tmp_path, MANIFEST, b'{"end": "2026-10-13"}')
    checkout = _commit(tmp_path, "panel through 13 Oct")
    outputs = _fake_recompute([])(tmp_path, DAY, GENERATED)
    _write(tmp_path, PACK, outputs["pack.json"])
    pack = _commit(tmp_path, "capture: the pack")
    _git(tmp_path, "checkout", "-q", "-b", "other-job", checkout)
    _write(tmp_path, MANIFEST, b'{"end": "2026-10-14"}')  # another job's push in the meantime
    _commit(tmp_path, "panel grows")
    _git(tmp_path, "checkout", "-q", "main")
    _git(tmp_path, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "merge", "-q", "--no-edit", "other-job")
    _write(tmp_path, RECORDS, outputs["forecasts.csv"])
    records = _commit(tmp_path, "capture: the records, after the pull")
    assert _git(tmp_path, "rev-parse", f"{records}^1") != checkout  # the records' parent already holds the grown panel
    seen = []
    result = LiveReplay(tmp_path, _fake_recompute(seen)).replay(DAY)
    assert result.matches and (result.pack_commit, result.inputs_commit) == (pack, checkout)
    assert seen == [b'{"end": "2026-10-13"}']  # never the panel pulled in later


def test_a_replay_that_differs_says_which_output(tmp_path):
    _git(tmp_path, "init", "-q")
    _write(tmp_path, MANIFEST, b"{}")
    _commit(tmp_path, "panel")
    _write(tmp_path, PACK, b"tampered")
    _commit(tmp_path, "capture: the pack")
    _write(tmp_path, RECORDS, _fake_recompute([])(tmp_path, DAY, GENERATED)["forecasts.csv"])
    _commit(tmp_path, "capture: the records")
    result = LiveReplay(tmp_path, _fake_recompute([])).replay(DAY)
    assert not result.matches and result.same == {"pack.json": False, "forecasts.csv": True}


def test_the_real_recompute_is_the_v2_capture(tmp_path):
    """Golden case A's inputs through the replay's recompute give golden case A's pack (only the calendar label of the
    golden differs: the replay hashes the real calendar file)."""
    golden = ROOT / "research" / "forecasts" / "v2" / "golden" / "case_a"
    inputs = tmp_path / "inputs"
    shutil.copytree(golden / "quotes", inputs / "research" / "data" / "quotes")
    (inputs / "research" / "data" / "nifty-panel").symlink_to(ROOT / "research" / "data" / "nifty-panel")
    (inputs / "research" / "data" / "calendar").symlink_to(ROOT / "research" / "data" / "calendar")
    shutil.copy(ROOT / "config.yaml", inputs / "config.yaml")
    out = recompute_live_day(inputs, date(2026, 10, 13), datetime(2026, 10, 13, 15, 5, tzinfo=IST))
    replayed, expected = json.loads(out["pack.json"]), json.loads((golden / "pack.json").read_bytes())
    assert replayed.pop("calendar_sha256") != expected.pop("calendar_sha256") == "golden-fixture"
    assert replayed == expected
    assert replayed["iv30"]["points"] == pytest.approx(14.8151, abs=1e-4)
