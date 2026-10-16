"""The registered research questions (story R1c): append-only, one alpha each, never edited."""

import pytest

from fno.factory.questions import QuestionError
from fno.factory.wiring import build_questions

from .helpers import commit, init_repo


def test_a_question_is_added_once_and_read_back(tmp_path):
    init_repo(tmp_path)
    questions = build_questions(tmp_path)
    questions.add("premium-when-calm", "Selling protected premium when the forecast is well below implied", 0.05)
    assert questions.get("premium-when-calm").alpha == 0.05
    with pytest.raises(QuestionError, match="already registered"):
        questions.add("premium-when-calm", "again", 0.01)
    with pytest.raises(QuestionError, match="not in research/factory/questions.csv"):
        questions.get("other")


@pytest.mark.parametrize(("qid", "alpha", "message"), [("Bad Id", 0.05, "lower-case"), ("ok", 0.5, "between 0 and 0.5"),
                                                       ("ok", 0, "between 0 and 0.5")])  # fmt: skip
def test_a_bad_question_is_refused(tmp_path, qid, alpha, message):
    init_repo(tmp_path)
    with pytest.raises(QuestionError, match=message):
        build_questions(tmp_path).add(qid, "text", alpha)


def test_an_edited_question_is_refused(tmp_path):
    init_repo(tmp_path)
    questions = build_questions(tmp_path)
    questions.add("q1", "first", 0.05)
    commit(tmp_path, "question")
    questions.store.file.write_text(questions.store.file.read_text().replace("0.05", "0.1"))
    with pytest.raises(QuestionError, match="not append-only"):
        questions.get("q1")
