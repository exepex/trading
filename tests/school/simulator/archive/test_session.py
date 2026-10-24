"""`school practice run --archive` (MS-SIM-e2): the run's files and report text saved with receipts, the report's first
line, and the default that archives nothing."""

import gzip
import subprocess
from datetime import date

import pytest

from fno.school.execution import practice_wiring
from fno.school.fakes import FakeSettlementSource
from fno.school.simulator import command
from fno.school.simulator.archive import names
from fno.school.simulator.archive.archive import PracticeArchive
from fno.school.simulator.archive.files import run_files
from fno.school.simulator.archive.inputs import CodeNotCommitted, code_identity, inputs_digest
from fno.school.simulator.constants import PRACTICE_LABEL
from fno.school.simulator.practice.render import left_out_lines
from fno.school.simulator.spreads.model import SpreadModel
from fno.school.simulator.spreads.recorded import Skipped
from fno.storage.data_store import DataStore
from fno.storage.receipts import ReceiptFolder
from tests.school.safety.law_builders import FixedMargin
from tests.school.simulator.archive.test_archive import DictDrive, FakePublisher, Reader
from tests.school.simulator.practice import test_fleet as tf
from tests.school.simulator.test_command import namespace

LEFT_OUT = Skipped([("NIFTY-W", date(2026, 10, 13), "capture_missing")])


class World:
    """A fake Drive and remote the command's archive is built over, kept between runs like the real ones."""

    def __init__(self, tmp_path):
        self.drive, self.folder = DictDrive(), ReceiptFolder(tmp_path / "receipts")
        self.publisher, self.built = FakePublisher(self.folder), []

    def archive(self, run: str) -> PracticeArchive:
        self.built.append(run)
        data = DataStore(self.drive, "data", self.folder, "practice archive", run)
        return PracticeArchive(data, self.publisher, Reader(self.drive))


@pytest.fixture
def world(tmp_path, monkeypatch):
    monkeypatch.setattr(practice_wiring, "build_settlement_source", lambda: FakeSettlementSource({}))
    parts, margin = tf.parts(), lambda cfg: FixedMargin()  # noqa: E731

    class Runner(command.PracticeRunner):
        def __init__(self, parts, home):
            super().__init__(parts, home, margin_for=margin)

    monkeypatch.setattr(command, "PracticeRunner", Runner)
    monkeypatch.setattr(command, "build_practice_parts", lambda cfg, today, folder: (parts, LEFT_OUT))
    monkeypatch.setattr(command, "code_identity", lambda root: "abc1234")
    made = World(tmp_path / "world")
    monkeypatch.setattr(command, "build_practice_archive", made.archive)
    return made


LEFT_OUT_LINES = left_out_lines(LEFT_OUT)


def run(tmp_path, **kw) -> tuple[int, list[str]]:
    lines: list[str] = []
    return command.cmd_practice_run(namespace(home=tmp_path / "home", **kw), out=lines.append), lines


def test_the_default_run_archives_nothing(world, tmp_path):
    code, lines = run(tmp_path)
    assert code == 0 and world.built == [] and not world.drive.files and world.publisher.commits == 0
    assert lines[0].startswith(f"{PRACTICE_LABEL} | local only, not archived")


def test_an_archived_run_says_so_on_its_first_line_with_the_count_folder_and_first_commit(world, tmp_path):
    code, lines = run(tmp_path, archive=True)
    (run_id,) = world.built
    files = list(world.drive.files)
    assert code == 0 and len(files) > 3 and all(f.startswith(f"data/{names.PRACTICE_AREA}/{run_id}/") for f in files)
    assert lines[0] == (f"{PRACTICE_LABEL} | archived: run {run_id}, {len(files)} files, "
                        f"receipts {names.receipts_folder(run_id)}, first receipt commit c1")  # fmt: skip
    assert all(text.startswith(PRACTICE_LABEL) for text in lines)


def test_the_report_text_is_the_last_file_and_carries_the_run_and_every_result_line(world, tmp_path):
    run(tmp_path, archive=True)
    (run_id,) = world.built
    saved = world.drive.files[f"data/{names.report_path(run_id)}"].decode().splitlines()
    assert saved[0].startswith(f"{PRACTICE_LABEL} | report text of run {run_id}")
    assert any("practice results are never used to choose, tune or rank" in text for text in saved)
    assert all(text.startswith(PRACTICE_LABEL) for text in saved) and not any("archived:" in t for t in saved)
    assert saved[-2:] == [t for t in LEFT_OUT_LINES]
    assert list(world.drive.files)[-1].endswith("report.txt")


