"""Story STR1b criterion 3: each structure code has its own broker approval date. A code's rows are written from its
own `passed_on` on (the day before is printed, never written), adding a code moves no other date, and anything but the
code -> {source, passed_on} map is refused."""

from datetime import date, timedelta

import pytest

from fno.nse_margins.broker_approvals import Approval, BrokerApprovals
from fno.nse_margins.job import NseMarginJob

from .span_builder import DAY, span_zip
from .test_job import MORNING, Alerts, done_before, margin_log, margins_file, weekday
from .test_one_side_rows import builder

GROWW = {"source": "Groww check", "passed_on": "2026-10-01"}


def run_with(tmp_path, approvals: BrokerApprovals) -> tuple[list[str], list[str]]:
    """(the codes written for DAY, the printed lines)."""
    tmp_path.mkdir(exist_ok=True)
    path, printed = margins_file(tmp_path, done_before(DAY)), []
    day_file = lambda day: (f"nsccl.{day:%Y%m%d}.i1.zip", {DAY: span_zip()}.get(day))  # noqa: E731
    job = NseMarginJob(day_file, builder(), margin_log(path), weekday, approvals, Alerts(), lambda: MORNING,
                       printed.append)  # fmt: skip
    assert job.run() == 0
    return [line.split(",")[0] for line in path.read_text().splitlines()[8:]], printed


def test_a_code_is_written_from_its_own_day_on_and_printed_the_day_before(tmp_path):
    four_leg = {code: Approval("check", date(2026, 10, 1)) for code in ("SF", "SC", "BF")}
    on_the_day, _ = run_with(tmp_path / "a", BrokerApprovals(four_leg | {"PCS": Approval("check", DAY)}))
    assert on_the_day == ["SF", "SC", "BF", "PCS"]
    before = BrokerApprovals(four_leg | {"PCS": Approval("check", DAY + timedelta(days=1))})
    the_day_before, printed = run_with(tmp_path / "b", before)
    assert the_day_before == ["SF", "SC", "BF"] and any(line.startswith("PCS,100,") for line in printed)


def test_adding_a_code_moves_no_other_date():
    block = {"SF": GROWW, "SC": GROWW, "BF": GROWW}
    old = BrokerApprovals.from_margins_block({"nse_span_check": block})
    new = BrokerApprovals.from_margins_block({"nse_span_check": block | {"CDS": {"source": "later", "passed_on": DAY}}})
    assert {c: new.by_code[c] for c in old.by_code} == dict(old.by_code)
    assert new.approves("CDS", DAY) and not new.approves("CDS", DAY - timedelta(days=1))


@pytest.mark.parametrize(
    "block",
    [
        {"source": "x", "passed_on": "2026-10-14"},  # the old single-date shape
        {"XX": GROWW},  # an unknown code
        {"SF": {"source": "x"}},  # no date
        {"SF": {"passed_on": "2026-10-14"}},  # no source
        {"SF": "2026-10-14"},  # not a map
        ["SF"],
    ],
    ids=["old_shape", "unknown_code", "no_date", "no_source", "not_a_map", "a_list"],
)
def test_anything_but_the_code_map_is_refused(block):
    with pytest.raises(ValueError, match="nse_span_check"):
        BrokerApprovals.from_margins_block({"nse_span_check": block})


def test_no_block_approves_nothing():
    assert not BrokerApprovals.from_margins_block({}).any_by(DAY)


def test_the_first_day_is_the_earliest_approval_and_none_without_any():
    later = Approval("later", date(2026, 10, 20))
    assert BrokerApprovals({"SF": later, "SC": Approval("check", date(2026, 10, 14))}).first_day() == date(2026, 10, 14)
    assert BrokerApprovals({}).first_day() is None
