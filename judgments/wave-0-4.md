# Wave 0 judgment, round 4 (2026-10-12)

Scope: 38ac221. Verdict: **FAIL** (1 should fix, 3 minor). N10-N13 and the round-3 classifier gaps CLOSED
(probes across midnight, two days, recovery mid-day, start-up with a failing store write).
Commands: pytest 176 passed; ruff check/format clean; tree clean after tests; 38 own headlines: 9 wrong now vs 12
before, remaining long-standing errors score 0, not the wrong sign.

- N16 (should fix): bare "hits" in RUPEE_FALLS: "Rupee hits one-year peak" -1.0; "Rupee hits record high" 0.0.
- N14 (minor): a recurring reference failure takes the alert slot on the tick the rate limit opens, so the
  dead-watcher alert never goes out while NSE is down.
- N15 (minor, pre-existing): kill bookkeeping in DayState: close_all and a second kill alert at midnight.
- N17 (minor, pre-existing): no day summary on kill-switch days; reference alerts around the clock (97 in 24 h).
