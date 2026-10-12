# Wave 2 judgment, round 1 (2026-10-12)

Scope: 64979af at HEAD 8b6451a. Verdict: **FAIL** (0 blocking, 1 should fix, 6 minor).
Commands: pytest 142 passed; ruff check/format clean; only exempt html_report.py over 350 lines. Calibration
reproduced: 45 sessions, whole-day median 0.119, last-hour 0.271, 44.8% of hours >= 0.30 (holds on 180 sessions).
Real participant OI file parsed (FII long share 0.096); live NIFTY/BANKNIFTY move ratios 1.26-1.54 (calls).
All criteria PASS on code and probes; nothing can enlarge a trade or bypass a limit; no secrets in logs.

1. Should fix: no tests for `archive_text_or_none` (404 -> None, other status -> error) or for
   `ReferenceData.load` surviving a failed FII load.
2. Minor: stale FII data (up to 20 days old) still votes as current.
3. Minor: MoveCheck lets an idea through silently when it cannot measure (no ATM IV, zero spot); untested.
4. Minor: FII vote reason misleading (prints tilt change as tilt; "added longs"; 0 shown as "cut").
5. Minor: hold_days is trading days in config but used as calendar days.
6. Minor: README not updated for wave 2 (guards, signals, modules).
7. Minor: calibration claims not reproducible from the repo (no script committed).
