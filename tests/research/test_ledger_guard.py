"""Ledger guard (story B4): a trial runs only if registered in a committed ledger with a frozen, unchanged protocol."""

import subprocess
from datetime import date
from pathlib import Path

import pytest

from fno.research_engine.ledger import COLUMNS, LEDGER_FILE, Ledger, NotRegistered, read_ledger

REPO_LEDGER = Path(__file__).resolve().parents[2] / LEDGER_FILE
PROTOCOL = "research/exp/PROTOCOL.md"


def git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.invalid")
    git(tmp_path, "config", "user.name", "test")
    (tmp_path / "research/exp").mkdir(parents=True)
    (tmp_path / PROTOCOL).write_text("rules v1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-qm", "protocol")
    return tmp_path


def commit(root, message):
    git(root, "add", ".")
    git(root, "commit", "-qm", message)
    return git(root, "rev-parse", "HEAD")


def freeze(root, ledger, trial_id, protocol_commit):
    rows = ledger.rows()
    for row in rows:
        if row["trial_id"] == trial_id:
            row["protocol_commit"] = protocol_commit
    from fno.research_engine.ledger import write_ledger

    ledger.file.write_text(write_ledger(rows))
    return commit(root, "freeze")


def test_an_unregistered_or_uncommitted_trial_is_refused(repo):
    ledger = Ledger(repo)
    with pytest.raises(NotRegistered, match="not in"):
        ledger.require_registered("P1")
    ledger.register("P1", "exp", "policy one", "prospective", True, PROTOCOL, date(2026, 10, 12))
    with pytest.raises(NotRegistered, match="committed"):
        ledger.require_registered("P1")  # only in the working tree


def test_a_registered_trial_needs_a_frozen_unchanged_protocol(repo):
    ledger = Ledger(repo)
    ledger.register("P1", "exp", "policy one", "prospective", True, PROTOCOL, date(2026, 10, 12))
    protocol_commit = commit(repo, "register P1")
    with pytest.raises(NotRegistered, match="no frozen protocol"):
        ledger.require_registered("P1")
    freeze(repo, ledger, "P1", protocol_commit)
    assert ledger.require_registered("P1")["trial_id"] == "P1"
    (repo / PROTOCOL).write_text("rules v2: changed after the freeze\n")
    with pytest.raises(NotRegistered, match="changed after it was frozen"):
        ledger.require_registered("P1")  # uncommitted change
    commit(repo, "change rules")
    with pytest.raises(NotRegistered, match="changed after it was frozen"):
        ledger.require_registered("P1")  # committed change


def test_a_protocol_commit_outside_history_is_refused(repo):
    ledger = Ledger(repo)
    ledger.register("P1", "exp", "policy one", "prospective", True, PROTOCOL, date(2026, 10, 12))
    commit(repo, "register")
    freeze(repo, ledger, "P1", "0" * 40)
    with pytest.raises(NotRegistered, match="not in history"):
        ledger.require_registered("P1")


def test_the_first_run_is_recorded_once(repo):
    ledger = Ledger(repo)
    ledger.register("P1", "exp", "policy one", "prospective", True, PROTOCOL, date(2026, 10, 12))
    ledger.mark_run("P1", date(2026, 11, 1))
    first = next(r for r in ledger.rows() if r["trial_id"] == "P1")
    ledger.mark_run("P1", date(2026, 12, 1))
    again = next(r for r in ledger.rows() if r["trial_id"] == "P1")
    assert first["first_run_on"] == again["first_run_on"] == "2026-11-01" and again["run_commit"]


def test_duplicates_and_bad_rows_are_refused(repo):
    ledger = Ledger(repo)
    ledger.register("P1", "exp", "policy one", "prospective", True, PROTOCOL)
    with pytest.raises(ValueError):
        ledger.register("P1", "exp", "again", "prospective", True, PROTOCOL)
    with pytest.raises(ValueError):
        ledger.register("P2", "exp", "bad kind", "guess", True, PROTOCOL)


