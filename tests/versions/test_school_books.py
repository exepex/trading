"""D6 accepts a market school driver version as a book id (story MS-P1h); the three books and old rows are unchanged."""

import pytest

from fno.books.version_registry import VersionError, parse_versions, render
from fno.constants import BOOKS

HEADER = "book,version_id,starts_on,registered_in_commit,components,reason\n"
COMMIT = "a" * 40


def row(book: str, version_id: str = "1", day: str = "2026-11-02") -> str:
    return f'{book},{version_id},{day},{COMMIT},"{{""card_sha256"":""{"b" * 64}""}}",pilot\n'


@pytest.mark.parametrize("book", ["school:CS1@1", "school:N0@1", "school:PS2@12", "school:REF@1"])
def test_a_school_driver_version_id_is_accepted(book):
    assert parse_versions(HEADER + row(book))[0].book == book


@pytest.mark.parametrize(
    "book",
    ["school:", "school:cs1@1", "school:CS1", "school:CS1@0", "school:CS1@1x", "school: CS1@1", "schoolCS1@1", "book4"],
)
def test_a_malformed_school_id_or_unknown_book_is_refused(book):
    with pytest.raises(VersionError, match="unknown book"):
        parse_versions(HEADER + row(book))


def test_the_three_books_parse_and_render_byte_identically():
    text = HEADER + "".join(row(book) for book in BOOKS)
    assert render(parse_versions(text)) == text


def test_each_school_version_has_its_own_order_like_any_book():
    rows = row("school:CS1@1") + row("school:CS1@2", "2", "2026-11-09") + row("school:DB1@1")
    assert [r.book for r in parse_versions(HEADER + rows)] == ["school:CS1@1", "school:CS1@2", "school:DB1@1"]
