"""An alert sender that tells its GitHub Actions step it has spoken (stories O8b and O8c, judges 240 and 246).

A workflow's own "the job failed" line must stay quiet when the step already posted its one line, and must speak when
the step failed without posting (an import crash, a sender that could not be built, an unexpected error). Wrapping the
step's sender records `posted=true` in the step's outputs (`$GITHUB_OUTPUT`) once Slack accepted a line; the workflow's
alert runs on `failure() && steps.<id>.outputs.posted != 'true'`. Outside Actions nothing is recorded."""

from __future__ import annotations

import os
from collections.abc import Mapping

from ..constants import ENV_GITHUB_OUTPUT
from .sender import SENT, AlertSender

POSTED = "posted=true\n"


class StepOutputAlerts(AlertSender):
    def __init__(self, inner: AlertSender, env: Mapping[str, str] = os.environ):
        self.inner, self.env = inner, env

    def send(self, text: str) -> str:
        outcome = self.inner.send(text)
        path = self.env.get(ENV_GITHUB_OUTPUT)
        if outcome == SENT and path:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write(POSTED)
        return outcome
