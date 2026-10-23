"""Story DR1's first dataset: A4h's close read (`fno/close_read/`), certified from the NSE index-list answers A4h
already saves (`closes/<yyyy>/<mm>/<day>.first.raw.json` and `.recheck.raw.json`): the shadow phase, A4h's code
unchanged. Those files are A4h's canonical JSON of the parsed answer (sorted keys), not NSE's own byte stream, so
integrity means "matches its receipt". A4h's own rules decide what a valid answer is (`read_answer`: NSE's stamp of
that day at or after 15:30, every index with a last and an open); this adds the sanity check and, for the certified
record, NSE's official index-close file within A4h's tolerance. Lines name indices and differences, never a level.

Which passing read is the record (the A4h builder's objection, 23 Oct): A4h rechecks at 16:00 because NSE's list can
still change after 15:30, and both reads carry the same stamp (23 Oct: "23-Oct-2026 15:30" at 15:40 and at 16:00),
so the stamp cannot order them. A value that changes after the 15:30 close is NSE's correction, so the provisional
record is the latest passing read, with any difference named; it never blocks. The certified record is the read
closest to NSE's official file. The certifier never alerts: A4h's overdue rule already alerts a day the official file
does not confirm."""

from __future__ import annotations

import json
from datetime import date

from ..close_read.answer import Refused, difference, read_answer
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
SUPERSEDED = "the later read supersedes the earlier ({changes})"
OFFICIAL = "closest to NSE's official file {filename}, within {tolerance}"
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
        """Passing versions come in read order (first, then recheck)."""
        day = date.fromisoformat(session)
        checked = [n for n in INDICES if n.checked]
        values = [read_answer(json.loads(data), day).values for _, data in passing]
        if level == CERTIFIED:
            filename, official = self.official.closes(day)
            gaps = [max(abs(v[n.listed]["last"] - official[n.official]) for n in checked) for v in values]
            best = min(range(len(passing)), key=lambda i: (gaps[i], i))  # equal quality: the read A4h's record cites
            return Choice(passing[best][0], OFFICIAL.format(filename=filename, tolerance=TOLERANCE))
        changes = [f"{n.listed} {difference(values[0][n.listed]['last'], values[-1][n.listed]['last'])}"
                   for n in checked if values[0][n.listed] != values[-1][n.listed]]  # fmt: skip
        if changes:
            return Choice(passing[-1][0], SUPERSEDED.format(changes=", ".join(changes)))
        names = ", ".join(n.listed for n in checked)  # equal values: the first read, the one A4h's record cites
        return Choice(passing[0][0], AGREE.format(count=len(passing), names=names))

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
    """Positive values for every index; the 20% band only for the indices NSE's circuit bands cover (NIFTY 50 and NIFTY
    BANK): INDIA VIX can move more than 20% in a day around a shock, and its list value is never certified."""
    for index in INDICES:
        last, opened = values[index.listed]["last"], values[index.listed]["open"]
        if last <= 0 or opened <= 0:
            return CheckResult("sanity", False, f"{index.listed} is not positive")
        if index.checked and abs(last / opened - 1) > MAX_MOVE:
            return CheckResult("sanity", False, f"{index.listed} closed more than {MAX_MOVE:.0%} from its open")
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
