"""Story E2's book-private packs: each book's pack holds its own files only, never another book's (every pair), no
link or `..` reaches another book, the packs folder and dot files stay out; and the pack store writes once."""

from itertools import permutations

import pytest

from fno.constants import BOOKS
from fno.desk.pack_items import PackError
from fno.desk.pack_store import PackStore
from fno.desk.private_pack import PrivatePackBuilder

from .builders import DAY

OWN_FOLDERS = {
    "book1_rules": "journal/book1_rules",
    "book2_hybrid": "journal/book2_hybrid",
    "book3_ai": "journal/book3_ai",
}


def plant(root):
    """A marker file in each book's account and decisions, in the playbook and in book3/."""
    for book, folder in OWN_FOLDERS.items():
        for sub in ("account/positions.json", "decisions/2026-10-12/d.json"):
            path = root / folder / sub
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"MARKER-{book}")
    (root / "playbook").mkdir()
    (root / "playbook" / "registry.csv").write_text("MARKER-playbook")
    (root / "book3").mkdir()
    (root / "book3" / "constitution-v1.yaml").write_text("MARKER-book3-constitution")


def text_of(pack) -> str:
    return pack.data.decode()


@pytest.mark.parametrize(("book", "other"), list(permutations(BOOKS, 2)))
def test_a_private_pack_never_holds_another_books_data(tmp_path, book, other):
    plant(tmp_path)
    data = text_of(PrivatePackBuilder(tmp_path).build(book, DAY))
    assert f"MARKER-{book}" in data and f"MARKER-{other}" not in data and f"journal/{other}" not in data


def test_book_1_reads_its_account_decisions_and_the_playbook_book_3_reads_book3(tmp_path):
    plant(tmp_path)
    paths = {b: [f["path"] for f in PrivatePackBuilder(tmp_path).build(b, DAY).body["files"]] for b in BOOKS}
    assert paths["book1_rules"] == [
        "journal/book1_rules/account/positions.json", "journal/book1_rules/decisions/2026-10-12/d.json",
        "playbook/registry.csv",
    ]  # fmt: skip
    assert "book3/constitution-v1.yaml" in paths["book3_ai"] and "playbook/registry.csv" not in paths["book3_ai"]
    assert "book3/constitution-v1.yaml" not in paths["book1_rules"] + paths["book2_hybrid"]


def test_a_link_into_another_book_is_refused(tmp_path):
    plant(tmp_path)
    link = tmp_path / "journal" / "book1_rules" / "account" / "peek.json"
    link.symlink_to(tmp_path / "journal" / "book2_hybrid" / "account" / "positions.json")
    with pytest.raises(PackError, match="resolves outside"):
        PrivatePackBuilder(tmp_path).build("book1_rules", DAY)


def test_packs_and_dot_files_stay_out(tmp_path):
    plant(tmp_path)
    account = tmp_path / "journal" / "book1_rules"
    (account / "account" / ".lock").write_text("host 123")
    (account / "packs" / "2026-10-12").mkdir(parents=True)
    (account / "packs" / "2026-10-12" / "private.json").write_text("{}")
    paths = [f["path"] for f in PrivatePackBuilder(tmp_path).build("book1_rules", DAY).body["files"]]
    assert not any(".lock" in p or "/packs/" in p for p in paths)


def test_an_unknown_book_is_refused(tmp_path):
    with pytest.raises(PackError):
        PrivatePackBuilder(tmp_path).build("book9", DAY)


def test_private_packs_are_byte_identical_when_built_twice(tmp_path):
    plant(tmp_path)
    first, second = (PrivatePackBuilder(tmp_path).build("book1_rules", DAY) for _ in range(2))
    assert first.data == second.data and first.sha256 == second.sha256


def test_the_store_writes_once_with_a_checkable_hash(tmp_path):
    plant(tmp_path)
    store, pack = PackStore(tmp_path), PrivatePackBuilder(tmp_path).build("book1_rules", DAY)
    path = store.write_private(pack)
    assert path == tmp_path / "journal/book1_rules/packs/2026-10-13/private.json" and path.read_bytes() == pack.data
    assert path.with_suffix(".sha256").read_text() == f"{pack.sha256}  private.json\n"
    assert store.write_private(pack) == path  # the same bytes again: accepted
    (tmp_path / "journal/book1_rules/account/positions.json").write_text("changed")
    with pytest.raises(PackError, match="written once"):
        store.write_private(PrivatePackBuilder(tmp_path).build("book1_rules", DAY))
    assert not list(path.parent.glob(".*.tmp"))
