"""Story F1t criteria 3c and 3d: the answer's labels, model rule and shape; no private account figure in any text,
with Indian and western digit grouping and rupee prefixes normalised (judge 301 addendum 1)."""

import pytest

from fno.ai_trading.answer import AnswerRefused, check_answer, complete_answer, labels_of
from fno.ai_trading.figures import figures, private_figures
from fno.constants import BOOK2_HYBRID

from .builders import COMMON_BODY, MODEL, draft, pointer, private_body, shape_check

PUBLIC = ("playbook",)


def private():
    return private_figures(private_body(), str(COMMON_BODY), PUBLIC)


def checked(tmp_path, **kwargs):
    labels = labels_of(pointer(tmp_path))
    return check_answer(complete_answer(draft(**kwargs), labels), labels, shape_check, private())


def test_a_good_answer_passes_with_its_model(tmp_path):
    result = checked(tmp_path)
    assert result.model_reported == MODEL and result.decision["action"] == "trade"


def test_the_labels_are_the_pointer_s_and_a_changed_label_is_refused(tmp_path):
    labels = labels_of(pointer(tmp_path))
    answer = complete_answer(draft(), labels) | {"private_pack_sha256": "0" * 64}
    with pytest.raises(AnswerRefused, match="private_pack_sha256 differ"):
        check_answer(answer, labels, shape_check, private())


@pytest.mark.parametrize("draft_value", [None, {}, {"decision": {}}, {"decision": {}, "model_reported": "m", "x": 1}])
def test_a_draft_of_the_wrong_shape_is_refused(tmp_path, draft_value):
    with pytest.raises(AnswerRefused, match="exactly the fields"):
        complete_answer(draft_value, labels_of(pointer(tmp_path)))


@pytest.mark.parametrize("model, ok", [(MODEL, True), ("claude-opus-5[1m]", True), ("unknown", True),
                                       ("", False), ("Opus 5.5", False), ("claude opus", False)])  # fmt: skip
def test_model_reported_is_a_model_id_or_unknown(tmp_path, model, ok):
    if ok:
        assert checked(tmp_path, model=model).model_reported == model
    else:
        with pytest.raises(AnswerRefused, match="exact model ID"):
            checked(tmp_path, model=model)


@pytest.mark.parametrize("reason, ok", [("r", True), ("x" * 600, True), ("x" * 601, False), ("", False),
                                        ("two\nlines", False)])  # fmt: skip
def test_the_reason_is_one_line_of_1_to_600_characters(tmp_path, reason, ok):
    if ok:
        checked(tmp_path, reason=reason)
    else:
        with pytest.raises(AnswerRefused, match="one line of 1 to 600"):
            checked(tmp_path, reason=reason)


def test_the_book_s_own_shape_check_runs(tmp_path):
    with pytest.raises(AnswerRefused, match="action is not allowed"):
        checked(tmp_path, action="double_the_size")


@pytest.mark.parametrize("text", ["fill was 1,23,456.75", "Rs 123456.75 paid", "₹1,23,456.75", "INR 123,456.75",
                                  "Rs.3,40,500 cash", "cash 340500", "cash 3,40,500.00"])  # fmt: skip
def test_a_private_figure_in_any_writing_is_refused_without_repeating_it(tmp_path, text):
    with pytest.raises(AnswerRefused, match="decision.reason quotes a private account figure") as refused:
        checked(tmp_path, reason=text)
    assert "456" not in str(refused.value) and "340" not in str(refused.value)


def test_a_private_figure_deep_inside_the_decision_is_found(tmp_path):
    with pytest.raises(AnswerRefused, match=r"decision.trades\[0\].reason quotes"):
        checked(tmp_path, trades=[{"opportunity_id": "o1", "reason": "my cash is 3,40,500"}])


def test_a_public_figure_and_short_numbers_are_accepted(tmp_path):
    checked(tmp_path, reason="strike 25150 again, 1 lot, 20 days, width 100 or 200 from the playbook")


@pytest.mark.parametrize("text, found", [
    ("1,25,000", {"125000"}), ("125,000", {"125000"}), ("Rs 1,25,000.50", {"125000.5"}), ("₹125000.50", {"125000.5"}),
    ("99", set()), ("100", {"100"}), ("0.5", {"0.5"}), ("007", set()), ("r10 abc123", set()), ("", set()),
])  # fmt: skip
def test_figures_are_normalised_and_counted_from_three_digits_or_a_decimal(text, found):
    assert figures(text) == found


def test_private_figures_leave_out_public_folders_and_the_common_pack():
    figures_ = private()
    assert "123456.75" in figures_ and "340500" in figures_
    assert "25150" not in figures_ and "200" not in figures_  # in the common pack; in the public playbook
    assert private_figures({"files": []}, "", PUBLIC) == set()


def test_labels_bind_the_cards_item_exactly(tmp_path):
    first, second = (
        labels_of(pointer(tmp_path)),
        labels_of(pointer(tmp_path, cards={"input_sha256": "", "role_set_version": "", "roles": []})),
    )
    assert first["cards_sha256"] != second["cards_sha256"] and first["book"] == BOOK2_HYBRID
