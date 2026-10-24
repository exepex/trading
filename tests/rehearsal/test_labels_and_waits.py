"""REH1, acceptance 3 and the owner's accelerated clock: every post through each Slack port starts with the label;
a rehearsal's wait jumps outside the capture windows, never past a part's start, and runs at real speed inside."""

from datetime import UTC, datetime, timedelta

from fno.alerts.sender import AlertSender
from fno.cards.posting import CardPoster
from fno.forecast_lab.delivery import ReportPoster
from fno.rehearsal.alert_label import LabelledAlerts
from fno.rehearsal.card_label import LabelledCardPoster
from fno.rehearsal.report_label import LabelledReportPoster
from fno.rehearsal.waits import SkippingWaiter

LABEL = "*DRY RUN, 2026-10-23 replay, not a real trading day*\nNot yet in rehearsal: x"


class Sent(AlertSender, CardPoster, ReportPoster):
    def __init__(self):
        self.texts = []

    def send(self, text):
        self.texts.append(text)
        return "sent"

    def post(self, text, attachments=None):
        self.texts.append(text)
        return "posted"


def test_each_port_s_decorator_puts_the_label_first_and_changes_nothing_else():
    sent = Sent()
    LabelledAlerts(sent, LABEL).send("alert")
    LabelledCardPoster(sent, LABEL).post("card")
    LabelledReportPoster(sent, LABEL).post("edition", [])
    assert sent.texts == [f"{LABEL}\nalert", f"{LABEL}\ncard", f"{LABEL}\nedition"]


T = datetime(2026, 10, 23, 8, 41, tzinfo=UTC)  # 14:11 IST


class Day:
    def __init__(self):
        self.now, self.parts_start, self.recording_until = T, T + timedelta(minutes=27), None  # parts at 14:38
        self.inner = []

    def jump_to(self, moment):
        self.now = max(self.now, moment)

    def recording(self):
        return self.recording_until is not None and self.now < self.recording_until

    def next_start(self):
        return self.parts_start

    def until(self, moment):  # the run's own waiter: services the parts, sleeps for real
        self.inner.append(moment)
        if self.parts_start is not None and self.now >= self.parts_start:
            self.parts_start, self.recording_until = None, self.now + timedelta(minutes=35)  # 14:38-15:13
        self.now = max(self.now, moment)


def waiter(day):
    return SkippingWaiter(day, lambda: day.now, day.jump_to, day.recording, day.next_start)


def test_a_skip_stops_at_the_parts_start_and_the_window_then_runs_at_real_speed():
    day = Day()
    waiter(day).until(T + timedelta(minutes=47))  # the desk's 14:58
    assert day.now == T + timedelta(minutes=47)
    assert T + timedelta(minutes=27) in day.inner  # the parts were serviced at 14:38, not skipped past
    steps = [b - a for a, b in zip(day.inner, day.inner[1:]) if b > T + timedelta(minutes=27)]
    assert steps and max(steps) <= timedelta(seconds=5)  # inside the window: 5-second real-speed steps


def test_with_nothing_to_record_a_wait_jumps_straight_to_its_moment():
    day = Day()
    day.parts_start = None
    waiter(day).until(T + timedelta(hours=1))
    assert day.now == T + timedelta(hours=1) and len(day.inner) <= 2


def test_a_clock_that_does_not_move_falls_back_to_a_real_wait_and_never_spins():
    day = Day()
    day.parts_start = None
    day.jump_to = lambda moment: None  # the replay clock is not this process's clock
    waiter(day).until(T + timedelta(hours=1))
    assert day.inner[-1] == T + timedelta(hours=1)
