"""Story R3 criterion 8: B0, the repository's measurement version, parses, is registered `research` and is shadowed
from the next session (its account is opened in each run); its first decision record is on the first session of a
30-45 day window, 16 Nov 2026 (judge 233). `is_measurement` is true for B0 alone."""

from datetime import date, timedelta

from fno.composition import build_session_calendar
from fno.config import ROOT
from fno.constants import PlaybookStatus
from fno.playbook.loader import PlaybookLoader, registry_path
from fno.playbook.measurement import is_measurement
from fno.playbook.opportunities import SHADOW, OpportunityFinder
from fno.playbook.registry import Registry
from fno.research_engine.cycles import TradingDays

REGISTERED = date(2026, 10, 16)
EXPIRIES = (date(2026, 11, 23), date(2026, 12, 29))  # NIFTY monthly: 24 Nov is a holiday, so November's is the 23rd


def repository_playbook():
    folder = ROOT / "playbook"
    return PlaybookLoader(folder, Registry(registry_path(folder)), ()).load()


def test_b0_is_a_registered_research_version_shadowed_from_the_next_session():
    playbook = repository_playbook()
    b0 = playbook.get("b0-monthly-sc", 1)
    assert b0.status == PlaybookStatus.RESEARCH and b0.structure.code == "SC" and b0.entry_conditions == ()
    assert b0 not in playbook.shadow_on(REGISTERED) and b0 in playbook.shadow_on(date(2026, 10, 19))
    assert b0 not in playbook.approved_on(date(2026, 10, 19))


def test_only_b0_is_a_measurement():
    playbook = repository_playbook()
    assert {s.name for s in playbook.strategies if is_measurement(s)} == {"b0-monthly-sc"}
    assert not is_measurement(playbook.get("example-sc-iv-rich-no-event", 1)) and not is_measurement(None)


def test_b0_s_first_decision_is_on_16_nov_the_first_session_of_december_s_window():
    """D2 records a shadow only on an opportunity: November's 30-45 day window opened on 9 Oct, before registration;
    December's opens on Sat 14 Nov, so nothing is recorded for B0 until Mon 16 Nov."""
    b0 = repository_playbook().get("b0-monthly-sc", 1)
    finder = OpportunityFinder(TradingDays(build_session_calendar()))
    days = [REGISTERED + timedelta(days=n) for n in range(1, 46)]
    found = {day: finder.find(b0, day, EXPIRIES, SHADOW) for day in days}
    [first] = [day for day, opportunities in found.items() if opportunities]
    assert first == date(2026, 11, 16) and [o.context.expiry for o in found[first]] == [date(2026, 12, 29)]
