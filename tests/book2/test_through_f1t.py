"""Story F5 on F1t's port (criteria 13 and 15): a real Book 2 decision passes F1t's real promotion and run check (one
run inside Book 2's write paths, every record a valid D3 record with the packs, the model, the session, the judge's
verdict file, the decision version and each chosen trade's `strategy_status`). A day trading the registered research
candidate is labelled "strategy not yet passed"; a day trading only the paper version "strategy passed"; a blocked
judge's day holds no chosen trade, so F1t's block check passes it."""

import pytest

from fno.ai_trading.promote import Promoter
from fno.ai_trading.run_check import NOT_YET_PASSED, PASSED
from fno.ai_trading.versions import BOOK2_WRITE_PATHS
from fno.constants import BOOK2_HYBRID
from tests.book3.builders import commit, init_repo

from .decider_builders import P, R, accepted, decider, decision, repository, slot


def promote(tmp_path, slots, **changes):
    init_repo(tmp_path)
    repository(tmp_path)
    commit(tmp_path, "envelopes and D6")
    promoter = Promoter(tmp_path, {BOOK2_HYBRID: decider(tmp_path)})
    return promoter.promote(accepted(decision(slots), **changes), BOOK2_WRITE_PATHS)


@pytest.mark.parametrize("slots, label", [
    ([slot(P), slot(R)], NOT_YET_PASSED),
    ([slot(P), slot(R, "no_trade")], PASSED),
    ([slot(P, "no_trade"), slot(R, "no_trade")], ""),
])  # fmt: skip
def test_a_book2_day_is_promoted_by_f1t_with_its_strategy_label(tmp_path, slots, label):
    promotion = promote(tmp_path, slots)
    assert promotion.promoted, promotion.reason
    assert promotion.strategy_label == label


def test_a_judge_blocked_day_passes_f1t_s_block_check_with_no_chosen_trade(tmp_path):
    promotion = promote(tmp_path, [slot(P), slot(R)], judge_blocks=True)
    assert promotion.promoted and promotion.strategy_label == ""
