# Response 154: BR1, the fast-evidence breadth track (design proposal, no code)

The owner's request (DESK_DECISIONS, 15 Oct 2026, 29d1fcef): "heavy usage, heavy predictions ... with evidence, with
proof ... fast track, but not because of luck." This file is for the judge and ChatGPT, then for the owner's decision.
Measured numbers come from `research/2026-10-15-breadth-sizing/`.

## The answer in five lines

1. **Breadth works, but only through the stocks.** On real data, forecast score differences across 194 F&O
   underlyings correlate at only rho = 0.052, so they act like **about 17.5 independent bets a day**. The 4 index
   underlyings together act like **about 1.6** (rho 0.51). Adding BANKNIFTY, FINNIFTY and MIDCPNIFTY to NIFTY barely
   speeds up evidence. Stock chains do. (Strong evidence for the window measured; one regime only.)
2. **Speed:** a forecaster with a 3% better Brier score than a strong baseline can be shown in about **5-6 months** of
   daily forecasts over the stocks. A 2% edge takes about **12-14 months**, and a 1% edge about **4-5 years**. On
   NIFTY alone the same 2% edge needs about 17 years.
3. **Use frequent, market-neutral targets.** "Does the next move beat the option-implied move?" gets 17.5 effective
   bets. Direction targets (up or down) mostly repeat the market: about 3.4 effective bets.
4. **The data exists now.** NSE's full daily F&O files are archived in Drive for every session from 2019, with every
   underlying in them. An end-of-day version can start without A4c. A4c and the stock chains matter only for a
   version at the 14:30 decision time.
5. **What makes it proof and not luck:** the targets, baselines, family size and looks are all written down before
   the first forecast. Every confirmatory test runs only on forecasts made after the freeze. Holm control covers the
   whole family. Nothing is retuned in place.

## 1. What was measured (`research/2026-10-15-breadth-sizing/`)

- **Data:** the last 300 sessions of NSE's UDiFF F&O bhavcopy (2025-07-29 to 2026-10-14), read only from the Drive
  raw archive.
- **Target:** `Y(u, t)` = 1 when the next close-to-close move of underlying `u` is at least its ATM-straddle implied
  daily move.
- **Forecasters compared:**
  - the market's own p (0.317), which assumes unbiased implied moves and normal returns;
  - a 60-session trailing frequency.
- **Scored:** 239 days, 194 underlyings (4 indices and 190 stocks).

| Quantity | Value | What it means |
|---|---|---|
| Base rate of Y | 0.281 (implied says 0.317) | options overprice the next day's move (the volatility risk premium); a target with an outcome on about 1 day in 3.5 |
| rho of outcomes Y across underlyings | 0.114, giving N_eff 8.4 of 194 | outcomes share a market-wide part (12% of their variance) |
| **rho of score differences** across underlyings | **0.052, giving N_eff 17.5** | what decides test speed: errors are less correlated than outcomes |
| rho of score differences, 4 indices | 0.514, giving N_eff 1.57 of 4 | the indices are almost one bet |
| rho of signed next-day returns | 0.291, giving N_eff 3.4 | direction targets have little breadth |
| SD of the daily cross-sectional mean score difference | 0.0182 (per underlying-day: 0.0754) | the denominator of every test below |
| Lag-1 autocorrelation of that daily mean | 0.045 | days are close to independent, so block length can be short |

**Effective breadth** is N_eff = N / (1 + (N - 1) rho). Its ceiling is 1 / rho, about 19. Thirty well-chosen
underlyings already give about 12, and 50 give about 14.

## 2. Months to show a realistic skill

The test is one-sided on the daily mean Brier difference against the baseline, with 80% power. The first Holm step is
at 0.05/K. The base Brier is 0.202. A "Brier skill" of 2% means 2% lower mean Brier than the baseline. Months count
21 sessions each.

