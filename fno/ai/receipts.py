"""When a book's file reached the repository, by GitHub's clock (story F1's receipt time). `PushReceipts` is the
interface; `GitHubActivityReceipts` reads the repository's activity log (`GET /repos/{owner}/{repo}/activity`), where
GitHub records each push to `main` with its server timestamp and the commits before and after it. A commit's receipt is
the push whose `after` contains it and whose `before` does not. A commit's own date is set by whoever made it and is
never used. Anything unclear raises `ReceiptUnknown`, which the collector treats as late (fails closed)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from datetime import datetime
from urllib.parse import parse_qsl, urlsplit

import requests

from .history import RepoHistory

ACTIVITY_URL = "https://api.github.com/repos/{repository}/activity"
ACTIVITY_PARAMS = {"ref": "refs/heads/main", "time_period": "week", "per_page": 100}
ACTIVITY_HEADERS = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
MAX_PAGES, TIMEOUT_SECONDS = 10, 30
NO_COMMIT = "0" * 40
ACCESS_REFUSED = (401, 403)


class ReceiptUnknown(RuntimeError):
    """GitHub's push time for the commit could not be established; the message says why."""


class ReceiptAccessDenied(ReceiptUnknown):
    """GitHub refused to show the activity log (HTTP 401 or 403): an access problem, not "no push yet"."""


class PushReceipts(ABC):
    @abstractmethod
    def received_at(self, commit: str) -> datetime:
        """GitHub's time of the push that first brought `commit` to `main`, or ReceiptUnknown."""


class GitHubActivityReceipts(PushReceipts):
    def __init__(self, repository: str, token: str, history: RepoHistory, get: Callable | None = None):
        self._repository, self._token, self._history = repository, token, history
        self._get = get or requests.get
        self._pushes: list[dict] | None = None

    def received_at(self, commit: str) -> datetime:
        for push in self._activity():
            before, after = push.get("before") or NO_COMMIT, push.get("after") or ""
            new = before == NO_COMMIT or not self._history.is_ancestor(commit, before)
            if self._history.is_ancestor(commit, after) and new:
                return datetime.fromisoformat(push["timestamp"])
        raise ReceiptUnknown(f"no push of {commit[:10]} in GitHub's activity log of main")

    def _activity(self) -> list[dict]:
        if self._pushes is None:
            pushes, url, params = [], ACTIVITY_URL.format(repository=self._repository), dict(ACTIVITY_PARAMS)
            for _ in range(MAX_PAGES):
                response = self._page(url, params)
                pushes += response.json()
                following = response.links.get("next", {}).get("url")
                if not following:
                    break
                # GitHub's next link names the repository by numeric ID (`/repositories/<id>/`), which the cloud
                # sessions' GitHub proxy refuses (HTTP 403); the same page is asked by owner/name with its cursor
                params = {**ACTIVITY_PARAMS, **dict(parse_qsl(urlsplit(following).query))}
            self._pushes = sorted(pushes, key=lambda p: p["timestamp"])  # oldest first: the first push wins
        return self._pushes

    def _page(self, url: str, params: dict | None):
        headers = {**ACTIVITY_HEADERS, "Authorization": f"Bearer {self._token}"}
        try:
            response = self._get(url, params=params, headers=headers, timeout=TIMEOUT_SECONDS)
        except requests.RequestException as error:
            raise ReceiptUnknown(f"GitHub's activity log not reached ({type(error).__name__})") from None
        if response.status_code in ACCESS_REFUSED:
            raise ReceiptAccessDenied(f"access refused: HTTP {response.status_code} from GitHub's activity log")
        if not response.ok:
            raise ReceiptUnknown(f"HTTP {response.status_code} from GitHub's activity log")
        return response
