"""Story O8 test fakes: a planted repository folder, a calendar, and push receipts given directly. The fake history
names a "commit" after the file (or the row) it first added, so each push time is planted per file or per row; a
commit's own date never exists here, as the check never reads one."""

from __future__ import annotations

import json
from datetime import date, datetime, time
from pathlib import Path

from fno.ai.receipts import PushReceipts, ReceiptUnknown
from fno.health.evidence import Evidence
from fno.models import IST
from fno.research_data.calendar import CsvSessionCalendar

SOURCE = "https://nsearchives.nseindia.com/content/circulars/test.pdf"
# 20 Oct 2026 a holiday, 21 Oct a muhurat-only session
CALENDAR = CsvSessionCalendar(
    f"date,kind,description,source_url\n2026-10-20,holiday,test holiday,{SOURCE}\n"
    f"2026-10-21,muhurat,test muhurat,{SOURCE}\n"
)
DAY = date(2026, 10, 15)  # a regular Thursday session


def ist(day: date, hour: int, minute: int = 0, second: int = 0) -> datetime:
    return datetime.combine(day, time(hour, minute, second), IST)


class FakeHistory:
    def first_commit_adding(self, path: str) -> str | None:
        return f"file:{path}"

    def first_commit_adding_text(self, path: str, text: str, since: date) -> str | None:
        return f"row:{path}:{text}"


class FakeReceipts(PushReceipts):
    def __init__(self):
        self.pushes: dict[str, datetime] = {}

    def received_at(self, commit: str) -> datetime:
        if commit not in self.pushes:
            raise ReceiptUnknown(f"no push of {commit}")
        return self.pushes[commit]

    def file(self, path: str, at: datetime) -> None:
        self.pushes[f"file:{path}"] = at

    def row(self, path: str, text: str, at: datetime) -> None:
        self.pushes[f"row:{path}:{text}"] = at


class Repo:
    """A planted repository: files written under `root`, push times planted in `receipts`."""

    def __init__(self, root: Path):
        self.root, self.receipts = Path(root), FakeReceipts()
        self.evidence = Evidence(self.root, FakeHistory(), self.receipts)

    def write(self, path: str, text: str) -> str:
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding="utf-8")
        return path

    def write_json(self, path: str, body: dict) -> str:
        return self.write(path, json.dumps(body))
