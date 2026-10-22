"""The version registry's command line takes a school driver version as a book (story MS-P1h, judge 480 minor c)."""

import argparse

import pytest

from fno.books.versions_cli import add_versions_parser


def parse(*args: str):
    parser = argparse.ArgumentParser()
    add_versions_parser(parser.add_subparsers(dest="cmd", required=True))
    return parser.parse_args(["versions", "register", *args, "--starts-on", "2026-11-02", "--components", "{}",
                              "--reason", "r"])  # fmt: skip


@pytest.mark.parametrize("book", ["book1_rules", "book2_hybrid", "book3_ai", "school:CS1@1", "school:N0@3"])
def test_a_book_or_a_school_driver_version_is_accepted(book):
    assert parse(book, "v1").book == book


@pytest.mark.parametrize("book", ["school:cs1@1", "school:CS1", "school:", "book4", "school:CS1@0"])
def test_anything_else_is_refused_by_the_command_line(book, capsys):
    with pytest.raises(SystemExit):
        parse(book, "v1")
    assert "or a school:<driver code>@<version>" in capsys.readouterr().err
