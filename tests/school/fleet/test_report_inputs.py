"""Story MS-P1j: g's two sections on j's real inputs (orchestrator's rulings, 22 Oct 2026): the 08:50 plan from the
previous slot names its source on every line and writes no record; the 20:05 section reads the sealed day and shows
the run's marks; the forecast lab's builder passes the inputs in, so no "not wired" alert."""

import hashlib
from datetime import datetime, time
from types import SimpleNamespace

from fno.models import IST
from fno.school.constants import DriverRole, RecordKind
from fno.school.contracts.clock import FixedClock
from fno.school.contracts.fleet import RunMode
from fno.school.fakes import FakeDriver, FakeMaxLossLaw
from fno.school.fleet.report_inputs import PreviousSlotToday, SealedDayInputs
from fno.school.fleet.runner import LATE_RERUN
from fno.school.reports.guard import with_school_sections
from fno.school.reports.today import TodaySection
from tests.school.contracts import builders as b
from tests.school.fleet.rig import DAY2, NoHistory, OpenGate, Rig, all_roads
from tests.school.fleet.test_rerun import crash_after
from tests.school.reports.test_editions import ON, lab_maker, make

CS1, N0 = all_roads("CS1"), all_roads("N0")
SOURCE = "plan from 02 Nov 2026 15:00 data, indicative prices, not today's quotes"


def ran(tmp_path) -> Rig:
    rig = Rig(tmp_path, (FakeDriver(CS1, b.put_spread()), FakeDriver(N0)), (FakeMaxLossLaw(10_000),))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    return rig


def inputs(rig: Rig, root):
    calendar = SimpleNamespace(previous_session=lambda session: b.SESSION)
    today = PreviousSlotToday(calendar, rig.fleet.catalogue, rig.fleet.snapshots, OpenGate(), rig.fleet.drivers,
                              NoHistory())  # fmt: skip
    roles = {"CS1@1": DriverRole.RULE, "N0@1": DriverRole.CONTROL}
    return today, SealedDayInputs(rig.dashcam, root, roles)


def stored(rig: Rig, root) -> dict:
    files = {key: hashlib.sha256(data).hexdigest() for key, data in rig.dashcam.files.items()}
    files |= {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(root.rglob("*")) if p.is_file()}
    return files | {"ledgers": repr(rig.accounts.ledgers), "tickets": repr(rig.ticket_accounts.ledgers)}


def test_every_08_50_line_names_its_source_and_the_plan_writes_no_record(tmp_path):
    rig = ran(tmp_path)
    today, _ = inputs(rig, tmp_path)
    before = stored(rig, tmp_path)
    text = TodaySection(today).render(DAY2)
    assert [t.driver_id for t in today.plan(DAY2)] == ["CS1@1"], "rule drivers only, from the previous slot"
    labelled = [line for line in text.lines if not line.startswith(("Paper", "NSE", "No latency"))]
    assert labelled[0].startswith("Banner:") and all(line.endswith(f"({SOURCE})") for line in labelled[:4])
    assert stored(rig, tmp_path) == before, "no dashcam file, account, ticket or counts file written"


def test_both_sections_render_from_the_real_inputs_passed_in_by_the_caller(tmp_path):
    rig = ran(tmp_path)
    for edition, title in (("morning", "Today"), ("evening", "How did today go")):
        maker = with_school_sections(lab_maker(edition), ON, inputs=lambda config: inputs(rig, tmp_path))
        made = make(maker, edition)
        assert made.alerts == () and f"School pilot, {title} (Paper" in made.text


def test_a_rerun_after_15_30_is_marked_and_the_evening_section_shows_the_mark(tmp_path):
    rig = ran(tmp_path)
    crash_after(rig, tmp_path, b.SESSION, RecordKind.OUTCOMES, RecordKind.DRIFT)
    rig.fleet.clock = FixedClock(datetime.combine(b.SESSION, time(16, 0), IST))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    _, day = inputs(rig, tmp_path)
    assert day.marks(b.SESSION) == (LATE_RERUN,)
    maker = with_school_sections(lab_maker("evening"), ON, inputs=lambda config: inputs(rig, tmp_path))
    made = maker.make(b.SESSION, datetime(2026, 11, 2, 20, 5), "evening", (), "a\n\nb")
    assert LATE_RERUN in made.text


def test_a_rerun_of_a_complete_session_after_15_30_adds_no_mark(tmp_path):
    rig = ran(tmp_path)
    rig.fleet.clock = FixedClock(datetime.combine(b.SESSION, time(16, 0), IST))
    rig.fleet.run(b.SESSION, RunMode.REPLAY)
    assert inputs(rig, tmp_path)[1].marks(b.SESSION) == ()


def test_the_day_inputs_pass_the_instructor_s_why_lines_through_and_none_without_a_source(tmp_path):
    rig = ran(tmp_path)
    _, plain = inputs(rig, tmp_path)
    source = SimpleNamespace(lines=lambda session: ("CS1@1 BANKNIFTY-M: net Rs -140; why: wrong direction",))
    with_why = SealedDayInputs(rig.dashcam, tmp_path, {}, source)
    assert plain.why(b.SESSION) == () and with_why.why(b.SESSION) == source.lines(b.SESSION)
