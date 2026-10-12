from datetime import datetime

from fno.config import load_config
from fno.constants import ENV_GROWW_ACCESS_TOKEN, ENV_GROWW_API_KEY
from fno.models import IST
from fno.providers import get_provider
from fno.providers.groww import token_day


def test_token_window_turns_over_at_six_ist():
    before = datetime(2026, 10, 13, 5, 59, tzinfo=IST)
    after = datetime(2026, 10, 13, 6, 0, tzinfo=IST)
    assert token_day(before).isoformat() == "2026-10-12"
    assert token_day(after).isoformat() == "2026-10-13"


def test_auto_uses_free_nse_without_groww_credentials(monkeypatch):
    monkeypatch.delenv(ENV_GROWW_ACCESS_TOKEN, raising=False)
    monkeypatch.delenv(ENV_GROWW_API_KEY, raising=False)
    assert get_provider("auto", load_config()).name == "nse"
