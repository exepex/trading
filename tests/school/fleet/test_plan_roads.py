"""Story MS-P1j4: the 08:50 plan asks each rule driver about its own card's roads only, as the slot does, and names a
driver whose plan failed instead of dropping it silently. Real drivers raise `OutOfScope` for another road
(`drivers/scope.py`); before this story that one raise emptied every driver's plan whenever NIFTY-W was open."""

from types import SimpleNamespace

from fno.school.constants import RoadCode
from fno.school.drivers.scope import check_scope
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.report_inputs import PreviousSlotToday
from fno.school.reports.today import TodaySection
from tests.school.contracts import builders as b
from tests.school.fleet.rig import NoHistory, OpenGate, Rig

ROADS = (RoadCode.BANKNIFTY_MONTHLY, RoadCode.NIFTY_WEEKLY)


class Scoped(FakeDriver):
    """A's fake driver with the real drivers' scope check: another road is a caller bug and raises."""

    def decide(self, road_day, snapshot, history, positions):
        check_scope(self.card, road_day, snapshot)
        return super().decide(road_day, snapshot, history, positions)


class Broken(FakeDriver):
    def decide(self, *args):
        raise KeyError("CE 54800 at 412.5")  # a message with a contract and a price: never shown


def planner(tmp_path, *drivers) -> PreviousSlotToday:
    rig = Rig(tmp_path, drivers, (FakeMaxLossLaw(10_000),), open_roads=ROADS)
    calendar = SimpleNamespace(previous_session=lambda session: b.SESSION)
    return PreviousSlotToday(calendar, rig.fleet.catalogue, rig.fleet.snapshots, OpenGate(), drivers, NoHistory())


def test_a_monthly_driver_plans_on_its_own_road_while_the_weekly_road_is_open_too(tmp_path):
    today = planner(tmp_path, Scoped(b.card("CS1"), b.put_spread()))  # BANKNIFTY-M only
    assert [(t.driver_id, t.road) for t in today.plan(b.SESSION)] == [("CS1@1", RoadCode.BANKNIFTY_MONTHLY)]
    assert today.not_planned(b.SESSION) == ()


def test_a_failing_driver_is_named_by_class_and_the_others_still_plan(tmp_path):
    today = planner(tmp_path, Broken(b.card("DB1"), b.put_spread()), Scoped(b.card("CS1"), b.put_spread()))
    assert [t.driver_id for t in today.plan(b.SESSION)] == ["CS1@1"]
    assert today.not_planned(b.SESSION) == ("DB1@1 (driver_error: KeyError)",)


def test_the_08_50_section_shows_the_failed_driver_and_never_its_message(tmp_path):
    today = planner(tmp_path, Broken(b.card("DB1"), b.put_spread()))
    lines = TodaySection(today).render(b.SESSION).lines
    shown = [line for line in lines if line.startswith("Not planned")]
    assert len(shown) == 1 and shown[0].startswith("Not planned, the driver failed: DB1@1 (driver_error: KeyError)")
    assert "54800" not in "\n".join(lines) and "412.5" not in "\n".join(lines)


def test_one_plan_is_made_per_session_however_often_it_is_read(tmp_path):
    calls = []

    class Counted(Scoped):
        def decide(self, *args):
            calls.append(1)
            return super().decide(*args)

    today = planner(tmp_path, Counted(b.card("CS1"), b.put_spread()))
    today.plan(b.SESSION), today.not_planned(b.SESSION), today.plan(b.SESSION)
    assert len(calls) == 1
