# Waves 0 and 1 judgment, round 2 (2026-10-12)

Scope: fixes in 8b6451a. Verdict: **FAIL** for both waves (no blocking; should fix open).
Commands: pytest 142 passed (3 runs, conftest guard never fired); ruff check/format clean; scan-once and news-once
leave the tree clean; all named regression tests pass.

Closed or accepted: wave 0 #1-5, 7-20 (14, 17, 19 accepted); wave 1 #1-9.
Not closed: wave 0 #6 (cost/rupee pattern spans clauses: "Dollar steady, Sensex rises 500 points" -1.0; "US
yields ease, Nifty gains 1%" -1.0; "Crude oil steady as Sensex rallies" -1.0; "Yields steady as Nifty falls" +1.0;
"Brent flat, Nifty climbs to record high" 0.0).

New findings
- N1 (should fix, wave 1): with the kill switch on, a trade whose chain cannot be priced stays open for good:
  `close_all` skips it, `kill_reported` is set after one attempt, ticks return early, the alert says all closed.
- N2 (should fix, wave 0): a failed ReferenceData load is never retried that day (state.day set before the load).
- N4 (minor): malformed news usage file can stop the watcher at start-up.
- N5 (minor): release time vs minute-precision closed_at; naive marker raises.
- N6 (minor): SAFEGUARDS does not say the automatic stop uses the current drawdown and restarts after resume.
- N7 (minor): conftest guard misses deleted files; fails beside a live desk on the same checkout.
- N8 (minor): shadow-book news-exit errors dropped silently.
- N9 (minor): no test for the dead-watcher alert.