def test_the_repository_ledger_counts_experiment_1_and_keeps_history_retrospective():
    rows = read_ledger(REPO_LEDGER.read_text())
    assert [r["trial_id"] for r in rows] == [str(i) for i in range(1, 100)] and tuple(rows[0]) == COLUMNS
    assert all(r["kind"] == "retrospective" for r in rows[:21])
    r2 = rows[52]  # R2 feasibility, registered after its protocol commit (story R2)
    assert (r2["kind"], r2["protocol_commit"]) == ("prospective", "93a19c318003994c6cedd070d038ee89d45dd74e")
    ft1 = rows[53]  # FT1 fill timing, registered after its protocol commit (story E8a)
    assert (ft1["kind"], ft1["hypothesis"], ft1["protocol_commit"]) == (
        "prospective",
        "no",
        "47d15989a4045a1804b235fcb5fad13ec7e2a7ea",
    )
    b0 = rows[54]  # B0, a measurement shadow (story R3): committed with its idea card, no hypothesis, never promoted
    assert (b0["kind"], b0["hypothesis"], b0["protocol_path"]) == ("prospective", "no", "research/ideas/B0.md")
    assert b0["description"].startswith("B0 measurement: never promoted")
    ledger = Ledger(REPO_LEDGER.parents[1])
    assert ledger.count("experiment-1") == {
        "registered_rows": 10,
        "hypotheses": 8,
    }  # P1-P8; controls are not hypotheses
    assert ledger.count("forecasts-v1") == {"registered_rows": 5, "hypotheses": 0}  # G1: diagnostics, not hypotheses
    assert ledger.count("forecasts-v2") == {"registered_rows": 5, "hypotheses": 0}  # G1 v2: live 15:00 inputs
    assert rows[41]["kind"] == "retrospective"  # desk meeting 2's put-spread model: a look at seen data (judge 93)
    assert ledger.count("weekly-weather-2026-10-14") == {"registered_rows": 10, "hypotheses": 10}  # W1-W5, filters
    gr1 = rows[55:70]  # GR1 sharper ranges (judge 428.2): C1-C11 hypotheses, FII/DII not tested, N0-A/B/C measurements
    assert ledger.count("gr1-sharper-ranges-2026-10-21") == {"registered_rows": 15, "hypotheses": 11}
    # EDGE1 (story EDGE1, protocol section 13): 24 tradeable variants, then the 4 naked measurements
    assert ledger.count("edge1-rule-based-option-trades-2026-10-22") == {"registered_rows": 28, "hypotheses": 24}
    assert [r["hypothesis"] for r in rows[70:98]] == ["yes"] * 24 + ["no"] * 4
    assert {(r["kind"], r["protocol_path"]) for r in gr1} == {("prospective", "research/gr1/PROTOCOL.md")}
    assert len({r["protocol_commit"] for r in gr1}) == 1 and "NOT TESTED" in rows[66]["description"]


def test_an_uncommitted_edit_to_a_registered_row_is_refused(repo):
    ledger = Ledger(repo)
    ledger.register("P1", "exp", "policy one", "prospective", True, PROTOCOL, date(2026, 10, 12))
    protocol_commit = commit(repo, "register")
    freeze(repo, ledger, "P1", protocol_commit)
    assert ledger.require_registered("P1")
    text = ledger.file.read_text().replace("policy one,prospective,yes", "policy one,prospective,no")
    ledger.file.write_text(text)  # e.g. quietly dropping it from the hypothesis family
    with pytest.raises(NotRegistered, match="uncommitted"):
        ledger.require_registered("P1")
    git(repo, "add", LEDGER_FILE)  # staged but not committed is still refused
    with pytest.raises(NotRegistered, match="uncommitted"):
        ledger.require_registered("P1")


def test_a_registration_only_on_another_branch_is_refused(repo):
    ledger = Ledger(repo)
    git(repo, "checkout", "-qb", "side")
    ledger.register("P9", "exp", "side idea", "prospective", True, PROTOCOL, date(2026, 10, 12))
    commit(repo, "register on a side branch")
    git(repo, "checkout", "-q", "-")
    assert not any(r["trial_id"] == "P9" for r in ledger.rows())
    with pytest.raises(NotRegistered, match="not in"):
        ledger.require_registered("P9")  # the run's own history has no registration
    git(repo, "checkout", "side", "--", LEDGER_FILE)  # row brought over without being committed here
    with pytest.raises(NotRegistered, match="uncommitted"):
        ledger.require_registered("P9")
