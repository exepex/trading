"""A14c families (owner, 16 Oct 2026): the factor file's one-time header change keeps every data row's bytes, the rows
written before it are read as `all`, each family carries only its own measured value, a family with no row is refused
by name, and the wired run measures only SF, SC and BF (C2 caps the STR1 codes' stressed SPAN)."""

from datetime import date

import pytest

from fno.composition import build_tradable_structures
from fno.config import load_app_config
from fno.constants import (
    FAMILY_DEBIT,
    OPTION_CALL,
    OPTION_PUT,
    STRESS_FACTOR_COLUMNS,
    STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES,
    STRUCTURE_FAMILIES,
)
from fno.nse_margins.stress_log import StressFactorFile, StressRowRefused
from fno.nse_margins.wiring import build_stress_factor_run
from fno.research_engine.structures import payoff_bounds

from .stress_days import planted, sf_tracker
from .test_prefetch import SlowDrive
from .test_stress_run import RUN_DAY, SPIKE, THROUGH, family_row, run

OLD_HEADER = ",".join(STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES) + "\n"
NEW_HEADER = ",".join(STRESS_FACTOR_COLUMNS) + "\n"
OLD_ROWS = (
    '2026-10-14,1.45,,,applied,"owner seed: response 77, decision 14 Oct",,\n'
    "2026-10-16,2.1,2.1,2.081729,applied,PDS 300 entered 2020-04-08 peak 2020-05-04 needed 2.0817,2026-10-15,"
    "54d0ab13ce131fff95a6e9108586d728944d746ce9e5d4b130d730a75cece46c\n"
)


def old_file(tmp_path):
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "stress_factor.csv"
    path.write_text(OLD_HEADER + OLD_ROWS, encoding="utf-8")
    return path


def test_the_first_family_run_changes_only_the_header_line(tmp_path):
    path = old_file(tmp_path)
    code, _, _ = run(tmp_path, planted(THROUGH, {SPIKE: 20.0}), run_day=date(2026, 11, 5))
    data = path.read_bytes()
    assert code == 0 and data.startswith((NEW_HEADER + OLD_ROWS).encode("utf-8"))
    assert [line.rsplit(",", 1)[1] for line in data.decode("utf-8").splitlines()[3:]] == ["debit", "credit"]
    assert not path.with_suffix(".tmp").exists()


def test_rows_written_before_the_family_column_are_read_as_all_and_force_a_full_run(tmp_path):
    """2.1 (an `all` row) stays in force for both families, but its measured value is no family's floor."""
    factor_file = StressFactorFile(old_file(tmp_path))
    for family in ("debit", "credit"):
        last = factor_file.last(family)
        assert (last.factor, last.unrounded, last.coverage_through) == (2.1, None, None)


def test_each_family_carries_only_its_own_measured_value(tmp_path):
    files = planted(date(2026, 12, 8), {SPIKE: 20.0})
    run(tmp_path, files, run_day=RUN_DAY)  # full: credit 1.686747 (SF), debit 1.0 (BF)
    _, credit, _ = run(tmp_path, files, run_day=date(2026, 12, 9))
    debit = family_row(tmp_path / "stress_factor.csv", "debit")
    assert credit[3] == "1.686747" and credit[5] == "carried from the run through 2026-11-04"
    assert debit[0] == "2026-12-09" and debit[3] == "1.000000" and debit[4] == "held" and debit[1] == "1.45"


def test_a_later_all_row_is_in_force_but_never_a_floor(tmp_path):
    path = tmp_path / "stress_factor.csv"
    path.write_text(NEW_HEADER + OLD_ROWS.splitlines(keepends=True)[0]
                    + "2026-10-20,1.6,1.6,1.550000,applied,BF 100,2026-10-19,ab,debit\n"
                    + "2026-10-21,1.8,1.8,,applied,owner hand value,2026-10-20,,all\n", encoding="utf-8")  # fmt: skip
    last = StressFactorFile(path).last("debit")
    assert (last.factor, last.unrounded, last.coverage_through) == (1.8, 1.55, date(2026, 10, 19))


def test_a_family_with_neither_its_own_row_nor_an_all_row_is_refused_by_name(tmp_path):
    path = tmp_path / "stress_factor.csv"
    path.write_text(NEW_HEADER + "2026-10-20,1.6,1.6,1.550000,applied,BF 100,2026-10-19,ab,debit\n", encoding="utf-8")
    with pytest.raises(StressRowRefused, match="no row for credit"):
        StressFactorFile(path).last("credit")


def test_a_run_that_cannot_measure_a_family_writes_no_row(tmp_path):
    code, row, sent = run(tmp_path, planted(THROUGH, {SPIKE: 20.0}), tracker=sf_tracker)
    assert code == 1 and row[0] == "2026-10-14" and "no debit holding completed in the archive" in sent[0]


