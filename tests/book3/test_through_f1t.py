"""Story F6 on F1t's port: a real Book 3 decision passes F1t's real promotion and run check (one run, its write
paths, every record a valid D3 record with the packs, the model, the session, the judge's verdict file, the decision
version under `served.ai_decision_version` and each chosen trade's `strategy_status`). Every Book 3 trade is labelled
"strategy not yet passed": every Book 3 spec is `research` (D5), which is correct and honest (orchestrator, 25 Oct)."""

from fno.ai_trading.promote import Promoter
from fno.ai_trading.run_check import NOT_YET_PASSED
from fno.ai_trading.versions import BOOK3_WRITE_PATHS
from fno.constants import BOOK3_AI
from tests.book3.engine_builders import OPPORTUNITY, accepted, decider, decision, repository, spec


def test_a_book3_trade_is_promoted_by_f1t_and_labelled_strategy_not_yet_passed(tmp_path):
    repository(tmp_path, [spec()])
    promotion = Promoter(tmp_path, {BOOK3_AI: decider(tmp_path)}).promote(
        accepted(tmp_path, decision(trades=[OPPORTUNITY])), BOOK3_WRITE_PATHS
    )
    assert promotion.promoted, promotion.reason
    assert promotion.strategy_label == NOT_YET_PASSED


def test_a_book3_no_trade_day_is_promoted_with_no_label(tmp_path):
    repository(tmp_path, [spec()])
    promotion = Promoter(tmp_path, {BOOK3_AI: decider(tmp_path)}).promote(accepted(tmp_path, decision()),
                                                                          BOOK3_WRITE_PATHS)  # fmt: skip
    assert promotion.promoted and promotion.strategy_label == ""
