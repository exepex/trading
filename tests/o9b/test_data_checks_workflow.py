"""O9b's data-checks.yml: daily, and on pushes that change the data tests or the store's code, never on receipt
pushes. Every job pushes receipts many times an hour, and GitHub keeps one pending run per concurrency group,
cancelling the rest (16 runs recorded as lost by O10's watcher on 23 Oct 2026)."""

import yaml

from fno.config import ROOT

WORKFLOW = ROOT / ".github" / "workflows" / "data-checks.yml"


def test_data_checks_runs_daily_and_on_test_or_store_changes_never_on_receipts():
    on = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))[True]  # YAML reads the key `on` as True
    assert on["schedule"] and "workflow_dispatch" in on
    paths = on["push"]["paths"]
    assert {"tests/**", "fno/storage/**"} <= set(paths)
    assert not [p for p in paths if p.startswith("receipts")]
