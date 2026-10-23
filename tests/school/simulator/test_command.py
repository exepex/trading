"""`python -m fno school practice run` (MS-SIM-d4)."""

import argparse
from datetime import date

import pytest

from fno.school.execution import practice_wiring
from fno.school.fakes import FakeSettlementSource
from fno.school.simulator import command
from fno.school.simulator.constants import PRACTICE_LABEL
from fno.school.simulator.practice.fleet import PracticeParts
from fno.school.simulator.spreads.recorded import Skipped
from tests.school.safety.law_builders import FixedMargin
from tests.school.simulator.practice import test_fleet as tf
from tests.school.simulator.source import builders as sb


def namespace(**kw) -> argparse.Namespace:
    base = {"first": sb.SESSION.replace(day=3), "last": sb.SESSION, "roads": ["NIFTY-M", "NIFTY-W"],
            "home": None, "config": None, "archive": False}  # fmt: skip
    return argparse.Namespace(**{**base, **kw})


def test_the_parser_registers_school_practice_run_with_its_options():
    top = argparse.ArgumentParser()
    commands = top.add_subparsers(dest="school_cmd")
    command.add_practice_parser(commands)
    args = top.parse_args(["practice", "run", "--from", "2024-03-04", "--to", "2024-03-08", "--roads", "NIFTY-M"])
    assert (args.first, args.last, args.roads) == (date(2024, 3, 4), date(2024, 3, 8), ["NIFTY-M"])
    assert args.func is command.cmd_practice_run


def test_an_unknown_road_is_refused_by_the_parser():
    top = argparse.ArgumentParser()
    command.add_practice_parser(top.add_subparsers(dest="c"))
    with pytest.raises(SystemExit):
        top.parse_args(["practice", "run", "--from", "2024-03-04", "--to", "2024-03-08", "--roads", "SENSEX"])


def test_a_refused_window_exits_2_names_the_road_and_builds_nothing(tmp_path, monkeypatch):
    def never(*args, **kwargs):
        raise AssertionError("the archive was built for a window that is refused")

    monkeypatch.setattr(command, "build_practice_parts", never)
    lines = []
    code = command.cmd_practice_run(namespace(roads=["FINNIFTY-M"], home=tmp_path), out=lines.append)
    assert code == command.REFUSED_EXIT == 2
    assert lines and all(text.startswith(PRACTICE_LABEL) for text in lines)
    assert "not_in_data_spend" in lines[0] and "FINNIFTY-M" in lines[0] and not list(tmp_path.iterdir())


def test_a_run_prints_only_labelled_lines_and_writes_under_the_given_home(tmp_path, monkeypatch):
    monkeypatch.setattr(practice_wiring, "build_settlement_source", lambda: FakeSettlementSource({}))
    parts = tf.parts()
    margin = lambda cfg: FixedMargin()  # noqa: E731

    class Runner(command.PracticeRunner):
        def __init__(self, parts, home):
            super().__init__(parts, home, margin_for=margin)

    monkeypatch.setattr(command, "PracticeRunner", Runner)
    monkeypatch.setattr(command, "build_practice_parts", lambda cfg, today, folder: (parts, Skipped()))
    lines = []
    assert command.cmd_practice_run(namespace(home=tmp_path), out=lines.append) == 0
    assert len(lines) > 10 and all(text.startswith(PRACTICE_LABEL) for text in lines)
    assert not any("left out:" in text for text in lines)
    assert isinstance(parts, PracticeParts) and any(tmp_path.rglob("*.jsonl.gz"))


def test_school_practice_run_is_registered_in_the_main_command_and_refuses_a_window_by_name(capsys):
    from fno import cli

    code = cli.main(
        ["school", "practice", "run", "--from", "2024-03-04", "--to", "2024-03-08", "--roads", "FINNIFTY-M"]
    )
    out = capsys.readouterr().out
    assert code == 2 and "not_in_data_spend" in out and out.startswith(PRACTICE_LABEL)


def test_the_first_line_of_a_report_says_local_only_not_archived():
    from fno.school.simulator.practice.render import NOT_ARCHIVED, render
    from fno.school.simulator.practice.report import PracticeReport

    lines = render(PracticeReport(sb.SESSION, sb.SESSION, ()))
    assert lines[0] == f"{PRACTICE_LABEL} | {NOT_ARCHIVED}" and "not archived" in lines[0]


def test_each_left_out_capture_is_named_in_the_output(monkeypatch, tmp_path):
    skipped = Skipped([("NIFTY-W", date(2026, 10, 13), "capture_missing")])
    monkeypatch.setattr(command, "build_practice_parts", lambda cfg, today, folder: (None, skipped))
    from fno.school.simulator.practice.report import PracticeReport

    empty = PracticeReport(sb.SESSION, sb.SESSION, ())
    monkeypatch.setattr(command, "PracticeRunner", lambda parts, home: type("R", (), {"run": lambda s, w: empty})())
    lines = []
    command.cmd_practice_run(namespace(home=tmp_path), out=lines.append)
    assert any(text.endswith("left out: NIFTY-W capture_missing: 2026-10-13") for text in lines)
