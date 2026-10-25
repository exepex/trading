"""STAB1: an edition builds its Drive-backed parts on first use, once, and then behaves as they do."""

from datetime import date, datetime

from fno.forecast_lab.edition_run import LazyComposer, LazyRecords

DAY = date(2026, 10, 26)


class Records:
    def __init__(self):
        self.calls = []

    def report(self, day):
        self.calls.append(("report", day))
        return "written"

    def write_report(self, day, report):
        self.calls.append(("write_report", day, report))

    def posted(self, day):
        self.calls.append(("posted", day))
        return True

    def mark_posted(self, day, outcome):
        self.calls.append(("mark_posted", day, outcome))

    def alerted(self, day):
        self.calls.append(("alerted", day))
        return False

    def mark_alerted(self, day, outcomes):
        self.calls.append(("mark_alerted", day, outcomes))


def test_the_records_are_built_on_first_use_once_and_every_call_reaches_them():
    built, real = [], Records()
    lazy = LazyRecords(lambda: built.append(1) or real)
    assert built == []
    assert lazy.report(DAY) == "written" and lazy.posted(DAY) is True and lazy.alerted(DAY) is False
    lazy.write_report(DAY, "r")
    lazy.mark_posted(DAY, "sent")
    lazy.mark_alerted(DAY, ["sent"])
    assert built == [1]
    assert [call[0] for call in real.calls] == ["report", "posted", "alerted", "write_report", "mark_posted",
                                                "mark_alerted"]  # fmt: skip
    assert real.calls[-1] == ("mark_alerted", DAY, ["sent"])


def test_the_composer_is_built_on_the_first_report_once():
    built, now = [], datetime(2026, 10, 26, 8, 38)

    class Real:
        def compose(self, day, at):
            return ("report", day, at)

    lazy = LazyComposer(lambda: built.append(1) or Real())
    assert built == []
    assert lazy.compose(DAY, now) == ("report", DAY, now) and lazy.compose(DAY, now) == ("report", DAY, now)
    assert built == [1]
