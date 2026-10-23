"""Story MS-P1j (orchestrator's ruling, 23 Oct 2026): a comparison card edited without its D6 rows is loud. One line
names `comparison_card_mismatch` after the decisions' seal, the CLI exits 1, nothing else is named, no record
changes. Planted on real git with h's fixture: the card edited, no rows naming the new version."""

from dataclasses import replace
from datetime import datetime
from types import SimpleNamespace

from fno.books.version_registry import render
from fno.books.versions import Versions
from fno.models import IST
from fno.school import cli, wiring
from fno.school.contracts.fleet import RunMode, SessionRun
from fno.school.contracts.seal import Seal
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.card_check import CardMismatchCheck
from fno.school.registration.counting import CARD_PATH, CountingRule
from fno.school.registration.wiring import D6VersionLookup, GitCountingHistory
from tests.school.contracts import builders as b
from tests.school.contracts.test_records import closed_record
from tests.school.contracts.test_settings import GOOD
from tests.school.fleet.rig import Rig, all_roads
from tests.school.registration.fakes import CARD_SHA, SESSION
from tests.school.registration.test_git_history import Repo, commit

NEW_CARD = "the comparison card\n\nversion: 3\n"


def sealed_on(repo: Repo, decision_commit: str, n: int = 2) -> tuple:
    record = closed_record()
    record = replace(record, session=SESSION, card_sha256=CARD_SHA,
                     decision=replace(record.decision, driver_id="CS1@1", session=SESSION))  # fmt: skip
    seal = Seal("dashcam/x.jsonl.gz", "ab" * 32, datetime(2026, 11, 30, 15, 3, tzinfo=IST), decision_commit)
    return (record,) * n, seal


def check(repo: Repo) -> CardMismatchCheck:
    rule = CountingRule(GitCountingHistory(repo.git), D6VersionLookup(Versions(repo.rows, repo.git)))
    return CardMismatchCheck(rule, lambda c: repo.git.committed_text(CARD_PATH, c))


def test_a_card_edited_without_rows_naming_it_is_named_once_with_its_version(tmp_path):
    repo = Repo(tmp_path)
    repo.register()
    commit(repo.path, CARD_PATH, NEW_CARD)  # the plant: a new card version, no D6 rows naming it
    records, seal = sealed_on(repo, repo.decide())
    assert check(repo)(records, seal) == (
        "comparison_card_mismatch: 2 of 2 decisions do not count until D6 rows name card v3; see the MS-P1j runbook",
    )


def test_rows_registered_after_the_seal_never_clear_the_decisions_it_sealed(tmp_path):
    """Judge K's note (judge 520): each decision is judged at its own seal's receipt commit, never at HEAD. Rows naming
    the new card, committed after the seal, count only later decisions; a rerun of this session still says so."""
    repo = Repo(tmp_path)
    repo.register()
    commit(repo.path, CARD_PATH, NEW_CARD)
    records, seal = sealed_on(repo, repo.decide())
    repo.rows.append(repo.row_naming(NEW_CARD, "2", SESSION))
    commit(repo.path, "journal/versions.csv", render(repo.rows))
    repo.decide("after the rows")  # HEAD is now past the rows: judged at HEAD, these decisions would count
    assert check(repo)(records, seal) == (
        "comparison_card_mismatch: 2 of 2 decisions do not count until D6 rows name card v3; see the MS-P1j runbook",
    )


def test_the_line_counts_only_the_mismatched_decisions_among_the_session_s(tmp_path):
    """Judge B's note (judge 507.7): one mismatched decision among others not counted for another reason gives N=1."""
    repo = Repo(tmp_path)
    repo.register()
    commit(repo.path, CARD_PATH, NEW_CARD)
    records, seal = sealed_on(repo, repo.decide(), n=1)
    unregistered = replace(records[0], decision=replace(records[0].decision, driver_id="DR1@1"))  # no D6 row at all
    line = check(repo)((records[0], unregistered, unregistered), seal)
    assert line == ("comparison_card_mismatch: 1 of 3 decisions do not count until D6 rows name card v3; "
                    "see the MS-P1j runbook",)  # fmt: skip


def test_counted_decisions_and_decisions_not_yet_counted_give_no_line(tmp_path):
    (tmp_path / "counted").mkdir()
    (tmp_path / "unset").mkdir()
    counted = Repo(tmp_path / "counted")
    counted.register()
    assert check(counted)(*sealed_on(counted, counted.decide())) == ()
    unset = Repo(tmp_path / "unset")
    unset.register(first=None)  # first_counted unset: nothing counts yet, which is never this line's business
    commit(unset.path, CARD_PATH, NEW_CARD)
    assert check(unset)(*sealed_on(unset, unset.decide())) == ()


def test_the_run_carries_the_line_and_a_rerun_says_it_again(tmp_path):
    line = ("comparison_card_mismatch: 1 of 1 decisions do not count until D6 rows name card v3",)
    rig = Rig(tmp_path, (FakeDriver(all_roads("CS1"), b.put_spread()),), (FakeMaxLossLaw(10_000),))
    rig.fleet.card_check = lambda records, seal: line
    files = None
    for _ in range(2):
        run = rig.fleet.run(b.SESSION, RunMode.REPLAY)
        assert run.warnings == line
        files = files or dict(rig.dashcam.files)
    assert rig.dashcam.files == files, "no record changes"


def test_the_run_command_prints_the_line_and_exits_1(monkeypatch):
    line = "comparison_card_mismatch: 1 of 1 decisions do not count until D6 rows name card v3"
    run = SessionRun(b.SESSION, RunMode.RECORD, "", warnings=(line,))
    monkeypatch.setattr(wiring, "build_fleet", lambda *a, **k: SimpleNamespace(run=lambda session, mode: run))
    monkeypatch.setattr(cli, "load_app_config", lambda: {"school": {**GOOD, "enabled": True}})
    said = []
    assert cli.cmd_run(SimpleNamespace(session=b.SESSION, replay=None), said.append) == 1
    assert line in said


def test_the_record_root_passes_the_check_and_a_replay_has_none(monkeypatch, tmp_path):
    from fno.school import replay_wiring
    from fno.school.fleet.card_check import no_check

    seen = {}
    for module in (wiring, replay_wiring):
        monkeypatch.setattr(
            module,
            "fleet_on",
            lambda cfg, stores, root, *rest, module=module, **k: seen.setdefault(module.__name__, (rest, k)),
        )
    for name in ("build_dashcam", "build_account_sync", "GitManifestRecorder"):
        monkeypatch.setattr(wiring, name, lambda *a, **k: None)
    wiring.build_fleet({"school": {**GOOD, "enabled": True}})
    replay_wiring.build_replay_fleet({}, b.SESSION, tmp_path)
    record_args = seen["fno.school.wiring"]
    assert any(isinstance(a, CardMismatchCheck) for a in (*record_args[0], *record_args[1].values()))
    replay_args = seen["fno.school.replay_wiring"]
    assert not any(isinstance(a, CardMismatchCheck) for a in (*replay_args[0], *replay_args[1].values()))
    assert no_check((), None) == ()
