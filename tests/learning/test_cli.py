"""LR1's command: a dry run prints and writes nothing; --post writes once and refuses a different second report."""

from types import SimpleNamespace

from fno.learning import cli
from fno.learning.report import PostMortemRecords, Report

from .fakes import SATURDAY


def _wiring(tmp_path, text):
    builder = SimpleNamespace(build=lambda week: Report(text, {"week": str(week)}))
    return SimpleNamespace(build_builder=lambda: builder, week_of=lambda d: d,
                           build_records=lambda: PostMortemRecords(tmp_path))  # fmt: skip


def test_dry_run_writes_nothing(tmp_path, capsys):
    assert cli._weekly(_wiring(tmp_path, "lines\n"), SATURDAY, post=False) == 0
    assert capsys.readouterr().out == "lines\n" and not any(tmp_path.iterdir())


def test_post_writes_once_and_refuses_a_different_report(tmp_path, capsys):
    assert cli._weekly(_wiring(tmp_path, "lines\n"), SATURDAY, post=True) == 0
    assert cli._weekly(_wiring(tmp_path, "lines\n"), SATURDAY, post=True) == 0
    assert "already written" in capsys.readouterr().out
    assert cli._weekly(_wiring(tmp_path, "other\n"), SATURDAY, post=True) == 1
    assert "a different report is already written" in capsys.readouterr().out
