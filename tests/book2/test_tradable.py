"""Story F5 criterion 13 (judge 632 B1 and SF1): Book 2's tradable versions are D2's approved set for the day plus the
registered research candidates still `research` through it, minus Book 2's research pauses; never a paused or retired
version; no shadow evaluated; the view travels in the run's snapshot so a replay rebuilds it, and Book 1's snapshot
bytes are unchanged."""

from datetime import timedelta

from fno.playbook.book2_playbook import Book2Playbook
from fno.playbook.decision_inputs import PlaybookSnapshot
from fno.playbook.registry import RegistryRow
from tests.playbook.evaluation_builders import DAY, playbook, strategy

PAPER, RESEARCH, UNREGISTERED = strategy("sc-paper"), strategy("sc-research", "research"), strategy("sc-new", "research")


def keys(strategies):
    return sorted(s.key for s in strategies)


def book2(*strategies, registered=(), rows=(), paused=frozenset()):
    base = playbook(*strategies, registered=registered)
    return Book2Playbook(base.strategies, (*base.rows, *rows), paused=paused)


def test_paper_versions_and_registered_research_candidates_are_tradable_but_no_shadow():
    view = book2(PAPER, RESEARCH, UNREGISTERED, registered=[RESEARCH.key])
    assert keys(view.approved_on(DAY)) == [("sc-paper", 1), ("sc-research", 1)]
    assert view.shadow_on(DAY) == ()  # Book 2 writes nothing into D2's shadow books
    assert keys(playbook(PAPER, RESEARCH, registered=[RESEARCH.key]).approved_on(DAY)) == [("sc-paper", 1)]  # Book 1


def test_a_version_paused_or_retired_that_day_is_not_tradable_that_day():
    paused = RegistryRow("sc-paper", 1, PAPER.parameters_sha256, "paused", DAY, "e6", "")
    assert book2(PAPER, rows=[paused]).approved_on(DAY) == ()
    retired = RegistryRow("sc-research", 1, RESEARCH.parameters_sha256, "retired", DAY, "owner", "")
    assert book2(RESEARCH, registered=[RESEARCH.key], rows=[retired]).approved_on(DAY) == ()


def test_a_research_candidate_registered_that_day_trades_from_the_next_session():
    today = RegistryRow("sc-new", 1, UNREGISTERED.parameters_sha256, "research", DAY, "desk", "")
    view = book2(UNREGISTERED, rows=[today])
    assert view.approved_on(DAY) == () and keys(view.approved_on(DAY + timedelta(days=1))) == [("sc-new", 1)]


def test_a_book2_research_pause_removes_only_that_version():
    view = book2(PAPER, RESEARCH, registered=[RESEARCH.key], paused=frozenset({RESEARCH.key}))
    assert keys(view.approved_on(DAY)) == [("sc-paper", 1)]


def test_the_view_travels_in_the_snapshot_and_book1_s_bytes_are_unchanged():
    files = {"sc-research-v1.yaml": "x"}
    plain = PlaybookSnapshot(files, "csv", "c" * 40)
    viewed = PlaybookSnapshot(files, "csv", "c" * 40, paused=("sc-research-v1",))
    assert "book2_paused" not in plain.to_json() and viewed.to_json()["book2_paused"] == ["sc-research-v1"]
    assert PlaybookSnapshot.from_json(viewed.to_json()) == viewed and PlaybookSnapshot.from_json(plain.to_json()) == plain
