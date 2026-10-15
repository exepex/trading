"""Story F9a criteria 1-2: same packs and snapshot (the run log's), the rotation (a no-trade day advances it, a day
without a row does not), and a bundled role never evaluated alone; control roles are never units."""

from datetime import date

import pytest

from fno.role_value.checks import RowRefused, checked
from fno.role_value.role_set import RoleSet, RoleSetError
from tests.role_value.builders import BOOK, ROLES, row

D1, D2, D3, D4 = date(2026, 12, 2), date(2026, 12, 3), date(2026, 12, 7), date(2026, 12, 8)
LOG = {d: f"snap-{d.isoformat()}" for d in (D1, D2, D3, D4)}


def check(rows):
    return checked(rows, lambda version: ROLES, LOG)


def test_the_units_are_in_identifier_order_and_the_rotation_follows_rows_not_calendar_days():
    assert ROLES.unit_ids == ("macro", "positioning", "vol")
    rows = [row(D1, "macro"), row(D2, "positioning"), row(D3, "vol"), row(D4, "macro")]  # D2 to D3 skips 2 days
    assert check(rows) == rows


def test_a_no_trade_or_unavailable_shadow_day_still_advances_the_rotation():
    rows = [row(D1, "macro", status="shadow_unavailable", pack="", snap="x"), row(D2, "positioning")]
    assert len(check(rows)) == 2


def test_a_row_for_the_wrong_unit_is_refused_with_its_day_and_unit():
    with pytest.raises(RowRefused, match="2026-12-03 unit 'vol': the rotation schedules 'positioning'"):
        check([row(D1, "macro"), row(D2, "vol")])


def test_different_packs_are_refused():
    with pytest.raises(RowRefused, match="different packs"):
        check([row(D1, "macro", shadow_pack="other")])


def test_different_snapshots_are_refused():
    with pytest.raises(RowRefused, match="different snapshots"):
        check([row(D1, "macro", shadow_snap="snap-other")])


def test_an_equal_snapshot_that_is_not_the_run_log_s_is_refused():
    with pytest.raises(RowRefused, match="not the run log's execution snapshot"):
        check([row(D1, "macro", snap="snap-wrong")])


def test_a_role_inside_a_bundle_is_refused_alone():
    with pytest.raises(RowRefused, match="belongs to the declared bundle 'vol'"):
        check([row(D1, "volatility_trader")])
    assert ROLES.bundle_of("options_strategist") == "vol" and "options_strategist" not in ROLES.unit_ids


def test_control_roles_are_never_units():
    with pytest.raises(RoleSetError, match="control roles"):
        RoleSet.of(BOOK, "1", {"risk": ["risk_manager"]})


def test_a_role_in_two_units_is_refused():
    with pytest.raises(RoleSetError, match="exactly one unit"):
        RoleSet.of(BOOK, "1", {"a": ["macro_economist"], "b": ["macro_economist", "x"]})
