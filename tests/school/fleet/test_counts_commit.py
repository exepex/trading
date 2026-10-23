"""Story MS-P1j (Judge B's note on judge 507.5): the counts' commit takes the session's named files only, never the
folder, so a timed-out writer's stray `.<name>.part` file in the counts folder is never committed. On real git: a
clone of a bare origin."""

import subprocess

import pytest

from fno.school.constants import SLOT_1500
from fno.school.dashcam.names import COUNTS_FOLDER
from fno.school.fleet.counts_commit import SessionFilesCommitter
from fno.school.fleet.counts_file import SessionCounts, marks_path
from fno.school.instructor.outputs.public_counts import counts_path as instructor_counts_path
from tests.school.contracts import builders as b


def git(folder, *args):
    return subprocess.run(["git", *args], cwd=folder, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def clone(tmp_path):
    origin, clone = tmp_path / "origin.git", tmp_path / "clone"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    git(tmp_path, "clone", "-q", str(origin), str(clone))
    for key, value in (("user.name", "test"), ("user.email", "test@example.invalid"), ("core.hooksPath", "hooks")):
        git(clone, "config", key, value)
    (clone / "README.md").write_text("x\n")
    git(clone, "add", "README.md")
    git(clone, "commit", "-q", "-m", "start")
    git(clone, "push", "-q", "origin", "HEAD:main")
    return clone


def test_only_the_session_s_named_files_are_committed_never_a_stray_part_file(clone):
    instructor = str(instructor_counts_path(b.SESSION))
    counts = SessionCounts(clone, SessionFilesCommitter(clone, clone / COUNTS_FOLDER, "Counts: {what}"),
                           lambda session: (str(instructor_counts_path(session)),))  # fmt: skip
    counts.write(b.SESSION, SLOT_1500, (), ())  # writes both of its files and commits them
    (clone / instructor).parent.mkdir(parents=True, exist_ok=True)
    (clone / instructor).write_text("session,driver\n")
    stray = (clone / instructor).with_name(f".{(clone / instructor).name}.part")
    stray.write_text("half written")
    other = clone / COUNTS_FOLDER / "notes.csv"  # not ignored: only the named-files commit keeps it out
    other.write_text("not the session's\n")
    counts.commit(b.SESSION)
    tracked = set(git(clone, "ls-tree", "-r", "--name-only", "origin/main").split())
    assert set(counts.files(b.SESSION)) - {str(marks_path(b.SESSION, SLOT_1500))} <= tracked  # no marks today
    assert instructor in tracked
    assert not {stray.relative_to(clone).as_posix(), other.relative_to(clone).as_posix()} & tracked