| Skill vs baseline | 194 underlyings, K = 12 | 194, K = 30 | 4 indices, K = 12 | NIFTY alone, K = 12 |
|---|---|---|---|---|
| 1% | 47 months | 55 | 512 | 803 |
| 2% | 12 months | 14 | 128 | 201 |
| 3% | 5.2 months | 6.1 | 57 | 89 |
| 5% | 1.9 months | 2.2 | 20 | 32 |

- **The arithmetic is strong evidence:** the SD and the correlation are measured.
- **Which skill is realistic is reasoning only.** Beating the raw implied p is easy, because options are biased
  upward. Beating a *calibrated* baseline by 2-3% is plausible for a good volatility forecaster. 5% would be
  exceptional.
- **This is why "fast" means months, not weeks.** A claim after a few weeks would be luck, or an edge too large to be
  believable.

## 3. Proposed design (for the story text after the owner's go)

1. **Universe, fixed by rule at the freeze:**
   - every F&O underlying with a traded ATM straddle on at least 80% of the last 60 sessions;
   - entries and exits from NSE's F&O list follow that rule, never a choice;
   - a delisted underlying stays scored up to its last session, so there is no survivorship bias.
2. **Targets:** at most 2 targets x 2 horizons, all frequent and close to market-neutral.
   - **T1:** the next move beats the implied daily move (as measured above).
   - **T2:** the 5-session move beats the implied 5-session move. Its windows overlap, so the confirmatory test uses
     non-overlapping blocks, as v4 does.
   - Optionally, a residual target (the move net of the index move against implied) if the story's sizing shows more
     breadth.
   - Direction targets: reported only, never confirmatory (N_eff 3.4).
3. **Decision time:**
   - **BR1-EOD**, buildable now: the forecast is made after the close of day t from the archived files, and committed
     before 09:15 on t+1.
   - **BR1-1430**, later: at v4's 14:30 snapshot, once A4c (indices first) and the stock chains are recorded live.
   - Both are scored separately. EOD is the evidence engine; 14:30 is what a trade would use.
4. **Baselines:** the primary is the strongest simple one, the calibrated market. That is the implied move rescaled by
   its trailing realised-to-implied ratio. It is M1's `VixScaledWeather` method with the underlying's straddle in
   place of VIX. Also reported: the trailing frequency and the raw implied p. A forecaster must beat the primary, not
   the raw implied p.
5. **Families:** the same targets, data packs and deadline for all three.
   - rule-based: code only;
   - hybrid: rules proposed by AI, applied by code to the whole universe;
   - AI: direct probabilities.
6. **Scoring and luck control:**
   - Brier and log score per underlying-day; the daily cross-sectional mean difference against the primary baseline;
     a block bootstrap or batch means on those daily means.
   - Holm over the whole registered family: K <= 12 means 3 families x 2 targets x 2 horizons.
   - Two looks at registered dates with v4's alpha split. Futility stops at look 1. The power report comes after 60
     days.
   - Every result is published, including losers.
7. **Held-back period:**
   - Confirmatory: only forecasts made after the BR1 freeze, which are forward and unseen by construction.
   - 2019-2025 history: development and sizing only, labelled exploratory, as v4's back-fill.
   - The 300 sessions above have been seen, for sizing only. They choose no rule and no threshold.

## 4. Data: now and later

| Needed | Exists now | After |
|---|---|---|
| EOD option closes, all underlyings | yes: UDiFF bhavcopy 2024-01 on (with `UndrlygPric`) and legacy 2019 to 2024-07, about 2,060 files in Drive raw, archived daily | n/a |
| Stock spot 2019-2023 | not in the legacy file (no underlying price column). The CM bhavcopy is archived only from 2025-10 | a CM bhavcopy back-fill from NSE's archive, or the near-month stock future as a proxy (the story decides) |
| Index closes, all indices | yes (`index-close` 2017 on) | n/a |
| 14:30 quotes, indices | no | A4c / NF step 8a (indices first) |
| 14:30 quotes, stocks | no | stock chains after A4c |
| Events per stock (results days) | partly (the filings archive, A12) | the story decides whether results days get a flag |

