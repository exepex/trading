"""`python -m fno desk ...`: the one parser of the paper desk's commands (judge 73: one parser, each story adds its
command here, never a second `desk` parser). Each command sets its own handler on its own subparser. Never orders."""

from __future__ import annotations

from ..scorecard.cli import add_scorecard_command
from .pack_cli import add_pack_command

COMMANDS = (add_pack_command, add_scorecard_command)  # stories E2 and E6


def add_desk_parser(subparsers) -> None:
    desk = subparsers.add_parser(
        "desk", help="the paper desk's commands: daily packs, scorecards and pause rules (never orders)"
    )
    actions = desk.add_subparsers(dest="desk_cmd", required=True)
    for add_command in COMMANDS:
        add_command(actions)
