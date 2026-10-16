"""Story F6 criterion 1 and design item 5: Book 3's tradable strategies on a day are the specs registered before it,
committed and unedited (D5's checks), keyed as D1's files; a spec proposed today trades from the next session."""

from datetime import timedelta

from fno.book3.registry import spec_path
from fno.book3.strategies import Book3Strategies
from fno.playbook.decision_inputs import PlaybookSnapshot
from fno.playbook.opened_playbook import OpenedPlaybook
from fno.research_engine.ledger import Git
from tests.book3.builders import PROVENANCE, commit, constitution, registry
from tests.book3.engine_builders import DAY, YESTERDAY, repository, spec


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
    assert tradable(tmp_path).snapshot.files == {}
    assert set(tradable(tmp_path, DAY + timedelta(days=1)).snapshot.files) == {"b3-sc-v1.yaml"}


def test_an_uncommitted_registration_is_excluded_with_d5_s_reason(tmp_path):
    repository(tmp_path)
    registry(tmp_path, today=YESTERDAY).register(spec("b3-late"), PROVENANCE, constitution())
    found = tradable(tmp_path)
    assert found.snapshot.files == {} and "not registered in a commit" in found.excluded["b3-late-v1"]


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
