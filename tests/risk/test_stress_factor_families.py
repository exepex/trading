"""A14c families in C2 and C4 (owner, 16 Oct 2026): a proposal reads its own family's k or an `all` row, never the
other family's; an unknown code and a family with no row refuse by name; the multiplier margin and C4's stressed SPAN
use the k of the proposal's structure. Every case runs in C2 and in C4's own reader."""

from datetime import date
from pathlib import Path

import pytest

from fno.checks.validity_factor import FactorProblem, factor_on
from fno.checks.validity_margin import stressed_per_lot
from fno.checks.validity_settings import MarginSettings
from fno.constants import OPTION_CALL, OPTION_PUT, STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES
from fno.research_engine.structures import Leg, possible_value
from fno.risk.inputs import RiskInputError, TradeTerms
from fno.risk.margin_age import DaysOld
from fno.risk.margins import MarginTable, MultiplierMargin
from fno.risk.settings import StressedMarginSettings
from fno.risk.stress_factor import factor_in_force, family_of
from tests.risk.test_whole_margin_stress import REAL, REAL_ROWS
from tests.stress_factor_files import HEADER

DAY = date(2026, 11, 9)
SEED = "2026-10-14,1.45,,,applied,seed,,\n"
DEBIT = "2026-11-08,1.2,1.2,1.15,applied,BF 100,2026-11-06,a,debit\n"
CREDIT = "2026-11-08,2.3,2.3,2.25,applied,SF 100,2026-11-06,b,credit\n"

SF_100 = [Leg(25_000.0, OPTION_CALL, -1), Leg(25_000.0, OPTION_PUT, -1), Leg(25_100.0, OPTION_CALL, 1),
          Leg(24_900.0, OPTION_PUT, 1)]  # fmt: skip
BF_100 = [Leg(leg.strike, leg.kind, -leg.side) for leg in SF_100]


def _file(tmp_path: Path, rows: str) -> Path:
    path = tmp_path / "stress_factor.csv"
    path.write_text(HEADER + rows, encoding="utf-8")
    return path


def c2(path: Path, day: date, structure: str) -> float:
    return factor_in_force(path, day, 30, family_of(structure)).factor


def c4(path: Path, day: date, structure: str) -> float:
    return factor_on(path, day, 30, structure)[1]


BOTH = pytest.mark.parametrize(("read", "error"), [(c2, RiskInputError), (c4, FactorProblem)], ids=["C2", "C4"])


@BOTH
@pytest.mark.parametrize(("structure", "factor"), [("SF", 2.3), ("SC", 2.3), ("PCS", 2.3), ("BF", 1.2), ("LC", 1.2),
                                                   ("PDS", 1.2)])  # fmt: skip
def test_each_proposal_reads_its_own_family_s_k(tmp_path, read, error, structure, factor):
    assert read(_file(tmp_path, SEED + DEBIT + CREDIT), DAY, structure) == factor


@BOTH
def test_the_other_family_s_later_row_never_moves_a_family_s_k(tmp_path, read, error):
    later_credit = "2026-11-08,3.0,3.0,2.95,applied,SC 300,2026-11-06,c,credit\n"
    path = _file(tmp_path, SEED + DEBIT + CREDIT + later_credit)
    assert read(path, DAY, "BF") == 1.2 and read(path, DAY, "SF") == 3.0


@BOTH
def test_an_all_row_stays_in_force_until_the_family_s_own_row(tmp_path, read, error):
    path = _file(tmp_path, SEED + DEBIT)
    assert read(path, DAY, "BF") == 1.2 and read(path, DAY, "SF") == 1.45
    assert read(path, date(2026, 11, 8), "BF") == 1.45  # the family row counts only from the day after it


@BOTH
def test_a_family_with_neither_its_own_row_nor_an_all_row_refuses_by_name(tmp_path, read, error):
    with pytest.raises(error, match="no factor row before 2026-11-09 for the credit family"):
        read(_file(tmp_path, DEBIT), DAY, "SF")


@BOTH
def test_a_code_with_no_family_refuses_by_name(tmp_path, read, error):
    with pytest.raises(error, match="XYZ has no structure family"):
        read(_file(tmp_path, SEED), DAY, "XYZ")


