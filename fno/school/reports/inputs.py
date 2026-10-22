"""What the sections read (story MS-P1g): small ports, so the sections know no store. The join-up (MS-P1j) wires them
to the roads, the dashcam's records, the ticket counts and the driver cards; tests use plain fakes."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from ..constants import DriverRole, RoadCode
from ..contracts.roads import RoadDay
from ..contracts.slot_file import SlotRecord
from ..contracts.tickets import OpportunityCounts


@dataclass(frozen=True)
class PlannedTrade:
    """One line of the 08:50 plan, made from yesterday's data with indicative prices; booked at the slot or dropped."""

    driver_id: str
    role: DriverRole
    road: RoadCode
    structure: str  # a structure code such as "PCS"; never a strike or a contract
    worst_loss: float  # rupees, every charge and pad included


class TodayInputs(Protocol):
    def roads(self, session: date) -> tuple[RoadDay, ...]:
        """The roads as the latest completed capture left them, closed ones with their one reason."""

    def plan(self, session: date) -> tuple[PlannedTrade, ...]:
        """The paper trades planned for the session's 15:00 slot."""


class DayInputs(Protocol):
    def records(self, session: date) -> tuple[SlotRecord, ...]:
        """The session's sealed decision and outcome records (the dashcam's replay reader)."""

    def counts(self, session: date) -> tuple[OpportunityCounts, ...]:
        """Eligible, fillable and executed per road and driver version (story MS-P1f)."""

    def role_of(self, driver_id: str) -> DriverRole:
        """The driver card's role: only rule drivers are shown as trades."""
