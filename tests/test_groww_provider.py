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


def test_a_key_alone_is_not_a_usable_groww_login_and_auto_falls_back(monkeypatch):
    from fno.constants import ENV_GROWW_API_SECRET, ENV_GROWW_TOTP_SECRET
    from fno.providers.groww import has_groww_credentials

    monkeypatch.delenv(ENV_GROWW_ACCESS_TOKEN, raising=False)
    monkeypatch.delenv(ENV_GROWW_TOTP_SECRET, raising=False)
    monkeypatch.delenv(ENV_GROWW_API_SECRET, raising=False)
    monkeypatch.setenv(ENV_GROWW_API_KEY, "k")
    assert not has_groww_credentials()
    assert get_provider("auto", load_config()).name == "nse"
    monkeypatch.setenv(ENV_GROWW_TOTP_SECRET, "JBSWY3DPEHPK3PXP")
    assert has_groww_credentials()
    assert get_provider("auto", load_config()).name in ("groww", "nse")  # nse when the SDK is not installed


def test_groww_signs_in_again_after_the_six_am_expiry(monkeypatch):
    import fno.providers.groww as groww

    signed_in = []

    class FakeApi:
        def __init__(self, token):
            signed_in.append(token)

    provider = groww.GrowwProvider.__new__(groww.GrowwProvider)
    provider.GrowwAPI, provider._api, provider._api_day = FakeApi, None, None
    provider._token = lambda: f"token{len(signed_in)}"
    clock = iter(
        [
            datetime(2026, 10, 13, 9, 0, tzinfo=IST),
            datetime(2026, 10, 13, 15, 0, tzinfo=IST),
            datetime(2026, 10, 14, 5, 59, tzinfo=IST),
            datetime(2026, 10, 14, 6, 1, tzinfo=IST),
        ]
    )
    monkeypatch.setattr(groww, "now_ist", lambda: next(clock))
    for _ in range(4):
        assert provider.api is not None
    assert signed_in == ["token0", "token1"]  # once on the 13th's token, again only after 06:00 on the 14th
