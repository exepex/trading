"""FL1-1d: the morning confirms each earlier evening's check against NSE's official close: confirmed, a different
close with the same verdict, or a correction (with one alert) when the verdict changes; a close not archived yet is
taken up by a later morning, and nothing is confirmed twice."""

from datetime import date

from fno.forecast_lab.composers import MorningComposer
from fno.forecast_lab.confirm import Confirmation
from fno.forecast_lab.maker import Made
from fno.forecast_lab.written import Verdict, WrittenReport

from .builders import SESSIONS, at

FRI, MON, TUE = date(2026, 10, 23), date(2026, 10, 26), date(2026, 10, 27)
BAND = (25000.0, 25200.0, 25400.0, 25600.0)


def verdict(day, close=25390.0):
    inside_50, inside_90 = BAND[1] <= close <= BAND[2], BAND[0] <= close <= BAND[3]
    return Verdict("NIFTY", day, "implied", close, inside_50, inside_90, BAND)


class Closes:
    def __init__(self, closes):
        self.closes = closes

    def close(self, underlying, day):
        return self.closes.get(day)


def confirmation(evenings, official, mornings=None):
    evening_records = {d: WrittenReport("", (), verdicts=(v,)) for d, v in evenings.items()}
    return Confirmation(evening_records.get, (mornings or {}).get, Closes(official), SESSIONS)


def test_an_agreeing_official_close_confirms_the_evening_s_check():
    confirmed = confirmation({FRI: verdict(FRI)}, {FRI: 25390.0}).confirm(MON)
    assert confirmed.lines == ("NIFTY Fri 23 Oct: the evening's check stands (official close 25,390.00)",)
    assert confirmed.alerts == () and confirmed.keys == ("NIFTY 2026-10-23",)


def test_a_different_close_with_the_same_verdict_is_noted_without_an_alert():
    confirmed = confirmation({FRI: verdict(FRI)}, {FRI: 25380.0}).confirm(MON)
    assert confirmed.lines == ("NIFTY Fri 23 Oct: official close 25,380.00, not 25,390.00 as read in the evening; "
                               "the verdict stands",) and confirmed.alerts == ()  # fmt: skip


def test_a_changed_verdict_is_a_correction_with_one_alert():
    confirmed = confirmation({FRI: verdict(FRI, close=25399.0)}, {FRI: 25401.5}).confirm(MON)
    (line,) = confirmed.lines
    assert line == ("NIFTY Fri 23 Oct: CORRECTION: the official close 25,401.50 (read 25,399.00 in the evening) makes "
                    "it Close call, not Correct") and confirmed.alerts == (line,)  # fmt: skip


def test_a_close_not_archived_waits_for_a_later_morning_and_a_settled_one_is_never_confirmed_again():
    first = confirmation({FRI: verdict(FRI)}, {}).confirm(MON)
    assert first.lines == ("NIFTY Fri 23 Oct: the official close is not archived yet; confirmed in a later morning",)
    assert first.keys == ()
    later = confirmation({FRI: verdict(FRI)}, {FRI: 25390.0}, {MON: WrittenReport("", (), matched=first.keys)})
    settled = later.confirm(TUE)
    assert settled.keys == ("NIFTY 2026-10-23",)
    done = confirmation({FRI: verdict(FRI)}, {FRI: 25390.0}, {TUE: WrittenReport("", (), matched=settled.keys)})
    assert done.confirm(date(2026, 10, 28)).lines == ()


def test_the_morning_report_keeps_what_it_confirmed_and_its_correction_alert():
    class Maker:
        def make(self, day, now, edition, alerts=(), checks="", confirmation=()):
            self.seen = (edition, alerts, confirmation)
            return Made("text", (), ("picture alert",), ())

    maker = Maker()
    written = MorningComposer(maker, confirmation({FRI: verdict(FRI, 25399.0)}, {FRI: 25401.5})).compose(
        MON, at(MON, 8, 50)
    )
    assert written.matched == ("NIFTY 2026-10-23",) and len(written.alerts) == 2
    assert maker.seen[0] == "morning" and maker.seen[2][0].startswith("NIFTY Fri 23 Oct: CORRECTION")