def test_only_dashcam_record_files_and_the_report_are_archived_not_counts_or_accounts(world, tmp_path):
    run(tmp_path, archive=True)
    kinds = {path.rsplit("/", 1)[-1].split(".")[1] if path.endswith(".gz") else "report" for path in world.drive.files}
    assert kinds == {"decisions", "drift", "outcomes", "report"}
    assert all(path.endswith((".jsonl.gz", "report.txt")) for path in world.drive.files)


def test_a_rerun_of_the_same_run_names_the_same_run_and_makes_no_second_commit(world, tmp_path):
    first_code, first = run(tmp_path, archive=True)
    commits = world.publisher.commits
    second_code, second = run(tmp_path / "again", archive=True)
    assert world.built[0] == world.built[1] and world.publisher.commits == commits
    assert first[0] == second[0] and first_code == second_code == 0


def test_every_archived_record_line_is_labelled(world, tmp_path):
    run(tmp_path, archive=True)
    rows = [path for path in world.drive.files if path.endswith(".jsonl.gz")]
    texts = [gzip.decompress(world.drive.files[p]) for p in rows]
    full = [text for text in texts if text]  # a slot with nothing to record is an empty file
    assert full and all(line.count(PRACTICE_LABEL.encode()) == 1 for text in full for line in text.splitlines())


def test_a_damaged_read_back_gives_local_only_with_the_reason_and_exit_1(world, tmp_path, monkeypatch):
    real = Reader.read
    monkeypatch.setattr(Reader, "read", lambda self, path: real(self, path) + b"x")
    code, lines = run(tmp_path, archive=True)
    assert code == 1 and lines[0].startswith(f"{PRACTICE_LABEL} | local only, not archived")
    assert "archiving stopped after 0 of" in lines[1] and "ArchiveDamaged" in lines[1]
    assert not any("archived: run" in text for text in lines)


def test_a_push_that_fails_midway_is_reported_partial_never_archived(world, tmp_path, monkeypatch):
    real = FakePublisher.publish

    def fail_second(self, drive_path, what):
        if self.commits >= 1:
            raise RuntimeError("receipts NOT pushed")
        return real(self, drive_path, what)

    monkeypatch.setattr(FakePublisher, "publish", fail_second)
    code, lines = run(tmp_path, archive=True)
    assert code == 1 and "local only, not archived" in lines[0]
    assert "archiving stopped after 1 of" in lines[1] and "receipts NOT pushed" in lines[1]


def test_uncommitted_code_is_refused_before_anything_runs(world, tmp_path, monkeypatch):
    def dirty(root):
        raise CodeNotCommitted("the code is not committed (fno/x.py)")

    monkeypatch.setattr(command, "code_identity", dirty)
    monkeypatch.setattr(command, "build_practice_parts", lambda *a: pytest.fail("the run started"))
    code, lines = run(tmp_path, archive=True)
    assert code == command.REFUSED_EXIT and "not committed" in lines[0] and world.built == []


def test_a_practice_receipt_is_in_the_practice_folder_and_never_in_the_pilots(world, tmp_path):
    run(tmp_path, archive=True)
    receipts = [p for p in world.folder.folder.rglob("*") if p.is_file()]
    assert receipts and all("/school-practice/" in p.as_posix() for p in receipts)
    assert not any("/data/school/" in p.as_posix() for p in receipts)


# ---- the parts ------------------------------------------------------------------------------------------------------


def test_the_files_come_in_scenario_then_path_order_under_the_run(tmp_path):
    run_id = names.run_id(*[__import__("datetime").date(2024, 3, d) for d in (4, 6)], ["NIFTY-M"], ["a"], "c", "d")
    for scenario, day in (("p75", "05"), ("median", "06"), ("median", "05")):
        file = tmp_path / scenario / "dashcam" / "school" / "dashcam" / "2024" / "03" / day / "1500.decisions.jsonl.gz"
        file.parent.mkdir(parents=True)
        file.write_bytes(b"x")
    found = [f.path for f in run_files(run_id, tmp_path, ("median", "p75"))]
    assert found == [names.file_path(run_id, s, f"2024/03/{d}/1500.decisions.jsonl.gz")
                     for s, d in (("median", "05"), ("median", "06"), ("p75", "05"))]  # fmt: skip


def test_the_inputs_digest_follows_every_spread_value_and_the_margin_label():
    from datetime import date

    from fno.school.simulator.spreads.bucket import bucket_of

    bucket = bucket_of("NIFTY", 100.0, 100.0, date(2024, 3, 4), date(2024, 3, 28))

    def model(value):
        return SpreadModel({bucket: {date(2024, 3, 4): value}})

    base = inputs_digest(model(0.01), "factor 1.5")
    assert inputs_digest(model(0.01), "factor 1.5") == base
    assert inputs_digest(model(0.02), "factor 1.5") != base and inputs_digest(model(0.01), "factor 1.6") != base


