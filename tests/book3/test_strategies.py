"""Story F6 criterion 1 and design item 5: Book 3's tradable strategies on a day are the specs registered before it,
committed and unedited (D5's checks), keyed as D1's files; a spec proposed today trades from the next session."""

from datetime import timedelta

from fno.book3.registry import spec_path
from fno.book3.strategies import Book3Strategies
from fno.playbook.decision_inputs import PlaybookSnapshot
from fno.playbook.opened_playbook import OpenedPlaybook
from fno.research_engine.ledger import Git
from tests.book3.builders import PROVENANCE, commit, constitution, registry
from tests.book3.engine_builders import DAY, YESTERDAY, repository, spec, spec_document


def tradable(root, day=DAY):
    return Book3Strategies(registry(root, today=day)).on(day, Git(root).head())


def test_a_spec_registered_yesterday_trades_today_and_its_committed_text_is_kept(tmp_path):
    repository(tmp_path, [spec("b3-sc")])
    found = tradable(tmp_path)
    assert set(found.snapshot.files) == {"b3-sc-v1.yaml"} and found.excluded == {}
    assert found.snapshot.files["b3-sc-v1.yaml"] == (tmp_path / spec_path("b3-sc-v1")).read_text()
    playbook = found.snapshot.playbook()
    assert isinstance(playbook, OpenedPlaybook) and [s.key for s in playbook.approved_on(DAY)] == [("b3-sc", 1)]


def test_a_spec_proposed_today_is_not_tradable_today_and_is_tomorrow(tmp_path):
    repository(tmp_path, [spec("b3-sc")], on=DAY)
    today = tradable(tmp_path)
    assert today.snapshot.files == {} and today.excluded == {}  # not yet open, not refused (D5 would refuse it too)
    assert set(tradable(tmp_path, DAY + timedelta(days=1)).snapshot.files) == {"b3-sc-v1.yaml"}


def test_an_uncommitted_registration_is_not_listed_at_all(tmp_path):
    """The registry is read as committed (judge 400): a row on disk only is not a registration yet."""
    repository(tmp_path)
    registry(tmp_path, today=YESTERDAY).register(spec("b3-late"), PROVENANCE, constitution())
    found = tradable(tmp_path)
    assert found.snapshot.files == {} and found.excluded == {}


def test_a_registry_missing_on_disk_still_lists_the_committed_strategies(tmp_path):
    repository(tmp_path, [spec("b3-sc")])
    (tmp_path / "book3/strategies/registry.csv").unlink()
    assert set(tradable(tmp_path).snapshot.files) == {"b3-sc-v1.yaml"}


def test_one_damaged_spec_is_excluded_and_the_others_stay_tradable(tmp_path):
    """Judge 400 should-fix 1: a spec that no longer parses never stops Book 3's day."""
    narrower = {**spec_document()["structure"], "widths": [200, 100]}
    repository(tmp_path, [spec("b3-sc"), spec("b3-two", structure=narrower)])
    (tmp_path / spec_path("b3-two-v1")).write_text("not: [valid\n")
    commit(tmp_path, "a damaged spec")
    found = tradable(tmp_path)
    assert set(found.snapshot.files) == {"b3-sc-v1.yaml"} and "b3-two-v1" in found.excluded


def test_a_spec_edited_after_registration_is_excluded(tmp_path):
    repository(tmp_path, [spec("b3-sc")])
    path = tmp_path / spec_path("b3-sc-v1")
    path.write_text(path.read_text() + "# a comment\n")
    commit(tmp_path, "edit the spec")
    found = tradable(tmp_path)
    assert found.snapshot.files == {} and "edited after it" in found.excluded["b3-sc-v1"]


def test_no_registry_means_nothing_tradable(tmp_path):
    repository(tmp_path)
    found = tradable(tmp_path)
    assert found.snapshot.files == {} and found.snapshot.playbook().approved_on(DAY) == ()


def test_the_snapshot_round_trips_through_d3_s_inputs_json(tmp_path):
    repository(tmp_path, [spec("b3-sc")])
    snapshot = tradable(tmp_path).snapshot
    again = PlaybookSnapshot.from_json(snapshot.to_json())
    assert again == snapshot and [s.key for s in again.playbook().approved_on(DAY)] == [("b3-sc", 1)]


def test_an_opened_playbook_never_approves_a_version_on_its_opening_day(tmp_path):
    """The second guard behind criterion 1: D2 reads only `approved_on`, and that excludes the opening day."""
    repository(tmp_path, [spec("b3-sc")])
    snapshot = tradable(tmp_path).snapshot
    opened_today = PlaybookSnapshot(
        snapshot.files, snapshot.registry_csv, snapshot.commit, {"b3-sc-v1": DAY.isoformat()}
    )
    assert opened_today.playbook().approved_on(DAY) == ()
    assert [s.key for s in opened_today.playbook().approved_on(DAY + timedelta(days=1))] == [("b3-sc", 1)]
    assert opened_today.playbook().shadow_on(DAY) == () and opened_today.playbook().status_on(DAY) == {}
