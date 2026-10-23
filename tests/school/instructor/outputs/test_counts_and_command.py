"""Part e's public counts file and command (story MS-INS, criteria 3, 7 and 8): codes and whole numbers only, passing
the record scan; the school's switch off prints "school off" and writes nothing; a dry run writes nothing; --write
writes the instructor's files and the counts file."""

import csv
from datetime import date
from types import SimpleNamespace

import pytest

from fno.composition import build_record_scanner
from fno.config import load_app_config
from fno.record_scan.record_files import NamedFiles
from fno.school.constants import SCHOOL_OFF_LINE
from fno.school.instructor.contracts import Cause
from fno.school.instructor.outputs.command import DRY, run
from fno.school.instructor.outputs.public_counts import HEADER, InstructorCountsFile
from fno.school.instructor.outputs.run import SessionResult
from fno.school.instructor.ports import InstructorConflict
from tests.school.instructor.builders import SESSIONS, classification

DAY = SESSIONS[2]
RECORDS = (classification(), classification(position_id="p2", is_ticket=True, net=50.0, primary=None, secondary=()),
           classification(position_id="p3", corrects="ab" * 32))  # fmt: skip


def test_the_counts_file_holds_codes_and_whole_numbers_and_passes_the_record_scan(tmp_path):
    file = InstructorCountsFile(tmp_path).write(DAY, RECORDS)
    assert build_record_scanner().scan(list(NamedFiles([file]).records())) == []
    rows = list(csv.DictReader(file.read_text().splitlines()))
    assert [(r["driver"], r["ticket"], r["primary"], r["count"]) for r in rows] == [
        ("CS1@1", "no", Cause.WRONG_DIRECTION.value, "1"),
        ("CS1@1", "yes", "unclassified", "1"),
    ]  # a recheck is not counted twice
    assert "Rs" not in file.read_text() and "95" not in file.read_text()


def test_the_counts_file_is_written_once(tmp_path):
    counts = InstructorCountsFile(tmp_path)
    counts.write(DAY, RECORDS)
    counts.write(DAY, RECORDS)
    with pytest.raises(InstructorConflict):
        counts.write(DAY, RECORDS[:1])
    assert InstructorCountsFile(tmp_path).write(date(2026, 11, 9), ()).read_text() == ",".join(HEADER) + "\n"


class Wiring(SimpleNamespace):
    def __init__(self, tmp_path):
        result = SessionResult(DAY, (), RECORDS[:1], (date(2026, 11, 3),))
        stub = SimpleNamespace(for_session=lambda session, write: self.calls.append((session, write)) or result)
        super().__init__(calls=[], build_instructor_run=lambda cfg: stub,
                         build_counts_file=lambda: InstructorCountsFile(tmp_path))  # fmt: skip


def school(enabled: bool) -> dict:
    config = load_app_config()
    return {**config, "school": {**config["school"], "enabled": enabled}}


def test_the_switch_off_prints_school_off_and_does_nothing(tmp_path):
    wiring = Wiring(tmp_path)
    assert run(["--session", str(DAY)], school(False), wiring) == [SCHOOL_OFF_LINE] and wiring.calls == []


def test_a_dry_run_writes_nothing_and_says_so(tmp_path):
    wiring = Wiring(tmp_path)
    lines = run(["--session", str(DAY)], school(True), wiring)
    assert wiring.calls == [(DAY, False)] and DRY in lines[0] and not list(tmp_path.rglob("*.csv"))
    assert lines[1] == "ALERT: outcomes files not readable: 2026-11-03" and lines[2].startswith("CS1@1 BANKNIFTY-M")


def test_write_writes_the_counts_file_too(tmp_path):
    wiring = Wiring(tmp_path)
    lines = run(["--session", str(DAY), "--write"], school(True), wiring)
    assert wiring.calls == [(DAY, True)] and DRY not in lines[0] and len(list(tmp_path.rglob("*.csv"))) == 1


def test_a_winners_why_line_reads_the_winner_form_and_an_update_says_so():
    from fno.school.instructor.contracts import Modifier
    from fno.school.instructor.outputs.why_line import why_line

    win = classification(net=120.0, primary=Cause.VOLATILITY_ROSE, secondary=(Cause.TIME_DECAY,),
                         modifier=Modifier.HARD_ROAD, corrects="ab" * 32)  # fmt: skip
    assert why_line(win) == ("CS1@1 BANKNIFTY-M: net Rs 120; why: volatility fell (also: time decay earned); hard road"
                             " (updated)")  # fmt: skip
    loss = classification(primary=None, secondary=(), modifier=Modifier.NOT_TESTABLE)
    assert why_line(loss) == "CS1@1 BANKNIFTY-M: net Rs -95; why: unclassified; road not compared yet"


def test_the_counts_file_sits_inside_ms_p1js_counts_folder_so_one_commit_takes_both():
    from fno.school.instructor.outputs.public_counts import counts_path

    assert str(counts_path(DAY)) == "research/school/counts/instructor/2026/11/20261104.csv"


def test_ms_p1js_entry_point_runs_the_session_and_writes_the_counts_file(tmp_path, monkeypatch):
    from fno.school.instructor import wiring

    fake = Wiring(tmp_path)
    monkeypatch.setattr(wiring, "build_instructor_run", fake.build_instructor_run)
    monkeypatch.setattr(wiring, "build_counts_file", fake.build_counts_file)
    result = wiring.run_instructor_session({}, DAY)
    assert fake.calls == [(DAY, True)] and result.classifications == RECORDS[:1]
    assert len(list(tmp_path.rglob("*.csv"))) == 1
    wiring.run_instructor_session({}, DAY, write=False)
    assert fake.calls[-1] == (DAY, False)
