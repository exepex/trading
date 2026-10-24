"""Judge 507.13's should-fix (owner: fix and one more check): a refused counts commit is loud. It is alerted to
#fno-desk by name ("counts NOT pushed <session>") and `school run` prints it and exits 1, on the first run and on the
rerun; nothing is reported as done; the rerun pushes once the push is no longer refused. On real git: a clone of a
bare origin whose push is refused by pointing it at no remote."""

from types import SimpleNamespace

from fno.school import cli, wiring
from fno.school.constants import SLOT_1500
from fno.school.contracts.fleet import RunMode
from fno.school.dashcam.names import COUNTS_FOLDER
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.counts_commit import SessionFilesCommitter
from fno.school.fleet.counts_file import SessionCounts
from tests.school.contracts import builders as b
from tests.school.contracts.test_settings import GOOD
from tests.school.fleet.rig import DAY2, Rig, all_roads
from tests.school.fleet.test_counts_commit import clone, git  # noqa: F401 - the real-git fixture

LAWS = (FakeMaxLossLaw(10_000),)
NOT_PUSHED = "counts NOT pushed"


def refuse_pushes(clone, refused: bool):  # noqa: F811
    origin = clone.parent / "origin.git"
    git(clone, "remote", "set-url", "origin", str(clone.parent / "nowhere.git") if refused else str(origin))


def tracked(clone) -> set[str]:  # noqa: F811
    git(clone, "fetch", "-q", "origin", "main")
    return set(git(clone, "ls-tree", "-r", "--name-only", "origin/main").split())


def record_rig(clone, alerts: list) -> Rig:  # noqa: F811
    rig = Rig(clone, (FakeDriver(all_roads("CS1"), b.put_spread()),), LAWS)
    committer = SessionFilesCommitter(clone, "Counts: {what}", (f"{COUNTS_FOLDER}/",))
    rig.fleet.counts = SessionCounts(clone, committer, alert=alerts.append)
    return rig


def cli_run(monkeypatch, fleet) -> tuple[int, list[str]]:
    monkeypatch.setattr(wiring, "build_fleet", lambda *a, **k: fleet)
    monkeypatch.setattr(cli, "load_app_config", lambda: {"school": {**GOOD, "enabled": True}})
    said = []
    return cli.cmd_run(SimpleNamespace(session=b.SESSION, replay=None), said.append), said


def test_a_refused_push_is_alerted_printed_and_exits_1_then_the_rerun_pushes_it(clone, monkeypatch):  # noqa: F811
    alerts = []
    rig = record_rig(clone, alerts)
    files = rig.fleet.counts.files(b.SESSION)
    refuse_pushes(clone, True)
    code, said = cli_run(monkeypatch, rig.fleet)
    assert code == 1 and any(line.startswith(f"{NOT_PUSHED} {b.SESSION}") for line in said)
    assert len(alerts) == 1 and alerts[0].startswith(f"{NOT_PUSHED} {b.SESSION}")
    code, said = cli_run(monkeypatch, rig.fleet)  # the rerun branch, still refused
    assert code == 1 and any(line.startswith(NOT_PUSHED) for line in said) and len(alerts) == 2
    refuse_pushes(clone, False)
    code, said = cli_run(monkeypatch, rig.fleet)  # nothing new to commit: the earlier commit is pushed
    assert code == 0 and not any(NOT_PUSHED in line for line in said) and len(alerts) == 2
    assert files[0] in tracked(clone)


def test_an_earlier_session_s_unpushed_counts_never_block_a_later_session_and_go_up_with_it(clone):  # noqa: F811
    alerts = []
    rig = record_rig(clone, alerts)
    refuse_pushes(clone, True)
    first = rig.fleet.run(b.SESSION, RunMode.RECORD)
    assert any(line.startswith(NOT_PUSHED) for line in first.warnings)
    refuse_pushes(clone, False)
    later = rig.at(DAY2).fleet.run(DAY2, RunMode.RECORD)
    assert later.warnings == () and len(alerts) == 1
    on_main = tracked(clone)
    assert rig.fleet.counts.files(b.SESSION)[0] in on_main and rig.fleet.counts.files(DAY2)[0] in on_main
    assert rig.fleet.counts.written(DAY2, SLOT_1500)
