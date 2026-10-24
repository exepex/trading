"""E8 rule 8 and acceptance 7: the private availability file, its seals, the restore path and the hashed-line rule."""

from __future__ import annotations

import subprocess
from datetime import date

import pytest

from fno.desk.owner_timing.availability import (
    AvailabilityRefused,
    AvailabilitySealer,
    SealedDriveAvailability,
    normalised_lines,
    prefix_sha256,
)
from fno.desk.owner_timing.seal_log import SHALLOW, GitSealLog
from tests.desk.builders import DictStore
from tests.desk_owner_timing.fakes import MemorySeals, calendar_file, ist

PATH = "private/availability.csv"
FRI, MON = date(2026, 10, 16), date(2026, 10, 19)
RUN, CARD = ist(date(2026, 10, 15), 14, 33), ist(date(2026, 10, 15), 15, 16)


def setup(text: bytes):
    store, seals = DictStore(), MemorySeals()
    store.put(PATH, text)
    return store, seals, SealedDriveAvailability(store, PATH, seals), AvailabilitySealer(store, PATH, seals)


def commit_last(seals: MemorySeals, at=RUN) -> None:
    seal, _ = seals.rows[-1]
    seals.rows[-1] = (seal, at)


def test_nothing_sealed_means_available():
    _, _, availability, _ = setup(calendar_file("2026-10-16,away"))
    assert not availability.away(FRI, CARD)


def test_an_away_row_sealed_before_the_card_counts():
    _, seals, availability, sealer = setup(calendar_file("2026-10-16,away"))
    sealer.seal(RUN)
    commit_last(seals)
    assert availability.away(FRI, CARD)
    assert not availability.away(MON, CARD)


def test_a_seal_never_committed_does_not_count():
    _, _, availability, sealer = setup(calendar_file("2026-10-16,away"))
    sealer.seal(RUN)
    assert not availability.away(FRI, CARD)


def test_a_row_appended_after_the_seal_is_late_and_ignored():
    store, seals, availability, sealer = setup(calendar_file("2026-10-19,away"))
    sealer.seal(RUN)
    commit_last(seals)
    store.put(PATH, calendar_file("2026-10-19,away", "2026-10-16,away"))
    assert not availability.away(FRI, CARD)
    assert availability.late_rows(CARD) == 1


def test_the_latest_row_of_a_date_wins():
    _, seals, availability, sealer = setup(calendar_file("2026-10-16,away", "2026-10-16,available"))
    sealer.seal(RUN)
    commit_last(seals)
    assert not availability.away(FRI, CARD)


def test_a_changed_sealed_line_refuses_until_restored():
    store, seals, availability, sealer = setup(calendar_file("2026-10-16,away"))
    sealer.seal(RUN)
    commit_last(seals)
    store.put(PATH, calendar_file("2026-10-17,away"))  # the owner "fixed" an old row
    with pytest.raises(AvailabilityRefused, match="restore the last sealed version"):
        availability.away(FRI, CARD)
    with pytest.raises(AvailabilityRefused, match="restore"):
        sealer.seal(CARD)
    assert len(seals.rows) == 1  # never re-sealed over a mismatch
    store.put(PATH, calendar_file("2026-10-16,away"))  # restored from Drive's version history
    assert availability.away(FRI, CARD)


def test_line_endings_and_trailing_spaces_hash_the_same():
    lf = normalised_lines(calendar_file("2026-10-16,away"))
    crlf = normalised_lines(calendar_file("2026-10-16,away  ", newline="\r\n") + b"\r\n\r\n")
    assert prefix_sha256(lf, 2) == prefix_sha256(crlf, 2)


def test_sealing_an_unchanged_file_adds_nothing():
    _, seals, _, sealer = setup(calendar_file("2026-10-16,away"))
    assert sealer.seal(RUN) is not None
    assert sealer.seal(CARD) is None
    assert len(seals.rows) == 1


@pytest.mark.parametrize("text", [b"2026-10-16,away", b"salt,short\n2026-10-16,away", calendar_file("16 Oct,away")])
def test_a_malformed_file_is_refused(text):
    _, _, _, sealer = setup(text)
    with pytest.raises(AvailabilityRefused):
        sealer.seal(RUN)


def test_a_lost_file_with_seals_is_refused():
    store, seals, availability, sealer = setup(calendar_file("2026-10-16,away"))
    sealer.seal(RUN)
    commit_last(seals)
    store.files.clear()
    with pytest.raises(AvailabilityRefused, match="missing"):
        availability.away(FRI, CARD)


def test_git_seal_log_counts_a_seal_only_after_its_commit(tmp_path):
    def git(*args):
        env = {"GIT_COMMITTER_DATE": "2026-10-15T14:34:00+05:30", "GIT_AUTHOR_DATE": "2026-10-15T14:34:00+05:30"}
        subprocess.run(
            ["git", *args], cwd=tmp_path, check=True, capture_output=True, env={**env, "HOME": str(tmp_path)}
        )

    git("init", "-q")
    git("config", "user.email", "t@example.invalid")
    git("config", "user.name", "t")
    git("config", "core.hooksPath", "/dev/null")
    log = GitSealLog(tmp_path, "research/desk/availability_seals.csv", ref="HEAD")
    seal = AvailabilitySealer(DictStore(), PATH, log)
    seal.store.put(PATH, calendar_file("2026-10-16,away"))
    sealed = seal.seal(RUN)
    assert log.latest() == sealed and log.sealed_before(CARD) is None  # written, not committed
    git("add", ".")
    git("commit", "-q", "-m", "seal")
    assert log.sealed_before(CARD) == sealed
    assert log.sealed_before(RUN) is None  # committed at 14:34, after 14:33


def test_git_seal_log_refuses_in_a_shallow_clone(tmp_path):
    """Judge 203 sf 1: a depth-1 clone dates every seal to its boundary commit, so the log refuses to answer."""

    def git(cwd, *args):
        subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *args], cwd=cwd, check=True, capture_output=True)

    origin = tmp_path / "origin"
    (origin / "research/desk").mkdir(parents=True)
    git(origin, "init", "-q")
    for n in (1, 2):
        (origin / "research/desk/availability_seals.csv").write_text(f"sealed_at,lines,sha256\nx,{n},{n:064x}\n")
        git(origin, "add", ".")
        git(origin, "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-q", "-m", f"c{n}")
    git(tmp_path, "clone", "-q", "--depth", "1", f"file://{origin}", "shallow")
    shallow = GitSealLog(tmp_path / "shallow", "research/desk/availability_seals.csv", ref="HEAD")
    with pytest.raises(AvailabilityRefused, match="git fetch --unshallow origin main") as refused:
        shallow.sealed_before(CARD)
    assert str(refused.value) == SHALLOW
    GitSealLog(origin, "research/desk/availability_seals.csv", ref="HEAD").sealed_before(CARD)  # full: answers