## 5. AI cost against BG1 (reasoning only: no AI book minutes are measured yet)

BG1 caps book and role minutes at 50% of the month's measured session minutes, a share and not a known number.
`accounting/ai_usage.csv` is not on main yet, so I can only give orders of magnitude:

| AI family covers | Sessions a day | Minutes a day (guess) | Minutes a month (21 sessions) |
|---|---|---|---|
| 3-4 indices | 1 | about 10-15 | about 200-300 |
| A fixed 30-name subset plus the indices | 1 | about 15-25 | about 300-500 |
| All 194 underlyings | 1, in batch | about 30-60 | about 600-1,300 |

Recommendation (reasoning only):
- The AI family forecasts a **fixed, pre-registered subset of about 30 underlyings**, chosen by a liquidity rank at the
  freeze. That gives about 12 of the 17.5 effective bets at about a third of the cost.
- The rule and hybrid families cover all 194 at no AI cost, because code runs them.
- The first two weeks are measured through F8 before the subset size is frozen.

## 6. Reuse, not rebuild

- **G7:** records through `forecast_v4_rules.records` (the same `Record`, validation and write-once `write`), with
  the question `<target>/<underlying>`. Baselines follow G7's base-rate and window pattern.
- **G8:**
  - the loss functions, `confirmatory_test` (batch means, studentized bootstrap), `futility_p` and the 60-outcome
    power report (`forecast_v4.power`) apply directly to the daily mean differences;
  - a new family file gets BR1's own K and the same Holm logic;
  - `fno/forecast_scoring/v4/` gets one new input adapter, not a second scorer.
- **M1:** the primary baseline is M1's VIX-scaled method per underlying. The weather colour is reported as a regime
  label. The weather code itself is not changed.
- **S1:** BR1's protocol items go in S1's format and are frozen with S1's freeze check before the first counted
  forecast.
- **Data:** the A3 panel builder already parses both bhavcopy formats. The story widens the reader from NIFTY to every
  underlying, with no new parser.

## 7. What we must NOT do (data snooping)

1. Pick targets, thresholds, the universe or the baseline after looking at outcomes. This includes the 300 sessions
   above, which were used only for sizing.
2. Count back-fill results as evidence, or tune a rule on history and "confirm" it on the same history.
3. Add or drop underlyings, targets or families after the freeze. That needs a new version and a new clock.
4. Look at interim results outside the two registered looks, or stop early on a good run.
5. Report the best of many families or targets without the whole family's Holm correction, or hide the losers.
6. Let an AI see the outcome or any data after its cutoff. The packs stay point in time, as v4's do.
7. Treat direction calls as breadth: they are mostly one market bet.
8. Read skill on the breadth target as money. Stock options have wide spreads, so a forecast edge is not a trading
   edge until E4-style fills on liquid names show it.

## 8. Open points for the owner and the reviewers

1. **EOD first?** I recommend it: it can start without A4c, and it is the evidence engine. The 14:30 version follows
   the live chains.
2. **The AI subset size,** about 30, once two weeks of F8 minutes exist.
3. **Which baseline is primary:** I propose the calibrated market. A weaker baseline would make "skill" easy and
   meaningless.
4. **The 2019-2023 stock spot source:** a CM back-fill, or the futures proxy.
5. **Limits, stated:**
   - one 14-month window was measured, and the correlation can rise in a crash, when everything moves together;
   - rho depends on the forecasters compared;
   - liquid large caps may be more correlated than the average;
   - the sizing story must re-measure on 2019-2024 (exploratory) before the freeze.

## Proposed stories (text only after the owner's go)

- **BR1a:** the protocol text (universe, targets, baselines, family, looks, held-back rule) in S1's format.
- **BR1b:** the all-underlying EOD panel from the archived bhavcopies, extending A3.
- **BR1c:** baselines and the rule family, with G7-layout records.
- **BR1d:** BR1 scoring in G8.
- **BR1e:** the hybrid and AI families, after BR1a's freeze.
