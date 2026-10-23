"""Story DR1's first dataset: A4h's close read (`fno/close_read/`), certified from the NSE index-list answers A4h
already saves (`closes/<yyyy>/<mm>/<day>.first.raw.json` and `.recheck.raw.json`): the shadow phase, A4h's code
unchanged. A4h's own rules decide what a valid answer is (`read_answer`: NSE's stamp of that day at or after 15:30,
every index with a last and an open); this adds the sanity check and, for the certified record, NSE's official
index-close file within A4h's tolerance. Lines name indices and differences, never a level (judge 440 SF1)."""

from __future__ import annotations

import json
from datetime import date

from ..close_read.answer import Refused, read_answer
from ..close_read.constants import INDICES, READ, RECHECK, TOLERANCE
from ..close_read.official import OfficialCloses
from ..close_read.records import raw_path, record_path
from ..storage.raw_store import RawFileStore
from .constants import CERTIFIED, DATA_AREA
from .models import CheckResult, Record, StagedVersion
from .rules import Choice, DatasetRules

DATASET = "closes"
MAX_MOVE = 0.20  # NSE's widest index circuit band: a close more than 20% from its open is not a real close
AGREE = "{count} passing version(s) agree on {names}"
DISAGREE = "the passing versions disagree on {names}; the certified record decides against NSE's official file"
OFFICIAL = "agrees with NSE's official file {filename} within {tolerance}"
MATCHES, DIFFERS, NO_A4H = "matches A4h's record", "differs from A4h's record (it cites {which})", "A4h wrote no record"


def a4h_raw_paths(session: str) -> list[str]:
    day = date.fromisoformat(session)
    return [f"{DATA_AREA}/{raw_path(day, which)}" for which in (READ, RECHECK)]


class ClosesRules(DatasetRules):
    name, version = DATASET, "1"

    def __init__(self, official: OfficialCloses):
        self.official = official

    def checks(self, session: str, level: str, data: bytes) -> list[CheckResult]:
        day = date.fromisoformat(session)
        try:
            payload = json.loads(data)
        except ValueError:
            return [CheckResult("layout", False, "not JSON")]
        try:
            values = read_answer(payload, day).values
        except Refused as refused:
            return [CheckResult("layout", True), CheckResult("stamp and indices", False, str(refused))]
        results = [CheckResult("layout", True), CheckResult("stamp and indices", True), _sanity(values)]
        if level == CERTIFIED:
            results.append(self._agreement(day, values))
        return results

    def choose(self, session: str, level: str, passing: list[tuple[StagedVersion, bytes]]) -> Choice:
        day = date.fromisoformat(session)
        checked = [n.listed for n in INDICES if n.checked]
        values = [read_answer(json.loads(data), day).values for _, data in passing]
        differing = [name for name in checked if len({tuple(sorted(v[name].items())) for v in values}) > 1]
        if level == CERTIFIED:  # every passing version agrees with the official file: any of them is the record
            filename, _ = self.official.closes(day)
            return Choice(passing[0][0], OFFICIAL.format(filename=filename, tolerance=TOLERANCE))
        if differing:
            return Choice(None, DISAGREE.format(names=", ".join(differing)))
        return Choice(passing[0][0], AGREE.format(count=len(passing), names=", ".join(checked)))

    def _agreement(self, day: date, values: dict) -> CheckResult:
        try:
            found = self.official.closes(day)
        except Exception as failure:  # noqa: BLE001 - a damaged official file fails the check with its class only
            return CheckResult("official file", False, f"unreadable ({type(failure).__name__})")
        if found is None:
            return CheckResult("official file", False, "no official index-close file in Drive yet")
        filename, official = found
        for name in (n for n in INDICES if n.checked):
            close = official.get(name.official)
            if close is None:
                return CheckResult("official file", False, f"{name.listed} not in {filename}")
            gap = abs(values[name.listed]["last"] - close)
            if gap > TOLERANCE + 1e-9:
                return CheckResult("official file", False, f"{name.listed} differs by {gap:.2f}")
        return CheckResult("official file", True)


def _sanity(values: dict) -> CheckResult:
    for name in (n.listed for n in INDICES):
        last, opened = values[name]["last"], values[name]["open"]
        if last <= 0 or opened <= 0:
            return CheckResult("sanity", False, f"{name} is not positive")
        if abs(last / opened - 1) > MAX_MOVE:
            return CheckResult("sanity", False, f"{name} closed more than {MAX_MOVE:.0%} from its open")
    return CheckResult("sanity", True)


class A4hRecordComparison:
    """The shadow's comparison: does the certifier choose the raw answer A4h's own record cites?"""

    def __init__(self, drive: RawFileStore):
        self.drive = drive

    def __call__(self, session: str, record: Record) -> str:
        data = self.drive.get(f"{DATA_AREA}/{record_path(date.fromisoformat(session))}")
        if data is None:
            return NO_A4H
        document = json.loads(data)
        if document.get("raw_sha256") == record.chosen.sha256:
            return MATCHES
        return DIFFERS.format(which=document.get("read", "another read"))
