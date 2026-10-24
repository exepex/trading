"""Criteria 4, 6 and 7 (story MS-P0b): the readers' honest, read-only reach and the single sign-in."""

from datetime import date
from pathlib import Path

import pytest

from fno.school.probes.answers import RawAnswer
from fno.school.probes.constants import NSE_USER_AGENT, Source
from fno.school.probes.groww_reader import GrowwAnswers, future_symbol
from fno.school.probes.nse_reader import NseGet
from fno.school.probes.slot_capture import near_money, near_monthly

from .fakes import Rig, status

PACKAGE = Path(__file__).resolve().parents[3] / "fno" / "school" / "probes"
BROWSER_TOKENS = ("Mozilla", "Chrome", "Safari", "AppleWebKit", "Gecko")


def test_every_nse_request_carries_exactly_the_honest_user_agent(tmp_path):
    rig = Rig(tmp_path)
    rig.run()
    assert rig.nse.calls == 44
    assert all(headers["User-Agent"] == NSE_USER_AGENT for headers in rig.nse.sent_headers)
    assert not any(token in NSE_USER_AGENT for token in BROWSER_TOKENS)


def test_nse_s_session_headers_are_replaced_not_added_to():
    class Session:
        headers = {"User-Agent": "Mozilla/5.0 Chrome", "Cookie": "x"}

    get = NseGet(Session())
    assert get.session.headers == {"User-Agent": NSE_USER_AGENT, "Accept": "application/json, text/plain, */*"}


def test_the_probe_sends_nse_nothing_but_get(tmp_path):
    rig = Rig(tmp_path)
    used = []

    class OnlyGet:
        """Any name but `get` and `headers` fails the run: nothing else of the session may be touched."""

        def __init__(self, inner):
            object.__setattr__(self, "inner", inner)

        def __getattr__(self, name):
            used.append(name)
            if name not in ("get", "headers"):
                raise AssertionError(f"session.{name} used")
            return getattr(self.inner, name)

    rig.tools.nse.http.session = OnlyGet(rig.nse)
    rig.run()
    assert set(used) == {"get"} and rig.nse.calls == 44


def test_no_module_the_probe_imports_names_a_trading_call_v4_or_the_fleet():
    from tests.intraday.test_read_only_and_fallback import FORBIDDEN, _closure

    modules = set()
    for file in sorted(PACKAGE.glob("*.py")):
        _closure(f"fno.school.probes.{file.stem}", modules)
    assert "fno.intraday.read_only" in modules and "fno.providers.groww" in modules
    assert not [m for m in modules if m.startswith(("fno.forecast_v4", "fno.school.fleet", "fno.v4_pack"))]
    found = {}
    for module in modules:
        path = PACKAGE.parents[2].joinpath(*module.split("."))
        file = path.with_suffix(".py") if path.with_suffix(".py").is_file() else path / "__init__.py"
        if hits := [name for name in FORBIDDEN if name in file.read_text(encoding="utf-8")]:
            found[module] = hits
    assert found == {}


def test_no_probe_module_names_the_trading_client():
    for module in PACKAGE.glob("*.py"):
        assert "GrowwAPI" not in module.read_text().replace("GrowwAPIRateLimitException", ""), module.name


def test_the_live_wiring_holds_groww_only_through_the_read_only_wrapper():
    wiring = (PACKAGE / "wiring.py").read_text()
    assert "ReadOnlyGroww(lambda: provider.api)" in wiring and "GrowwReader(client," in wiring


def test_a_failed_sign_in_stops_groww_with_no_second_sign_in(tmp_path):
    class SignIn(Exception):
        pass

    rig = Rig(tmp_path)
    tries = []

    class NeverSignedIn:
        def __getattr__(self, name):
            tries.append(name)
            raise SignIn("token refused")

    rig.tools.groww.client = NeverSignedIn()
    code, lines = rig.run()
    assert len(tries) == 1 and code == 1
    assert rig.counts().stops[Source.GROWW] == "p0b groww stopped for the day at 10:07: sign-in failed: SignIn"


def test_a_good_sign_in_is_used_for_the_whole_day(tmp_path):
    rig = Rig(tmp_path)
    signed_in = []
    made_up = rig.tools.groww.client

    class Provider:
        @property
        def api(self):
            if not signed_in:
                signed_in.append(1)
            return made_up

    from fno.intraday.read_only import ReadOnlyGroww

    provider = Provider()
    rig.tools.groww.client = ReadOnlyGroww(lambda: provider.api)
    rig.run()
    assert signed_in == [1] and rig.groww.calls == 206


@pytest.mark.parametrize(
    ("error_code", "status_seen"), [("429", 429), ("401", 401), ("503", 503), ("GA001", None), ("", None)]
)
def test_groww_errors_become_their_code_and_class_name_only(error_code, status_seen):
    class GrowwAPIException(Exception):
        code = error_code

    answer = GrowwAnswers(lambda error: False).ask(lambda: (_ for _ in ()).throw(GrowwAPIException("secret")), bool)
    assert answer.status == status_seen and answer.error_name == "GrowwAPIException"


def test_the_shared_rate_limit_check_decides_a_groww_429():
    class Limited(Exception):
        pass

    answers = GrowwAnswers(lambda error: isinstance(error, Limited))
    assert answers.ask(lambda: (_ for _ in ()).throw(Limited()), bool).rate_limited


def test_a_groww_timeout_is_flagged():
    class GrowwAPITimeoutException(Exception):
        pass

    answer = GrowwAnswers(lambda e: False).ask(lambda: (_ for _ in ()).throw(GrowwAPITimeoutException()), bool)
    assert answer.timed_out


def test_near_month_is_the_last_listed_expiry_of_the_first_month():
    weeklies = [date(2026, 11, 3), date(2026, 11, 10), date(2026, 11, 24), date(2026, 12, 29), date(2026, 10, 27)]
    assert near_monthly(weeklies, date(2026, 10, 29)) == date(2026, 11, 24)
    assert near_monthly([date(2026, 10, 29)], date(2026, 10, 29)) == date(2026, 10, 29)  # expiry day itself
    assert near_monthly([], date(2026, 10, 29)) is None


def test_near_money_is_atm_and_two_listed_strikes_each_side():
    strikes = [100.0, 110.0, 120.0, 130.0, 140.0, 150.0, 160.0]
    assert near_money(strikes, 131.0) == [110.0, 120.0, 130.0, 140.0, 150.0]
    assert near_money(strikes, 99.0) == [100.0, 110.0, 120.0]  # edge of the list: fewer, never invented
    assert near_money([], 100.0) == [] and near_money(strikes, 0) == []


def test_future_symbols_take_groww_s_form():
    assert future_symbol("RELIANCE", date(2026, 11, 24)) == "RELIANCE26NOVFUT"


def test_a_raw_answer_s_hash_is_stable_whatever_the_key_order():
    assert RawAnswer(payload={"a": 1, "b": 2}).sha256() == RawAnswer(payload={"b": 2, "a": 1}).sha256()


def test_a_401_from_nse_s_first_request_stops_it_before_any_other(tmp_path):
    rig = Rig(tmp_path, nse_faults={1: status(401)})
    rig.run()
    assert rig.nse.calls == 1
