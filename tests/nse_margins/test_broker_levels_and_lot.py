"""A14c part 2 after judge 630: exposure judged over NIFTY's two readings (before the first basket and after the last),
so a move during the run is never a false mismatch; the one lot checked against NSE's dated lot (A20a's file) before
any basket is sent; and the wiring needing neither the Groww SDK nor Drive until a request is due."""

import sys
from datetime import date

from fno.nse_margins.broker_compare import Levels, compare
from fno.nse_margins.broker_lot import NseDatedLot
from fno.nse_margins.calculator import NseIndexOptionExposure
from fno.school.constants import ClosureReason
from fno.school.contracts.roads import DatedLot
from fno.school.roads.ports import LotProblem

from .broker_fakes import BASKETS, LEVEL, LOT, FakeBroker, at, exposure_at, make_check
from .span_builder import DAY

SF100 = ("SF", 100.0)
MOVED = LEVEL * 1.0012  # judge 630's case: NIFTY +0.12% while the baskets are asked


def _charged_at(broker: FakeBroker, level: float) -> None:
    """Groww charged every basket at `level`."""
    for key, basket in BASKETS.items():
        broker.answers[key] = (basket.span_expected, exposure_at(basket, level))


def test_a_move_during_the_run_is_inside_the_range_and_every_basket_is_ok():
    check, broker, record, alerts, *_ = make_check(at(10, 0))
    broker.after = MOVED
    _charged_at(broker, MOVED)
    assert check.run() == 0 and alerts.sent == []
    assert {r.status for r in record.written[0]} == {"ok"}
    assert {(r.levels.before, r.levels.after) for r in record.written[0]} == {(LEVEL, MOVED)}


def test_the_same_answers_against_a_still_reading_are_mismatches():
    """Why the second reading matters: with NIFTY read still, the moved charges are beyond 0.1%."""
    check, broker, record, alerts, *_ = make_check(at(10, 0))
    _charged_at(broker, MOVED)
    check.run()
    short_legged = [r for r in record.written[0] if r.exposure_expected]
    assert short_legged and {r.status for r in short_legged} == {"mismatch"} and len(alerts.sent) == 1


def test_a_planted_wrong_exposure_on_a_still_index_is_a_mismatch_and_inside_a_moving_range_too():
    basket = BASKETS[SF100]
    for after in (None, MOVED):
        check, broker, record, *_ = make_check(at(10, 0))
        broker.after = after
        broker.answers[SF100] = (basket.span_expected, exposure_at(basket, max(LEVEL, after or LEVEL)) * 1.002)
        check.run()
        assert record.written[0][0].status == "mismatch", after


def test_no_second_reading_judges_at_the_first_and_never_calls_a_mismatch():
    basket = BASKETS[SF100]
    check, broker, record, alerts, printed, _ = make_check(at(10, 0))
    broker.after = ConnectionError("token=secret")
    broker.answers[SF100] = (basket.span_expected, exposure_at(basket) * 1.002)
    assert check.run() == 1 and alerts.sent == []
    first, *rest = record.written[0]
    assert first.status == "error" and "no second reading (NIFTY quote: ConnectionError)" in first.detail
    assert {r.status for r in rest} == {"ok"} and first.levels == Levels(LEVEL, None, "NIFTY quote: ConnectionError")
    assert "secret" not in "".join(printed)


def test_a_rate_step_inside_the_range_is_an_error_not_a_guess():
    """SF 100's short 20,000 call is more than 10% out of the money below NIFTY 18,181.82: two rates in the range."""
    basket = BASKETS[SF100]
    rule = NseIndexOptionExposure()
    answer = (basket.span_expected, rule.per_unit(basket.legs, 18_182.0, basket.expiry, DAY) * LOT)
    found = compare(basket, answer, Levels(18_181.0, 18_183.0), rule, LOT, DAY)
    assert found.status == "error" and found.detail == "exposure rate step inside the NIFTY range 18181.00-18183.00"
    still = compare(basket, answer, Levels(18_182.0, 18_183.0), rule, LOT, DAY)
    assert still.status == "ok"  # one rate in the range: linear, judged as usual


def test_a_lot_differing_from_nse_s_dated_lot_sends_no_basket():
    check, broker, record, alerts, printed, _ = make_check(at(10, 0), dated_lot=lambda day, expiry: LOT + 10)
    assert check.run() == 1 and broker.asked == [] and alerts.sent == []
    expiry = BASKETS[SF100].expiry
    assert {r.detail for r in record.written[0]} == {f"lot {LOT} differs from NSE's dated lot {LOT + 10} for {expiry}"}


def test_no_dated_lot_or_an_unreadable_lot_file_is_an_error_retried_the_same_day():
    for dated_lot, want in (
        (lambda day, expiry: "lot_unavailable", "no dated NSE lot for 2026-11-23 on 2026-10-14 (lot_unavailable)"),
        (lambda day, expiry: (_ for _ in ()).throw(ConnectionError("x")), "ConnectionError"),
    ):
        check, broker, record, *_ = make_check(at(10, 0), dated_lot=dated_lot)
        assert check.run() == 1 and broker.asked == []
        assert {(r.status, r.detail) for r in record.written[0]} == {("error", want)}


def test_the_dated_lot_is_read_with_the_school_s_reader_for_the_basket_s_expiry_month():
    asked = []

    class Lots:
        def __init__(self, found):
            self.found = found

        def lot(self, underlying, session, expiries):
            asked.append((underlying, session, expiries))
            return self.found

    expiry = date(2026, 11, 24)
    dated = NseDatedLot(lambda: Lots(DatedLot(65, "fo_mktlots.csv")))
    assert dated(DAY, expiry) == dated(DAY, expiry) == 65  # read once a run: 15 baskets, one Drive download
    assert NseDatedLot(lambda: Lots(LotProblem(ClosureReason.LOT_UNAVAILABLE)))(DAY, expiry) == "lot_unavailable"
    assert asked == [("NIFTY", DAY, (expiry,))] * 2


def test_the_wiring_uses_the_row_builder_s_lot_and_needs_no_groww_sdk(monkeypatch):
    """CI installs requirements.txt only: no `growwapi`. Building the check imports nothing of it (judge 630)."""
    from fno.config import load_app_config
    from fno.nse_margins import broker_wiring

    monkeypatch.setitem(sys.modules, "growwapi", None)  # any import of it now fails
    monkeypatch.setattr(broker_wiring, "now_ist", lambda: at(9, 0))
    cfg = load_app_config()
    check = broker_wiring.build_broker_check(cfg, env={})
    check.print_line = lambda line: None
    assert check.run() == 0
    assert check.lot_size == check.parts.baskets.builder.calculator.lot_size == cfg["lot_sizes"]["NIFTY"]
    assert isinstance(check.parts.dated_lot, NseDatedLot)
