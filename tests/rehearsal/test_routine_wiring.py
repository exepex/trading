"""REH1c: with the mode set, the cue jobs' session, A22's parts and A16b's candles are their recorded forms, built
without Drive (signed in to at the first read, which says which settings are missing when there are none); a real
run keeps the live ones."""

from datetime import date

import pytest

from fno.constants import ENV_FNO_REHEARSAL
from fno.intraday.candle_source import GrowwCandleSource
from fno.preopen.parts import NseGiftNifty
from fno.rehearsal.candle_wiring import rehearsed_candle_source
from fno.rehearsal.cue_wiring import rehearsed_cue_session
from fno.rehearsal.mode import Rehearsal
from fno.rehearsal.preopen_wiring import rehearsed_preopen_parts
from fno.rehearsal.record_drive import NO_DRIVE, RecordFiles
from fno.rehearsal.recorded_candles import RecordedCandles
from fno.rehearsal.recorded_cues import RecordedCueSession
from fno.rehearsal.recorded_preopen import RecordedPreopenPart
from fno.storage.wiring import OWNER_UPLOAD_SETTINGS


@pytest.fixture
def rehearsing(monkeypatch, tmp_path):
    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(date(2026, 10, 23), tmp_path, tmp_path).to_env())
    for name in OWNER_UPLOAD_SETTINGS:
        monkeypatch.delenv(name, raising=False)


def test_each_routine_source_is_its_recorded_form_built_without_drive(rehearsing):
    assert isinstance(rehearsed_cue_session(object()), RecordedCueSession)
    assert isinstance(rehearsed_candle_source(object()), RecordedCandles)
    (part,) = rehearsed_preopen_parts([NseGiftNifty(None, None)])
    assert isinstance(part, RecordedPreopenPart) and part.name == "gift"


def test_a_first_read_without_drive_names_the_missing_settings(rehearsing):
    with pytest.raises(RuntimeError, match="FNO_GDRIVE_"):
        RecordFiles("raw")("yahoo/preopen/x.json")
    assert "FNO_GDRIVE_" in NO_DRIVE


def test_a_real_run_keeps_the_live_sources(monkeypatch):
    monkeypatch.delenv(ENV_FNO_REHEARSAL, raising=False)
    live = GrowwCandleSource(None, None)
    session, parts = object(), [NseGiftNifty(None, None)]
    assert rehearsed_cue_session(session) is session and rehearsed_candle_source(live) is live
    assert rehearsed_preopen_parts(parts) is parts
