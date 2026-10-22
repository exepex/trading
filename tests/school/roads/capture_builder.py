"""Plants recorded 3 pm captures (marker, sidecar, quote file) the way A4/A4c/A4f write them, with a knob for each fault
of story 3.5, for the roads and quality tests. Fixed values only: no live strike, price or capture."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone

from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.quotes.snapshot_rows import COLUMNS, snapshot_csv
from fno.research_data.calendar import CsvSessionCalendar
from fno.school.constants import ExpiryKind, RoadCode
from fno.school.contracts.roads import ROADS, ROADS_BY_CODE, DatedLot, Road
from fno.storage.raw_store import RawFileStore

IST = timezone(timedelta(hours=5, minutes=30))
SESSION = date(2026, 11, 2)  # a Monday
HOLIDAY = date(2026, 11, 3)
WEEKEND = date(2026, 11, 7)
SOURCE = "https://example.test/circular"
CALENDAR = CsvSessionCalendar(
    f"date,kind,description,source_url\n{HOLIDAY},holiday,test holiday,{SOURCE}\n"
    f"2026-11-08,muhurat,test muhurat evening,{SOURCE}\n"
)
MONTHLIES = (date(2026, 11, 24), date(2026, 12, 29))
WEEKLIES = (date(2026, 11, 10), date(2026, 11, 17))
SPOT, STEP, STRIKES = 1050.0, 100.0, tuple(700.0 + 100.0 * n for n in range(8))
LOT = DatedLot(30, "lots/fixture.csv")


class DictStore(RawFileStore):
    name = "dict store"

    def __init__(self):
        self.files: dict[str, bytes] = {}

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        self.files[path] = data


def expiries_of(road: Road) -> tuple[date, ...]:
    return WEEKLIES if road.expiry_kind is ExpiryKind.WEEKLY else MONTHLIES


def price(strike: float, kind: str, spot: float = SPOT) -> float:
    """A no-arbitrage mid: intrinsic plus a time value that fades from the money (every vertical inside its width)."""
    intrinsic = max(spot - strike, 0.0) if kind == "CE" else max(strike - spot, 0.0)
    return round(intrinsic + 30.0 * 0.9 ** (abs(strike - spot) / STEP), 2)


def chain_rows(snapshot_id: str, expiries: tuple[date, ...], spot: float = SPOT, spread: float = 1.0) -> list[dict]:
    rows = []
    for expiry in expiries:
        for strike in STRIKES:
            for kind in ("CE", "PE"):
                mid = price(strike, kind, spot)
                row = dict.fromkeys(COLUMNS, "")
                row.update(
                    snapshot_id=snapshot_id, expiry=expiry.isoformat(), strike=f"{strike:g}", type=kind,
                    bid=f"{mid - spread / 2:g}", ask=f"{mid + spread / 2:g}", last=f"{mid:g}", bid_qty="1000",
                    ask_qty="1000", spot=f"{spot:.2f}", valid="true", provider="groww",
                )  # fmt: skip
                rows.append(row)
    return rows


@dataclass
class Plant:
    """What to record for one road-session. The defaults are a good capture; each field plants one fault."""

    road: Road
    session: date = SESSION
    expiries: tuple[date, ...] | None = None  # in the quote file and the sidecar
    started: tuple[int, int] = (15, 2)
    complete: bool = True
    in_window: bool = True
    marker: str | None = "canonical"  # None: no marker file; "none": A4's marker for a day with no capture
    sidecar: bool = True
    quote_file: bool = True
    tamper: bool = False  # the quote file's bytes change after the sidecar recorded their SHA-256
    short_by: int = 0  # rows the file lacks against the sidecar's count
    change_rows: list = field(default_factory=list)  # callables (rows) -> None, to plant a bad price

    @property
    def snapshot_id(self) -> str:
        return f"{self.road.stem}_{self.session:%Y%m%d}_{self.started[0]:02d}{self.started[1]:02d}00"

    def write(self, stores: dict[str, RawFileStore] | RawFileStore) -> "Plant":
        store = stores[self.road.dataset] if isinstance(stores, dict) else stores
        expiries = self.expiries or expiries_of(self.road)
        rows = chain_rows(self.snapshot_id, expiries)
        for change in self.change_rows:
            change(rows)
        data = snapshot_csv(rows)
        began = datetime(self.session.year, self.session.month, self.session.day, *self.started, 0, tzinfo=IST)
        meta = {
            "snapshot_id": self.snapshot_id, "underlying": self.road.underlying, "provider": "groww",
            "started_at": began.isoformat(), "finished_at": (began + timedelta(minutes=2)).isoformat(),
            "expiries": [e.isoformat() for e in expiries], "spot": SPOT, "expected_contracts": len(rows),
            "recorded_contracts": len(rows), "failures": [] if self.complete else ["one contract failed"],
            "complete": self.complete, "in_window": self.in_window, "csv_sha256": hashlib.sha256(data).hexdigest(),
        }  # fmt: skip
        if self.short_by:
            data = snapshot_csv(rows[: -self.short_by])
            meta["csv_sha256"] = hashlib.sha256(data).hexdigest()
        if self.tamper:
            data = data.replace(b"1000", b"9999", 1)
        path = lambda name: QuoteSnapshotRecorder.path(self.session, name, self.road.dataset)  # noqa: E731
        if self.quote_file:
            store.put(path(f"{self.snapshot_id}.csv"), data)
        if self.sidecar:
            store.put(path(f"{self.snapshot_id}.meta.json"), json.dumps(meta, sort_keys=True).encode())
        if self.marker is not None:
            name = f"{self.road.stem}_{self.session:%Y%m%d}.canonical"
            store.put(path(name), (self.snapshot_id if self.marker == "canonical" else self.marker).encode())
        return self


def all_roads_planted(store: RawFileStore, session: date = SESSION, **faults) -> dict[RoadCode, Plant]:
    return {road.code: Plant(road, session, **faults).write(store) for road in ROADS}


def road(code: RoadCode) -> Road:
    return ROADS_BY_CODE[code]


class FixedExpiries:
    """ExpirySource: what the listing says each road records (by default the fixture's own expiries)."""

    def __init__(self, override: dict | None = None, unavailable: bool = False):
        self.override, self.unavailable = override or {}, unavailable

    def expected(self, road: Road, session: date):
        from fno.school.roads.ports import ExpiryUnavailable

        if self.unavailable:
            raise ExpiryUnavailable("no NSE file")
        return self.override.get(road.code, expiries_of(road))


class FixedLots:
    """LotSource: one lot for every road, or none."""

    def __init__(self, lot: DatedLot | None = LOT):
        self.lot_for_all, self.asked = lot, []

    def lot(self, underlying: str, session: date, expiries: tuple[date, ...]):
        self.asked.append((underlying, session, expiries))
        return self.lot_for_all
