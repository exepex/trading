"""Judge 78's point for D3: a record's `served` carries every component of the version, and D6 scores it only when all
are present and equal; the record also keeps the registry state and the commit the run read (judge 74)."""

import json
from datetime import date

from fno.books.version_registry import VersionRow
from fno.books.versions import Segments, Versions
from fno.playbook.decision_record import decision_facts
from fno.playbook.wiring import snapshot_playbook

from .builders import COMMIT, doc, run_day, snapshot

DECISION_COMMIT = "d" * 40


class EveryCommitBefore:
    """A history where every row was committed before every decision (D6's git ancestry is tested in tests/versions)."""

    def first_commit_containing(self, text, path):
        return "e" * 40

    def is_ancestor(self, older, newer):
        return older != newer


def stored(tmp_path):
    run = run_day(tmp_path, snapshot(doc("sc-a")))
    return run, json.loads((run / "sc-a-v1_2026-11-27.json").read_text())


def segment(record, served):
    version = VersionRow("book1_rules", "book1-v1", date(2026, 10, 1), "e" * 40, record["served"], "test")
    facts = decision_facts({**record, "served": served}, DECISION_COMMIT)
    return Segments(Versions([version], EveryCommitBefore()), [facts]).segment_of(facts.decision_id)


def test_a_record_with_every_component_is_scored_and_one_missing_is_not(tmp_path):
    _, record = stored(tmp_path)
    assert segment(record, record["served"]).label == "book1_rules/book1-v1"
    partial = {k: v for k, v in record["served"].items() if k != "config"}
    assert segment(record, partial).label == "unscored"


def test_the_record_keeps_the_registry_state_and_commit_it_read(tmp_path):
    run, record = stored(tmp_path)
    inputs = json.loads((run / "inputs.json").read_text())
    assert record["header"]["registry_commit"] == COMMIT == inputs["playbook"]["commit"]
    assert inputs["playbook"]["registry_csv"].startswith("name,version,sha256,status,changed_on")
    assert "sc-a,1," in inputs["playbook"]["registry_csv"] and "sc-a-v1.yaml" in inputs["playbook"]["files"]


def test_the_app_snapshot_reads_the_repository_playbook():
    playbook = snapshot_playbook()
    assert "example-sc-iv-rich-no-event-v1.yaml" in playbook.files and len(playbook.commit) == 40
    assert playbook.playbook().get("example-sc-iv-rich-no-event", 1).status == "research"
