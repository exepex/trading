# Wave 2 judgment, round 2 (2026-10-12)

Scope: fixes in 71c82ba. Verdict: **PASS** (no blocking, no should fix; 4 minor).
Commands: pytest 148 passed; ruff check/format clean; `python -m fno calibrate`: 45 sessions, whole-day 0.12,
last-hour 0.26, 42.6% of hours >= 0.30 (531 sessions over 60 days: 0.26, 42.5%); move ratios at 2.8-day hold:
calls 0.83-1.51x, puts 0.67-1.21x (1 of 42 over 1.5x); calibrate with the network down prints no traceback and
writes nothing into the repository.

Round-1 findings 1-7: all CLOSED (tests, staleness probes Fri->Mon to Wed->Tue, NOT_MEASURABLE note, new reason
text, consistent calendar-day hold, README checked against code, calibrate reproduces both calibrations).

Minor
1. WAVES.md W2.2 text imprecise after the hold change (calls 0.83-1.51x, puts 0.67-1.21x: the limit rarely bites).
2. Calendar-day conversion and MoveCheck setup written three times; calibrate ignores the configured take-profit.
3. `calibrate` hides failure (0 sessions printed as 0.0%, exit 0; any --range accepted).
4. Response claimed calibrate output was in the session log (it was not); NOT_MEASURABLE wording incomplete.