def test_the_wired_run_measures_only_the_structures_c2_does_not_cap(tmp_path):
    run_ = build_stress_factor_run(load_app_config(), date(2026, 11, 8), day_file=SlowDrive(), root=tmp_path)
    assert sorted(s.code for s in run_.sources.new_tracker().structures) == ["BF", "SC", "SF"]


def test_one_family_without_its_own_measured_row_makes_the_whole_run_full(tmp_path):
    """Credit has a measured row, debit only the `all` seed: the run reads every session from the first."""
    rows = OLD_ROWS.splitlines(keepends=True)[0] + "2026-11-05,1.7,1.7,1.686747,applied,SF 100,2026-11-04,ab,credit\n"
    code, credit, _ = run(tmp_path, planted(date(2026, 12, 8), {SPIKE: 20.0}), run_day=date(2026, 12, 9), rows=rows)
    evidence = (tmp_path / "evidence" / "stress_evidence_2026-12-09.md").read_text(encoding="utf-8")
    assert code == 0 and evidence.startswith("# Stress factor run 2026-12-09 (full)")
    assert credit[3] == "1.686747" and "carried" not in credit[5]


def test_every_tradable_structure_has_the_family_its_payoff_bounds_give():
    """Debit: the position is never worth less than 0; credit: never more than 0 (story text). Every structure the
    desk may build has one family, and the table names no other code."""
    chain = frozenset((float(k), kind) for k in range(23_000, 27_001, 50) for kind in (OPTION_CALL, OPTION_PUT))
    codes = set()
    for structure in build_tradable_structures():
        for width in (100.0, 200.0, 300.0):
            least, most = payoff_bounds(structure.legs(chain, 25_000.0, width))
            family = STRUCTURE_FAMILIES[structure.code]
            assert least >= 0 if family == FAMILY_DEBIT else most <= 0, (structure.code, width, least, most)
        codes.add(structure.code)
    assert codes == set(STRUCTURE_FAMILIES)


@pytest.mark.parametrize("ending", ["\r\n", ""], ids=["CRLF", "no last newline"])
def test_the_header_change_keeps_crlf_bytes_and_a_missing_last_newline(tmp_path, ending):
    """Line 1 alone changes (its own line ending kept); a file without a last newline gets one before the new rows."""
    path = tmp_path / "stress_factor.csv"
    body = OLD_ROWS.replace("\n", ending) if ending else OLD_ROWS.rstrip("\n")
    header = OLD_HEADER.replace("\n", ending or "\n")
    path.write_bytes((header + body).encode("utf-8"))
    run(tmp_path, planted(THROUGH, {SPIKE: 20.0}))
    kept = NEW_HEADER.replace("\n", ending or "\n") + body
    data = path.read_bytes().decode("utf-8")
    assert data.startswith(kept)
    added = data[len(kept) :].strip("\r\n").splitlines()
    assert [line.rsplit(",", 1)[1] for line in added] == ["debit", "credit"]


def test_a_header_that_is_not_one_of_the_two_exact_lines_writes_nothing(tmp_path):
    """A quoted header passes every reader, but rows appended under the old one would be read as `all`."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "stress_factor.csv"
    quoted = ",".join(f'"{name}"' for name in STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES) + "\n"
    path.write_text(quoted + OLD_ROWS, encoding="utf-8")
    code, _, sent = run(tmp_path, planted(THROUGH, {SPIKE: 20.0}))
    assert code == 1 and path.read_text(encoding="utf-8") == quoted + OLD_ROWS
    assert "line 1 must be exactly as_of,factor" in sent[0]


def test_a_row_with_more_fields_than_the_header_is_refused(tmp_path):
    path = tmp_path / "stress_factor.csv"
    family_row_under_old_header = "2026-10-20,1.2,1.2,1.15,applied,BF,2026-10-19,ab,debit\n"
    path.write_text(OLD_HEADER + OLD_ROWS + family_row_under_old_header, encoding="utf-8")
    with pytest.raises(StressRowRefused, match="row 4 has more fields than the header"):
        StressFactorFile(path).last("debit")


def test_one_owner_approval_applies_a_fall_in_both_families(tmp_path):
    _, credit, sent = run(tmp_path, planted(THROUGH, {SPIKE: 8.0}), approved="da0f769d")
    debit = family_row(tmp_path / "stress_factor.csv", "debit")
    assert credit[1:5] == ["1.3", "1.3", "1.253012", "applied"] and debit[1:5] == ["1", "1", "1.000000", "applied"]
    assert sent[0].count("fall approved by the owner, DESK_DECISIONS da0f769d") == 2
