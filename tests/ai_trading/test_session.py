"""Story F1t criteria 3, 3c, 3d and 4: the routine side checks the pointer and the committed common pack before any
input is shown, prints the model rule first, seals only a checked answer once, and reveals from the pointer's time.
It runs with the standard library only, and its working folder is git-ignored."""

import json
import subprocess
import sys

import pytest

from fno.ai.seal import Commitment, open_reveal
from fno.ai.sealed_publish import SealRefused
from fno.ai_trading.answer import MODEL_RULE, AnswerRefused
from fno.ai_trading.paths import WORK_FOLDER, commitment_path, common_pack_path, reveal_path
from fno.ai_trading.pointer import PointerRefused
from fno.ai_trading.session import StepRefused
from fno.config import ROOT
from tests.ai.fakes import Clock, git

from .builders import DAY, PROMPTS, at, draft, make_repo, pointer, registry
from .fakes import DecisionRoutine


@pytest.fixture
def repo(tmp_path):
    return make_repo(tmp_path)


def routine(repo, when=(15, 2)):
    return DecisionRoutine(repo, registry(repo), Clock(at(*when)))


def test_brief_prints_the_model_rule_first_then_the_prompt_and_the_input(repo):
    fake = routine(repo)
    fake.session().brief(pointer(repo).to_text())
    assert fake.printed[0] == MODEL_RULE and fake.printed[1].startswith("# book2_hybrid decision prompt")
    assert fake.printed[2].startswith("INPUT (seal by 15:10:00")
    shown = json.loads(fake.printed[3])
    assert sorted(shown) == ["analyst_cards", "common_pack", "private_pack"]
    assert shown["private_pack"]["book"] == "book2_hybrid"


def test_nothing_of_the_input_is_shown_when_a_check_fails(repo):
    fake = routine(repo)
    with pytest.raises(PointerRefused):
        fake.session().brief("{}")
    (repo / common_pack_path(DAY)).write_text("{}", encoding="utf-8")
    with pytest.raises(StepRefused, match="not the one fired"):
        fake.session().brief(pointer(repo).to_text())
    (repo / common_pack_path(DAY)).unlink()
    with pytest.raises(StepRefused, match="no committed common pack"):
        fake.session().brief(pointer(repo).to_text())
    assert fake.printed == []


def test_a_prompt_edited_after_registration_is_refused_before_any_input(repo):
    fake, text = routine(repo), pointer(repo).to_text()
    (repo / PROMPTS["book2_hybrid"]).write_text("changed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from version 1"):
        fake.session().brief(text)
    assert fake.printed == []


def test_seal_publishes_only_a_commitment_and_reveal_hashes_to_it(repo):
    fake = routine(repo)
    fake.run(pointer(repo).to_text(), draft(), at(15, 8))
    commitment = Commitment.from_text((repo / commitment_path(DAY, "book2_hybrid")).read_text())
    reveal = (repo / reveal_path(DAY, "book2_hybrid")).read_text()
    answer = open_reveal(reveal, commitment)
    assert answer["decision"]["action"] == "trade" and answer["book"] == "book2_hybrid"
    assert "trade" not in (repo / commitment_path(DAY, "book2_hybrid")).read_text()
    assert fake.clock.now == at(15, 10, 10)  # the reveal waited for the pointer's reveal time


def test_a_refused_answer_names_what_to_fix_and_publishes_nothing(repo):
    fake = routine(repo)
    with pytest.raises(AnswerRefused, match="private account figure"):
        fake.run(pointer(repo).to_text(), draft(reason="cash 3,40,500 left"), at(15, 8))
    assert not (repo / commitment_path(DAY, "book2_hybrid")).exists() and len(fake.transport.commits) == 0


def test_a_second_seal_is_refused_and_keeps_the_first_salt(repo):
    fake = routine(repo)
    fake.run(pointer(repo).to_text(), draft(), at(15, 8), reveal=False)
    sealed = (repo / WORK_FOLDER / "sealed.json").read_text()
    with pytest.raises(SealRefused, match="sealed once"):
        fake.session().seal(repo / WORK_FOLDER / "answer.json")
    assert (repo / WORK_FOLDER / "sealed.json").read_text() == sealed


def test_steps_out_of_order_are_refused(repo):
    with pytest.raises(StepRefused, match="run the steps in order"):
        routine(repo).session().reveal()


def test_the_working_folder_is_never_staged(repo):
    (repo / ".gitignore").write_text((ROOT / ".gitignore").read_text(encoding="utf-8"), encoding="utf-8")
    routine(repo).session().brief(pointer(repo).to_text())
    git(repo, "add", "-A")
    assert WORK_FOLDER not in git(repo, "status", "--porcelain")


def test_the_routine_side_imports_with_the_standard_library_only():
    code = "import sys; sys.path = [p for p in sys.path if 'packages' not in p]; import fno.ai_trading.__main__"
    done = subprocess.run([sys.executable, "-S", "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert done.returncode == 0, done.stderr


def test_the_decision_run_times_itself_with_f8c_s_mechanism_under_its_own_role(repo):
    from fno.ai.paths import timing_path
    from fno.ai.usage_record import book_and_role

    routine(repo).run(pointer(repo).to_text(), draft(), at(15, 8))
    timing = json.loads((repo / timing_path(DAY, "book2_hybrid", "decision")).read_text())
    assert timing["session_id"] == "session_test" and timing["started_at"] == at(15, 2).isoformat()
    assert not (repo / timing_path(DAY, "book2_hybrid")).exists()  # the forecast's own file is never touched
    assert book_and_role(timing_path(DAY, "book2_hybrid", "decision").split("/")[-1]) == (
        "book2_hybrid", "book2_hybrid trading decision")  # fmt: skip
    assert book_and_role(timing_path(DAY, "book3_ai").split("/")[-1]) == ("book3_ai", "")


def test_a_timing_that_cannot_be_published_never_costs_the_reveal(repo):
    fake = DecisionRoutine(repo, registry(repo), Clock(at(15, 2)), session_id="")
    fake.run(pointer(repo).to_text(), draft(), at(15, 8))
    assert (repo / reveal_path(DAY, "book2_hybrid")).is_file()
    assert any("timing NOT published" in line for line in fake.printed)


def test_a_timing_file_of_an_unknown_run_is_refused():
    from fno.ai.usage_record import book_and_role

    with pytest.raises(ValueError, match="not an AI book's run"):
        book_and_role("2026-10-19_book2_hybrid_lunch.timing.json")
