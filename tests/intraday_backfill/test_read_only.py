"""Story A16b, criteria 5 and 10: a whole back-fill through `GrowwCandleSource` and A16's `ReadOnlyGroww` over a fake
SDK whose order, position, margin and funds calls fail; the pacing; the import closure of the new modules names no
trading call; a planted secret never reaches an output."""

import ast
import re
from datetime import date
from pathlib import Path

import pytest

import fno
from fno.intraday import backfill_wiring
from fno.intraday.candle_source import MIN_GAP_SECONDS, CandleCallFailed, GrowwCandleSource
from fno.intraday.read_only import ReadOnlyGroww, ReadOnlyViolation
from fno.storage.raw_store import LocalFolderStore
from tests.intraday.groww_fakes import FORBIDDEN, ForbiddenCall
from tests.intraday_backfill.fakes import CALENDAR, FETCHED, START, FakeNse, build, session_data

WEEK = [date(2026, 9, 28), date(2026, 9, 29), date(2026, 9, 30), date(2026, 10, 1)]
PLANTED = "planted-secret-7f3a9c"
TRADING_CALL = re.compile(r"\b(place|modify|cancel)_\w*order|get_positions|get_holdings|_margin_details|funds", re.I)


class FakeCandleSdk:
    """The SDK's read answer for candles; every trading name fails the test."""

    EXCHANGE_NSE, SEGMENT_CASH = "NSE", "CASH"
    CANDLE_INTERVAL_MIN_1, CANDLE_INTERVAL_MIN_15 = "1minute", "15minute"

    def __init__(self, fifteen: dict, minutes: dict, error: Exception | None = None):
        self.answers = {self.CANDLE_INTERVAL_MIN_15: fifteen, self.CANDLE_INTERVAL_MIN_1: minutes}
        self.error, self.calls = error, []

    def __getattr__(self, name):
        if name in FORBIDDEN:
            raise ForbiddenCall(f"the back-fill called {name}")
        raise AttributeError(name)

    def get_historical_candles(self, exchange, segment, groww_symbol, start_time, end_time, candle_interval,
                               timeout=None):  # fmt: skip
        self.calls.append((groww_symbol, segment, candle_interval, start_time, end_time))
        if self.error:
            raise self.error
        start, end = date.fromisoformat(start_time[:10]), date.fromisoformat(end_time[:10])
        days = self.answers[candle_interval]
        return {"candles": [row for day in sorted(days) if start <= day <= end for row in days[day]]}


class SteppedClock:
    """A monotonic clock that moves only when slept on (each call itself takes no time)."""

    def __init__(self):
        self.now, self.slept = 100.0, []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.slept.append(seconds)
        self.now += seconds


def _source(sdk, clock=None):
    clock = clock or SteppedClock()
    return GrowwCandleSource(ReadOnlyGroww(lambda: sdk), lambda: FETCHED, clock.sleep, clock.monotonic), clock


def test_a_whole_back_fill_runs_through_the_read_only_client_and_never_a_trading_call(tmp_path):
    fifteen, minutes, nse = session_data(WEEK)
    sdk = FakeCandleSdk(fifteen, minutes)
    source, clock = _source(sdk)
    report = build(tmp_path, source, FakeNse(nse)).run(START, WEEK[3])
    assert report.complete and len(report.written) == 4
    assert {(symbol, segment) for symbol, segment, *_ in sdk.calls} == {("NSE-NIFTY", "CASH")}
    assert [c[2] for c in sdk.calls] == ["15minute", "1minute", "1minute", "1minute", "1minute"]
    with pytest.raises(ReadOnlyViolation):
        ReadOnlyGroww(lambda: sdk).place_order  # noqa: B018 - refused before it reaches the SDK


def test_no_two_calls_start_less_than_half_a_second_apart(tmp_path):
    fifteen, minutes, nse = session_data(WEEK)
    clock = SteppedClock()
    original = clock.monotonic
    starts = []
    sdk = FakeCandleSdk(fifteen, minutes)
    real_call = sdk.get_historical_candles
    sdk.get_historical_candles = lambda **kw: starts.append(original()) or real_call(**kw)
    source, _ = _source(sdk, clock)
    build(tmp_path, source, FakeNse(nse)).run(START, WEEK[3])
    gaps = [b - a for a, b in zip(starts, starts[1:], strict=False)]
    assert len(starts) == 5 and min(gaps) >= MIN_GAP_SECONDS and clock.slept == [MIN_GAP_SECONDS] * 4


def test_a_failing_call_is_named_by_class_only_and_a_planted_secret_reaches_no_output(tmp_path, capsys):
    fifteen, minutes, nse = session_data(WEEK)
    source, _ = _source(FakeCandleSdk(fifteen, minutes, error=RuntimeError(f"401 token={PLANTED}")))
    with pytest.raises(CandleCallFailed, match="^Groww 15m 2026-09-28..2026-10-01: RuntimeError$"):
        source.candles(WEEK[0], WEEK[3])
    report = build(tmp_path, source, FakeNse(nse)).run(START, WEEK[3])
    written = [p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()]
    assert PLANTED not in repr(report) and not [b for b in written if PLANTED.encode() in b]


