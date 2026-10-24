"""Story G11 criterion C17: the AI books' v4 run cost, per book, from BG1's ledger (start-to-end minutes, what the
cap counts) and the runs' own timing files (working: start to seal; waiting: seal to end; reveal calls). Good: a
week's numbers. Bad: a file without a seal time is "working unknown", never 0. Boundary: one run, p50 = p95. Empty:
"no v4 runs yet"; before the go-live date, nothing."""

import json
from datetime import date, datetime, time, timedelta

from fno.ai.paths import timing_path
from fno.ai.v4_cost import V4CostReport
from fno.constants import BOOK2_HYBRID, BOOK3_AI
from fno.models import IST

LIVE = date(2026, 10, 26)


class Ledger:
    def __init__(self, rows=()):
        self._rows = list(rows)

    def rows(self):
        return self._rows


def timing(root, day, book, work_min, wait_min, calls, sealed=True):
    start = datetime.combine(day, time(14, 41), IST)
    record = {"session_id": "session_x", "model": "", "started_at": start.isoformat(),
              "ended_at": (start + timedelta(minutes=work_min + wait_min)).isoformat(),
              "sealed_at": (start + timedelta(minutes=work_min)).isoformat() if sealed else None,
              "reveal_calls": calls}  # fmt: skip
    path = root / timing_path(day, book)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record))
    return {"date": day.isoformat(), "book": book, "minutes": f"{work_min + wait_min:.2f}"}


def test_a_weeks_runs_show_bg1s_minutes_and_work_and_wait_apart(tmp_path):
    rows = [timing(tmp_path, LIVE + timedelta(days=d), BOOK3_AI, 2 + d, 24 - d, 3) for d in range(5)]
    rows.append({"date": "2026-10-23", "book": BOOK3_AI, "minutes": "4.38"})  # a v2 run before go-live: left out
    line = V4CostReport(tmp_path, Ledger(rows), LIVE).lines()[1]
    assert line == (
        "Omenix F&O AI v4 cost (BG1): book3_ai: 5 run(s) in BG1's ledger, minutes p50 26.00, p95 26.00; "
        "working p50 4.00, p95 6.00; waiting p50 22.00, p95 24.00; reveal calls p50 3.00, p95 3.00"
    )


def test_a_run_without_a_seal_time_is_working_unknown_never_zero(tmp_path):
    rows = [timing(tmp_path, LIVE, BOOK2_HYBRID, 3, 25, 4, sealed=False)]
    line = V4CostReport(tmp_path, Ledger(rows), LIVE).lines()[0]
    assert "working unknown; waiting unknown" in line and line.endswith("working unknown on 1 run(s) (no seal time)")


def test_one_run_has_p50_equal_to_p95(tmp_path):
    rows = [timing(tmp_path, LIVE, BOOK3_AI, 3.5, 24.5, 3)]
    assert "working p50 3.50, p95 3.50" in V4CostReport(tmp_path, Ledger(rows), LIVE).lines()[1]


def test_no_runs_say_so_and_no_live_date_prints_nothing(tmp_path):
    assert V4CostReport(tmp_path, Ledger(), LIVE).lines()[0].endswith("book2_hybrid: no v4 runs yet")
    assert V4CostReport(tmp_path, Ledger(), None).lines() == []
