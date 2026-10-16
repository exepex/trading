"""GitHub's side of the kick (story A19, scope 7): how many news-capture runs are queued or in progress, the
completed run from the `workflow_run` event, and the dispatch. REST calls with the job's own `GITHUB_TOKEN`; the
token is sent only to api.github.com and never printed."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

import requests

from .kick import CompletedRun

API = "https://api.github.com/repos/{repository}"
WORKFLOW_FILE = "news-capture.yml"
ACTIVE_STATUSES = ("queued", "in_progress", "waiting", "pending", "requested")
RAN = ("success", "failure")
TIMEOUT_SECONDS = 30


class GitHubError(RuntimeError):
    pass


class WorkflowRuns(ABC):
    @abstractmethod
    def active_count(self) -> int: ...

    @abstractmethod
    def completed(self, event: dict) -> CompletedRun: ...

    @abstractmethod
    def dispatch(self) -> None: ...


class GitHubWorkflowRuns(WorkflowRuns):
    def __init__(self, repository: str, token: str, ref: str = "main", session: requests.Session | None = None):
        self.base, self.ref = API.format(repository=repository), ref
        self.session = session or requests.Session()
        self.headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

    def active_count(self) -> int:
        total = 0
        for status in ACTIVE_STATUSES:
            body = self._get(f"/actions/workflows/{WORKFLOW_FILE}/runs", {"status": status, "per_page": 1})
            total += int(body.get("total_count", 0))
        return total

    def completed(self, event: dict) -> CompletedRun:
        run = event["workflow_run"]
        jobs = self._get(f"/actions/runs/{run['id']}/jobs", {"per_page": 100}).get("jobs", [])
        steps_ran = any(step.get("conclusion") in RAN for job in jobs for step in job.get("steps") or [])
        return CompletedRun(run["conclusion"], _time(run["run_started_at"]), _time(run["updated_at"]), steps_ran,
                            run["html_url"])  # fmt: skip

    def dispatch(self) -> None:
        url = f"{self.base}/actions/workflows/{WORKFLOW_FILE}/dispatches"
        response = self._call("post", url, json={"ref": self.ref})
        if response.status_code != 204:
            raise GitHubError(f"dispatch refused (HTTP {response.status_code})")

    def _get(self, path: str, params: dict) -> dict:
        response = self._call("get", self.base + path, params=params)
        if response.status_code != 200:
            raise GitHubError(f"GitHub answered HTTP {response.status_code} for {path.split('?')[0]}")
        return response.json()

    def _call(self, method: str, url: str, **kwargs):
        try:
            return self.session.request(method, url, headers=self.headers, timeout=TIMEOUT_SECONDS, **kwargs)
        except requests.RequestException as exc:
            raise GitHubError(f"GitHub did not answer ({type(exc).__name__})") from exc


def read_event(path: str | None) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else {}


def _time(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00"))
