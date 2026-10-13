"""Experiment 1's policies and opposite controls (story B3) equal the protocol's formulas (section 6) on every
combination of feature values, including None (a condition with a None input is not met)."""

import itertools

import pytest
from policy_fixtures import F1, F2, F3

from fno.research_engine.experiment_1 import EXPERIMENT_1


def protocol(code, f1, f2, f3):
    """Protocol section 6, transcribed by hand (independent of experiment_1.py)."""
    known, pos = f1 is not None, f1 is not None and f1 > 0
    return {
        "P1": "SC", "P2": "SF", "P3": "BF",
        "P4": "SC" if pos else None,
        "P5": ("SC" if pos else "BF") if known else None,
        "P6": "SC" if pos and f3 is False else None,
        "P7": "SC" if f2 is True else None,
        "P8": "SF" if pos else None,
        "P4 opposite": "SC" if known and f1 <= 0 else None,
        "P5 opposite": ("BF" if f1 > 0 else "SC") if known else None,
        "P6 opposite": "SC" if known and (f1 <= 0 or f3 is True) else None,
        "P7 opposite": "SC" if f2 is False else None,
        "P8 opposite": "SF" if known and f1 <= 0 else None,
    }[code]  # fmt: skip


CASES = list(itertools.product([None, -1.5, 0.0, 2.0], [None, True, False], [True, False]))


@pytest.mark.parametrize("f1, f2, f3", CASES)
def test_every_policy_and_opposite_follows_the_protocol(f1, f2, f3):
    values = {F1: f1, F2: f2, F3: f3}
    for spec in EXPERIMENT_1.policies:
        for policy in filter(None, (spec.policy, spec.opposite)):
            assert policy.decide(values) == protocol(policy.code, f1, f2, f3), policy.code


def test_the_registry_matches_the_protocol_table_and_the_ledger():
    specs = {s.code: s for s in EXPERIMENT_1.policies}
    assert list(specs) == [f"P{i}" for i in range(1, 9)]
    assert {c: s.compared_with for c, s in specs.items() if s.compared_with} == {
        "P4": ("P1",), "P5": ("P1", "P4"), "P6": ("P1", "P4"), "P7": ("P1",), "P8": ("P2",),
    }  # fmt: skip
    assert [s.trial_id for s in specs.values()] + list(EXPERIMENT_1.control_trials) == [str(i) for i in range(22, 32)]
    assert [c for c, s in specs.items() if s.conditional] == ["P4", "P5", "P6", "P7", "P8"]
    assert EXPERIMENT_1.hypotheses == 8
