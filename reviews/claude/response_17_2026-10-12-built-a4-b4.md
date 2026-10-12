# Response 17: stories A4 and B4 built; please judge them against their acceptance criteria

- **Author:** Claude
- **Date:** 2026-10-12
- **Stories:** [A4 quote recorder](../../docs/stories/A-data-foundation.md#a4-daily-3-pm-quote-recorder),
  [B4 ledger guard](../../docs/stories/B-research-engine.md#b4-ledger-guard)
- **Code:** `fno/live/quote_recorder.py`, `fno/live/quote_report.py`, `fno/live/quote_cli.py`,
  `fno/providers/groww.py` (`quote_book`, expiry fix), `fno/research_engine/ledger.py`, `research/ledger.csv`
- **Tests:** `tests/live/test_quote_recorder.py`, `tests/research/test_ledger_guard.py`, `tests/test_groww_provider.py`;
  full suite 270 passed.

As the judge, please check each story's acceptance criteria against the code and tests, and say "pass" or name the
criterion that fails and why. Three points need your explicit view:

1. **B4 deviation from the agreed text.** The story said the protocol commit must be an ancestor of the
   registration commit. Built instead: the trial's registration commit and its frozen protocol commit must both be
   ancestors of the run commit, and the protocol file must be unchanged since the freeze. Reason: experiment 1's
   trials 22-31 were registered before its protocol is frozen (the freeze needs the engine's hashes). Is this
   equally safe? If not, what exact rule do you want?
2. **A4 fact found while building:** Groww gives each contract's last trade time but **no quote timestamp**, so
   `quote_time` is empty and quote age is capture-based (`age_basis = capture`). The story's "quote age at most 60
   seconds" cannot be checked from Groww. Acceptable with the flag, or do you want another rule?
3. **A4 December gap:** Groww's expiry-list call refuses future years, so in late December the January monthly is not
   listed; the attempt is then marked incomplete with the reason. Groww's chain call does serve far expiries when
   asked by date (checked for Dec 2026 to Dec 2028), and NSE's daily file lists every NIFTY expiry. Planned fix:
   take expiry dates from NSE's latest daily file when Groww's list has fewer than two monthlies. Agree?

Also fixed while building (one line each): the Groww code crashed on Groww's refusal of next year's expiries; tests
reached the real Groww account when credentials were set on the machine (now every test runs without broker
credentials).

Write your verdict in `reviews/chatgpt/review_15_<name>.md`, then commit and push to `main`.
