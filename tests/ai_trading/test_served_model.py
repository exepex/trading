"""Story F1t criterion 3c (revision 2, judges 621 and 623): the model checked is the one that served the session
(`last_served_model`, copied from the session tool), with the configured model beside it; an instructions line alone
is not verified (the orchestrator's ruling). Every case but the first is no trade."""

import pytest

from fno.ai.outcome import MODEL_MISMATCH
from fno.ai_trading.answer import AnswerRefused, check_answer, complete_answer, labels_of
from fno.ai_trading.outcome import ACCEPTED, MODEL_UNVERIFIED

from .builders import MODEL, draft, pointer, shape_check
from .test_outcome import judged

OTHER = "claude-sonnet-5-5"


def test_the_session_tool_reporting_the_registered_model_served_and_configured_is_accepted(tmp_path):
    outcome = judged(tmp_path)
    assert (outcome.status, outcome.model_source, outcome.model_check) == (ACCEPTED, "session_tool", "match")


def test_a_fallback_model_that_served_while_the_registered_one_was_configured_is_a_mismatch(tmp_path):
    outcome = judged(tmp_path, model=OTHER, configured=MODEL)
    assert outcome.status == MODEL_MISMATCH and OTHER in outcome.reason and outcome.answer is None


def test_a_configured_model_other_than_the_registered_one_is_a_mismatch(tmp_path):
    assert judged(tmp_path, model=MODEL, configured=OTHER).status == MODEL_MISMATCH


@pytest.mark.parametrize(
    ("source", "model"), [("instructions", MODEL), ("none", "unknown"), ("session_tool", "unknown")]
)
def test_any_source_but_the_session_tool_or_an_unknown_model_is_unverified(tmp_path, source, model):
    outcome = judged(tmp_path, model=model, source=source)
    assert outcome.status == MODEL_UNVERIFIED and outcome.answer is None


def test_a_context_suffix_on_the_served_model_still_matches(tmp_path):
    assert judged(tmp_path, model=f"{MODEL}[1m]").status == ACCEPTED  # fno/ai's comparison, as for forecasts


@pytest.mark.parametrize(("fields", "named"), [
    ({"model_source": "memory"}, "model_source"),
    ({"model_reported": "Claude Opus"}, "model_reported"),
    ({"model_configured": ""}, "model_configured"),
    ({"model_source": "none", "model_reported": MODEL}, "model_source"),
])  # fmt: skip
def test_seal_refuses_model_fields_it_cannot_read(tmp_path, fields, named):
    labels = labels_of(pointer(tmp_path))
    answer = complete_answer(draft(), labels) | fields
    with pytest.raises(AnswerRefused, match=named):
        check_answer(answer, labels, shape_check, set())


def test_an_answer_without_its_model_fields_is_refused(tmp_path):
    with pytest.raises(AnswerRefused, match="exactly the fields"):
        complete_answer({"decision": {"action": "trade", "reason": "x"}, "model_reported": MODEL}, {})
