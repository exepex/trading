"""The practice fleet (MS-SIM-d2): a second instance of the pilot's own SchoolFleet over fixture history."""

import gzip
import json
from datetime import timedelta
from pathlib import Path

import pytest

from fno.config import ROOT, load_config
from fno.school.constants import SCHOOL_OFF_LINE, RoadCode
from fno.school.contracts.fleet import RunMode
from fno.school.execution import practice_wiring
from fno.school.execution.practice_wiring import PRACTICE
from fno.school.fakes import FakeSettlementSource
from fno.school.fleet.runner import SchoolFleet
from fno.school.simulator.constants import PRACTICE_LABEL
from fno.school.simulator.practice.dashcam import labels
from fno.school.simulator.practice.fleet import PracticeParts, build_practice_fleet
from fno.school.simulator.spreads.model import Scenario, SpreadModel
from fno.school.simulator.windows import PracticeWindows
from tests.school.safety.law_builders import FixedMargin
from tests.school.simulator.source import builders as sb

CFG = load_config(ROOT / "config.yaml")
FACTOR_FILE = ROOT / "research" / "data" / "margins" / "stress_factor.csv"


def history_days(count: int = 30):
    first = sb.SESSION - timedelta(days=count)
    return [d for d in (first + timedelta(days=i) for i in range(count + 1)) if d.weekday() < 5 and d != sb.HOLIDAY]


def parts(tmp_path: Path | None = None, spreads: SpreadModel | None = None) -> PracticeParts:
    days = history_days()
    chain = sb.DictChain(*[sb.chain(u, d) for u in ("NIFTY", "BANKNIFTY") for d in days])
    merged: dict = {}
    for code in (RoadCode.NIFTY_MONTHLY, RoadCode.NIFTY_WEEKLY, RoadCode.BANKNIFTY_MONTHLY):
        merged.update(sb.full_model(code).by_session)
    return PracticeParts(CFG, ROOT, FACTOR_FILE, sb.CALENDAR, chain, sb.TERMS, PracticeWindows(),
                         spreads if spreads is not None else SpreadModel(merged))  # fmt: skip


@pytest.fixture(autouse=True)
def archive_stubbed(monkeypatch):
    """Settlement reads the Drive archive in the real wiring; a fixture day has none, so the source is a fake."""
    monkeypatch.setattr(practice_wiring, "build_settlement_source", lambda: FakeSettlementSource({}))


def fleet(tmp_path, **kw):
    return build_practice_fleet(
        parts(**kw), sb.SESSION, Scenario.MEDIAN, tmp_path, margin_for=lambda cfg: FixedMargin()
    )


def test_it_is_the_pilots_own_fleet_class_with_the_practice_rules(tmp_path):
    built = fleet(tmp_path)
    assert type(built) is SchoolFleet and built.rules is PRACTICE
    assert built.clock.now().hour == 15 and built.clock.now().minute == 30


def test_it_runs_even_though_the_pilots_switch_is_off(tmp_path):
    assert CFG["school"]["enabled"] is False  # the pilot's switch stays off in the file
    run = fleet(tmp_path).run(sb.SESSION, RunMode.REPLAY)
    assert run.status != SCHOOL_OFF_LINE and run.decisions


def test_a_session_gives_one_sealed_decision_per_scheduled_road_and_driver(tmp_path):
    run = fleet(tmp_path).run(sb.SESSION, RunMode.REPLAY)
    roads = {r.road for r in run.decisions}
    assert roads == {RoadCode.NIFTY_MONTHLY, RoadCode.NIFTY_WEEKLY, RoadCode.BANKNIFTY_MONTHLY,
                     RoadCode.FINNIFTY_MONTHLY, RoadCode.MIDCPNIFTY_MONTHLY}  # fmt: skip
    closed = {r.road for r in run.decisions if r.road_closed_by is not None}
    assert closed == {RoadCode.FINNIFTY_MONTHLY, RoadCode.MIDCPNIFTY_MONTHLY}  # not in DATA_SPEND: closed, in the count
    assert run.decisions_seal is not None


def test_every_stored_record_line_of_the_run_carries_the_practice_label(tmp_path):
    run = fleet(tmp_path).run(sb.SESSION, RunMode.REPLAY)
    data = (tmp_path / "dashcam" / run.decisions_seal.path).read_bytes()
    found = labels(data)
    assert found and set(found) == {PRACTICE_LABEL}
    assert PRACTICE_LABEL in json.dumps(json.loads(gzip.decompress(data).splitlines()[0]))


def test_nothing_is_written_outside_the_practice_folder(tmp_path):
    before = {p for p in ROOT.glob("journal/school/**/*")}
    fleet(tmp_path).run(sb.SESSION, RunMode.REPLAY)
    assert {p for p in ROOT.glob("journal/school/**/*")} == before
    assert any(tmp_path.rglob("*.jsonl.gz"))


def test_the_trades_really_fill_none_is_refused_by_a_stale_seal(tmp_path):
    """The clock sits at the close: a later one made every fill a `stale_seal` (law 6) and the run still looked fine."""
    run = fleet(tmp_path).run(sb.SESSION, RunMode.REPLAY)
    filled = [f for f in run.fills if f.legs]
    assert filled and len(filled) == len(run.fills)
    assert all(f.filled_at == fleet(tmp_path).clock.now() for f in filled)


def test_a_rerun_of_the_same_session_seals_nothing_new(tmp_path):
    first = fleet(tmp_path).run(sb.SESSION, RunMode.REPLAY)
    again = fleet(tmp_path).run(sb.SESSION, RunMode.REPLAY)
    assert again.decisions_seal.sha256 == first.decisions_seal.sha256
