# EDGE1 results: simple rule-based NIFTY and BANKNIFTY option trades after real costs

Protocol `research/edge1/PROTOCOL.md` (revision 7, frozen at `bf2d9e4e`, `FREEZE.md`). Run 1 `selection.json`
(81f02afe; the original, pre-revision-7 run is `selection_rev6.json`, d4ea08d6), run 2 `final.json` (1e43260c), both
from the same frozen code with `fno/` and `config.yaml` unchanged; judge B reproduced run 1 byte for byte. Trials
71-98 (`research/ledger.csv`), one Holm family at 0.05. **Every figure is exploratory** (spent and exposed data,
protocol section 2); rupees are for 1 lot of the time, after C1's charges and a Rs 1 pad a leg a side.

## Answer

**None of the 24 variants passed both runs, and nothing is nominated for a forward shadow.** 23 failed run 1's cost
screen and were therefore not tested out of sample (protocol section 11); the one run-1 passer lost money in run 2.
[strong evidence that these 24 variants show no edge after costs; it does not prove that no edge exists]

- Run 1 (decisions 2019-2022) screened 24 tradeable variants; 23 failed G1 (a conservative lower bound of the mean
  gross minus costs). Every NIFTY variant lost money on average, from Rs -632 to Rs -2,085 a trade.
- One passed: **BANKNIFTY short iron fly, take profit at half the credit (SF TP50)**, 21 trades, decided mean Rs
  1,839 a trade, G1 net on the bound +Rs 608.
- Run 2 (decisions 2023 to Sep 2026, read once) tested it: **40 complete trades, mean Rs -337 a trade** (Rs -530 at a
  Rs 2 pad), win share 40%, one-sided p = 0.91, Holm: not significant. It failed every nomination condition. Its take
  profit never fired in 43 trades (`final.json`, exits all planned). Post-hoc, after run 2, not decided on
  (`research/edge1-posthoc/tp_check.py`): in the 11-16 sessions between entry and the 21-day exit, the fly's lowest
  mark was 0.52 of the credit at best and about 0.93 in the median trade.
- The factory's sample plan (G3) for that variant needed 133 trades, about 25 years at 5.25 trades a year: even a
  genuine edge of its run-1 size could not have been confirmed in a forward shadow in any useful time.

## Run 1, original and corrected (revision 7, owner's decision "fix and re-run, report both")

The original run let impossible prices decide exits (stale last-trade closes: a 300-wide spread priced at 392; a
lower-strike put dearer than a higher one). Revision 7 makes such days unusable for entry, triggers and exits
(each vertical in [0, width] and the position in its bounds); an impossible T21 exit is kept out of the decided
mean, its all-trades value a clipped proxy.

