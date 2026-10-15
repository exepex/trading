"""FT1 criterion 10 and section 17: the fetch plan, the paced read-only candle source, the Drive archive with its
manifest (no price), the resumable fetch with one retry and no call in market hours, and the read-only closure."""

import ast
import gzip
import json
from datetime import date, datetime, time
from pathlib import Path

import pytest
from ft1study.archive import FIELDS, ContractArchive, CopyDamaged
from ft1study.candles import MIN_GAP_SECONDS, CandleCallFailed, ContractAnswer, GrowwContractCandles
from ft1study.days import DecisionDay
from ft1study.entries import Entry
from ft1study.fetch import Fetcher, MarketHours, MarketOpen
from ft1study.plan import FetchItem, fetch_plan
from ft1study.times import Moment

from fno.intraday.read_only import ReadOnlyGroww
from fno.research_engine.structures import BOUGHT, SOLD, Leg
from fno.storage.raw_store import LocalFolderStore
from tests.intraday.groww_fakes import FORBIDDEN
from tests.research_ft1.ft1_fakes import FakeCalendar, row

ROOT = Path(__file__).resolve().parents[2]
STUDY = ROOT / "research" / "2026-10-16-fill-timing"
EXPIRY = date(2025, 1, 30)
AT = datetime(2025, 1, 8, 20, 0)


def answer(symbol: str, start: date, end: date, close: float = 100.0) -> ContractAnswer:
    rows = [row(start, time(14, 45), close)]
    raw = json.dumps({"candles": rows}, sort_keys=True, separators=(",", ":")).encode()
    return ContractAnswer(symbol, start, end, raw, rows, AT, AT)


def entry(day: date, next_session: date, strikes=(23000.0, 23200.0)) -> Entry:
    legs = (Leg(strikes[0], "CE", SOLD), Leg(strikes[1], "CE", BOUGHT))
    return Entry(DecisionDay(day, next_session, EXPIRY, 10), Moment(day, time(15)), "CCS", 200, 23000.0, legs)


def test_the_plan_takes_each_contract_once_from_its_first_day_to_its_last_next_session_with_the_future():
    plan = fetch_plan([entry(date(2025, 1, 8), date(2025, 1, 9)), entry(date(2025, 1, 10), date(2025, 1, 13))])
    assert plan == sorted(
        FetchItem(EXPIRY, s, date(2025, 1, 8), date(2025, 1, 13))
        for s in ("NSE-NIFTY-30Jan25-23000-CE", "NSE-NIFTY-30Jan25-23200-CE", "NSE-NIFTY-30Jan25-FUT")
    )


def test_a_window_over_90_days_is_split():
    plan = fetch_plan([entry(date(2025, 1, 1), date(2025, 1, 2)), entry(date(2025, 4, 30), date(2025, 5, 2))])
    future = [i for i in plan if i.symbol.endswith("FUT")]
    assert [(i.start, i.end) for i in future] == [
        (date(2025, 1, 1), date(2025, 3, 31)),
        (date(2025, 4, 1), date(2025, 5, 2)),
    ]


class CandleApi:
    EXCHANGE_NSE, SEGMENT_FNO, CANDLE_INTERVAL_MIN_15 = "NSE", "FNO", "15minute"

    def __init__(self, fail=()):
        self.calls, self.fail = [], set(fail)

    def get_historical_candles(self, exchange, segment, groww_symbol, start_time, end_time, candle_interval, timeout):
        self.calls.append((exchange, segment, groww_symbol, start_time, end_time, candle_interval))
        if groww_symbol in self.fail:
            raise ConnectionError("secret-token-in-text")
        return {"candles": [row(date(2025, 1, 8), time(14, 45), 101.0)]}


def test_the_source_calls_only_through_the_read_only_client_paced_and_names_errors_by_class_only():
    api, slept, clock = CandleApi(fail={"BAD"}), [], iter([0.0, 0.0, 0.1, 0.5, 0.6, 1.1])
    source = GrowwContractCandles(ReadOnlyGroww(lambda: api), lambda: AT, slept.append, lambda: next(clock))
    found = source.candles("NSE-NIFTY-30Jan25-23000-CE", date(2025, 1, 8), date(2025, 1, 9))
    assert found.rows and api.calls[0] == ("NSE", "FNO", "NSE-NIFTY-30Jan25-23000-CE", "2025-01-08 09:00:00",
                                           "2025-01-09 15:59:59", "15minute")  # fmt: skip
    with pytest.raises(CandleCallFailed) as failure:
        source.candles("BAD", date(2025, 1, 8), date(2025, 1, 8))
    assert "ConnectionError" in str(failure.value) and "secret" not in str(failure.value)
    assert slept == [pytest.approx(MIN_GAP_SECONDS - 0.1)]


