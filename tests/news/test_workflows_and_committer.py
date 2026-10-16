"""Story A19 criterion 13 (the two workflows as written) and the committer's paths."""

import subprocess

import yaml

from fno.config import ROOT
from fno.news.committer import NewsCommitter

FOLDER = ROOT / ".github" / "workflows"


def load(name):
    flow = yaml.safe_load((FOLDER / name).read_text(encoding="utf-8"))
    return flow, flow[True]  # YAML 1.1 reads the key `on` as True


def steps(flow):
    [job] = flow["jobs"].values()
    return job, {step.get("name", step.get("uses", step.get("run"))): step for step in job["steps"]}


def test_news_capture_keeps_one_poller_ends_before_its_limit_and_chains():
    flow, on = load("news-capture.yml")
    assert list(on) == ["workflow_dispatch"]  # started only by itself or the kick
    assert flow["concurrency"] == {"group": "news-capture", "cancel-in-progress": False}
    assert flow["permissions"] == {"contents": "write", "actions": "write"}
    job, named = steps(flow)
    assert job["timeout-minutes"] == 355
    assert named["Poll the feeds"]["run"] == "python -m fno news run --max-minutes 340"
    assert named["Poll the feeds"]["id"] == "loop"
    successor = named["Start the successor"]
    assert successor["if"] == "${{ always() && steps.loop.outputs.successor == 'true' }}"
    assert successor["run"] == "gh workflow run news-capture.yml --ref main"
    assert named["Probe the feeds from this runner (status and counts only)"]["continue-on-error"] is True
    assert named["Alert #fno-desk when the job itself failed"]["if"] == "${{ failure() }}"


def test_secrets_reach_the_jobs_only_through_env():
    for name in ("news-capture.yml", "news-capture-kick.yml"):
        flow, _ = load(name)
        job, named = steps(flow)
        assert all("secrets." not in str(step.get("run", "")) for step in named.values())
        assert all(
            str(value).startswith("${{ secrets.") or "github.token" in str(value) for value in job["env"].values()
        )


def test_the_kick_runs_on_crons_inside_the_window_and_on_completed_runs():
    flow, on = load("news-capture-kick.yml")
    assert on["workflow_run"] == {"workflows": ["news-capture"], "types": ["completed"]}
    assert "concurrency" not in flow  # a kick is never replaced in a queue (O10: a cancelled kick is a failure)
    for cron in on["schedule"]:
        minute, hour = (int(x) for x in cron["cron"].split()[:2])
        ist_minutes = (hour * 60 + minute + 330) % 1440
        assert 7 * 60 <= ist_minutes < 23 * 60  # inside the owner's 07:00-23:00 IST window
    assert len(on["schedule"]) == 6
    assert flow["permissions"] == {"contents": "write", "actions": "write"}
    _, named = steps(flow)
    assert named["Start news-capture if none is alive"]["run"] == "python -m fno news kick"


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


def test_committer_adds_only_news_receipts_and_the_error_log(tmp_path):
    repo = tmp_path
    git(repo, "init", "-q")
    for path in (
        "receipts/data/news/parts/a.sha256",
        "receipts/data/intraday/b.sha256",
        "research/ops/capture_errors.csv",
    ):
        (repo / path).parent.mkdir(parents=True, exist_ok=True)
        (repo / path).write_text("x\n")
    committer = NewsCommitter(repo, repo / "receipts" / "data" / "news", "research/ops/capture_errors.csv")
    assert committer._paths() == ["receipts/data/news", "research/ops/capture_errors.csv"]
    assert committer.pending() == ["receipts/data/news/parts/a.sha256", "research/ops/capture_errors.csv"]
    assert committer.owns("research/ops/capture_errors.csv") and not committer.owns("receipts/data/intraday/b.sha256")


def test_committer_skips_a_missing_error_log(tmp_path):
    git(tmp_path, "init", "-q")
    (tmp_path / "receipts/data/news").mkdir(parents=True)
    (tmp_path / "receipts/data/news/a.sha256").write_text("x\n")
    committer = NewsCommitter(tmp_path, tmp_path / "receipts" / "data" / "news", "research/ops/capture_errors.csv")
    assert committer._paths() == ["receipts/data/news"]
