"""REH1j, J3's walk and J6: whether fno has a command is decided by fno's own parser, word by word, never by an error
text; `build_parser()` is the parser `main` parses with."""

import argparse

import pytest

from fno import cli
from fno.rehearsal.built_commands import is_built


@pytest.mark.parametrize(
    ("arguments", "built"),
    [
        (("margins", "stress-factor"), True),  # good: a full real path
        (("pricedist", "record", "--day", "2026-10-23", "--live"), True),  # the walk stops at the first option
        (("card", "daily", "--on", "2026-10-23", "--post"), True),
        (("margins", "stress-broker-check"), False),  # bad: a missing child under a real parent
        (("quotes", "no-such-part"), False),  # bad: under a group whose own handler dispatches its subcommands
        (("quotes", "record"), True),  # that group's handler serves its real subcommand
        (("margins",), False),  # boundary: a prefix of a real command has no handler
        (("no-such-command",), False),
        ((), False),  # empty: no command at all
    ],
)
def test_the_walk_over_fno_s_own_parser(arguments, built):
    assert is_built(arguments) is built


def test_every_command_fno_has_is_built_and_every_group_alone_is_not():
    leaves, groups = [], []

    def walk(parser: argparse.ArgumentParser, path: tuple[str, ...]) -> None:
        found = [a for a in parser._actions if isinstance(a, argparse._SubParsersAction)]
        if not found:
            leaves.append(path)
            return
        groups.append(path)
        for word, child in found[0].choices.items():
            walk(child, (*path, word))

    walk(cli.build_parser(), ())
    assert len(leaves) > 50 and all(is_built(path) for path in leaves)
    assert all(not is_built(path) for path in groups if path)  # each group needs one of its commands


def test_main_parses_with_build_parser(monkeypatch):
    seen = []

    class Recording(argparse.ArgumentParser):
        def parse_args(self, argv=None):
            seen.append(argv)
            return argparse.Namespace(func=lambda args: 7)

    monkeypatch.setattr(cli, "build_parser", lambda: Recording())
    assert cli.main(["anything"]) == 7 and seen == [["anything"]]
