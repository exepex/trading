"""Story P6 criterion 4 (orchestrator, 13 Oct 2026: the publish runs in GitHub Actions): after publishing, the run reads
back what the store holds with the publisher's role and checks every page's SHA-256 against the records it built,
printing only counts and hashes; a second run of the same day adds no rows; a read-back that differs alerts."""

from pathlib import Path

import yaml

from fno.market_read_models.local_publisher import LocalFolderPublisher

from .test_market_contract_and_run import DAY, Rows, example_rows, run

WORKFLOW = Path(__file__).parents[2] / ".github" / "workflows" / "market-publish.yml"


def test_the_run_reads_back_every_page_and_prints_only_counts_and_hashes(tmp_path):
    market, alerts, _ = run(tmp_path, Rows(example_rows()))
    code, lines = market.run(DAY)
    assert code == 0 and alerts.sent == [] and lines[0].endswith("(1277 rows added)")
    assert lines[1].startswith("read back 1277 pages of nse-2026-10-12-") and lines[1].endswith("the built records")
    assert len(lines) == 2 + 12  # one line per block
    assert any(line.startswith("    chain_rows 21 pages, SHA-256 of their hashes ") for line in lines)
    assert all(len(line.split()[-1]) == 64 for line in lines[2:])  # counts and hashes only


def test_a_second_run_of_the_same_day_adds_no_rows(tmp_path):
    market, _, _ = run(tmp_path, Rows(example_rows()))
    first, again = market.run(DAY), market.run(DAY)
    assert again[0] == 0 and again[1][0].endswith("(0 rows added)") and again[1][1:] == first[1][1:]


class LosesAPage(LocalFolderPublisher):
    def stored(self, publication_id):
        return {k: v for k, v in super().stored(publication_id).items() if k != "overview_sectors"}


def test_a_read_back_that_differs_from_the_built_records_fails_and_alerts(tmp_path):
    market, alerts, _ = run(tmp_path, Rows(example_rows()))
    market.publisher = LosesAPage(tmp_path)
    code, lines = market.run(DAY)
    assert code == 1 and "NOT published (read-back)" in alerts.sent[0] and "overview_sectors" in alerts.sent[0]


def test_the_workflow_publishes_the_previous_session_daily_or_a_given_day_and_never_prints_the_url():
    text = WORKFLOW.read_text()
    flow = yaml.safe_load(text)
    triggers = flow[True]  # YAML 1.1 reads the key "on" as True
    assert triggers["workflow_dispatch"]["inputs"]["day"]["required"] is False
    assert triggers["workflow_dispatch"]["inputs"]["check_only"]["type"] == "boolean"
    assert [s["cron"] for s in triggers["schedule"]] == ["40 1 * * *"]  # 07:10 IST, before 07:30 (Actions starts late)
    job = flow["jobs"]["publish"]
    assert job["env"]["FNO_DB_URL"] == "${{ secrets.FNO_DB_URL }}"
    steps = " ".join(str(step.get("run", "")) for step in job["steps"])
    assert "python -m fno market daily" in steps and "FNO_DB_URL" not in steps  # never echoed or pasted
    check, archive = (
        next(s for s in job["steps"] if command in str(s.get("run"))) for command in ("db-check", "daily")
    )
    assert "if" not in check and archive["if"] == "${{ !inputs.check_only }}"  # the check always runs first
    assert any("failure()" in str(step.get("if", "")) for step in job["steps"])  # one line to #fno-desk
