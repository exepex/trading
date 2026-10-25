"""REC1 criteria 1 and 2 (the closed sets and the reason order): the answers and codes are exactly the story's."""

from fno.recommend.constants import REASON_TEXT, EvidenceRung, NoTradeReason, PaperAnswer, RealMoneyAnswer


def test_real_money_has_exactly_two_answers_and_no_buy():
    assert [a.value for a in RealMoneyAnswer] == ["do_not_trade_real_money", "eligible_for_your_own_review"]
    assert not any("buy" in a.value for a in RealMoneyAnswer)


def test_paper_has_exactly_two_answers():
    assert [a.value for a in PaperAnswer] == ["paper_trade", "no_trade"]


def test_the_reasons_are_the_story_s_set_in_its_priority_order():
    assert [r.value for r in NoTradeReason] == [
        "data_check_failed", "step_problems", "no_established_version", "quote_gate_failed", "weather_red",
        "risk_cap", "brake", "no_candidate",
    ]  # fmt: skip


def test_every_reason_has_a_plain_text():
    assert set(REASON_TEXT) == set(NoTradeReason)
    assert all(text and text[0].islower() for text in REASON_TEXT.values())


def test_the_rungs_are_zero_to_three_and_only_three_is_established():
    assert [(r.name, int(r)) for r in EvidenceRung] == [
        ("UNPROVEN", 0), ("EXPLORATORY", 1), ("WATCHING", 2), ("ESTABLISHED", 3),
    ]  # fmt: skip
