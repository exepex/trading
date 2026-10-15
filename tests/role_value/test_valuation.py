"""Story F9a criteria 8-9: both actions valued by S3's standard unit; a no-trade either way is 0 and a change; an open
action makes the pair wait; a record on another pack is not scored."""

from datetime import date

from fno.constants import Decision
from fno.role_value import valuation
from fno.role_value.valuation import NOT_SCORED, SCORED, WAITING, value_pair
from fno.scoreboard import matched, matched_actions, standard_unit
from tests.role_value.unit_fixture import DAY, EXIT, NET, QUOTES, common, setup, unit
from tests.scoreboard.matched_builders import record

SKIP = {"outcome": Decision.NO_TRADE, "reason": "no trade today", "legs": ()}


def test_the_valuation_is_s3_s_own_code_not_a_copy():
    assert valuation.StandardUnit is standard_unit.StandardUnit
    assert valuation.unit_legs is matched.unit_legs and valuation.action_of is matched_actions.action_of


def test_a_trade_against_a_shadow_no_trade_is_a_change_worth_the_trade_s_net(tmp_path):
    pack = setup(tmp_path)
    pair = value_pair([record("o1", pack=pack)], [record("o1", pack=pack, **SKIP)], common(tmp_path), DAY,
                      unit(tmp_path), EXIT)  # fmt: skip
    assert (pair.status, pair.difference, pair.changed) == (SCORED, NET, True)
    assert pair.max_loss_difference == 7615.0  # S3's one-lot maximum loss of the long call (HeldMaxLoss)


def test_the_reverse_counts_with_its_sign(tmp_path):
    pack = setup(tmp_path)
    pair = value_pair([record("o1", pack=pack, **SKIP)], [record("o1", pack=pack)], common(tmp_path), DAY,
                      unit(tmp_path), EXIT)  # fmt: skip
    assert (pair.difference, pair.changed) == (-NET, True)


def test_two_equal_decisions_are_unchanged_and_differ_by_zero(tmp_path):
    pack = setup(tmp_path)
    same = [record("o1", pack=pack)]
    pair = value_pair(same, same, common(tmp_path), DAY, unit(tmp_path), EXIT)
    assert (pair.status, pair.difference, pair.changed) == (SCORED, 0.0, False)


def test_an_action_not_yet_exited_waits(tmp_path):
    pack = setup(tmp_path)
    pair = value_pair([record("o1", pack=pack)], [record("o1", pack=pack, **SKIP)], common(tmp_path), DAY,
                      unit(tmp_path, {DAY: QUOTES[DAY]}), EXIT)  # fmt: skip
    assert pair.status == WAITING


def test_a_record_on_another_pack_or_a_missing_decision_is_not_scored(tmp_path):
    pack = setup(tmp_path)
    other = value_pair([record("o1", pack="other")], [record("o1", pack=pack)], common(tmp_path), DAY,
                       unit(tmp_path), EXIT)  # fmt: skip
    missing = value_pair([record("o1", pack=pack)], None, common(tmp_path), DAY, unit(tmp_path), EXIT)
    assert other.status == missing.status == NOT_SCORED
    assert "shadow decision not found" in missing.note


def test_the_unit_is_called_for_each_take(tmp_path):
    pack = setup(tmp_path)
    calls = []
    real_unit = unit(tmp_path)

    class Spy:
        def value(self, *args):
            calls.append(args)
            return real_unit.value(*args)

    value_pair([record("o1", pack=pack)], [record("o1", pack=pack, **SKIP)], common(tmp_path), DAY, Spy(), EXIT)
    assert len(calls) == 1 and calls[0][1:] == (DAY, date(2026, 11, 3), EXIT)
