"""Story B3 criteria 1, 2, 4 and 5 on a synthetic decisive period of 60 opportunities: the runner checks the guard
before reading data, two runs give byte-identical results files, a policy that never trades scores 0 and fails
criterion 1, and each criterion shows its value, threshold and pass, the policy passing only if all pass."""

import json
from datetime import date

import pytest
from policy_fixtures import F1, F2, F3, cycle, result

from fno.constants import PERIOD_CHALLENGE, CycleStatus
from fno.research_data.panel_reader import NiftyPanel
from fno.research_engine.experiment_1 import EXPERIMENT_1
from fno.research_engine.features import Feature, ResearchData
from fno.research_engine.ledger import NotRegistered
from fno.research_engine.opportunities import checked_status
from fno.research_engine.results_file import results_json, results_markdown
from fno.research_engine.runner import ExperimentRunner
from fno.research_engine.trial_guard import TrialGuard

CYCLES = [cycle(i) for i in range(60)]  # decision days from 1 Jan 2019, every 30 days: all inside 2019-2023
NETS = {"SC": 1000.0, "SF": -500.0, "BF": -300.0}


class PassGuard(TrialGuard):
    def __init__(self):
        self.calls = []

    def check(self, trial_ids, protocol_path, decisive):
        self.calls.append((tuple(trial_ids), protocol_path, decisive))


class RefuseGuard(TrialGuard):
    def check(self, trial_ids, protocol_path, decisive):
        raise NotRegistered("trial 99 is not registered: it is not in research/ledger.csv")


class Fixed(Feature):
    """F1 positive on two of three cycles, F2 never known, F3 false."""

    def __init__(self, name):
        self.name = name

    def value(self, data, decision_day, context):
        index = next(i for i, c in enumerate(CYCLES) if c.decision_day == decision_day)
        return {F1: 1.0 if index % 3 else -1.0, F2: None, F3: False}[self.name]


class Code:
    def __init__(self, code):
        self.code = code


class Simulator:
    def simulate(self, c, structure):
        losing = c == CYCLES[5] and structure.code == "SC"
        return result(c, structure.code, -2000.0 if losing else NETS[structure.code])


def runner(guard=None, load=None):
    return ExperimentRunner(
        guard=guard or PassGuard(),
        load_data=load or (lambda period: ResearchData(NiftyPanel((), {}, {}), ())),
        build_cycles=lambda panel: CYCLES,
        features=[Fixed(F1), Fixed(F2), Fixed(F3)],
        structures=[Code("SF"), Code("SC"), Code("BF")],
        build_simulator=lambda panel: Simulator(),
        ledger_count=lambda name: {"registered_rows": 10, "hypotheses": 8},
        inputs=lambda: {"panel_manifest": "test"},
    )


@pytest.fixture(scope="module")
def document():
    return runner().run(EXPERIMENT_1, PERIOD_CHALLENGE)


def test_the_guard_runs_before_any_data_is_read():
    def load(period):
        raise AssertionError("data read before the guard")

    with pytest.raises(NotRegistered, match="not registered"):
        runner(RefuseGuard(), load).run(EXPERIMENT_1, PERIOD_CHALLENGE)
    guard = PassGuard()
    runner(guard).run(EXPERIMENT_1, "discovery")
    assert guard.calls == [(EXPERIMENT_1.trial_ids, EXPERIMENT_1.protocol_path, False)]


def test_two_runs_give_byte_identical_results_files(document):
    again = runner().run(EXPERIMENT_1, PERIOD_CHALLENGE)
    assert results_json(again) == results_json(document)
    assert results_markdown(json.loads(results_json(again))) == results_markdown(json.loads(results_json(document)))


def test_a_policy_that_never_trades_scores_zero_and_fails_criterion_1(document):
    p7 = document["policies"]["P7"]  # F2 is never known: no trade on all 60
    assert p7["summary"]["total_net"] == 0.0 and p7["summary"]["status_counts"] == {"no_trade": 60}
    first = p7["verdict"]["criteria"][0]
    assert (first["name"], first["value"], first["threshold"], first["passed"]) == ("1_total_net", 0.0, 0.0, False)
    assert p7["verdict"]["verdict"] == "fail"


def test_every_criterion_shows_value_threshold_and_pass_and_all_must_pass(document):
    p1, p4 = document["policies"]["P1"]["verdict"], document["policies"]["P4"]["verdict"]
    assert all(set(c) == {"name", "value", "rule", "threshold", "passed"} for c in p1["criteria"])
    assert [c["name"] for c in p1["criteria"]] == ["1_total_net", "2_bootstrap_lower_bound", "7_max_modelled_loss"]
    assert p1["verdict"] == "pass" and document["policies"]["P1"]["summary"]["total_net"] == 59 * 1000.0 - 2000.0
    by_name = {c["name"]: c for c in p4["criteria"]}
    assert by_name["4_above_P1"]["passed"] is False and by_name["4_above_P1"]["threshold"] == 57_000.0
    assert by_name["1_total_net"]["passed"] and p4["verdict"] == "fail"  # one failed criterion fails the policy
    assert document["overall"] == {"status": "complete", "passing_policies": ["P1"]}


def test_branch_tests_use_the_protocols_opportunities(document):
    p5 = {c["name"]: c for c in document["policies"]["P5"]["verdict"]["criteria"]}
    p6 = {c["name"]: c for c in document["policies"]["P6"]["verdict"]["criteria"]}
    assert p5["5_bf_branch"]["value"] == 20 * -300.0  # P5 chose BF on the 20 cycles with F1 <= 0
    assert p6["6_event_filter"]["value"] == 0.0  # F3 never true: the filter removed nothing, so not below zero
    assert p6["6_event_filter"]["passed"] is False


def test_an_unknown_status_is_an_error_not_a_zero():
    with pytest.raises(ValueError, match="unknown cycle status"):
        checked_status("stale")
    assert checked_status(CycleStatus.BAD_PRICES) == "bad_prices"


def test_criterion_7_breach_voids_the_run():
    class BigLoss(Simulator):
        def simulate(self, c, structure):
            r = super().simulate(c, structure)
            return result(c, structure.code, r.net, max_loss=10_000.01) if c == CYCLES[0] else r

    run = runner()
    run.build_simulator = lambda panel: BigLoss()
    document = run.run(EXPERIMENT_1, PERIOD_CHALLENGE)
    assert document["overall"] == {"status": "void", "passing_policies": []}


def test_discovery_has_no_pass_fail(document):
    discovery = runner().run(EXPERIMENT_1, "discovery")
    assert "overall" not in discovery and all("verdict" not in p for p in discovery["policies"].values())
    assert discovery["period"] == {"name": "discovery", "start": "2024-01-01", "end": "2026-10-09"}
    assert discovery["opportunities"] == []  # the synthetic cycles are all in 2019-2023
    assert date.fromisoformat(document["opportunities"][-1]["cycle"]["decision_day"]) <= date(2023, 12, 31)
