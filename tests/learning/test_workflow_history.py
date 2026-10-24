"""Story LR1, fetch-depth fix (orchestrator, 24 Oct 2026; found by the v4 freeze builder's self-review): the weekly job
runs G8's v4 report and commits it. After protocol v4's freeze that report checks the record's protocol commit in the
git history, which a shallow checkout lacks, so the job checks out the full history."""

from pathlib import Path

import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / ".github" / "workflows" / "postmortem-weekly.yml"


def test_the_weekly_job_checks_out_the_full_history_before_g8s_report():
    steps = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))["jobs"]["postmortem"]["steps"]
    checkout = steps[0]
    assert checkout["uses"].startswith("actions/checkout@") and checkout["with"]["fetch-depth"] == 0
    report = next(i for i, s in enumerate(steps) if "forecast-v4-scores report" in s.get("run", ""))
    assert report > 0
