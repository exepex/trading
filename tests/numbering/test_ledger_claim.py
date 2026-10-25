"""Story O12e, criteria 3 and 5: a block of trial ids is claimed on `main` like any number (git decides the race),
and the evaluation freeze and the factory take their trial from their experiment's block, never "highest plus one".
"""

from datetime import UTC, datetime

import pytest

from fno.evaluation.freeze import FreezeRefused, ProtocolFreezer, freeze_path
from fno.factory.registration import RegistrationError
from fno.numbering.blocks import LEDGER, LEDGER_TRIAL
from fno.numbering.categories import CLAUDE_RESPONSE
from fno.numbering.claim import Claim, ClaimRefused, ClaimRequest, NumberClaimer
from fno.numbering.git_main import GitMain
from fno.playbook.history import PlaybookGit
from fno.research_engine.ledger import COLUMNS
from tests.numbering.helpers import HEADER, origin_and_clones, origin_file
from tests.numbering.test_claim import RivalFirst
from tools import claim_number

NOW = datetime(2026, 10, 25, 1, 0, 0, tzinfo=UTC)
MAIN = {
    LEDGER_TRIAL.registry: HEADER + "1-2,old,existing,\n115-120,edge2-f6,session_o,2026-10-25T00:00:00Z\n",
    LEDGER: ",".join(COLUMNS) + "\n" + "".join(f"{n},old,t,prospective,no,2026-10-25,,,,\n" for n in (1, 2, 108)),
}


def claimer(clone, git_main=None):
    return NumberClaimer(git_main or GitMain(clone), clock=lambda: NOW, pause=lambda _: None)


def block(slug="edge2-f7", session="session_a", **extra):
    return ClaimRequest(LEDGER_TRIAL, slug, session, **extra)


def test_a_block_starts_after_every_block_and_ledger_id_on_main(tmp_path):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    assert claimer(clone).claim(block(count=6)) == Claim("ledger-trial", "121-126", "edge2-f7")
    assert origin_file(tmp_path, LEDGER_TRIAL.registry).endswith("121-126,edge2-f7,session_a,2026-10-25T01:00:00Z")


def test_a_block_starts_after_a_ledger_id_typed_past_every_block(tmp_path):
    """An id written into the ledger by hand, outside any block, is never handed out again."""
    typed = {**MAIN, LEDGER: MAIN[LEDGER] + "130,hand,t,prospective,no,2026-10-25,,,,\n"}
    clone, _ = origin_and_clones(tmp_path, typed)
    assert claimer(clone).claim(block(count=2)).number == "131-132"


def test_one_id_without_a_count(tmp_path):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    assert claimer(clone).claim(block()).number == "121"


def test_two_racing_block_claims_get_blocks_that_do_not_overlap(tmp_path):
    clone_a, clone_b = origin_and_clones(tmp_path, MAIN)
    rival = RivalFirst(GitMain(clone_a), lambda: claimer(clone_b).claim(block("edge2-f8", "session_b", count=3)))
    assert claimer(clone_a, rival).claim(block(count=6)).number == "124-129"
    rows = origin_file(tmp_path, LEDGER_TRIAL.registry).splitlines()[3:]
    assert [row.split(",")[:3] for row in rows] == [["121-123", "edge2-f8", "session_b"],
                                                    ["124-129", "edge2-f7", "session_a"]]  # fmt: skip


@pytest.mark.parametrize("exact", ["118-122", "2", "100-108"])
def test_an_exact_block_overlapping_a_block_or_a_ledger_id_is_refused(tmp_path, exact):
    clone, _ = origin_and_clones(tmp_path, MAIN)
    with pytest.raises(ClaimRefused, match=rf"ledger-trial {exact} overlaps .* on main"):
        claimer(clone).claim(block(exact=exact))
    assert claimer(clone).claim(block(exact="130-131")).number == "130-131"


@pytest.mark.parametrize(
    ("extra", "reason"),
    [
        ({"count": 0}, "--count 0: at least 1"),
        ({"exact": "9-3"}, "a block <a>-<b> with a <= b"),
        ({"exact": "121-122", "count": 2}, "without --count"),
    ],
)
def test_a_bad_block_request_is_refused_before_any_git(extra, reason):
    with pytest.raises(ClaimRefused, match=reason):
        NumberClaimer(git=None).claim(block(**extra))


def test_count_is_for_blocks_only():
    with pytest.raises(ClaimRefused, match="--count is for ledger-trial blocks only"):
        NumberClaimer(git=None).claim(ClaimRequest(CLAUDE_RESPONSE, "x", "session_a", count=2))


def test_the_tool_claims_a_block_and_says_to_merge_main_then_register(capsys):
    class Fixed:
        def claim(self, request):
            assert (request.category, request.count) == (LEDGER_TRIAL, 6)
            return Claim("ledger-trial", "121-126", request.slug)

    argv = ["ledger-trial", "edge2-f7", "--session", "session_a", "--count", "6"]
    assert claim_number.main(argv, claimer=Fixed()) == 0
    assert capsys.readouterr().out.splitlines() == [
        "claimed: ledger-trial 121-126 -> edge2-f7",
        "next: merge main into your branch (git pull --no-rebase origin main), then register trials 121-126 with an "
        "experiment that starts with 'edge2-f7'",
    ]


@pytest.fixture
def evaluation_repo(tmp_path):
    from tests.evaluation.builders import protocol_repo

    protocol_repo(tmp_path)
    return tmp_path


def freeze_with_claims(root, claims: str):
    from tests.playbook.builders import commit_all

    (root / LEDGER_TRIAL.registry).write_text(HEADER + claims, encoding="utf-8")
    commit_all(root, "claims")
    return ProtocolFreezer(root, PlaybookGit(root)).freeze(NOW.date())


@pytest.mark.parametrize(
    "claims",
    [
        "1,old,existing,\n10-19,breadth-protocol,session_t,2026-10-25T00:00:00Z\n",  # none for its experiment
        "1-2,old,existing,\n3-9,breadth-protocol,session_t,2026-10-25T00:00:00Z\n",  # 2 is another experiment's
    ],
)
def test_the_evaluation_freeze_without_a_free_id_in_its_block_is_refused_before_writing(evaluation_repo, claims):
    with pytest.raises(FreezeRefused, match=r"no free id in a block claimed for experiment 'evaluation-protocol-v1'"):
        freeze_with_claims(evaluation_repo, claims)
    assert not (evaluation_repo / freeze_path(1)).exists()


def test_the_evaluation_freeze_takes_the_lowest_free_id_of_its_block(evaluation_repo):
    from fno.research_engine.ledger import read_ledger

    freeze_with_claims(evaluation_repo, "1,old,existing,\n5-9,evaluation-protocol,session_t,2026-10-25T00:00:00Z\n")
    assert read_ledger((evaluation_repo / LEDGER).read_text())[-1]["trial_id"] == "5"


def test_a_factory_card_in_no_claimed_block_is_refused(tmp_path):
    from fno.factory.wiring import build_registration, read_idea
    from tests.factory.helpers import BLOCK, init_repo, write_card

    root = init_repo(tmp_path)
    write_card(root, BLOCK.replace("x1-test", "y9-test"))
    with pytest.raises(RegistrationError, match=r"no free id in a block claimed for experiment 'y9-test'"):
        build_registration(root).register(read_idea("X1", root), NOW.date())
