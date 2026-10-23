"""FL1-1e: one Drive data file read by its own receipt, verified on real O9 parts: no receipt is "not out yet" (None);
a receipted file Drive lost or changed is a named problem, never a value."""

import pytest

from fno.forecast_lab.verified_file import DAMAGED, MISSING, Unverified

from .drive_files import DriveFiles

PATH = "data/closes/2026/10/2026-10-23.json"


def test_a_receipted_file_is_read_and_one_without_a_receipt_is_not_out_yet(tmp_path):
    parts = DriveFiles(tmp_path)
    assert parts.files.read(PATH) is None
    parts.put(PATH, b'{"day": "2026-10-23"}')
    assert parts.files.read(PATH) == b'{"day": "2026-10-23"}'


def test_a_file_drive_lost_or_changed_is_a_named_problem(tmp_path):
    for problem, spoil in ((MISSING, DriveFiles.lose), (DAMAGED, DriveFiles.damage)):
        parts = DriveFiles(tmp_path / problem)
        parts.put(PATH, b"{}")
        spoil(parts, PATH)
        with pytest.raises(Unverified, match=f"{PATH}: {problem}") as raised:
            parts.files.read(PATH)
        assert raised.value.problem == problem
