"""Story A19: every wiring function builds with fake settings (the self-review found no test imported wiring.py, so a
missing dependency would only show in the first live run)."""

from fno.news import wiring
from fno.news.committer import NewsCommitter
from fno.news.github_runs import GitHubWorkflowRuns

FAKE_ENV = {"GITHUB_REPOSITORY": "exepex/trading", "GITHUB_TOKEN": "t", "GITHUB_RUN_ID": "7",
            "GITHUB_SERVER_URL": "https://github.com"}  # fmt: skip


def test_every_part_builds(monkeypatch):
    monkeypatch.delenv("FNO_SLACK_BOT_TOKEN", raising=False)
    settings = wiring.build_settings()
    assert len(wiring.build_sources(settings)) == len(settings.active_feeds())
    assert wiring.build_window(settings).is_open is not None
    assert wiring.build_stale_rule() is not None
    assert isinstance(wiring.build_committer(), NewsCommitter)
    episodes = wiring.build_episodes(env=FAKE_ENV)
    assert episodes.log.run_url == "https://github.com/exepex/trading/actions/runs/7"
    assert isinstance(wiring.build_workflow_runs(FAKE_ENV), GitHubWorkflowRuns)
    assert wiring.run_url({}) == "local run"
