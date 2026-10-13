"""Story A4 extended for B7: the recorder also records India VIX and the NIFTY futures during the capture, from a
`LevelSource`; a level it cannot read is a recorded failure that never blocks the option capture."""

import json
from datetime import date, datetime

from fno import composition
from fno.models import IST
from fno.quotes.market_levels import (
    FutureLevel,
    LevelSource,
    MarketLevels,
    NseLevelSource,
    parse_index_futures,
    parse_india_vix,
)
from fno.quotes.recorder import QuoteSnapshotRecorder
from fno.research_data.quote_snapshots import RecordedSnapshots
from fno.storage.raw_store import LocalFolderStore

from .test_quote_recorder import Clock, FakeProvider
from .test_recorder_calendar import CALENDAR, TUESDAY

ALL_INDICES = {  # the shape NSE's /api/allIndices returned on 13 Oct 2026
    "timestamp": "13-Oct-2026 15:30",
    "data": [{"index": "NIFTY 50", "last": 22721.95}, {"index": "INDIA VIX", "last": 14.04}],
}
FUTURES = {  # the shape of /api/liveEquity-derivatives?index=nse50_fut (fields trimmed)
    "data": [
        {"underlying": "NIFTY", "expiryDate": "23-Nov-2026", "lastPrice": 22965, "volume": 426010},
        {"underlying": "NIFTY", "expiryDate": "27-Oct-2026", "lastPrice": 22860, "volume": 3932695},
    ]
}


def test_nse_payloads_parse_to_vix_and_futures():
    assert parse_india_vix(ALL_INDICES) == (14.04, "13-Oct-2026 15:30")
    assert parse_index_futures(FUTURES, "NIFTY") == (
        FutureLevel(date(2026, 10, 27), 22860.0, 3932695),
        FutureLevel(date(2026, 11, 23), 22965.0, 426010),
    )


def test_a_failing_endpoint_is_recorded_not_raised():
    def nse_json(path, params):
        if "allIndices" in path:
            raise ConnectionError("blocked")
        return FUTURES

    levels = NseLevelSource(nse_json).levels("NIFTY")
    assert levels.india_vix is None and len(levels.futures) == 2
    assert levels.failures == ("india vix: ConnectionError: blocked",)


class Levels(LevelSource):
    name = "fake"

    def levels(self, underlying):
        return MarketLevels(14.04, "13-Oct-2026 14:55", (FutureLevel(date(2026, 10, 27), 22860.0, 100),))


def test_the_recorder_writes_the_levels_and_live_features_read_them_back(tmp_path):
    clock = Clock(TUESDAY)
    traded = datetime(2026, 10, 13, 14, 58, tzinfo=IST)
    recorder = QuoteSnapshotRecorder(
        FakeProvider(traded=traded), LocalFolderStore(tmp_path), clock.now, clock.sleep, calendar=CALENDAR,
        levels=Levels(),
    )  # fmt: skip
    result = recorder.record()
    assert result.complete  # the levels never change what "complete" means for the option capture
    meta = json.loads((tmp_path / recorder.path(TUESDAY.date(), f"{result.snapshot_id}.meta.json")).read_text())
    assert (meta["india_vix"], meta["levels_source"], meta["levels_failures"]) == (14.04, "fake", [])
    snapshot = RecordedSnapshots(LocalFolderStore(tmp_path)).snapshot(TUESDAY.date())
    assert snapshot.vix == 14.04 and snapshot.future_for(date(2026, 10, 27)).close == 22860.0


def test_the_app_records_levels_from_nse(monkeypatch):
    monkeypatch.setattr(composition, "get_provider", lambda name, cfg: FakeProvider())
    assert isinstance(composition.build_quote_recorder({}).levels, NseLevelSource)
