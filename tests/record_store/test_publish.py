"""Judge 543 SF1: a record counts only once origin's main holds it. With real git and a bare origin: a refused push
prints "record NOT pushed", alerts and exits 1; the rerun pushes the stuck record; a record another certifier pushed
first is a named conflict, never overwritten."""

import subprocess
from types import SimpleNamespace

import pytest

from fno.close_read.constants import READ
from fno.record_store.cli import cmd_certify
from fno.record_store.constants import PROVISIONAL
from fno.record_store.publisher import GitRecordPublisher
from fno.record_store.record_folder import RecordFolder
from fno.storage.manifest_commit import GitManifestRecorder
from tests.record_store.helpers import LEVELS, SESSION, World, answer

RECORD = f"receipts/records/closes/2026/10/{SESSION}.provisional.json"
REFUSE = "#!/bin/sh\necho 'push refused by the test origin' >&2\nexit 1\n"


def git(where, *args):
    return subprocess.run(["git", "-C", str(where), *args], capture_output=True, text=True, check=True).stdout


def clone(tmp_path, origin, name):
    where = tmp_path / name
    git(tmp_path, "clone", "-q", str(origin), name)
    for key, value in (("user.name", "test"), ("user.email", "test@example.invalid"), ("core.hooksPath", "hooks")):
        git(where, "config", key, value)
    (where / "hooks").mkdir()
    return where


@pytest.fixture
def origin(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    seed = clone(tmp_path, origin, "seed")
    (seed / "README.md").write_text("seed\n")
    git(seed, "add", "README.md")
    git(seed, "commit", "-q", "-m", "seed")
    git(seed, "push", "-q", "origin", "HEAD:main")
    return origin


def certifier_in(tmp_path, origin, name, data):
    repository = clone(tmp_path, origin, name)
    world = World(tmp_path / f"{name}-world")
    world.a4h_saves(READ, data)
    folder = repository / "receipts/records"
    committer = GitManifestRecorder(repository, folder, message="Records: test ({what})", label="records")
    world.records = RecordFolder(folder, GitRecordPublisher(repository, committer))
    return world.certifier()


class Alerts:
    def __init__(self):
        self.sent = []

    def send(self, text):
        self.sent.append(text)
        return "sent"


def certify(certifier, alerts):
    args = SimpleNamespace(dataset="closes", day=SESSION, level=PROVISIONAL, commit=True)
    lines = []
    return cmd_certify(args, lines.append, certifier, alerts), lines


def on_origin(origin, path=RECORD):
    shown = subprocess.run(["git", "-C", str(origin), "show", f"main:{path}"], capture_output=True, check=False)
    return shown.stdout if shown.returncode == 0 else None


def test_a_record_counts_once_origin_holds_it(tmp_path, origin):
    code, lines = certify(certifier_in(tmp_path, origin, "a", answer()), Alerts())
    assert code == 0 and "provisional: recorded" in lines[0] and on_origin(origin) is not None


def test_a_refused_push_alerts_exits_1_and_the_rerun_pushes_the_stuck_record(tmp_path, origin):
    hook = origin / "hooks" / "pre-receive"
    hook.write_text(REFUSE)
    hook.chmod(0o755)
    certifier, alerts = certifier_in(tmp_path, origin, "a", answer()), Alerts()
    code, lines = certify(certifier, alerts)
    assert code == 1 and "record NOT pushed: not on origin/main after the push (push refused" in lines[0]
    assert alerts.sent == [f"Omenix F&O records: {lines[0]}"] and on_origin(origin) is None
    hook.unlink()
    code, lines = certify(certifier, Alerts())  # the record is local and committed: the committer sees nothing new
    assert code == 0 and "already recorded" in lines[0] and on_origin(origin) is not None


def test_a_record_another_certifier_pushed_first_is_a_conflict_never_an_overwrite(tmp_path, origin):
    other = {**LEVELS, "NIFTY 50": (22745.0, 22700.0)}
    first_run = certifier_in(tmp_path, origin, "first", answer(levels=other))
    second_run = certifier_in(tmp_path, origin, "second", answer())  # both checkouts made before either pushes
    assert certify(first_run, Alerts())[0] == 0
    first = on_origin(origin)
    alerts = Alerts()
    code, lines = certify(second_run, alerts)
    assert code == 1 and "conflict: the record names" in lines[0] and "a person decides" in lines[0]
    assert len(alerts.sent) == 1 and on_origin(origin) == first
