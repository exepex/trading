"""REH1s (the REC1 builder's 23 Oct rehearsal printed "Groww unavailable (SDK not installed); using the NSE website for
option chains"): with no Groww SDK, every 3 pm recorder's builder falls back to NSE's website, and under the mode each
is still its recorded form, whose provider is never asked; a direct call to that provider is refused before it is
sent. Run in a fresh process (the HTTP guard changes the process), as the guard's own test is."""

import subprocess
import sys

PROBE = """import os, sys
from datetime import date
from pathlib import Path
from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.mode import Rehearsal
os.environ[ENV_FNO_REHEARSAL] = Rehearsal.new(date(2026, 10, 23), Path(sys.argv[1]), Path(sys.argv[1])).to_env()
import fno.providers.groww as groww
def no_sdk():
    raise ImportError("SDK not installed")
groww.has_groww_credentials = no_sdk
from fno.rehearsal.process import install_process
install_process()
from fno.composition import build_quote_recorder
from fno.config import load_app_config
from fno.quotes.index_wiring import build_index_quote_recorders
from fno.quotes.window_wiring import build_window_quote_recorder
from fno.rehearsal.http_guard import RehearsalCallRefused
cfg = load_app_config()
built = {"3 pm": build_quote_recorder(cfg), **build_index_quote_recorders(cfg),
         "v4": build_window_quote_recorder(cfg, "v4")}
for name, recorder in built.items():
    provider = getattr(recorder.provider, "inner", recorder.provider)
    try:
        provider.expiries("NIFTY")
        outcome = "REACHED"
    except RehearsalCallRefused:
        outcome = "REFUSED"
    except Exception as other:
        outcome = "OTHER " + type(other).__name__
    print(name, type(recorder).__name__, type(provider).__name__, outcome)
"""
NAMES = ("3 pm", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTY weekly", "v4")


def test_with_no_groww_sdk_every_3_pm_recorder_is_recorded_and_its_nse_fallback_refused(tmp_path):
    done = subprocess.run([sys.executable, "-c", PROBE, str(tmp_path)], capture_output=True, text=True, timeout=120,
                          check=True)  # fmt: skip
    assert done.stdout.splitlines() == [f"{name} RecordedRecorder NSEProvider REFUSED" for name in NAMES]
    assert done.stderr.count("using the NSE website for option chains") == 3  # each builder's own fallback, once
