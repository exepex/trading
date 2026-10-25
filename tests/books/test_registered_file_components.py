"""Judge 633.1 (terms v1): every active D6 row's file components equal their files' SHA-256 on disk. A one-byte edit of
a registered envelope or constitution would make C4 refuse every Book 2 or Book 3 trade (`envelope_registered`,
`ConstitutionMode`) while every other test stays green; this test makes CI say so."""

import hashlib
from datetime import date
from pathlib import Path

import pytest

from fno.book3.constitution import COMPONENT
from fno.books.registered_components import RegisteredComponents
from fno.books.version_registry import VersionRegistry
from fno.playbook.envelope_files import COMPONENT_PREFIX, ENVELOPE_FOLDER, EnvelopeFiles

ROOT = Path(__file__).resolve().parents[2]
FAR = date(2099, 12, 31)  # the latest row of each book: the one in force from its start
CONSTITUTION_FILE = "book3/constitution-v1.yaml"  # the file Book 3's latest row registers; a new version moves it


def file_problems(root: Path, book: str) -> list[str]:
    components = RegisteredComponents(VersionRegistry(root / "journal" / "versions.csv"))(book, FAR)
    envelopes = {f"{COMPONENT_PREFIX}{k[0]}-v{k[1]}": e.sha256 for k, e in EnvelopeFiles(root).all().items()}
    constitution = hashlib.sha256((root / CONSTITUTION_FILE).read_bytes()).hexdigest()
    problems = []
    for key, sha in components.items():
        if key.startswith(COMPONENT_PREFIX) and envelopes.get(key) != sha:
            problems.append(f"{book} {key}: registered {sha[:12]}, file {str(envelopes.get(key))[:12]}")
        if key == COMPONENT and sha != constitution:
            problems.append(f"{book} {COMPONENT}: registered {sha[:12]}, file {constitution[:12]}")
    return problems


@pytest.mark.parametrize("book", ["book2_hybrid", "book3_ai"])
def test_every_active_rows_file_components_equal_their_files(book):
    assert file_problems(ROOT, book) == []


def test_a_one_byte_edit_of_a_registered_file_is_caught(tmp_path):
    import shutil

    for part in ("journal/versions.csv", f"playbook/{ENVELOPE_FOLDER}", "book3"):
        source, target = ROOT / part, tmp_path / part
        target.parent.mkdir(parents=True, exist_ok=True)
        (shutil.copytree if source.is_dir() else shutil.copyfile)(source, target)
    constitution = tmp_path / CONSTITUTION_FILE
    constitution.write_text(constitution.read_text(encoding="utf-8") + " ", encoding="utf-8")
    envelope = next((tmp_path / "playbook" / ENVELOPE_FOLDER).glob("*.yaml"))
    envelope.write_text(envelope.read_text(encoding="utf-8") + "#", encoding="utf-8")
    ((book3,), (book2,)) = file_problems(tmp_path, "book3_ai"), file_problems(tmp_path, "book2_hybrid")
    edited = hashlib.sha256(constitution.read_bytes()).hexdigest()
    assert book3 == f"book3_ai constitution: registered 645a383c2399, file {edited[:12]}"  # fails on the hash itself
    assert book2.startswith("book2_hybrid trade_envelope:b0-monthly-sc-v1: registered 94749b4ef1b1, file ")
