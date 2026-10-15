"""`python -m fno role-value report` (story F9a): the parser and a refusal printed, never a traceback."""

from fno.cli import main
from fno.role_value import cli


def test_a_refused_row_is_printed_with_exit_2_never_a_traceback(monkeypatch, capsys):
    class Report:
        def build(self, period):
            raise cli_refusal

    from fno.role_value.checks import RowRefused

    cli_refusal = RowRefused("book2_hybrid 2026-11-02 unit 'vol': the rotation schedules 'macro' for this day")
    monkeypatch.setattr("fno.role_value.wiring.build_role_value_report", lambda cfg: Report())
    code = main(["role-value", "report", "--book", "book2_hybrid", "--from", "2026-11-01", "--to", "2026-11-30",
                 "--common-start", "2026-12-02"])  # fmt: skip
    assert code == cli.EXIT_REFUSED
    assert "refused: book2_hybrid 2026-11-02 unit 'vol'" in capsys.readouterr().out
