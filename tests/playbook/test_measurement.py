"""Story R3 criterion 8: B0, the repository's measurement version, parses, is registered `research` and is shadowed
from the next session; `is_measurement` is true for it alone (the worked example is not a measurement)."""

from datetime import date

from fno.config import ROOT
from fno.constants import PlaybookStatus
from fno.playbook.loader import PlaybookLoader, registry_path
from fno.playbook.measurement import is_measurement
from fno.playbook.registry import Registry

REGISTERED = date(2026, 10, 16)


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
