"""The rates workflow (story A21, criterion 14): twice a day, watched by O10, only the Drive and #fno-desk secrets."""

import re
from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "rates-daily.yml"
WATCHER = WORKFLOW.parent / "capture-watch.yml"
ALLOWED = {"FNO_GDRIVE_FOLDER_ID", "FNO_GDRIVE_OAUTH_CLIENT_ID", "FNO_GDRIVE_OAUTH_CLIENT_SECRET",
           "FNO_GDRIVE_OAUTH_REFRESH_TOKEN", "FNO_SLACK_BOT_TOKEN"}  # fmt: skip


def test_two_daily_runs_watched_by_o10():
    workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    on = workflow.get("on", workflow.get(True))
    assert [c["cron"] for c in on["schedule"]] == ["10 3 * * *", "10 13 * * *"]  # 08:40 and 18:40 IST
    watched = yaml.safe_load(WATCHER.read_text(encoding="utf-8"))
    assert workflow["name"] in watched.get("on", watched.get(True))["workflow_run"]["workflows"]


def test_only_the_drive_and_desk_secrets_and_no_market_brief_variable():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert set(re.findall(r"secrets\.([A-Z_]+)", text)) == ALLOWED
    assert "SLACK_WEBHOOK" not in text and "market-brief" not in text


def test_it_commits_the_receipts_and_the_error_rows_in_one_step_and_fails_if_the_push_fails():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert re.findall(r"git add (receipts research/ops/capture_errors.csv)", text) == [
        "receipts research/ops/capture_errors.csv"]  # fmt: skip
    commit = text[text.index("Commit the receipts") :]
    assert "exit 1" in commit and "if: ${{ always() }}" in commit
