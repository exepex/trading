"""Story D6: no version declared after its decisions (1), a served-model mismatch is unscored and pauses scoring
until a new version (2), deterministic segments (3)."""

from datetime import date

from fno.books.version_registry import VersionRow
from fno.books.versions import Segments
from tests.playbook.builders import commit_all

from .builders import BOOK, MODEL_A, MODEL_B, Repo

D1, D2, D3, D4 = date(2026, 10, 20), date(2026, 10, 21), date(2026, 10, 22), date(2026, 10, 23)


def test_a_version_registered_after_a_decision_is_not_its_version(tmp_path):
    repo = Repo(tmp_path)
    early = repo.decision(D2)  # committed before the version row exists
    repo.register("v1", starts_on=D1)  # starts "before" the decision's day, but registered after it
    late = repo.decision(D2)
    segments = Segments(repo.versions(), [early, late])
    assert not segments.segment_of(early.decision_id).scored
    assert "no version registered" in segments.segment_of(early.decision_id).reason
    assert segments.segment_of(late.decision_id).label == f"{BOOK}/v1"


def test_a_version_starts_on_its_day_not_before(tmp_path):
    repo = Repo(tmp_path)
    repo.register("v1", starts_on=D2)
    before, on = repo.decision(D1), repo.decision(D2)
    segments = Segments(repo.versions(), [before, on])
    assert not segments.segment_of(before.decision_id).scored and segments.segment_of(on.decision_id).scored


def test_a_served_model_mismatch_is_unscored_and_pauses_scoring_until_a_new_version(tmp_path):
    repo = Repo(tmp_path)
    repo.register("v1", starts_on=D1)
    fine = repo.decision(D1)
    fallback = repo.decision(D2, served=MODEL_B)  # an unplanned model fallback
    after = repo.decision(D3)  # back on the registered model, still paused
    repo.register("v2", starts_on=D4, components=MODEL_A)
    resumed = repo.decision(D4)
    versions = repo.versions()
    segments = Segments(versions, [resumed, after, fallback, fine])
    assert segments.segment_of(fine.decision_id).label == f"{BOOK}/v1"
    assert segments.segment_of(fallback.decision_id).label == "unscored"
    assert "['model']" in segments.segment_of(fallback.decision_id).reason
    assert segments.segment_of(after.decision_id).label == "unscored"
    assert "paused since 2026-10-21" in segments.segment_of(after.decision_id).reason
    assert segments.segment_of(resumed.decision_id).label == f"{BOOK}/v2"
    assert [segments.scoring_paused(BOOK, d) for d in (D1, D2, D3, D4)] == [False, True, True, False]


def test_a_pause_in_one_book_leaves_the_others_scored(tmp_path):
    repo = Repo(tmp_path)
    repo.register("v1", starts_on=D1)
    repo.register("r1", starts_on=D1, components={"playbook": "abc"}, book="book1_rules")
    fallback = repo.decision(D2, served=MODEL_B)
    book1 = repo.decision(D2, served={"playbook": "abc"}, book="book1_rules")
    segments = Segments(repo.versions(), [fallback, book1])
    assert segments.segment_of(book1.decision_id).label == "book1_rules/r1"
    assert not segments.scoring_paused("book1_rules", D2)


def test_segments_do_not_depend_on_the_order_decisions_are_given(tmp_path):
    repo = Repo(tmp_path)
    repo.register("v1", starts_on=D1)
    decisions = [repo.decision(D1), repo.decision(D2, served=MODEL_B), repo.decision(D3)]
    versions = repo.versions()
    forward = {d.decision_id: Segments(versions, decisions).segment_of(d.decision_id) for d in decisions}
    backward = {d.decision_id: Segments(versions, decisions[::-1]).segment_of(d.decision_id) for d in decisions}
    assert forward == backward


def test_active_version_is_the_latest_started(tmp_path):
    repo = Repo(tmp_path)
    repo.register("v1", starts_on=D1)
    repo.register("v2", starts_on=D3)
    versions = repo.versions()
    assert versions.active_version(BOOK, D2).version_id == "v1" and versions.active_version(BOOK, D3).version_id == "v2"
    assert versions.active_version(BOOK, date(2026, 10, 1)) is None


def test_components_frozen_outside_the_decisions_history_do_not_count(tmp_path):
    """`registered_in_commit` must be in the decision's history too: a row naming a commit git does not hold is not
    the active version for any decision."""
    repo = Repo(tmp_path)
    repo.registry.append(VersionRow(BOOK, "v1", D1, "b" * 40, MODEL_A, "test"))
    commit_all(tmp_path, "register v1 against an unknown commit")
    decision = repo.decision(D2)
    assert not Segments(repo.versions(), [decision]).segment_of(decision.decision_id).scored