def git(repo, *args) -> str:
    done = subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True)
    return done.stdout


def code_repo(path):
    """A repository whose HEAD holds all four code paths."""
    path.mkdir()
    git(path, "init", "-q")
    git(path, "config", "user.email", "t@example.test")
    git(path, "config", "user.name", "t")
    (path / "fno").mkdir()
    (path / "fno" / "a.py").write_text("x = 1\n")
    (path / "tools").mkdir()
    (path / "tools" / "t.py").write_text("t = 1\n")
    (path / "config.yaml").write_text("a: 1\n")
    (path / "requirements.txt").write_text("numpy>=2\n")
    git(path, "add", "-A")
    git(path, "commit", "-q", "-m", "code")
    return path


def data_commit(repo, name="r"):
    (repo / "receipts").mkdir(exist_ok=True)
    (repo / "receipts" / f"{name}.sha256").write_text(f"{name}\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", f"a receipt {name}")


def test_the_code_is_named_only_when_committed_and_untracked_files_are_named(tmp_path):
    repo = code_repo(tmp_path / "r")
    assert len(code_identity(repo)) == 12
    (repo / "fno" / "a.py").write_text("x = 2\n")
    with pytest.raises(CodeNotCommitted, match="fno/a.py"):
        code_identity(repo)
    git(repo, "checkout", "--", "fno")
    (repo / "fno" / "newpkg").mkdir()
    (repo / "fno" / "newpkg" / "b.py").write_text("y = 1\n")
    with pytest.raises(CodeNotCommitted, match="newpkg/b.py"):  # the file itself is named, not only its new folder
        code_identity(repo)


def test_data_and_receipt_commits_do_not_change_the_identity_but_code_and_requirements_do(tmp_path):
    """The run's own receipt commits move HEAD; a rerun of the same code must still name the same run."""
    repo = code_repo(tmp_path / "r")
    first = code_identity(repo)
    data_commit(repo)
    git(repo, "commit", "-q", "--allow-empty", "-m", "nothing")
    assert code_identity(repo) == first
    (repo / "fno" / "a.py").write_text("x = 2\n")
    git(repo, "commit", "-q", "-am", "more code")
    second = code_identity(repo)
    (repo / "requirements.txt").write_text("numpy>=2.1\n")  # a library change can change a result
    with pytest.raises(CodeNotCommitted, match="requirements.txt"):
        code_identity(repo)
    git(repo, "commit", "-q", "-am", "a library")
    assert len({first, second, code_identity(repo)}) == 3


@pytest.mark.parametrize("path", ["fno/a.py", "tools/t.py", "config.yaml", "requirements.txt"])
def test_a_committed_change_to_any_one_code_path_changes_the_identity_and_an_uncommitted_one_is_refused(tmp_path, path):
    repo = code_repo(tmp_path / "r")
    before = code_identity(repo)
    (repo / path).write_text("changed\n")
    with pytest.raises(CodeNotCommitted, match=path):
        code_identity(repo)
    git(repo, "commit", "-q", "-am", "changed")
    assert code_identity(repo) != before


def test_a_shallow_clone_gives_the_same_identity_as_the_full_one_before_and_after_unshallowing(tmp_path):
    """Judge 533: the container clones at depth 50 and the run's own publisher unshallows it."""
    origin = code_repo(tmp_path / "origin")
    expected = code_identity(origin)
    for number in range(4):
        data_commit(origin, f"r{number}")
    shallow = tmp_path / "shallow"
    git(tmp_path, "clone", "-q", "--depth", "2", origin.as_uri(), str(shallow))
    assert git(shallow, "rev-parse", "--is-shallow-repository").strip() == "true"
    assert code_identity(shallow) == expected
    data_commit(shallow, "own")  # the run's own receipt commit
    assert code_identity(shallow) == expected
    git(shallow, "fetch", "-q", "--unshallow")
    assert code_identity(shallow) == expected


def test_a_repository_whose_commits_hold_none_of_the_code_is_refused_by_the_missing_path(tmp_path):
    repo = tmp_path / "r"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "t@example.test")
    git(repo, "config", "user.name", "t")
    data_commit(repo)  # a commit exists, but it holds only a receipt
    with pytest.raises(CodeNotCommitted, match="path 'fno' does not exist"):
        code_identity(repo)


def test_a_repository_with_no_commit_at_all_is_refused(tmp_path):
    (tmp_path / "r").mkdir()
    git(tmp_path / "r", "init", "-q")
    with pytest.raises(CodeNotCommitted):
        code_identity(tmp_path / "r")
