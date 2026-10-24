"""A16b's candle source in a rehearsal (story REH1b), chosen by `build_candle_backfill`: Groww in a real run, the
day's recorded answers when rehearsing (the record checkout's manifests, the real Drive's raw copies, read-only)."""

from __future__ import annotations

import os
import time
from collections.abc import Mapping

from .mode import rehearsal


def rehearsed_candle_source(source, env: Mapping[str, str] = os.environ):
    mode = rehearsal(env)
    if mode is None:
        return source
    from ..config import ROOT
    from ..intraday.backfill_daily import MANIFESTS
    from ..models import now_ist
    from ..storage.wiring import MANIFEST_FOLDER, RAW_AREA
    from .record_drive import RecordFiles
    from .recorded_candles import RecordedCandles

    manifests = mode.record / MANIFEST_FOLDER.relative_to(ROOT) / MANIFESTS
    return RecordedCandles(manifests, RecordFiles(RAW_AREA), now_ist, time.sleep)  # Drive at the first read
