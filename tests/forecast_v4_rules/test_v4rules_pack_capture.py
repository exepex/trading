"""Story G7b completion, part b2 (criteria 2-4 live, 13, 21): the post-release capture's rows and terms, the stored
monthly ratio, the 15:10 refusal, write-once Drive files, and the pack-derived rows' own method hash."""

import ast
import json
from datetime import date, datetime, time, timedelta
from pathlib import Path

import pytest

from fno.constants import (
    V1_RV_1S,
    V2_RV_5S,
    V3_RV_20S,
    V4_BASELINE_BASE_RATE,
    V4_BASELINE_OPTION_IMPLIED_PROB,
    V4_BASELINE_PREMIUM_ADJUSTED,
    V4_BASELINE_RAW_IMPLIED,
    V4_RV_BELOW_WEEKLY_IV,
    V5_INSIDE_STRADDLE,
)
from fno.forecast_v4_rules.baselines import NOT_ELIGIBLE, OK, Ewma
from fno.forecast_v4_rules.constants import (
    V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY,
    V4_RULE_V4_EWMA_CHI2,
    V4_RULE_V5_EWMA_LOGNORMAL,
)
from fno.forecast_v4_rules.drive_records import live_path, read_live
from fno.forecast_v4_rules.implied import HorizonRv, ImpliedBaselines, IvPoint, PremiumRatio
from fno.forecast_v4_rules.intraday_series import RATIO_CLOSE_PROXY, RATIO_INTRADAY
from fno.forecast_v4_rules.live_quotes import TwoSided
from fno.forecast_v4_rules.option_terms import OptionTermsRule
from fno.forecast_v4_rules.pack_capture import (
    PACK_FORECASTERS,
    CaptureRefused,
    ChangedRow,
    PackForecasts,
    PackInputs,
    capture_pack,
    terms_path,
)
from fno.forecast_v4_rules.ratio_store import StoredRatio, ratio_path
from fno.forecast_v4_rules.records import LIVE
from fno.forecast_v4_rules.series import DayValue, Outcome
from fno.models import IST
from fno.research_data.calendar import load_session_calendar
from fno.research_engine.implied_vol import Black76
from fno.storage.raw_store import RawFileConflict
from fno.v4_pack.guard import PACK_READERS, PackBindingRefused
from tests.forecast_v4_rules.option_fixtures import LISTED, MONTHLY, RATE, TRADED, WEEKLY, D, chain

ROOT = Path(__file__).resolve().parents[2]
CALENDAR = load_session_calendar(ROOT / "research" / "data" / "calendar" / "nse_sessions.csv")
SESSIONS = [date(2017, 1, 2) + timedelta(n) for n in range((date(2026, 12, 31) - date(2017, 1, 2)).days + 1)]
SESSIONS = [d for d in SESSIONS if CALENDAR.session_kind(d) == "regular"]
SHA = "e" * 64
METHOD = "f" * 64
NOW = datetime.combine(D, time(14, 45), IST)
FORWARD = 26080.0


class Drive:
    def __init__(self, fail_at: int | None = None):
        self.files, self.puts, self.fail_at = {}, 0, fail_at

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        self.puts += 1
        if self.puts == self.fail_at:
            raise OSError("Drive refused the upload")
        if path in self.files and self.files[path] != data:
            raise RawFileConflict(path)
        self.files[path] = data


def unit_ratio(value: float) -> PremiumRatio:
    """600 one-day points from 2024, each with ratio `value` (IV30 sqrt(365): raw_h(t) = 1)."""
    days = [date(2024, 1, 1) + timedelta(n) for n in range(600)]
    eod = {d: IvPoint(365**0.5, False) for d in days}
    return PremiumRatio(eod, {d: HorizonRv(value, d + timedelta(1)) for d in days})


REFIT = date(2026, 10, 1)


def forecasts(drive: Drive, today=REFIT, outcomes=None, intraday_ratio=None) -> PackForecasts:
    """Yardstick B on a stored ratio of 0.6; A on `intraday_ratio` (none: an empty window, not eligible)."""

    def implied(measure: str, ratio: PremiumRatio):
        return {q: ImpliedBaselines(h, SESSIONS, StoredRatio(ratio, q, measure, today, drive.get, drive.put))
                for q, h in ((V1_RV_1S, 1), (V2_RV_5S, 5), (V3_RV_20S, 20))}  # fmt: skip

    both = {RATIO_CLOSE_PROXY: implied(RATIO_CLOSE_PROXY, unit_ratio(0.6)),
            RATIO_INTRADAY: implied(RATIO_INTRADAY, intraday_ratio or PremiumRatio({}, {}))}  # fmt: skip
    rv = [DayValue(d, 0.00008) for d in SESSIONS if d < D]
    rule = OptionTermsRule(Black76(), RATE, CALENDAR)
    outcomes = outcomes or {V4_RV_BELOW_WEEKLY_IV: [], V5_INSIDE_STRADDLE: []}
    return PackForecasts(both, Ewma(rv), rule, outcomes, METHOD)


