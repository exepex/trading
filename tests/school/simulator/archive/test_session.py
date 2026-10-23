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
from fno.school.simulator.archive.inputs import CodeNotCommitted, code_commit, inputs_digest
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
    monkeypatch.setattr(command, "code_commit", lambda root: "abc1234")
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

    monkeypatch.setattr(command, "code_commit", dirty)
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


def test_the_code_commit_is_named_only_for_committed_code(tmp_path):
    def git(*args):
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "t@example.test")
    git("config", "user.name", "t")
    (tmp_path / "fno").mkdir()
    (tmp_path / "fno" / "a.py").write_text("x = 1\n")
    (tmp_path / "config.yaml").write_text("a: 1\n")
    git("add", "-A")
    git("commit", "-q", "-m", "one")
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=tmp_path, capture_output=True, text=True).stdout.strip()
    assert code_commit(tmp_path) == head[:12]
    (tmp_path / "fno" / "a.py").write_text("x = 2\n")
    with pytest.raises(CodeNotCommitted, match="fno/a.py"):
        code_commit(tmp_path)
    git("checkout", "--", "fno")
    (tmp_path / "fno" / "newpkg").mkdir()
    (tmp_path / "fno" / "newpkg" / "b.py").write_text("y = 1\n")
    with pytest.raises(CodeNotCommitted, match="newpkg/b.py"):  # the file itself is named, not only its new folder
        code_commit(tmp_path)
