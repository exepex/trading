"""REC1b's line (judge 641 m2): it names itself, an eligible version "for your own review, never a buy", a rung-3
trade by its version, and keeps the counts honest; it reads only the record and its receipt."""

from fno.recommend.constants import NoTradeReason, RealMoneyAnswer
from fno.recommend.post import recommendation_line
from fno.recommend.store import Saved
from tests.recommend.builders import established_day, no_trade, paper_trade

SAVED = Saved("recommend/2026/11/2026-11-02.json", "ab" * 32, "e" * 40)


def test_no_established_version():
    line = recommendation_line(no_trade(), SAVED)
    assert "Real money: DO NOT TRADE (no version has passed)." in line
    assert "Paper: NO TRADE (no_established_version: " in line
    assert line.endswith("Record recommend/2026/11/2026-11-02.json, SHA-256 abababababab.")


def test_an_established_version_not_eligible_under_rm1():
    line = recommendation_line(established_day(), SAVED)
    assert "Real money: DO NOT TRADE (no established version is eligible under the real-money gate, RM1)." in line
    assert "Paper: NO TRADE (no_candidate: " in line


def test_an_eligible_version_is_named_never_as_a_buy():
    record = established_day(real_money=RealMoneyAnswer.ELIGIBLE_FOR_YOUR_OWN_REVIEW, eligible_version="school:CS1@1")
    assert "Real money: school:CS1@1 is eligible for your own review, never a buy (RM1)." in recommendation_line(
        record, SAVED
    )


def test_a_rung_3_trade_is_named_and_not_counted_as_unrecommended():
    line = recommendation_line(paper_trade(), SAVED)
    assert "Paper: TRADE of school:CS1@1 (established, rung 3)." in line
    assert "Paper, not a recommendation: 0 trade(s)" in line


def test_a_failed_check_says_so():
    line = recommendation_line(no_trade(reason=NoTradeReason.DATA_CHECK_FAILED), SAVED)
    assert "Paper: NO TRADE (data_check_failed: " in line