def stored_ratios(drive: Drive) -> Drive:
    """The October ratios stored on their refit day (1 Oct), as the capture of that day would have."""
    for q in (V1_RV_1S, V2_RV_5S, V3_RV_20S):
        StoredRatio(unit_ratio(0.6), q, RATIO_CLOSE_PROXY, REFIT, drive.get, drive.put).at(REFIT)
        StoredRatio(PremiumRatio({}, {}), q, RATIO_INTRADAY, REFIT, drive.get, drive.put).at(REFIT)
    return drive


def inputs(**changes) -> PackInputs:
    fields = dict(day=D, release_label="A", release_sha256=SHA, pack_sha256=SHA, iv30=IvPoint(0.15, False),
                  spot=26010.0, chain=chain(WEEKLY, FORWARD, 0.138) + chain(MONTHLY, FORWARD, 0.14),
                  future_expiry=MONTHLY, future=TwoSided(26075.0, 26085.0, TRADED), v4_expiry=WEEKLY,
                  listed=LISTED)  # fmt: skip
    return PackInputs(**{**fields, **changes})


def run(drive: Drive, now=NOW, **changes):
    return capture_pack(forecasts(drive, today=D), inputs(**changes), lambda: now, drive.get, drive.put)


def test_a_day_writes_every_pack_row_and_both_terms_once():
    drive = stored_ratios(Drive())
    paths = run(drive)
    assert len(paths) == len(PACK_FORECASTERS) + 2
    rows = {key: read_live(drive.files[live_path(*key, D)]) for key in PACK_FORECASTERS}
    assert all(label == "A" and row.label == LIVE and row.method_sha256 == METHOD for row, label in rows.values())
    raw = rows[(V4_BASELINE_RAW_IMPLIED, V2_RV_5S)][0]
    assert raw.status == OK and float(raw.value) == pytest.approx(0.15**2 * 7 / 365)  # 27 Oct -> 3 Nov
    premium = rows[(V4_BASELINE_PREMIUM_ADJUSTED, V2_RV_5S)][0]
    assert (
        float(premium.value) == pytest.approx(0.6 * 0.15**2 * 7 / 365)
        and premium.forecaster_version == "1 ratio close_proxy"
    )
    implied_probability = rows[(V4_BASELINE_OPTION_IMPLIED_PROB, V5_INSIDE_STRADDLE)][0]
    assert implied_probability.status == OK
    assert implied_probability.forecaster_version == "1 risk-neutral, not a real-world probability"
    assert rows[(V4_RULE_V4_EWMA_CHI2, V4_RV_BELOW_WEEKLY_IV)][0].status == OK
    assert rows[(V4_RULE_V5_EWMA_LOGNORMAL, V5_INSIDE_STRADDLE)][0].status == OK
    assert rows[(V4_BASELINE_BASE_RATE, V5_INSIDE_STRADDLE)][0].status == NOT_ELIGIBLE  # no live outcome yet
    shas = {key: row.pack_sha256 for key, (row, _) in rows.items()}
    no_pack = {(V4_BASELINE_BASE_RATE, q) for q in (V4_RV_BELOW_WEEKLY_IV, V5_INSIDE_STRADDLE)}
    assert {k for k, s in shas.items() if s == ""} == no_pack and set(shas.values()) == {"", SHA}
    # each row hashes what it read: raw V2/V3 share IV30, each yardstick's V1-V3 rows share one ratio here, both base
    # rates are empty
    assert len({row.inputs_sha256 for row, _ in rows.values()}) == 7
    v4_terms = json.loads(drive.files[terms_path(V4_RV_BELOW_WEEKLY_IV, D)])
    assert v4_terms["expiry"] == "2026-11-03" and v4_terms["pack_sha256"] == SHA


def test_a_rerun_minutes_later_after_a_partial_failure_completes_the_day():
    drive = stored_ratios(Drive(fail_at=7))  # 3 ratio files, then the 4th row's upload fails
    with pytest.raises(OSError):
        run(drive)
    drive.fail_at = None
    paths = run(drive, now=NOW + timedelta(minutes=7))
    assert all(p in drive.files for p in paths)


