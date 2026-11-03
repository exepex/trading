"""Judge 652 should-fix 1 and minor 1: what a registered AI decision version may write is F1t's only guard on what its
run may commit, so no write path of any registered version may cover the owner's constitution, any file whose
SHA-256 a D6 row registers, or a v4 byte-checked or recorded file; and each registered prompt is the file it names."""

import hashlib
import subprocess
from pathlib import Path

import pytest

from fno.ai_trading.versions import REGISTRY, VERSIONS
from fno.ai_trading.write_snapshot import is_under
from fno.books.version_registry import VersionRegistry
from fno.books.versions import VERSIONS_FILE
from fno.forecast_scoring.v4.freeze_check import RECORDED, byte_checked

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = "book3/constitution-v1.yaml"


def tracked_files() -> list[str]:
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    return [name for name in listed.decode("utf-8").split("\0") if name and (ROOT / name).is_file()]


def d6_hashed_files() -> list[str]:
    """Every tracked file whose SHA-256 is a component of some D6 row (envelopes, constitutions, cards, prompts)."""
    hashes = {value for row in VersionRegistry(ROOT / VERSIONS_FILE).rows() for value in row.components.values()}
    return [name for name in tracked_files() if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() in hashes]


def protected() -> list[str]:
    return sorted({CONSTITUTION, *d6_hashed_files(), *byte_checked(ROOT), *RECORDED})


@pytest.mark.parametrize("version", VERSIONS, ids=lambda v: v.label.split("/sha256")[0])
def test_no_write_path_covers_a_protected_file(version):
    covered = [path for path in protected() if is_under(ROOT, ROOT / path, version.write_paths)]
    assert covered == []


def test_the_protected_set_is_real():
    """The check above is only as good as its list: the constitution and both D6 file components are in it."""
    found = protected()
    assert CONSTITUTION in found and "playbook/envelopes/b0-monthly-sc-v1.yaml" in found and len(byte_checked(ROOT)) > 5


def test_a_write_path_widened_to_the_constitution_s_folder_would_be_caught():
    assert is_under(ROOT, ROOT / CONSTITUTION, ("book3/",)) and not is_under(ROOT, ROOT / CONSTITUTION,
                                                                            ("book3/strategies/",))  # fmt: skip


@pytest.mark.parametrize("version", VERSIONS, ids=lambda v: v.label.split("/sha256")[0])
def test_each_registered_prompt_is_the_file_it_names(version):
    assert REGISTRY.current(version.book).prompt_text(ROOT) == (ROOT / version.prompt_file).read_text(encoding="utf-8")
