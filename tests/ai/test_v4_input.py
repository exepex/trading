"""Story G11 round 2b, step 1 (response 272): the AI books' v4 input, built from the released pack and the closes;
Hybrid alone sees the rules slot's and the primary baseline's values, with the envelope around the baseline; the input
of a realistic full pack fits the 64 KiB pointer."""

from dataclasses import replace
from datetime import date, datetime, time, timedelta

import pytest

from fno.ai.export import canonical
from fno.ai.v4_input import V4InputFor, build_v4_input, input_sha256
from fno.constants import BOOK2_HYBRID, BOOK3_AI, V4_BASELINE_BASE_RATE, V6_BIG_MOVE_1S, V6_BIG_MOVE_5S
from fno.models import IST
from fno.v4_pack.model import ChainQuote, FutureQuote, Iv30, Level, Pack, VixLevel
from fno.weather.constants import WEATHER_MODEL_VIX

DAY = date(2026, 10, 26)
WEEKLY, MONTHLY = date(2026, 10, 27), date(2026, 11, 24)
QUESTIONS = (V6_BIG_MOVE_1S, V6_BIG_MOVE_5S)
RULES_FORECASTER = WEATHER_MODEL_VIX  # V6's rules slot is the market weather (decision 70)
POINTER_CAP = 64 * 1024
METHOD = "atm_iv30_g1/sha256:" + "c" * 64


def at(hh, mm, ss=0):
    return datetime.combine(DAY, time(hh, mm, ss), IST)


def chain(spot=25012.4):
    """Every 50-point strike from 22,000 to 28,000 on two expiries: a full NSE chain's size."""
    quotes = []
    for expiry in (WEEKLY, MONTHLY):
        for strike in range(22000, 28001, 50):
            for kind in ("CE", "PE"):
                intrinsic = max(0.0, spot - strike) if kind == "CE" else max(0.0, strike - spot)
                mid = round(intrinsic + 80.0, 2)
                quotes.append(
                    ChainQuote(expiry, float(strike), kind, mid - 0.5, mid + 0.5, mid, at(14, 29), at(14, 30, 5))
                )
    return tuple(quotes)


def a_pack():
    return Pack(DAY, "A", "groww", "groww_api", "a4/2026-10-26/attempt-1", at(14, 32), Level(25012.4, at(14, 30, 1)),
                FutureQuote(MONTHLY, 25110.0, 25108.5, 25111.0, at(14, 30, 2)), VixLevel(11.82, at(14, 30, 3), None),
                chain(), Iv30(0.112, False, (WEEKLY, MONTHLY), METHOD, at(14, 31)))  # fmt: skip


def closes(n=260):
    first = DAY - timedelta(days=n + 1)
    return [((first + timedelta(days=i)).isoformat(), 24000.0 + i * 3.7, 12.0 + (i % 7) / 10) for i in range(n)]


def who(book):
    return V4InputFor(book, f"{book}/v2/sha256:{'a' * 64}/isolation:sealed_same_day", DAY, QUESTIONS, "d" * 64)


RULES = {V6_BIG_MOVE_1S: {RULES_FORECASTER: 0.06, V4_BASELINE_BASE_RATE: 0.04},
         V6_BIG_MOVE_5S: {RULES_FORECASTER: 0.19, V4_BASELINE_BASE_RATE: None}}  # fmt: skip


def test_book3_sees_the_pack_and_the_closes_and_no_rules_answer():
    built = build_v4_input(who(BOOK3_AI), a_pack(), closes(), None, None)
    assert "rules" not in built and built["questions"] == list(QUESTIONS) and built["pack_sha256"] == "d" * 64
    assert len(built["closes_before_day"]) == 260 and built["derived"]["trailing_rv20_points_with_1430_spot"] > 0


def test_hybrid_sees_the_rules_and_the_envelope_around_the_primary_baseline_only():
    built = build_v4_input(who(BOOK2_HYBRID), a_pack(), closes(), RULES, 0.10)
    assert built["rules"]["by_question"][V6_BIG_MOVE_1S][RULES_FORECASTER] == 0.06
    assert built["rules"]["envelope"] == {V6_BIG_MOVE_1S: [0.0, 0.14], V6_BIG_MOVE_5S: None}  # no baseline: no envelope


def test_rules_belong_to_hybrid_alone_and_the_pack_must_be_the_days():
    with pytest.raises(ValueError, match="Hybrid's input only"):
        build_v4_input(who(BOOK3_AI), a_pack(), closes(), RULES, None)
    with pytest.raises(ValueError, match="the pack is for"):
        build_v4_input(who(BOOK3_AI), replace(a_pack(), day=DAY + timedelta(days=1)), closes(), None, None)


def test_the_atm_straddle_per_expiry_and_the_chain_near_spot_of_the_nearest_expiry():
    summary = build_v4_input(who(BOOK3_AI), a_pack(), closes(), None, None)["pack"]
    weekly = summary["atm_by_expiry"][0]
    assert (weekly["expiry"], weekly["strike"], weekly["straddle_mid"]) == ("2026-10-27", 25000.0, 172.4)
    strikes = {q["strike"] for q in summary["chain_near_spot"]}
    assert min(strikes) >= 25012.4 * 0.95 and max(strikes) <= 25012.4 * 1.05 and len(summary["atm_by_expiry"]) == 2


def test_the_input_hash_is_of_the_canonical_json_and_moves_with_any_value():
    built = build_v4_input(who(BOOK3_AI), a_pack(), closes(), None, None)
    assert input_sha256(built) == input_sha256(dict(reversed(list(built.items()))))  # key order never matters
    moved = build_v4_input(who(BOOK3_AI), replace(a_pack(), spot=Level(25013.0, at(14, 30, 1))), closes(), None, None)
    assert input_sha256(moved) != input_sha256(built)


def test_a_full_packs_input_fits_the_64_kib_pointer():
    for book, rules, width in ((BOOK3_AI, None, None), (BOOK2_HYBRID, RULES, 0.10)):
        size = len(canonical(build_v4_input(who(book), a_pack(), closes(), rules, width)))
        assert size < POINTER_CAP * 0.6, size  # measured, with room for the pointer's other fields
