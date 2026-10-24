"""FL1-1 and FL1-1d: `python -m fno lab open|close` builds that edition, prints the run's lines and exits 1 only when
the report was not posted."""

from argparse import ArgumentParser, Namespace
from datetime import date

import pytest

from fno.cli import main
from fno.forecast_lab.cli import add_lab_parser, cmd_lab
from fno.forecast_lab.edition_run import LabResult

DAY = date(2026, 10, 21)


class Lab:
    def __init__(self, result: LabResult):
        self.result, self.days = result, []

    def run(self, day):
        self.days.append(day)
        return self.result


@pytest.mark.parametrize(("result", "code"), [(LabResult(["posted"]), 0), (LabResult(["a", "b"], failed=True), 1)])
@pytest.mark.parametrize(("action", "edition"), [("open", "morning"), ("close", "evening")])
def test_each_action_builds_its_edition_and_the_exit_code_follows_the_post(monkeypatch, result, code, action, edition):
    lab, built = Lab(result), []
    monkeypatch.setattr("fno.forecast_lab.wiring.build_edition", lambda e: built.append(e) or lab)
    printed = []
    assert cmd_lab(Namespace(action=action, day=DAY), out=printed.append) == code
    assert printed == result.lines and lab.days == [DAY] and built == [edition]


def test_the_parser_reads_the_day_and_runs_the_command():
    parser = ArgumentParser()
    add_lab_parser(parser.add_subparsers())
    args = parser.parse_args(["lab", "close", "--day", "2026-10-21"])
    assert args.func is cmd_lab and args.day == DAY


def test_the_app_runs_the_command(monkeypatch, capsys):
    monkeypatch.setattr("fno.forecast_lab.wiring.build_edition", lambda edition: Lab(LabResult(["posted"])))
    assert main(["lab", "close", "--day", "2026-10-21"]) == 0 and capsys.readouterr().out == "posted\n"
