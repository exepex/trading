"""REH1b: in a rehearsal NSE's archive answers only from the record already in Drive; a missing file is "not
recorded", never fetched, never retried, never archived."""

from datetime import date

import pytest

from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.mode import Rehearsal
from fno.storage.raw_source import NseDailyFoSource, RawSourceUnavailable
from fno.storage.wiring import build_nse_source


def test_a_rehearsal_s_nse_source_never_sends_and_says_not_recorded(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(date(2026, 10, 23), tmp_path, tmp_path).to_env())
    source = build_nse_source(NseDailyFoSource)
    slept = []
    source.sleep = slept.append
    with pytest.raises(RawSourceUnavailable, match="rehearsal:NOT_RECORDED .*not sent"):
        source.fetch(NseDailyFoSource.path_for(date(2026, 10, 23)))
    assert slept == []  # no retry, no wait


def test_without_the_mode_the_source_s_session_is_the_paced_one(monkeypatch):
    monkeypatch.delenv(ENV_FNO_REHEARSAL, raising=False)
    assert type(build_nse_source(NseDailyFoSource).session).__name__ == "PacedSession"


def test_the_evening_s_fii_dii_snapshot_is_not_recorded_never_a_guard_refusal(monkeypatch, tmp_path):
    """The orchestrator's point: an input the record does not hold is an honest "not recorded", not a fault at the
    HTTP guard. NSE's FII/DII values go through the same never-sending session."""
    from fno.storage.snapshot_source import FiiDiiCashBySessionSource

    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(date(2026, 10, 23), tmp_path, tmp_path).to_env())
    source = build_nse_source(FiiDiiCashBySessionSource)
    with pytest.raises(
        RawSourceUnavailable, match="rehearsal:NOT_RECORDED https://www.nseindia.com/api/fiidiiTradeReact"
    ):
        source.fetch(FiiDiiCashBySessionSource.path_for(date(2026, 10, 23)))