def test_a_changed_row_for_the_day_is_refused():
    drive = stored_ratios(Drive())
    run(drive)
    with pytest.raises(ChangedRow, match="different row"):
        run(drive, iv30=IvPoint(0.2, False))


def test_a_system_late_day_writes_nothing():
    drive = stored_ratios(Drive())
    before = dict(drive.files)
    with pytest.raises(CaptureRefused, match="system_late"):
        run(drive, release_label="system_late", release_sha256="")
    assert drive.files == before


def test_a_pack_other_than_the_released_one_is_refused_by_g10s_guard():
    drive = stored_ratios(Drive())
    with pytest.raises(PackBindingRefused):
        run(drive, pack_sha256="d" * 64)


def test_the_guard_counts_these_forecasters_as_pack_readers_and_the_base_rate_as_none():
    for forecaster, _ in PACK_FORECASTERS:
        assert (forecaster in PACK_READERS) is (forecaster != V4_BASELINE_BASE_RATE)


def test_void_terms_give_missing_rule_and_baseline_rows_and_are_written():
    drive = stored_ratios(Drive())
    run(drive, v4_expiry=None, future=None)
    v4 = read_live(drive.files[live_path(V4_RULE_V4_EWMA_CHI2, V4_RV_BELOW_WEEKLY_IV, D)])[0]
    v5 = read_live(drive.files[live_path(V4_BASELINE_OPTION_IMPLIED_PROB, V5_INSIDE_STRADDLE, D)])[0]
    assert v4.status == v5.status == "missing" and v4.value == v5.value == ""
    assert json.loads(drive.files[terms_path(V5_INSIDE_STRADDLE, D)])["reason"] == "no_future_quote"


def test_a_flagged_iv30_gives_no_implied_value():
    drive = stored_ratios(Drive())
    run(drive, iv30=IvPoint(0.15, True))
    for key in ((V4_BASELINE_RAW_IMPLIED, V2_RV_5S), (V4_BASELINE_PREMIUM_ADJUSTED, V3_RV_20S)):
        assert read_live(drive.files[live_path(*key, D)])[0].status == "missing"


def test_both_yardsticks_are_written_each_labelled_by_its_measure():
    drive = stored_ratios(Drive())
    run(drive)
    for question, days in ((V1_RV_1S, 1), (V2_RV_5S, 7)):
        b = read_live(drive.files[live_path(V4_BASELINE_PREMIUM_ADJUSTED, question, D)])[0]
        a = read_live(drive.files[live_path(V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY, question, D)])[0]
        assert (
            float(b.value) == pytest.approx(0.6 * 0.15**2 * days / 365)
            and b.forecaster_version == "1 ratio close_proxy"
        )
        assert a.status == NOT_ELIGIBLE and a.forecaster_version == "1 ratio intraday"  # no intraday window stored


def test_yardstick_a_has_a_value_when_its_own_window_is_stored():
    drive = Drive()
    for q in (V1_RV_1S, V2_RV_5S, V3_RV_20S):
        StoredRatio(unit_ratio(0.6), q, RATIO_CLOSE_PROXY, REFIT, drive.get, drive.put).at(REFIT)
        StoredRatio(unit_ratio(0.8), q, RATIO_INTRADAY, REFIT, drive.get, drive.put).at(REFIT)
    run(drive)
    a = read_live(drive.files[live_path(V4_BASELINE_PREMIUM_ADJUSTED_INTRADAY, V1_RV_1S, D)])[0]
    assert float(a.value) == pytest.approx(0.8 * 0.15**2 * 1 / 365)


def test_a_missed_refit_day_leaves_the_month_without_a_ratio():
    drive = Drive()  # no ratio stored on 1 Oct; the 27 Oct capture must not compute one late
    run(drive)
    assert read_live(drive.files[live_path(V4_BASELINE_PREMIUM_ADJUSTED, V2_RV_5S, D)])[0].status == NOT_ELIGIBLE
    assert not any(p.startswith("v4/ratios/") for p in drive.files)


@pytest.mark.parametrize("at, refused", [(time(15, 9, 59), False), (time(15, 10), True)])
def test_the_capture_refuses_from_15_10(at, refused):
    drive = stored_ratios(Drive())
    before = dict(drive.files)
    now = datetime.combine(D, at, IST)
    if refused:
        with pytest.raises(CaptureRefused):
            run(drive, now=now)
        assert drive.files == before
    else:
        assert run(drive, now=now)