@BOTH
def test_an_unknown_family_value_refuses(tmp_path, read, error):
    with pytest.raises(error, match="family 'mixed'"):
        read(_file(tmp_path, SEED + "2026-11-08,1.2,1.2,1.15,applied,x,2026-11-06,a,mixed\n"), DAY, "BF")


def test_the_margins_use_the_k_of_the_proposal_s_structure(tmp_path):
    """Raising only the credit row moves SF's stressed margin in C2 and C4 and leaves BF's untouched (NSE's real
    14 Oct rows; decided on 20 Oct so the rows are within C2's seven-day margin age)."""
    day, figures = date(2026, 10, 20), []
    for credit_k in ("2.3", "3.0"):
        credit = f"2026-10-16,{credit_k},{credit_k},2.25,applied,SF 100,2026-10-15,b,credit\n"
        folder = tmp_path / credit_k
        folder.mkdir()
        path = _file(folder, SEED + DEBIT.replace("2026-11-08", "2026-10-16") + credit)
        settings = StressedMarginSettings("multiplier", path, 30, None)
        c2 = MultiplierMargin(MarginTable(REAL_ROWS, DaysOld(7), 65), settings)
        c4 = MarginSettings(REAL_ROWS, 7, None, "multiplier", path, 30)
        row = {}
        for code, width in (("SF", 100.0), ("BF", 300.0)):
            terms = TradeTerms(code, width, 1)
            row[code] = round(c2.margin(terms, day), 2)
            row[f"{code} at entry"] = round(c2.margin_at_entry(terms, day), 2)
            assert c2.record(day, code)["stress_factor_row"]["family"] == ("credit" if code == "SF" else "debit")
            assert round(stressed_per_lot(REAL, (code, width, 1), day, c4, 65), 2) == row[code]
        figures.append(row)
    for name in ("SF", "SF at entry"):
        assert figures[1][name] > figures[0][name]
    for name in ("BF", "BF at entry"):
        assert figures[1][name] == figures[0][name]


@BOTH
def test_a_family_row_under_the_old_header_is_refused_not_read_as_all(tmp_path, read, error):
    path = tmp_path / "stress_factor.csv"
    path.write_text(",".join(STRESS_FACTOR_COLUMNS_BEFORE_FAMILIES) + "\n" + SEED + CREDIT, encoding="utf-8")
    with pytest.raises(error, match="row 3 has more fields than the header"):
        read(path, DAY, "BF")


@BOTH
def test_the_30_day_age_applies_to_each_family_s_own_row(tmp_path, read, error):
    """Debit's own row of 8 Oct is 31 days old on 8 Nov while credit's of 5 Nov is fresh (the seed is older still)."""
    rows = SEED.replace("2026-10-14", "2026-10-01") + DEBIT.replace("2026-11-08", "2026-10-08")
    path = _file(tmp_path, rows + CREDIT.replace("2026-11-08", "2026-11-05"))
    assert read(path, date(2026, 11, 8), "SF") == 2.3
    with pytest.raises(error, match="of 2026-10-08 is not valid on 2026-11-08"):
        read(path, date(2026, 11, 8), "BF")


def test_a_decision_record_on_a_day_needs_the_structure(tmp_path):
    settings = StressedMarginSettings("multiplier", _file(tmp_path, SEED), 30, None)
    c2 = MultiplierMargin(MarginTable(REAL_ROWS, DaysOld(7), 65), settings)
    assert "stress_factor_row" not in c2.record()
    with pytest.raises(RiskInputError, match="needs the proposal's structure"):
        c2.record(date(2026, 10, 20))


@pytest.mark.parametrize(
    ("legs", "value", "possible"),
    [
        (SF_100, -100.0, False), (SF_100, -99.95, True), (SF_100, 0.0, False), (SF_100, -0.05, True),
        (BF_100, 0.0, False), (BF_100, 0.05, True), (BF_100, 100.0, False), (BF_100, 100.5, False),
    ],
)  # fmt: skip
def test_a_price_is_possible_only_strictly_inside_the_payoff_bounds(legs, value, possible):
    """B2's BAD_PRICES rule, shared by A14c: a credit at least the width, or a debit at most zero, is impossible."""
    assert possible_value(legs, value) is possible
