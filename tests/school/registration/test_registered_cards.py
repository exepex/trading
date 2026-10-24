"""The frozen driver cards and what registers them (story MS-P1h): every card carries the band the comparison card
freezes, and every card file's SHA-256 is the one its D6 row and the comparison card name."""

import csv
import hashlib
import json
import re
from pathlib import Path

import pytest
import yaml

from fno.research_engine.ledger import Git
from fno.school.registration.counting import CARD_PATH
from fno.school.registration.wiring import CARD_COMPONENT, COMPARISON_COMPONENT

ROOT = Path(__file__).resolve().parents[3]
CARDS = sorted((ROOT / "research/school/cards").glob("*.yaml"))
CARD = (ROOT / CARD_PATH).read_text()
BAND = int(re.search(r"(\d+) strike steps", CARD).group(1))


def driver_id(card: Path) -> str:
    document = yaml.safe_load(card.read_text())
    return f"{document['code']}@{document['version']}"


def test_every_driver_card_carries_the_band_the_comparison_card_freezes():
    assert len(CARDS) == 12
    for card in CARDS:
        assert yaml.safe_load(card.read_text())["band_steps"] == BAND, card.name


def test_no_driver_card_is_still_marked_draft():
    assert not [c.name for c in CARDS if "DRAFT" in c.read_text()]


def d6_rows() -> dict[str, dict]:
    with (ROOT / "journal/versions.csv").open() as handle:
        return {row["book"]: row for row in csv.DictReader(handle) if row["book"].startswith("school:")}


def test_every_driver_card_file_is_registered_in_d6_with_its_own_sha256():
    rows = d6_rows()
    assert sorted(rows) == sorted(f"school:{driver_id(card)}" for card in CARDS)
    for card in CARDS:
        row = rows[f"school:{driver_id(card)}"]
        assert json.loads(row["components"])[CARD_COMPONENT] == hashlib.sha256(card.read_bytes()).hexdigest(), card.name
        assert "trial 99" in row["reason"] and "CARD_P1 v2" in row["reason"]


def test_the_comparison_card_names_every_card_file_and_its_sha256():
    for card in CARDS:
        line = next(raw for raw in CARD.splitlines() if f"`{card.relative_to(ROOT)}`" in raw)
        assert line.startswith(f"| {driver_id(card)} |") and hashlib.sha256(card.read_bytes()).hexdigest() in line


def test_every_row_was_registered_in_a_commit_that_holds_its_card_file_as_it_is():
    git = Git(ROOT)
    if git.is_shallow():
        pytest.skip("a shallow clone cannot show the registration commit")
    for card in CARDS:
        commit = d6_rows()[f"school:{driver_id(card)}"]["registered_in_commit"]
        assert git.committed_text(str(card.relative_to(ROOT)), commit) == card.read_text(), card.name


def test_the_measurement_trial_is_in_the_ledger_and_the_gate_log_and_the_card_names_it():
    ledger = {row["trial_id"]: row for row in csv.DictReader((ROOT / "research/ledger.csv").open())}
    row = ledger["99"]
    assert (row["hypothesis"], row["kind"], row["protocol_path"]) == ("no", "prospective", CARD_PATH)
    gates = [r for r in csv.DictReader((ROOT / "research/factory/gates.csv").open()) if r["trial_id"] == "99"]
    assert [(g["gate"], g["outcome"]) for g in gates] == [("G0", "idea")]
    assert "trial: 99" in CARD and "99:" in CARD
    assert "99 (market school pilot P1" in (ROOT / "research/DATA_SPEND.md").read_text()


def test_every_row_names_the_comparison_card_as_it_was_when_the_row_was_registered():
    git = Git(ROOT)
    if git.is_shallow():
        pytest.skip("a shallow clone cannot show the registration commit")
    for card in CARDS:
        row = d6_rows()[f"school:{driver_id(card)}"]
        committed = git.committed_text(CARD_PATH, row["registered_in_commit"])
        assert json.loads(row["components"])[COMPARISON_COMPONENT] == hashlib.sha256(committed.encode()).hexdigest()
        assert "version: 2" in committed, "the rows name version 2 of the comparison card"


def test_the_ledger_row_of_trial_99_names_the_commit_that_froze_card_version_2():
    git = Git(ROOT)
    if git.is_shallow():
        pytest.skip("a shallow clone cannot show the commit")
    with (ROOT / "research/ledger.csv").open() as handle:
        row = next(r for r in csv.DictReader(handle) if r["trial_id"] == "99")
    committed = git.committed_text(CARD_PATH, row["protocol_commit"])
    assert committed is not None and "\nversion: 2\n" in committed
    assert git.is_ancestor(row["protocol_commit"], "HEAD")
    for registered in d6_rows().values():
        assert (
            json.loads(registered["components"])[COMPARISON_COMPONENT] == hashlib.sha256(committed.encode()).hexdigest()
        )


def test_the_real_rows_and_the_real_card_pass_the_counting_rule_once_a_first_counted_session_is_set():
    """Everything registered here, judged by the real rule on the real history, with only the first counted session
    (unset by design until the 10-session gate) supplied."""
    from datetime import date

    from fno.books.version_registry import parse_versions
    from fno.books.versions import Versions
    from fno.school.constants import RoadCode
    from fno.school.registration.counting import CountCandidate, CountingRule, FirstCounted
    from fno.school.registration.wiring import D6VersionLookup, GitCountingHistory

    git = Git(ROOT)
    if git.is_shallow():
        pytest.skip("a shallow clone cannot show the history")

    class WithFirstCounted(GitCountingHistory):
        def first_counted_at(self, commit):
            return FirstCounted(date(2026, 10, 22), git.commits_touching("journal/versions.csv")[0])

    rows = parse_versions((ROOT / "journal/versions.csv").read_text())
    rule = CountingRule(WithFirstCounted(git), D6VersionLookup(Versions(rows, git)))
    head = git.head()
    for card in CARDS:
        sha = hashlib.sha256(card.read_bytes()).hexdigest()
        verdict = rule.verdict(CountCandidate(date(2026, 11, 30), RoadCode.NIFTY_MONTHLY, driver_id(card), sha, head))
        assert verdict.counted, (card.name, verdict.reason)
