# Experiment 1 results: the 2019-2023 challenge

**Nothing passed.** None of the 8 policies made money that survives the protocol's test after all charges and pads.
Selling protected NIFTY premium, every month or only when options looked expensive, **lost money in 2019-2023**. The
one positive total (P3, buying an iron fly every month, +Rs 24,120) fails the statistical test and rests on
impossible exit prices; without those it is about -Rs 2,600. Under the owner's rule, nothing from this experiment goes
to paper trading.

What this is: a **historical holdout with pre-freeze exposure of predictors and of some forecast-target outcomes;
rules fixed before any exposure** (protocol §10). Daily closes (close-proxy), not 15:00 quotes. A pass would only
have been a gate to paper trading, never proof; a fail means "insufficient evidence under a strict test with 60
opportunities", not proof that no edge exists.

## How it was run

- Protocol v2.2, frozen at commit `9d16431` (freeze commit `c52a6b8`, ledger step `0c1c957`); judge 53 passed the
  freeze on condition that the run uses the frozen files.
- Run from a git worktree at `0c1c957` (identical to `c52a6b8` except the ledger's `protocol_commit`, which the guard
  needs). `sha256sum -c` against FREEZE.md's 45 hashes: **all 45 OK** there. On `main` the same check fails for 3
  files changed after the freeze for unrelated reasons (`warmup_closes.csv`, `panel_reader.py`, `composition.py`), so
  `main` was not used. numpy 2.5.3, as frozen.
- Command: `python -m fno research run 2026-10-12-experiment-1 --period challenge`. Ledger trials 22-31:
  `first_run_on` 2026-10-13, `run_commit` `0c1c957eb49cfa3c2ea3efb6b93befa66d6b6928`.
- Executed twice from the same commit to prove determinism: byte-identical (`results_challenge.json` SHA-256
  `4826897ed4d7e4edf738ec49b926111eb924e3c47cf471fb0aaa73d4e6aff9b6`). The second run is a reproduction, not a second
  trial; nothing was changed between them. (One attempt in between was refused by the guard because the first run's
  ledger record was not yet committed; it read no data.)
- Opportunities: 60 (12 a year), decided 2019-2023; the last exits in January 2024 (hence "2024" in the year columns).

## Results per policy (60 opportunities each; no trade counts Rs 0)

| Policy | Rule | Total net (Rs) | Traded | Win rate | Worst | Max drawdown | Longest losing run | Verdict |
|---|---|---|---|---|---|---|---|---|
| P1 | SC every month | -34,486 | 58 | 50% | -11,346 | 40,607 | 4 | fail |
| P2 | SF every month | -58,219 | 56 | 30% | -13,728 | 60,293 | 8 | fail |
| P3 | BF every month | +24,120 | 50 | 22% | -4,474 | 36,955 | 21 | fail |
| P4 | SC if F1 > 0 | -29,190 | 35 | 49% | -11,346 | 31,607 | 2 | fail |
| P5 | SC if F1 > 0, else BF | -806 | 46 | 43% | -11,346 | 17,734 | 4 | fail |
| P6 | SC if F1 > 0 and no event | -18,468 | 24 | 54% | -11,346 | 23,367 | 2 | fail |
| P7 | SC if VIX above its median | -25,281 | 25 | 40% | -11,346 | 30,775 | 3 | fail |
| P8 | SF if F1 > 0 | -13,243 | 36 | 42% | -3,302 | 16,738 | 3 | fail |

Criterion 2 (bootstrap lower bound of mean net per opportunity, one-sided 99.375%, i.e. 95% Bonferroni over 8
policies) is negative for every policy: from -1,783 (P1) to -613 (P3) Rs per opportunity. Criterion 7 (modelled
maximum loss at most Rs 10,000) holds for every policy (largest 9,952).

**By calendar year of exit (Rs):**

| Policy | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 (Jan exits) |
|---|---|---|---|---|---|---|
| P1 SC | -8,133 | +1,258 | -4,218 | -9,649 | -8,808 | -4,935 |
| P2 SF | -20,396 | -13,645 | -7,803 | -7,417 | -6,790 | -2,168 |
| P3 BF | +24,014 | +23,972 | +8,032 | -20,068 | -10,990 | -840 |

Short structures lost in almost every year, not one bad year. P3's gain is all 2019-2021, then it loses.

## Controls (criterion 3) and comparisons (criteria 4-6)

| Policy | Its total | C1 random timing, 95th pct | C2 opposite condition | Criterion 3 |
|---|---|---|---|---|
| P4 | -29,190 | 1,685 | -12,422 | fail (below both) |
| P5 | -806 | 13,958 | -45,575 | fail (below random timing) |
| P6 | -18,468 | 8,449 | -23,144 | fail (below random timing) |
| P7 | -25,281 | 8,002 | -9,205 | fail (below both) |
| P8 | -13,243 | -21,296 | -28,960 | pass (above both), but criteria 1-2 fail |