def test_an_answer_without_a_candle_list_is_transient(tmp_path):
    class Empty(FakeCandleSdk):
        def get_historical_candles(self, **kwargs):
            return {"error": "x"}

    source, _ = _source(Empty({}, {}))
    with pytest.raises(CandleCallFailed, match="no candle list"):
        source.minute_candles(WEEK[0])


def _imported(path: Path, node: ast.ImportFrom) -> list[Path]:
    """The `fno` files one `from ... import ...` names (the module itself, or a submodule it imports)."""
    if node.level:
        base, parts = path.parents[node.level - 1], (node.module or "").split(".") if node.module else []
    elif (node.module or "").startswith("fno."):
        base, parts = Path(fno.__file__).parent.parent, node.module.split(".")
    else:
        return []
    targets = [base.joinpath(*parts)] + [base.joinpath(*parts, alias.name) for alias in node.names]
    return [t.with_suffix(".py") for t in targets if t.with_suffix(".py").is_file()] + [
        t / "__init__.py" for t in targets if (t / "__init__.py").is_file()
    ]


def _closure(root: Path) -> set[Path]:
    """Every `fno` file the root imports, directly or not (imports inside functions included)."""
    found, todo = set(), [root]
    while todo:
        path = todo.pop()
        if path not in found:
            found.add(path)
            tree = ast.parse(path.read_text(encoding="utf-8"))
            todo += [p for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) for p in _imported(path, node)]
    return found


def test_the_import_closure_of_the_back_fill_names_no_trading_call():
    closure = _closure(Path(backfill_wiring.__file__))
    assert {"backfill.py", "candle_source.py", "read_only.py", "groww.py"} <= {p.name for p in closure}
    hits = {p.relative_to(Path(fno.__file__).parent).as_posix(): TRADING_CALL.findall(p.read_text()) for p in closure}
    assert not {path: found for path, found in hits.items() if found}
    assert len(closure) > 20  # the walk really follows the imports


def test_the_cli_names_an_unexpected_error_by_class_only(tmp_path, monkeypatch, capsys):
    from fno.intraday import backfill_cli

    def explode(cfg, folder):
        raise RuntimeError(f"GROWW_API_SECRET={PLANTED}")

    monkeypatch.setattr(backfill_wiring, "build_candle_backfill", explode)
    monkeypatch.setattr("fno.config.load_app_config", lambda path: {})
    args = type("Args", (), {"config": None, "intraday_cmd": "backfill", "start": None, "end": date(2026, 10, 1),
                             "dry_run": tmp_path})()  # fmt: skip
    assert backfill_cli.cmd_backfill(args) == 1
    out = capsys.readouterr().out
    assert out.strip() == "candle back-fill stopped (RuntimeError); what it wrote stays, run it again"
    assert PLANTED not in out  # nothing of the text, the class only


def test_a_sign_in_failure_is_a_named_transient_failure_without_its_text():
    def signing_in():
        raise RuntimeError(f"login refused for key {PLANTED}")

    source = GrowwCandleSource(ReadOnlyGroww(signing_in), lambda: FETCHED, lambda s: None, lambda: 0.0)
    with pytest.raises(CandleCallFailed, match="^Groww 1m 2026-09-28..2026-09-28: RuntimeError$"):
        source.minute_candles(WEEK[0])


def test_the_verifier_is_built_without_groww_and_archives_nothing(tmp_path, monkeypatch):
    def refuse(*args, **kwargs):
        raise AssertionError("the verifier touched Groww or an archiving store")

    monkeypatch.setattr(backfill_wiring, "GrowwProvider", refuse)
    monkeypatch.setattr(backfill_wiring, "build_owner_drive_store", refuse)
    monkeypatch.setattr(backfill_wiring, "build_owner_drive", lambda: LocalFolderStore(tmp_path))
    monkeypatch.setattr(backfill_wiring, "build_raw_stores", lambda: [])
    monkeypatch.setattr(backfill_wiring, "build_nse_source", lambda kind: None)
    monkeypatch.setattr(backfill_wiring, "build_session_calendar", lambda: CALENDAR)
    monkeypatch.setattr(backfill_wiring, "SERIES_START", START)
    monkeypatch.setattr(backfill_wiring, "CANDLE_FOLDER", tmp_path / "table")  # never main's real back-fill rows
    monkeypatch.setattr(backfill_wiring, "MANIFEST_FOLDER", tmp_path / "manifests")
    verifier = backfill_wiring.build_candle_verifier()
    assert verifier.nse.library.archive is None and verifier.problems() == []
