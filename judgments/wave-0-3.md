# Waves 0 and 1 judgment, round 3 (2026-10-12)

Scope: 32b24fc (fixes 71c82ba..32b24fc). Verdict: **wave 0 FAIL** (2 should fix), **wave 1 PASS**.
Commands: pytest 160 passed, tree clean afterwards; ruff check/format clean; line limits met.

Round-2 items closed: W0 #6 (34-headline probe: no regressions; all round-2 cases fixed), N1 (61 ticks: retries
every review, rate-limited alerts, closes once the chain returns), N2, N4 (12 damaged files), N5, N6, N7 (guard
catches deleted/new/changed files; env flag skips), N8, N9.

New findings
- N10 (should fix, wave 0): a failed reference load leaves yesterday's day state and reference in use: scans run
  on yesterday's ban list and lot sizes, the day summary is skipped.
- N11 (should fix, wave 0): the one-time "news watcher stopped" alert is lost if another problem alert went out in
  the previous 15 minutes (flag set before the rate-limited send).
- N12 (minor, wave 1): the kill-switch retry runs around the clock (93 alerts in 24 h for an unpriceable trade).
- N13 (minor, wave 0): the start-up `_start_day_if_needed` call is no longer wrapped; a store/clock error there stops
  the desk.
- Minor classifier gaps: "Crude up 3%", "Rupee down 20 paise" score 0; "US yields rise to 16-year high" scores 0;
  "Rupee recovers from record low" scores -1.
