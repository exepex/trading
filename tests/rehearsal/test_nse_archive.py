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
