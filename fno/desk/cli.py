"""`python -m fno desk ...`: the one parser of the paper desk's commands (judge 73: one parser, each story adds its
command here, never a second `desk` parser). Each command sets its own handler on its own subparser. Never orders."""

from __future__ import annotations

from ..scorecard.cli import add_scorecard_command

COMMANDS = (add_scorecard_command,)  # story E6; E2 adds its `pack` command here


def add_desk_parser(subparsers) -> None:
    desk = subparsers.add_parser("desk", help="the paper desk's commands: scorecards and pause rules (never orders)")
    actions = desk.add_subparsers(dest="desk_cmd", required=True)
    for add_command in COMMANDS:
        add_command(actions)
