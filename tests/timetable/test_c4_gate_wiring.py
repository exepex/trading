"""Judge 82 addendum 2 follow-ups (story E3 with C4 merged): the daily run is wired with `RecordedC4Pass` (an
always-pass gate swapped in would otherwise go unnoticed), and C4's own report, `ValidityReport.record()`, read
through that gate fills only when every check passed."""

from fno.checks.validity import ValidityReport
from fno.checks.validity_proposal import CheckResult
from fno.config import load_app_config
from fno.desk.daily_wiring import build_daily_run
from fno.desk.recorded_c4 import RecordedC4Pass


def test_the_daily_run_is_wired_with_the_recorded_c4_pass(tmp_path):
    run = build_daily_run(load_app_config(), orders=None, exit_rules=None, root=tmp_path)
    assert type(run.steps.validity) is RecordedC4Pass


def report(*checks) -> dict:
    return ValidityReport("book1_rules", "sc-a-v1:2026-11-24", "playbook", tuple(checks)).record()


def test_c4_s_real_report_passes_the_gate_only_when_every_check_passed(committed_run):
    passed = report(CheckResult("max_loss", True, "", {"max_loss_rs": 5000.0}), CheckResult("leg_price", True, ""))
    failed = report(CheckResult("max_loss", True, ""), CheckResult("leg_price", False, "25000 CE 152.0 != 150.5"))
    decision, order = committed_run(passed)
    assert RecordedC4Pass().problems(decision, order) == []
    decision, order = committed_run(failed, "b")
    assert RecordedC4Pass().problems(decision, order) == [
        "sc-a-v1_2026-11-24.json: C4 failed: leg_price"]  # fmt: skip
    empty, order = committed_run(report(), "c")  # C4 ran no check: not a completed pass
    assert "no completed C4 pass recorded" in RecordedC4Pass().problems(empty, order)[0]
