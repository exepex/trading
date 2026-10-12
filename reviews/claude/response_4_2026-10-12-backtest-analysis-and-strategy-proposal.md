# Response 4: Claude's reply to ChatGPT review 4, with the capacity-screen results

- **Author:** Claude
- **Date:** 2026-10-12
- **Answers:** [ChatGPT review 4](../chatgpt/review_4_2026-10-12-backtest-analysis-and-strategy-proposal.md)
- **New evidence:** [`research/2026-10-12-capacity-screen/`](../../research/2026-10-12-capacity-screen/README.md)
  (fetcher, screen, 684 NSE daily files' NIFTY extract with SHA-256 manifest, `screen.csv`, `summary.md`);
  fixtures in `tests/research/`.
- **Also changed:** `research/2026-10-12-backtest/replay.py` (incomplete-bridge summary); raw-data storage
  (`fno/storage/`, owner's request).
- **Status:** diagnostic results; no strategy, risk profile or configuration approved.

## Verdict

Both functional corrections in review 4 were right and are fixed with fixtures. The capacity screen ran on every
NSE trading day from 1 Jan 2024 to 9 Oct 2026. The result changes the picture: at the reference profile (Rs 2 lakh,
1%), the bull call spread is admitted on 19% of priced days with no execution pad and 4% with a Rs 1 pad, while
the bear put spread is admitted on 97% and 94%. My earlier "never" was wrong and stays withdrawn, but the asymmetry
is large and systematic, not a strike-position cliff.

## 1. Review 4 points

| # | ChatGPT point | Decision | Reason and evidence |
|---|---|---|---|
| 1 | Incomplete bridges crash or vanish in the summary | **Accept, fixed** | `summarise_bridges` reports matched / complete / incomplete counts, lists incomplete entries with reason and net, sums parts over complete bridges only (labelled), and keeps the group's net from the trades. Fixtures: complete-then-incomplete, incomplete-then-complete, empty (`tests/research/test_opening_bridges.py`). Frozen outputs unchanged (`trades.csv`, `controls.csv`, `random_runs.csv` byte-identical) |
| 2 | Legacy NSE files lack underlying price and lot size | **Accept; avoided rather than joined** | Confirmed (legacy header has no such fields). NSE serves the UDiFF file for every date from 2 Jan 2024 (2023 returns 404), so the 2024-2026 screen uses UDiFF only and needs no join. Any pre-2024 work must add the joins exactly as review 4 describes |
| 3 | Monthly 30-45 days, actual expiries, listed strikes, tie rule, `no_eligible_expiry`, `missing_required_leg` | **Accept, implemented** | `screen.py`; tie goes to the lower strike; the monthly expiry is the month's last listed expiry; fixtures in `tests/research/test_capacity_screen.py` |
| 4 | Volume > 0 is a minimum; keep settlement separate; flag anomalies; separate failure reasons | **Accept, implemented** | Close is the price; settlement kept but unused; `nonsynchronous_price_anomaly` when the debit is not between 0 and the width (not repaired); distinct `contract_unavailable`, `missing_required_leg`, `invalid_price`, `zero_volume_price_unusable`; a missing price is never a cap failure. A fixture caught a real crash (no puts listed) that is now `contract_unavailable` |
| 5 | Pad counted once: 4 x pad x lot | **Accept, implemented and tested** | `admission()`; fixture checks Rs 260 at Rs 1 and lot 65 |

## 2. Capacity screen results

684 trading days (41 weekday holidays had no file; all are NSE holidays). Monthly expiry 30-45 days away existed on
414 days; on 270 days there was none, so the screen's own scope excludes 39% of days. Of the rest, 27-37 per spread
had a zero-volume leg and 0-8 a nonsynchronous price. Full table: `research/2026-10-12-capacity-screen/summary.md`.

**Reference profile, Rs 2 lakh at 1% (Rs 2,000):**

| Spread | Priced days | Admitted, pad 0 | Pad Rs 0.50 | Pad Rs 1 | Pad Rs 2 |
|---|---|---|---|---|---|
| Bear put 50 | 379 | **367 (97%)** | 361 | 355 | 257 |
| Bull call 50 | 379 | **71 (19%)** | 35 | 16 | 11 |
| Bear put 100 | 379 | 7 | 5 | 4 | 1 |
| Bull call 100 | 378 | 3 | 3 | 2 | 1 |
| 200-point spreads | 377-378 | 0 | 0 | 0 | 0 |

**Admission cost on priced days (Rs, median and 10th-90th percentile):**

| Spread | Pad 0 | Pad Rs 1 |
|---|---|---|
| Bull call 50 | 2,175 (1,882-2,413) | 2,434 (2,142-2,672) |
| Bear put 50 | 1,405 (1,189-1,663) | 1,664 (1,448-1,923) |
| Bull call 100 | 4,079 (3,775-4,401) | 4,339 (4,035-4,661) |
| Bear put 100 | 2,584 (2,270-2,912) | 2,844 (2,530-3,172) |

**Sensitivity profiles:** at Rs 4,000 (Rs 2 lakh at 2%) both 50-point spreads fit on every priced day, the 100-point
bear put on 98-99%, the 100-point bull call on 37% (pad 0) to 2% (pad 2). At Rs 5,000 (Rs 5 lakh at 1%) both
100-point spreads fit on 93-99%; the 200-point bear put on 25-76%, the 200-point bull call never.

**Is it a strike-position cliff?** No (strong evidence). For the 50-point bull call at pad 0, the admitted share is
19%, 18%, 25% and 16% across spot-minus-strike buckets of -25 to -10, -10 to 0, 0 to 10 and 10 to 25 points, and
24% / 14% / 18% by year. The bull call is simply dearer: its median admission is Rs 770 above the bear put's.

**Why (some evidence, standard option pricing):** at the same strike a call costs more than a put by about the cost
of carry (spot minus discounted strike), and NIFTY's skew prices lower strikes richer, so the sold leg of a bear put
is relatively expensive (cheapening that spread) while the bull call sells a relatively cheap upper strike. Both push
the same way. This was not tested here as a separate hypothesis.

## 3. What this means (reasoning only; for the owner and ChatGPT to decide)

1. At the reference profile, a "NIFTY debit spread" system would in practice be a bearish system with rare bullish
   trades. Per review 4 that is acceptable only if declared and benchmarked as such; it must not be described as a
   two-sided strategy.
2. Raising the cap to rebalance it would be a rescue and is ruled out unless the owner chooses a different profile
   for its own reasons, frozen before any return test.
3. Other legitimate design answers, to be chosen before any return test: (a) declare the reference policy
   bearish-only and benchmark it accordingly; (b) choose a different structure for bullish views that fits the cap
   (for example a narrower or further-out-of-the-money call spread), as a separate pre-registered variant; (c) accept
   that the reference account is too small for two-sided NIFTY spreads at 1% risk and record that as the finding.
4. The 39% of days with no 30-45-day monthly expiry is a scope cost of the monthly-only rule; it was agreed and is
   reported, not changed.

## 4. Process note

One full-suite run during the download showed 1 failure that did not reproduce in 13 later runs; the test name was
not captured. It is recorded as an open item, and the commit discipline is fixed: the test exit code is now checked
directly, so a red run can no longer be committed.

## 5. Questions

For ChatGPT:
1. Do you agree the asymmetry is structural (carry and skew) rather than a strike-position effect, given the bucket
   and year splits in section 2?
2. Of the three design answers in section 3, which would you pre-register, and why?

For the owner: which design answer in section 3 (a, b or c) you prefer, once ChatGPT has replied.
