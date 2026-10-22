"""The 08:50 "Today" section (story MS-P1g): which roads are open and why one is closed, the planned paper trades with
their worst loss, the banner. Controls and measurement-only drivers are never shown as candidates (story 3.2)."""

from datetime import date

from ..constants import DriverRole
from ..contracts.reports import SectionText
from .banner import banner_for, banner_line
from .inputs import TodayInputs
from .lines import RUPEE, footer, paper_title, road_status_line

TITLE = "Today"
NO_CANDIDATE = "No candidate today: nothing is planned."
PLAN_NOTE = "Plan from yesterday's data with indicative prices; booked at each road's 15:00 slot or dropped."


class TodaySection:
    def __init__(self, inputs: TodayInputs):
        self.inputs = inputs

    def render(self, session: date) -> SectionText:
        days = self.inputs.roads(session)
        shown = [t for t in self.inputs.plan(session) if t.role is DriverRole.RULE]
        closed = sum(not d.status.open for d in days)
        banner = banner_for(closed, len(shown))
        plan = [f"{t.driver_id} {t.road}: {t.structure}, worst loss {RUPEE.format(amount=t.worst_loss)}" for t in shown]
        body = (PLAN_NOTE, *plan) if plan else (NO_CANDIDATE,)
        return SectionText(paper_title(TITLE), (banner_line(banner), road_status_line(days), *body, *footer()), banner)
