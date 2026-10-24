"""A4h criterion 8 (judge 440 SF1): O1 keeps every printed line in the public `journal/runs/<date>.json`, and an alert
Slack did not take is printed with its text, so no line and no alert of any path holds a planted level in any format."""

from datetime import date

from fno.close_read.constants import READ, RECHECK
from tests.close_read.fakes import DAY, PREVIOUS, Alerts, Answers, Clock, MemoryStore, Official, answer, at, reader

PLANTED = {"NIFTY 50": (22811.37, 23016.43), "NIFTY BANK": (54976.91, 55707.82), "INDIA VIX": (15.71, 14.79)}
MOVED = {"NIFTY 50": (22813.47, 23016.43), "NIFTY BANK": (54979.13, 55707.82), "INDIA VIX": (16.93, 14.79)}
RANGES = {"NIFTY 50": (23121.37, 22650.13, 22889.17), "NIFTY BANK": (55868.33, 54697.29, 55488.43),
          "INDIA VIX": (17.21, 14.53, 14.83)}  # fmt: skip
MOVED_RANGES = {"NIFTY 50": (23123.61, 22650.13, 22889.17), "NIFTY BANK": (55868.33, 54695.07, 55488.43),
                "INDIA VIX": (17.21, 14.53, 14.91)}  # fmt: skip
OFFICIAL_RANGES = {"Nifty 50": (23119.71, 22651.47), "Nifty Bank": (55866.19, 54698.53), "India VIX": (17.97, 14.41)}
OFFICIAL = {"Nifty 50": 22817.59, "Nifty Bank": 54971.27, "India VIX": 17.83}  # differs: the alert path runs too
NEXT, LATER = date(2026, 10, 22), date(2026, 10, 26)


def _forms(value: float) -> set[str]:
    """Each way a level could be printed; whole numbers only for index levels (VIX's 16 would match a "16:00")."""
    forms = {f"{value}", f"{value:.2f}", f"{value:,.2f}", f"{value:.1f}", f"{value:,.1f}"}
    return forms | ({f"{round(value)}", f"{round(value):,}"} if value >= 1000 else set())


def _every_path() -> list[str]:
    store, out, alerts = MemoryStore(), [], Alerts()

    def run(source, now, which=READ, official=None):
        reader(store, source, Clock(now), official or Official(), alerts, out).run(which)

    run(Answers(answer(levels=PLANTED, ranges=RANGES)), at(15, 40))  # the read
    run(Answers(answer(levels=PLANTED, ranges=RANGES)), at(15, 45))  # a rerun
    run(Answers(answer(levels=MOVED, ranges=MOVED_RANGES)), at(16, 0), RECHECK)  # the recheck, every index moved
    run(
        Answers(answer("21-Oct-2026 15:29", levels=PLANTED, ranges=RANGES)), at(16, 0, day=date(2026, 10, 22))
    )  # a refusal
    run(Answers(answer(levels=PLANTED, ranges=RANGES)), at(16, 0, day=date(2026, 10, 23)), RECHECK)  # read at recheck
    run(
        Answers(answer(levels=PLANTED, ranges=RANGES)),
        at(15, 41, day=LATER),
        official=Official({DAY: OFFICIAL}, ranges=OFFICIAL_RANGES),
    )  # the confirms
    return out + alerts.sent


def test_no_printed_line_or_alert_holds_a_planted_level_in_any_format():
    text = "\n".join(_every_path())
    assert "close confirm 2026-10-21: NIFTY 50 differs by" in text and "close recheck" in text  # every path ran
    assert "high differs by" in text and "previous_close differs by" in text  # A4h-2's fields reached the lines
    planted = (*PLANTED.values(), *MOVED.values(), *RANGES.values(), *MOVED_RANGES.values(), *OFFICIAL_RANGES.values())
    values = [v for group in planted for v in group] + list(OFFICIAL.values()) + list(PREVIOUS.values())
    found = sorted(form for value in values for form in _forms(value) if form in text)
    assert found == []
