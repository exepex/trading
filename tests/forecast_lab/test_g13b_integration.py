"""FL1-1 over G13b's real classes (on `main`): a record from G13b's own builder, sealed through its own seal check,
scored by its own `row_scores` and read back by its `RangeForecasts` and `RangeScores` through FL1's adapter, so a
change of G13b's record or score shape fails here, not on the first live day."""

import json
from datetime import date, datetime

from fno.forecast_lab.g13b_adapter import G13bRanges
from fno.forecast_lab.match import MatchSection, next_ranges
from fno.forecast_lab.sessions import RegularSessions
from fno.models import IST
from fno.price_ranges.build import CAPTURE
from fno.price_ranges.folders import live_path, scores_path
from fno.price_ranges.reader import RangeForecasts, RangeScores, receipt_file
from fno.price_ranges.scores import resolved, row_scores
from fno.price_ranges.sealing import SealCheck
from fno.price_ranges.seals import Seals
from tests.price_distribution.builders import DAY, chain_day, drive_store
from tests.price_ranges.builders import CALENDAR, builder, closes

MONDAY, CLOSE = date(2026, 10, 19), 23_100.0  # DAY is Friday 16 Oct; N1's target is Monday 19 Oct
PUSHED = datetime(2026, 10, 16, 15, 50, tzinfo=IST)


class Closes:
    def close(self, underlying, day):
        return CLOSE if day == MONDAY else None


def ranges(tmp_path, pushed_at: datetime = PUSHED) -> G13bRanges:
    root = tmp_path / "cache"
    record = builder().build("NIFTY", DAY, "1545", chain_day(day=DAY), closes(), CAPTURE, "live",
                             "2026-10-16T15:45:00+05:30")  # fmt: skip
    file = root / "data" / live_path("NIFTY", DAY, "1545")
    file.parent.mkdir(parents=True)
    file.write_text(json.dumps(record))
    scored, _ = resolved([(record, True)], lambda u, d: CLOSE if d == MONDAY.isoformat() else None)
    scores = root / "data" / scores_path(datetime(2026, 10, 19, 16, 0, tzinfo=IST), "ab" * 6)
    scores.parent.mkdir(parents=True)
    scores.write_text(json.dumps({"schema": "g13b_scores_v1", "rows": row_scores(scored)}))
    store, _, _ = drive_store(tmp_path / "seals")
    pushed = {receipt_file(live_path("NIFTY", DAY, "1545")): pushed_at}
    seals = Seals(SealCheck(pushed.get, CALENDAR), store, receipt_file, lambda: datetime(2026, 10, 19, 16, tzinfo=IST))
    return G13bRanges(RangeForecasts(root, seals), RangeScores(root))


def test_g13b_s_real_record_and_scores_reach_the_report(tmp_path):
    source = ranges(tmp_path)
    issue = source.sealed("NIFTY", DAY, "1545")
    assert issue.sealed_at == PUSHED and not issue.late and {r.horizon for r in issue.rows} == {"N1", "N3"}
    shown = next_ranges("NIFTY", issue, PUSHED)
    assert any(line.startswith("  N1 (2026-10-19) rv20: 5/25/50/75/95 ") for line in shown)
    match = MatchSection(source, Closes(), RegularSessions(CALENDAR))
    lines = match.match_lines("NIFTY", MONDAY)
    assert lines[1] == " N1, issued 2026-10-16 15:45 at 22990.00:" and any("close 23100.00" in x for x in lines)
    assert match.seal_lines("NIFTY", MONDAY)[1] == [
        "NIFTY N3 for 2026-10-19 (issued 2026-10-14): no forecast was sealed; nothing to score"
    ]
    assert source.scored_days("NIFTY", MONDAY) == [MONDAY] and {s.method for s in source.history("NIFTY", MONDAY)}


def test_g13b_s_own_late_verdict_reaches_fl1_through_the_adapter(tmp_path):
    """Judge 422 (M16): G13b's SealCheck marks a record pushed after the next session's 09:15 late; the adapter keeps
    that verdict and FL1 refuses and alerts the forecast."""
    source = ranges(tmp_path, pushed_at=datetime(2026, 10, 19, 9, 16, tzinfo=IST))
    assert source.sealed("NIFTY", DAY, "1545").late is True
    lines, alerts = MatchSection(source, Closes(), RegularSessions(CALENDAR)).seal_lines("NIFTY", MONDAY)
    assert alerts[0] == ("NIFTY N1 for 2026-10-19 (issued 2026-10-16): sealed late (2026-10-19 09:16:00+05:30); "
                         "not shown as a forecast")  # fmt: skip