| Variant | Original run 1: taken / complete, decided mean | Corrected run 1: complete, impossible exits, decided mean, all-trades mean | Rs 2 pad mean | historical-STT mean | worst trade | max drawdown | G1 net on the bound |
|---|---|---|---|---|---|---|---|
| BANKNIFTY SC2 EXP | 18 / 18, -2,042 | 18, 0, -2,042, -2,042 | -2,307 | -1,999 | -9,567 | -56,195 | too few run-1 trades |
| BANKNIFTY SC2 SL2 | 18 / 17, -380 | 17, 1, -380, -161 | -554 | -318 | -5,622 | -15,220 | too few run-1 trades |
| BANKNIFTY SC2 T21 | 18 / 17, -380 | 17, 1, -380, -161 | -554 | -318 | -5,622 | -15,220 | too few run-1 trades |
| BANKNIFTY SC2 TP50 | 18 / 17, 93 | 17, 1, 105, 298 | -68 | 170 | -5,622 | -14,935 | too few run-1 trades |
| BANKNIFTY SC3 EXP | 15 / 15, -2,087 | 15, 0, -2,087, -2,087 | -2,187 | -2,047 | -8,309 | -40,177 | too few run-1 trades |
| BANKNIFTY SC3 SL2 | 15 / 14, -879 | 14, 1, -879, -646 | -1,079 | -822 | -5,527 | -23,760 | too few run-1 trades |
| BANKNIFTY SC3 T21 | 15 / 14, -879 | 14, 1, -879, -646 | -1,079 | -822 | -5,527 | -23,760 | too few run-1 trades |
| BANKNIFTY SC3 TP50 | 15 / 15, -457 | 15, 0, -457, -457 | -657 | -399 | -5,527 | -23,760 | too few run-1 trades |
| BANKNIFTY SF EXP | 22 / 22, -1,646 | 22, 0, -1,646, -1,646 | -1,746 | -1,584 | -4,213 | -38,832 | -2,754 |
| BANKNIFTY SF SL2 | 22 / 21, 154 | 19, 3, 566, 41 | 366 | 655 | -2,830 | -4,838 | too few run-1 trades |
| BANKNIFTY SF T21 | 22 / 21, 154 | 19, 3, 566, 41 | 366 | 655 | -2,830 | -4,838 | too few run-1 trades |
| BANKNIFTY SF TP50 | 22 / 21, 2,250 | 21, 1, 1,839, 1,557 | 1,639 | 1,931 | -2,830 | -4,838 | 608 PASS |
| NIFTY SC2 EXP | 33 / 33, -944 | 33, 0, -944, -944 | -1,061 | -912 | -9,135 | -46,347 | -2,581 |
| NIFTY SC2 SL2 | 33 / 33, -988 | 33, 0, -849, -849 | -1,267 | -806 | -7,512 | -30,101 | -1,462 |
| NIFTY SC2 T21 | 33 / 33, -849 | 33, 0, -849, -849 | -1,267 | -806 | -7,512 | -30,101 | -1,462 |
| NIFTY SC2 TP50 | 33 / 33, -832 | 33, 0, -832, -832 | -1,249 | -788 | -7,512 | -29,523 | -1,450 |
| NIFTY SC3 EXP | 28 / 28, -2,085 | 28, 0, -2,085, -2,085 | -2,278 | -2,058 | -9,331 | -64,430 | -3,841 |
| NIFTY SC3 SL2 | 28 / 28, -753 | 28, 0, -753, -753 | -1,347 | -717 | -5,907 | -24,635 | -1,427 |
| NIFTY SC3 T21 | 28 / 28, -753 | 28, 0, -753, -753 | -1,347 | -717 | -5,907 | -24,635 | -1,427 |
| NIFTY SC3 TP50 | 28 / 28, -753 | 28, 0, -753, -753 | -1,347 | -717 | -5,907 | -24,635 | -1,427 |
| NIFTY SF EXP | 41 / 41, -818 | 41, 0, -818, -818 | -1,072 | -767 | -8,210 | -44,722 | -1,912 |
| NIFTY SF SL2 | 41 / 41, -1,251 | 39, 2, -858, -1,051 | -1,360 | -789 | -4,077 | -33,653 | -1,131 |
| NIFTY SF T21 | 41 / 41, -1,251 | 39, 2, -858, -1,051 | -1,360 | -789 | -4,077 | -33,653 | -1,131 |
| NIFTY SF TP50 | 41 / 41, -1,037 | 39, 2, -632, -836 | -1,134 | -563 | -4,077 | -29,062 | -1,012 |

**The passer with and without the +Rs 21,533 trade** (the 16 Nov 2021 cycle, whose target fired on an impossible
mark in the original run; the owner asked for this comparison; post-hoc, not decided on:
`research/edge1-posthoc/passer.py` on a checkout of 3152ed44 and of 81f02afe):

| | Original run 1 | Corrected run 1 |
|---|---|---|
| 16 Nov 2021 cycle | target on 30 Nov 2021, impossible prices, +Rs 21,533 | target on 3 Dec 2021, valid prices, +Rs 12,891 |
| Decided mean, 21 complete trades | Rs 2,250 | Rs 1,839 |
| Decided mean without that cycle, 20 trades | Rs 1,286 | Rs 1,286 |
| G1 net on the bound | +634 | +608 |

The other 20 trades are identical in both runs. Run 1's BANKNIFTY SF trades all fall in 2020-2022 (2019's entries had
untraded legs), so the passer rested on 21 trades in three years, two of them volatile.

## Run 2, the tested variant

| BANKNIFTY SF TP50 | Run 1 (corrected) | Run 2 |
|---|---|---|
| Cycles / taken / complete | 48 / 22 / 21 | 44 / 43 / 40 |
| Decided mean (Rs 2 pad) | 1,839 (1,639) | -337 (-530) |
| All-trades mean, proxy for impossible exits (Rs 2 pad) | 1,557 | -432 (-623) |
| Historical-STT mean | 1,931 | -295 |
| Today's lot (30) re-run, decided mean (post-hoc, after run 2, not decided on: `research/edge1-posthoc/today_lot.py`) | 2,244 | -473 |
| Win share | 71% | 40% |
| Worst trade / max drawdown | -2,830 / -4,838 | -4,363 / -21,589 |
| Impossible exits / trigger days skipped | 1 / 27 | 3 / 9 |
| Mean margin, return on margin (calculator only, unchecked) | 44,271, 3.5% | 53,981, -1.0% |
| One-sided p, Holm | - | 0.91, not significant |

