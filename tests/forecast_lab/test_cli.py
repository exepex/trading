"""FL1-1: `python -m fno lab close` prints the run's lines and exits 1 only when the report was not posted (O1's
`Alerted` then alerts it once; the command never alerts its own failure)."""

from argparse import ArgumentParser, Namespace
from datetime import date

import pytest

from fno.cli import main
from fno.forecast_lab.cli import add_lab_parser, cmd_lab
from fno.forecast_lab.lab_close import LabResult

DAY = date(2026, 10, 21)


class Lab:
    def __init__(self, result: LabResult):
        self.result, self.days = result, []

    def run(self, day):
        self.days.append(day)
        return self.result


@pytest.mark.parametrize(("result", "code"), [(LabResult(["posted"]), 0), (LabResult(["a", "b"], failed=True), 1)])
def test_the_exit_code_follows_the_post(monkeypatch, result, code):
    lab = Lab(result)
    monkeypatch.setattr("fno.forecast_lab.wiring.build_lab_close", lambda: lab)
    printed = []
    assert cmd_lab(Namespace(action="close", day=DAY), out=printed.append) == code
    assert printed == result.lines and lab.days == [DAY]


def test_the_parser_reads_the_day_and_runs_the_command():
    parser = ArgumentParser()
    add_lab_parser(parser.add_subparsers())
    args = parser.parse_args(["lab", "close", "--day", "2026-10-21"])
    assert args.func is cmd_lab and args.day == DAY


def test_the_app_runs_the_command(monkeypatch, capsys):
    monkeypatch.setattr("fno.forecast_lab.wiring.build_lab_close", lambda: Lab(LabResult(["posted"])))
    assert main(["lab", "close", "--day", "2026-10-21"]) == 0 and capsys.readouterr().out == "posted\n"