- F1 > 0 ("options priced above recent realised volatility") did **not** help the condor: P4 lost more than its
  opposite (-29,190 vs -12,422). It did help the short fly a little (P8 -13,243 vs its opposite -28,960; P8 beats
  P2), but P8 still lost money.
- P5's long-fly branch summed +28,384 (criterion 5 holds) and P6's event filter removed trades that lost -10,721
  (criterion 6 holds); both policies still fail criteria 1-3.
- P7's VIX filter lost more than its opposite.

## Data anomalies: investigated, not changed (the protocol is frozen)

Protocol §4 says a realised loss above the cap is reported and investigated, never hidden. Two appear:

| Cycle (exit) | Structure | Net | Modelled max | Cause (strong evidence: the prices themselves) |
|---|---|---|---|---|
| 9 May 2019 | SC | -11,346 | 8,152 | At exit NIFTY closed 11,301.80; the 11550 put closed 415.25 (45 contracts), about 248 intrinsic; put spread 415.25 - 107.35 (settlement) = 307.90 > width 300 |
| 8 Aug 2019 | SF | -13,728 | 7,411 | At exit NIFTY closed 11,032.45; the ATM 11650 put closed **715.20 on 3 contracts** (settlement 600.35, intrinsic about 618); put spread 715.20 - 323.10 = 392.10 > width 300 |

- These are stale last-trade closes of thin 2019 options (old-format files), not parsing errors: the close is NSE's
  last trade, made earlier in a day when NIFTY moved. The same 8 Aug close gives BF +15,747 on that cycle, and the BF
  entry used an 11850 call settlement (206.40) above the 11650 call (197.80), also impossible.
- **Impossible exits (report-only flag, protocol §4):** 7 traded results. Without them: SC -23,140 instead of -34,486;
  SF -42,703 instead of -58,219; **BF -2,642 instead of +24,120**. The conclusion "nothing passes" does not depend on
  them; P3's positive total does.
- **No-settlement sensitivity** (opportunities needing any settlement price counted as no trade): every policy is
  negative, P3 -42,641.

## What each role reads (labels per AGENTS.md)

- **Statistician (strong evidence for this test):** 0 of 8 pass; every bootstrap lower bound is below zero; the
  year-block bounds (sensitivity) are negative too (-572 to -1,606). With 60 opportunities a small edge could hide,
  but the point estimates for the selling policies are clearly negative, not marginal.
- **F&O trader (some evidence):** protected monthly premium selling at the owner's cap (wings at most 300 points)
  lost in 2019-2023 after Rs 1 pads and Groww charges (in the already-seen 2024-26 discovery period SC made +5,055 and
  SF lost -18,286). Pads (Rs 520) plus charges (about Rs 230-390) cost about Rs 750-900 per four-leg round trip
  (B2's hand-worked cases), against an average SC result of -Rs 595 per traded month here.
- **Volatility trader (some evidence):** "implied above realised" as a monthly entry filter did not select better
  condor months; for the fly it reduced losses but did not create profit.
- **Risk manager (strong evidence on the data):** the Rs 10,000 cap holds on the model but not on close-proxy exits:
  two realised losses above it, both from stale closes. A live desk must exit on quotes, not last trades.
- **Data and backtesting engineer:** thin 2019-2021 option closes are the weakest input; any future protocol should
  price exits with a liquidity floor or quotes (a new experiment, never this one).
- **Red team:** the holdout was partly exposed before the freeze (§10); exposure could only flatter a pass, and there
  is none, so it does not change this result.
- **Portfolio manager / head of desk:** no NIFTY monthly protected-premium rule from this experiment goes to paper
  trading. Books 1 and 2 record "no approved strategy" for now; research continues (new registered trials only).

## Caveats

- Label: historical holdout with pre-freeze exposure of predictors and of some forecast-target outcomes; rules fixed
  before any exposure. Not a forward test; not a 15:00 desk validation.
- Today's lot (65) and today's charges (STT 0.15%) applied to 2019-2023, as the protocol says; the effect of the
  lower historical charges and lot sizes is not measured here.
- Close-proxy prices; no bid-ask; Rs 1 pad assumed.
- Fails are "insufficient evidence", not proof of no edge; a fail may return only as a new registered trial with a new
  protocol and unused data.
- **Follow-up for later experiments:** the trial guard should verify the frozen engine and data hashes itself (today
  it checks only the protocol text; this run's integrity rests on the manual `sha256sum -c`).

Files: `results_challenge.json` and `results_challenge.md` (engine output, unedited), `FREEZE.md`, `PROTOCOL.md`.