## The naked strangle and straddle (measured only: not tradeable under the house rules)

| Measurement (not tradeable under the house rules) | Run | Complete | Decided mean | Win share | Largest loss per lot | Max drawdown | Mean margin (unchecked) |
|---|---|---|---|---|---|---|---|
| BANKNIFTY NS T21 | run 1 | 21 | 2,618 | 0.6667 | 35,086 | -48,459 | 117,156 |
| BANKNIFTY NS T21 | run 2 | 35 | 1,431 | 0.7143 | 79,627 | -79,627 | 143,558 |
| BANKNIFTY NT T21 | run 1 | 31 | 2,460 | 0.6452 | 39,661 | -51,777 | 115,689 |
| BANKNIFTY NT T21 | run 2 | 42 | 1,584 | 0.6429 | 84,883 | -86,789 | 144,820 |
| NIFTY NS T21 | run 1 | 33 | 2,486 | 0.6061 | 26,390 | -26,390 | 99,540 |
| NIFTY NS T21 | run 2 | 43 | 3,823 | 0.7442 | 50,332 | -51,062 | 128,167 |
| NIFTY NT T21 | run 1 | 41 | 207 | 0.561 | 33,811 | -63,568 | 100,857 |
| NIFTY NT T21 | run 2 | 44 | 4,745 | 0.75 | 54,712 | -54,712 | 130,363 |

They earned the most on average, and each had a single trade that lost 2.6 to 8.5 times the Rs 10,000 cap
(March 2026 in run 2: NIFTY strangle -50,332, BANKNIFTY straddle -84,883 a lot), needing Rs 1-1.45 lakh of margin a
lot. They are the premium the house rules forbid collecting: positive on average, ruinous in the tail. Never
nominated (owner's Q1 answer); no rule change is proposed here. [some evidence: 21-44 trades, one tail event decides
the drawdown]

## What each role takes from it

- **Statistician:** at a 90% one-sided bound, 24 variants with no edge would pass about 2.4 times by chance (fewer
  here, as costs are subtracted, and the variants are correlated) [reasoning only]; one pass was no evidence, and it
  reversed out of sample. The 25-year sample plan says this family cannot be settled by
  forward data at one trade a month.
- **Options strategist:** defined-risk monthly condors and flies on daily closes, entered 30-45 days out and closed at
  21 days, give back the premium in costs and tails; the take-profit rule only paid in a volatile regime.
- **Risk manager:** the only positive means come from naked short premium, with single losses 2.6-8.5x the cap; nothing here
  supports loosening the cap.
- **F&O trader:** daily closes of far strikes are often stale (impossible prices up to 3 a variant); any rule that
  acts on them intraday needs live quotes, not end-of-day closes.
- **Portfolio manager:** no EDGE1 variant goes to an R3 shadow. Book 1's choices are unaffected.

## Limits

- Daily closes only: a stale close inside its bounds cannot be detected; entries and exits at closes, not quotes.
- BANKNIFTY 2019 had untraded legs at most entries, so its run 1 is effectively 2020-2022.
- Margin is "calculator only, unchecked" (no independent historical source); 3 run-2 entries have no margin because
  the SPAN file names the moved expiry's old date (2023-06-28, 2024-03-27, 2025-01-30).
- The impossible-price check assumes credit verticals (true of every EDGE1 structure; a shared side-neutral version
  is the A4 builder's RECHECK1 work).
- Lots before 2024 come from NSE's circular schedule (`LOT_CHECK.md`); BANKNIFTY's 2020 circular number was not found.
- Deviation from protocol section 13: ledger rows 71-98 name the cards' commit (e7a2029d) as `protocol_commit`, not
  FREEZE.md's, because the ledger guard checks that commit against each row's `protocol_path` (its idea card), which
  the branch freeze does not contain; the frozen protocol and code are in FREEZE.md (bf2d9e4e), kept in history.
- Today's-lot figures are for the passer only, post-hoc (section 12 asked for them beside every variant; the output
  files do not carry them).
