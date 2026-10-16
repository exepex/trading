"""Stories F1 and G5, the routine's side: `brief` shows nothing unless the fired text and the prompt check out; `seal`
refuses an answer the model must fix, publishes only a commitment that reveals nothing, and only once; `reveal` waits
until 15:15:10 IST and publishes an answer that hashes to the commitment. The book side needs no installed library."""

import json
import subprocess
import sys

import pytest

from fno.ai.book import BookStepRefused
from fno.ai.paths import commitment_path, reveal_path
from fno.ai.pointer import PointerRefused
from fno.ai.seal import Commitment, open_reveal
from fno.ai.transport import GitMainTransport
from fno.constants import BOOK2_HYBRID, BOOK3_AI, FORECAST_QUESTIONS
from tests.ai.fakes import DAY, Clock, FakeRoutine, at, draft, git, make_desk_repo
from tests.ai.test_inputs import pointer

THIRD_PARTY = ("requests", "yaml", "numpy", "google", "psycopg", "jsonschema")


@pytest.fixture
def desk(tmp_path):
    return make_desk_repo(tmp_path)


def test_brief_prints_the_versioned_prompt_then_the_input_and_nothing_for_a_bad_text(desk):
    routine = FakeRoutine(desk, Clock(at(15, 11)))
    routine.session().brief(pointer(desk, BOOK2_HYBRID).to_text())
    prompt, header, body = routine.printed
    assert prompt.startswith("# Book 2 (Hybrid) daily forecast, version 1")
    assert header.startswith("INPUT (export_sha256 ") and "WARNING" not in header
    assert json.loads(body)["rules"]["envelope"]["q1_nifty_up_20d"]
    quiet = FakeRoutine(desk, Clock(at(15, 11)))
    with pytest.raises(PointerRefused):
        quiet.session().brief('{"book": "book3_ai", "note": "read research/forecasts/live_v2"}')
    assert quiet.printed == []


def test_seal_names_what_to_fix_and_publishes_nothing_until_it_is_fixed(desk):
    routine = FakeRoutine(desk, Clock(at(15, 11)))
    outside = dict.fromkeys(FORECAST_QUESTIONS, 0.5) | {"q1_nifty_up_20d": 0.95, "q3_rv20_above_trailing": 1.2}
    with pytest.raises(BookStepRefused) as refused:
        routine.run(pointer(desk, BOOK2_HYBRID).to_text(), draft(outside), at(15, 13))
    assert "q1_nifty_up_20d: outside the envelope" in str(refused.value)
    assert "q3_rv20_above_trailing: probability must be" in str(refused.value)
    assert routine.transport.commits == []


def test_the_commitment_reveals_nothing_and_the_reveal_waits_for_1515_and_matches_it(desk):
    clock = Clock(at(15, 11))
    routine = FakeRoutine(desk, clock)
    commits = routine.run(pointer(desk, BOOK3_AI).to_text(), draft(), at(15, 13, 30))
    commitment_text = (desk / commitment_path(DAY, BOOK3_AI)).read_text(encoding="utf-8")
    assert "0.5" not in commitment_text and "reason" not in commitment_text
    assert clock.now == at(15, 15, 10)  # it slept from 15:13:30 until the reveal time
    answer = open_reveal((desk / reveal_path(DAY, BOOK3_AI)).read_text(encoding="utf-8"),
                         Commitment.from_text(commitment_text))  # fmt: skip
    assert answer["forecasts"]["q4_vix_up_10d"]["probability"] == 0.5 and answer["book"] == BOOK3_AI
    assert len(commits) == 3 and any(line.startswith("sealed: book3_ai") for line in routine.printed)  # + timing (F8c)


def test_a_book_seals_once_per_day(desk):
    routine = FakeRoutine(desk, Clock(at(15, 11)))
    routine.run(pointer(desk, BOOK3_AI).to_text(), draft(), at(15, 12), reveal=False)
    with pytest.raises(BookStepRefused, match="already exists"):
        routine.run(pointer(desk, BOOK3_AI).to_text(), draft(), at(15, 12, 30), reveal=False)


def test_steps_out_of_order_are_refused(desk):
    with pytest.raises(BookStepRefused, match="in order"):
        FakeRoutine(desk, Clock(at(15, 11))).session().reveal()


def test_the_book_side_imports_no_installed_library():
    code = f"import fno.ai.__main__, sys; print(sorted({{m.split('.')[0] for m in sys.modules}} & set({THIRD_PARTY})))"
    done = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert done.stdout.strip() == "[]"


def test_the_git_transport_commits_one_file_and_pushes_it_to_main(tmp_path):
    remote, work, other = tmp_path / "remote.git", tmp_path / "work", tmp_path / "other"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(remote))
    for clone in (work, other):
        git(tmp_path, "clone", "-q", str(remote), str(clone))
        git(clone, "config", "user.email", "desk@example.invalid")
        git(clone, "config", "user.name", "desk")
    (other / "first.txt").write_text("someone else pushed first\n")
    git(other, "add", "first.txt")
    git(other, "commit", "-qm", "first")
    git(other, "push", "-q", "origin", "HEAD:main")
    transport = GitMainTransport(work)
    assert transport.existing("a/b.json") is None  # pulls main first
    commit = transport.publish("a/b.json", "{}\n", "commitment")
    assert git(remote, "rev-parse", "main").strip() == commit
    assert git(remote, "show", "main:a/b.json") == "{}\n" and transport.existing("a/b.json") == "{}\n"