def test_the_archive_keeps_drive_first_a_manifest_row_without_a_price_and_one_row_per_identical_answer(tmp_path):
    archive = ContractArchive(LocalFolderStore(tmp_path / "drive"), tmp_path / "manifest.csv")
    first = archive.save(EXPIRY, answer("S", date(2025, 1, 8), date(2025, 1, 9)))
    assert archive.save(EXPIRY, answer("S", date(2025, 1, 8), date(2025, 1, 9))) == first
    lines = (tmp_path / "manifest.csv").read_text().splitlines()
    assert lines[0] == ",".join(FIELDS) and len(lines) == 2  # the columns hold no price
    assert first.startswith("groww/options/nifty-candles-15m/2025/2025-01-30/S_20250108_20250109_")
    stored = (tmp_path / "drive" / first).read_bytes()
    assert gzip.decompress(stored) == answer("S", date(2025, 1, 8), date(2025, 1, 9)).raw
    assert archive.copies("S") == [[row(date(2025, 1, 8), time(14, 45), 100.0)]]
    assert archive.held("S", date(2025, 1, 8), date(2025, 1, 9)) and not archive.held("S", EXPIRY, EXPIRY)


def test_a_changed_drive_copy_is_refused_and_a_verified_one_is_cached(tmp_path):
    archive = ContractArchive(LocalFolderStore(tmp_path / "drive"), tmp_path / "m.csv", tmp_path / "cache")
    path = archive.save(EXPIRY, answer("S", date(2025, 1, 8), date(2025, 1, 9)))
    archive.copies("S")
    assert len(list((tmp_path / "cache").iterdir())) == 1
    (tmp_path / "drive" / path).write_bytes(gzip.compress(b'{"candles": []}', mtime=0))
    assert archive.copies("S")  # the verified cached copy is read, not the changed Drive one
    fresh = ContractArchive(LocalFolderStore(tmp_path / "drive"), tmp_path / "m.csv")
    with pytest.raises(CopyDamaged):
        fresh.copies("S")


class Source:
    def __init__(self, fail_once=(), fail_always=()):
        self.calls, self.fail_once, self.fail_always = [], set(fail_once), set(fail_always)

    def candles(self, symbol, start, end):
        self.calls.append(symbol)
        if symbol in self.fail_always or symbol in self.fail_once:
            self.fail_once.discard(symbol)
            raise CandleCallFailed(symbol)
        return answer(symbol, start, end)


def hours(now: datetime) -> MarketHours:
    return MarketHours(FakeCalendar(), lambda: now)


def test_the_fetch_skips_held_windows_retries_a_failure_once_and_lists_what_still_fails(tmp_path):
    archive = ContractArchive(LocalFolderStore(tmp_path / "drive"), tmp_path / "m.csv")
    items = [FetchItem(EXPIRY, s, date(2025, 1, 8), date(2025, 1, 9)) for s in ("A", "B", "C", "D")]
    archive.save(EXPIRY, answer("A", date(2025, 1, 8), date(2025, 1, 9)))
    source = Source(fail_once={"B"}, fail_always={"C"})
    report = Fetcher(source, archive, hours(AT)).run(items)
    assert source.calls == ["B", "C", "D", "B", "C"]
    assert (report.already_held, report.fetched, [i.symbol for i in report.failed]) == (1, 2, ["C"])


def test_no_call_is_made_in_market_hours_on_a_session_day_and_weekends_are_open(tmp_path):
    archive = ContractArchive(LocalFolderStore(tmp_path / "drive"), tmp_path / "m.csv")
    items = [FetchItem(EXPIRY, "A", date(2025, 1, 8), date(2025, 1, 9))]
    with pytest.raises(MarketOpen):
        Fetcher(Source(), archive, hours(datetime(2025, 1, 8, 15, 44))).run(items)
    assert Fetcher(Source(), archive, hours(datetime(2025, 1, 11, 11, 0))).run(items).fetched == 1  # a Saturday


def _imports(file: Path, package: list[str]) -> list[str]:
    names = []
    for node in ast.walk(ast.parse(file.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = package[: len(package) - node.level + 1] if node.level else []
            target = ".".join(base + ([node.module] if node.module else []))
            names += [target] + [f"{target}.{alias.name}" for alias in node.names]
    return names


def _file(module: str) -> Path | None:
    base = STUDY if module.startswith("ft1study") else ROOT
    path = base.joinpath(*module.split("."))
    for file in (path.with_suffix(".py"), path / "__init__.py"):
        if file.is_file():
            return file
    return None


def test_the_studys_import_closure_names_no_order_position_holdings_or_margin_call():
    todo = ["study"] + [f"ft1study.{f.stem}" for f in (STUDY / "ft1study").glob("*.py")]
    seen: dict[str, Path] = {}
    while todo:
        module = todo.pop()
        file = STUDY / "study.py" if module == "study" else _file(module)
        if module in seen or file is None:
            continue
        seen[module] = file
        package = module.split(".")[:-1] if file.name != "__init__.py" else module.split(".")
        todo += [n for n in _imports(file, package) if n.startswith(("fno", "ft1study"))]
    assert "fno.providers.groww" in seen and "fno.intraday.read_only" in seen and len(seen) > 30
    hits = {m: [n for n in FORBIDDEN if n in f.read_text(encoding="utf-8")] for m, f in seen.items()}
    assert {m: h for m, h in hits.items() if h} == {}
