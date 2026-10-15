"""A scripted NSE for story A9b: each request gets the next answer (a status with headers, or an exception)."""

from datetime import date

import requests

import fno.filings.sources
import fno.storage.snapshot_source
import fno.vix_history.source  # noqa: F401 - imported for their NseArchiveSource subclasses
from fno.storage.raw_source import NseArchiveSource

DAY = date(2026, 10, 14)


def answer(status: int, content: bytes = b"", **headers) -> requests.Response:
    response = requests.Response()
    response.status_code, response._content = status, content
    response.headers.update({k.replace("_", "-"): v for k, v in headers.items()})
    return response


class ScriptedNse:
    """A session whose GET and HEAD return (or raise) the scripted answers in order."""

    def __init__(self, *answers):
        self.answers, self.requests = list(answers), []

    def _next(self, method: str, url: str, **kwargs):
        self.requests.append((method, url))
        found = self.answers.pop(0)
        if isinstance(found, Exception):
            raise found
        return found

    def get(self, url, **kwargs):
        return self._next("GET", url, **kwargs)

    def head(self, url, **kwargs):
        return self._next("HEAD", url, **kwargs)


def nse_source_classes() -> list[type[NseArchiveSource]]:
    """Every NseArchiveSource subclass in the package (they all share the policy)."""
    found, todo = [], [NseArchiveSource]
    while todo:
        for cls in todo.pop().__subclasses__():
            found.append(cls)
            todo.append(cls)
    return sorted(set(found), key=lambda c: c.__qualname__)


def a_path(cls: type[NseArchiveSource]) -> str:
    """A path the class can turn into a URL."""
    try:
        return cls.path_for(DAY)
    except (ValueError, KeyError, TypeError):
        return f"{cls.dataset}/2026/10/a_file_14102026.xml"


def source_with(cls: type[NseArchiveSource], session: ScriptedNse, waits: list, now=None) -> NseArchiveSource:
    clock = (lambda: now) if now else None
    return cls(session, sleep=waits.append, **({"clock": clock} if clock else {}))
