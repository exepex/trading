"""Composition root of story A19: settings, feeds, the Drive store, O10's error log, alerts, the calendar, the
committer and GitHub's runs are wired here and nowhere else."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import UTC, datetime

from ..composition import build_alert_sender
from ..config import load_app_config
from ..http_pacing import PacedSession
from ..storage.data_wiring import DATA_AREA, RECEIPTS_FOLDER, build_data_store, build_drive_cache, receipt_folder
from ..storage.wiring import REPOSITORY, build_session_calendar
from .committer import NewsCommitter
from .episodes import Episodes
from .error_log import CaptureEpisodeLog
from .fetch import RssFeedSource
from .github_runs import GitHubWorkflowRuns
from .names import WRITER
from .settings import NewsSettings, news_settings
from .stale import StaleRule
from .store import NewsStore
from .times import TIME_FORMATS
from .window import PollingWindow

RUN_URL = "{server}/{repository}/actions/runs/{run_id}"
LOCAL_RUN = "local run"
NO_GITHUB = "GITHUB_REPOSITORY and GITHUB_TOKEN are needed to read or start news-capture runs"


def now_utc() -> datetime:
    return datetime.now(UTC)


def build_settings(env=os.environ) -> NewsSettings:
    return news_settings(load_app_config(), frozenset(TIME_FORMATS))


def build_sources(settings: NewsSettings, clock: Callable[[], datetime] = now_utc) -> list[RssFeedSource]:
    session = PacedSession()
    return [RssFeedSource(feed, clock, session) for feed in settings.active_feeds()]


def build_window(settings: NewsSettings) -> PollingWindow:
    return PollingWindow(settings.window)


def build_store(run_id: str | None = None) -> NewsStore:
    data = build_data_store(WRITER, run_id)
    return NewsStore(data, receipt_folder(), build_drive_cache())


def build_episodes(clock: Callable[[], datetime] = now_utc, env=os.environ) -> Episodes:
    from ..health.capture_errors import CaptureError  # story O10's one format
    from ..health.wiring import build_capture_error_log

    log = CaptureEpisodeLog(build_capture_error_log(), CaptureError, run_url(env))
    return Episodes(log, build_alert_sender(), clock)


def build_stale_rule() -> StaleRule:
    return StaleRule(build_session_calendar())


def build_committer() -> NewsCommitter:
    from ..health.capture_errors import CAPTURE_ERRORS_FILE

    folder = REPOSITORY / RECEIPTS_FOLDER / DATA_AREA / "news"
    return NewsCommitter(REPOSITORY, folder, CAPTURE_ERRORS_FILE)


def build_workflow_runs(env=os.environ) -> GitHubWorkflowRuns:
    repository, token = env.get("GITHUB_REPOSITORY"), env.get("GITHUB_TOKEN")
    if not repository or not token:
        raise RuntimeError(NO_GITHUB)
    return GitHubWorkflowRuns(repository, token)


def run_url(env=os.environ) -> str:
    if not env.get("GITHUB_RUN_ID"):
        return LOCAL_RUN
    return RUN_URL.format(server=env.get("GITHUB_SERVER_URL", "https://github.com"),
                          repository=env.get("GITHUB_REPOSITORY", ""), run_id=env["GITHUB_RUN_ID"])  # fmt: skip