def test_the_deadline_is_checked_before_every_write():
    drive = stored_ratios(Drive())
    times = iter([datetime.combine(D, time(15, 9, 59), IST)] * 4 + [datetime.combine(D, time(15, 10), IST)] * 20)
    with pytest.raises(CaptureRefused, match="deadline"):
        capture_pack(forecasts(drive, today=D), inputs(), lambda: next(times), drive.get, drive.put)
    assert sum(p.startswith("v4/records/live/") for p in drive.files) == 3  # the 4th clock reading came after 15:10


def test_only_the_days_own_run_writes():
    with pytest.raises(CaptureRefused, match="not today"):
        run(Drive(), now=NOW + timedelta(days=1))


def test_the_months_ratio_is_stored_on_its_refit_day_with_its_window_and_read_back():
    drive = Drive()
    stored = StoredRatio(unit_ratio(0.6), V2_RV_5S, RATIO_CLOSE_PROXY, REFIT, drive.get, drive.put)
    assert stored.at(REFIT) == pytest.approx(0.6)
    document = json.loads(drive.files[ratio_path(RATIO_CLOSE_PROXY, V2_RV_5S, REFIT)])
    assert (document["count"], document["first"], document["last"]) == (600, "2024-01-01", "2025-08-22")
    assert len(document["inputs_sha256"]) == 64
    assert ratio_path(RATIO_CLOSE_PROXY, V2_RV_5S, REFIT) == "v4/ratios/close_proxy/v2_rv_next_5_sessions/2026-10.json"
    later = StoredRatio(unit_ratio(0.9), V2_RV_5S, RATIO_CLOSE_PROXY, D, drive.get, drive.put)  # data changed since
    assert later.at(REFIT) == pytest.approx(0.6)
    empty = StoredRatio(PremiumRatio({}, {}), V3_RV_20S, RATIO_CLOSE_PROXY, REFIT, drive.get, drive.put)
    assert empty.at(REFIT) is None
    assert json.loads(drive.files[ratio_path(RATIO_CLOSE_PROXY, V3_RV_20S, REFIT)])["ratio"] is None
    assert StoredRatio(unit_ratio(0.9), V3_RV_20S, RATIO_CLOSE_PROXY, REFIT, drive.get, drive.put).at(REFIT) is None


def test_base_rates_read_only_outcomes_resolved_before_the_day():
    resolved = [Outcome(D - timedelta(days=30 + i), i % 2 == 0, D - timedelta(days=1)) for i in range(500)]
    late = [Outcome(D - timedelta(days=10), True, D)]  # resolved on the day itself: not known at its cutoff
    drive = stored_ratios(Drive())
    outcomes = {V4_RV_BELOW_WEEKLY_IV: resolved + late, V5_INSIDE_STRADDLE: resolved[:499]}
    capture_pack(forecasts(drive, today=D, outcomes=outcomes), inputs(), lambda: NOW, drive.get, drive.put)
    v4 = read_live(drive.files[live_path(V4_BASELINE_BASE_RATE, V4_RV_BELOW_WEEKLY_IV, D)])[0]
    v5 = read_live(drive.files[live_path(V4_BASELINE_BASE_RATE, V5_INSIDE_STRADDLE, D)])[0]
    assert float(v4.value) == pytest.approx(0.5) and v5.status == NOT_ELIGIBLE


def package_imports(name: str, package: Path, seen: set[str]) -> set[str]:
    """The files of `package` that `name` imports, directly or through each other (relative imports only)."""
    tree = ast.parse((package / name).read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 1:
            module = f"{node.module}.py" if node.module else None
            targets = [module] if module else [f"{a.name}.py" for a in node.names]
            for target in targets:
                if (package / target).is_file() and target not in seen:
                    seen.add(target)
                    package_imports(target, package, seen)
    return seen


def test_criterion_21_the_pack_rows_method_hash_covers_the_captures_whole_closure():
    from fno.forecast_v4_rules import wiring

    package = Path(wiring.__file__).parent
    closure = package_imports("pack_wiring.py", package, {"pack_wiring.py"})  # the capture's composition root
    named = {"v4_expiry.py", "live_quotes.py", "option_terms.py", "option_probabilities.py", "option_outcomes.py",
             "implied.py", "series.py", "baselines.py", "records.py", "eod_iv30.py"}  # judge 585's list  # fmt: skip
    assert closure <= set(wiring.PACK_METHOD_FILES) and named <= set(wiring.PACK_METHOD_FILES)
    assert wiring.method_sha256(wiring.PACK_METHOD_FILES) not in {
        wiring.method_sha256(),
        wiring.method_sha256(wiring.IMPLIED_METHOD_FILES),
    }
