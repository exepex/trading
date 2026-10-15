# Response 154: BR1, the fast-evidence breadth track (design proposal, no code), revision 1

The owner's request (DESK_DECISIONS, 15 Oct 2026, 29d1fcef): "heavy usage, heavy predictions ... with evidence, with
proof ... fast track, but not because of luck." This file is for judge G (judge 165), ChatGPT, then the owner.
Measured numbers come from `research/2026-10-15-breadth-sizing/` (`results/` holds every output).

Revision 1 answers judge 165 (FAIL: 1 blocking, 7 should-fix). Each finding was re-checked on the data before it was
accepted. The answers are at the end.

## The answer in six lines

1. **Breadth helps, but less than the first draft said.** Across about 140-200 F&O underlyings, a realistic
   volatility forecaster's daily errors behave like **about 9 independent bets a day**. The 4 index underlyings
   together behave like about 1.5. The 17.5 of the first draft was one easy pair of forecasters. (Strong evidence for
   2024-2026.)
2. **Speed, honestly:**
   - a believable **3% edge** over a strong baseline shows in about **8-10 months** of daily forecasts;
   - a **2% edge** in about **17-22 months**;
   - on the indices alone the same 2% edge needs about **7 years**.

   These assume K = 3 confirmatory tests, v4's 0.02 per look, 80% power, and the day-to-day correlation counted.
   Faster than that is luck or an unbelievable edge.
3. **Fast evidence comes from stocks, not from adding BANKNIFTY, FINNIFTY and MIDCPNIFTY.** Use frequent,
   volatility-type targets. Direction calls are mostly one market bet.
4. **An end-of-day version can start from data we already have.** NSE's full daily F&O files for every underlying
   are archived in Drive daily: in the current format from 2024, in the old format from 2019. A4c and the stock chains
   matter only for a 14:30 version.
5. **Corporate actions must be removed first** (judge 165's blocking finding). A split or demerger looks like a
   -50% to -160% "move". I propose a data-native rule, measured to catch all of them and no real crash (section 1).
6. **Proof, not luck:**
   - everything is written down before the first counted forecast;
   - only forecasts after the freeze count;
   - Holm control covers the whole family;
   - the baseline is chosen by a rule;
   - nothing is retuned in place.

## 1. The target and the corporate-action rule

**Target T1.** `Y(u, t)` = 1 when the next close-to-close move of underlying `u` is at least its ATM-straddle implied
daily move. It is frequent:

| Base rate | 2024 | 2025 | 2026 to date |
|---|---|---|---|
| Measured | 0.257 | 0.235 | 0.266 |
| Face-value implied p | 0.317 | 0.317 | 0.317 |

Options overprice tomorrow's move. This is the volatility risk premium.

**Corporate actions (blocking finding 1, accepted).** NSE's daily file gives the unadjusted spot, so splits, bonuses
and demergers look like crashes. Measured in 2024-2026:
- **Rule:** a day is a contract-adjustment day, excluded from scoring, when fewer than half of a stock's listed
  strikes on day t (for an expiry listed on both days) are still listed on t+1. NSE replaces every strike of an
  adjusted contract.
- **It catches the corporate actions:** KOTAKBANK's 5:1 split (14 Jan 2026) and TATAMOTORS' demerger (14 Oct 2025)
  kept 0% of their strikes, as did the contract adjustments of TRENT (4 Jun 2026, spot x 0.67) and VEDL (30 Apr 2026,
  spot x 0.35).
- **It leaves real moves alone:** KAYNES (-22%, 14 May 2026), POLICYBZR (-45%) and every one of the 27 names that
  fell 15% or more on 4 Jun 2024 (the election result) kept 100% of their strikes.
- **The alternative was worse:** a rule on the market-lot size missed every demerger. It also dropped NSE's routine
  lot revisions: 1,214 days, against 41 for the strike rule, in the last 300 sessions.
- **After the rule,** all 64 moves of 15% or more in 2024-2026 are real market moves, each checked by hand.
- **Why the exclusion is safe:** the excluded days are known in advance (NSE's circulars), are not forecasts, and
  apply to every family alike.
- **Second source:** NSE's corporate-action list (archived daily since Oct 2026) is the cross-check. BR1a records any
  day where the two disagree.

## 2. What was measured (2024-01-01 to 2026-10-14, 631 scored days)

Five forecasters, each using only outcomes resolved before day t:
- `market`: the implied move at face value;
- `trail60`: the share of Y over the last 60 sessions;
- `cal20` and `cal60`: the implied move scaled by the trailing 20 or 60 realised-to-implied ratio;
- `tilt`: `cal60` x 1.15, a forecaster uniformly more volatility-bullish than `cal60`, which is the realistic kind of
  "view".

The test statistic is the daily cross-sectional mean of the Brier difference between two forecasters.

| Pair (all 138 names) | rho of differences | Effective bets a day | SD of daily mean | Lag-1 autocorrelation |
|---|---|---|---|---|
| cal60 vs trail60 (two near-identical baselines) | 0.017 | 41.5 | 0.0063 | 0.16 |
| cal60 vs cal20 | 0.031 | 26.4 | 0.0144 | 0.11 |
| market vs trail60 (the first draft's pair) | 0.049 | 17.8 | 0.0176 | 0.09 |
| **cal60 vs tilt (a realistic volatility view)** | **0.105** | **9.0** | **0.0198** | **0.15** |
| Top 30 by option turnover, cal60 vs tilt | 0.134 | 6.1 | 0.0241 | 0.10 |
| The 4 indices, cal60 vs tilt | 0.517 | 1.6 | 0.0475 | 0.04 |
| Outcomes Y themselves | 0.107 | about 9 | n/a | n/a |
| Signed next-day returns (direction targets), first-draft window | 0.291 | 3.4 | n/a | n/a |

**What this means (some evidence):** effective breadth depends on how the forecasters differ. A forecaster with a
view that tilts the same way across all names on a given day gets only about 9 effective bets. This is about the same
as the outcomes' own breadth. The realistic floor is about 9, not 17.5.

**Regime check, the same realistic pair by calendar year:**

| Year | Names | SD of daily mean | Lag-1 | 2% months (K=3, 0.02 per look) | 3% months |
|---|---|---|---|---|---|
| 2024 (the election crash) | 179 | 0.0190 | 0.26 | **21.5** | **9.5** |
| 2025 | 184 | 0.0177 | 0.10 | 14.7 | 6.5 |
| 2026 to date | 198 | 0.0196 | 0.14 | 16.8 | 7.5 |

The day-to-day correlation of the daily mean was not counted in the first draft. It reaches 0.26 in 2024, and raises
the months by up to 1.7x. It is counted everywhere here as an AR(1) inflation, (1 + lag1) / (1 - lag1).

## 3. Months to show a skill (realistic pair, all names, 2024-2026, 80% power, one-sided)

"2% skill" means a mean Brier 2% lower than the baseline's.

| Skill | K=3, 0.05 | **K=3, 0.02 per look (proposed)** | K=12, 0.05 | K=12, 0.02 per look |
|---|---|---|---|---|
| 2% | 13.8 | **17.2** | 18.9 | 22.3 |
| 3% | 6.1 | **7.6** | 8.4 | 9.9 |

The same skill on smaller universes, at K = 3 and 0.02 per look:

| Skill | Top 30 names | The 4 indices |
|---|---|---|
| 2% | 22.0 | 81 |
| 3% | 9.8 | 36 |

Judge 165's 8.4 months at K = 3 used the easier market-vs-trailing pair, one look at 0.05, and no lag-1 correction.
With those settings my script gave 8.5 on its window before I added the lag-1 correction; with the correction it is
9.4.

**The skill sizes are reasoning only.** 2-3% over a strong, calibrated baseline is plausible for a good volatility
forecaster. 5% would be exceptional. Skill on the targets alone is not money (section 9, item 8).

## 4. Proposed design (for the story text after the owner's go)

1. **Universe, fixed by rule at the freeze:**
   - every F&O underlying with a traded ATM straddle on at least 80% of the last 60 sessions, and at least 60
     resolved outcomes;
   - entries and exits follow NSE's F&O list by that rule;
   - a delisted name stays scored to its last session, so there is no survivorship bias.
2. **Confirmatory family, recommended: K = 3** (should-fix 8, accepted):
   - T1 only, end of day only, one test per family (rule, hybrid, AI) against the primary baseline;
   - reported only, never claimed: T2 (5-session moves), direction, the residual target and the 14:30 version;
   - the alternative, K = 12 (2 targets x 2 times x 3 families), costs about 30% more time (table above).
3. **Decision time:** BR1-EOD is the forecast after day t's close, committed before 09:15 on t+1. BR1-1430 is
   reported only once A4c and the stock chains are live.
4. **Baselines** (should-fix 3, accepted):
   - Three simple baselines are registered: `market`, `trail60` and `cal60`. They differ from each other by 0.5-2.5%
     in Brier, which is the size of the skill targeted.
   - **The primary is chosen by a written rule before the freeze:** the registered baseline with the lowest mean
     Brier on the whole 2019-2025 exploratory history (2019-2023 with spot from the near-month future).
   - A claim must also not lose to either other baseline on the confirmatory data. That is reported, not tested.
   - None of the three wins clearly. `cal60` vs `trail60` (t > 0: `trail60` better):
     - +1.65 on all names, 2024-2026;
     - -1.64 on the judge's window after the corporate-action rule (it was +3.25 before the rule);
     - +3.31 on the top 30.
5. **Families, all on the same targets, packs and deadline:**
   - rule: code only;
   - hybrid: rules proposed by AI and applied by code. **Its rule set is frozen at the freeze; a new rule is a new
     version with a new clock** (should-fix 7, accepted);
   - AI: direct probabilities on a fixed subset (section 6).
   - **The rule and hybrid families are scored both on all names and on the AI's subset,** so the AI comparison is
     like for like (should-fix 5, accepted).
6. **Claim rule** (should-fix 4, accepted):
   - The test is a plain one-sided Holm on `forecast_v4.confirmatory.confirmatory_test`'s p (batch means and
     studentized bootstrap) on the daily mean Brier differences.
   - Blocks are 5 sessions (lag-1 up to 0.26), with at least 12 blocks before a member is judged.
   - The rate is 0.02 per look, at two registered looks (v4's split), with futility at look 1.
   - **Not used:** v4's `calibrated_p` thresholds and its NIFTY judgeability gates (`crash_dominated` and the rest).
     They were calibrated on v4's NIFTY members and do not carry over.
   - BR1a states whether BR1 needs its own crash gate, after the 2019-2025 re-measure.
7. **Freeze gate, the regime** (should-fix 6, accepted): before the freeze, BR1a re-measures the SD and lag-1 by
   calendar year on 2019-2025, with the near-month future as spot where the old files have none. The look dates are
   set from the **worst** year, not from an average. On 2024-2026 the worst year so far is 2024.
8. **Results days** (judge note, accepted): skill is reported separately on a stock's results days and other days.
   A forecaster that knows the results calendar gains legitimately but trivially.

## 5. Data: now and later

| Needed | Exists now | After |
|---|---|---|
| End-of-day option closes, every underlying | yes: the current format 2024-01 on (with spot) and the old format 2019 to 2024-07, about 2,060 files in Drive raw, archived daily | n/a |
| Stock spot 2019-2023 | no spot column in the old format | the near-month stock future as spot (BR1a decides; the CM bhavcopy archive starts only in 2025-10) |
| Contract-adjustment days | from the files themselves (the strike rule); NSE's corporate-action list from Oct 2026 | n/a |
| Index closes | yes, 2017 on | n/a |
| 14:30 quotes, indices / stocks | no | A4c / stock chains |

## 6. AI cost against BG1 (reasoning only: no AI book minutes are measured yet)

BG1 caps book and role minutes at 50% of the month's measured session minutes. `accounting/ai_usage.csv` is not on
main yet.

| AI family covers | Minutes a day (guess) | Minutes a month | Effective bets a day (realistic pair) | 2% in (months) |
|---|---|---|---|---|
| The 4 indices | about 10-15 | about 200-300 | 1.6 | 81 |
| **A fixed 30-name subset, by option turnover at the freeze** | about 15-25 | about 300-500 | **6.1** | **22** |
| All names | about 30-60 | about 600-1,300 | 9.0 | 17 |

**Recommendation (reasoning only):** the AI family uses the fixed 30-name subset. That gives about 2/3 of the full
breadth at about a third of the cost, and 2% skill in about 22 months, not the first draft's figure. The first two
weeks of F8 minutes set the final size before the freeze. The rule and hybrid families cost no AI minutes.

## 7. Reuse, not rebuild

- **G7:** `forecast_v4_rules.records` (the same `Record`, validation and write-once `write`), with the question
  `<target>/<underlying>`.
- **G8:** `confirmatory_test`, `futility_p` and the 60-outcome power report in `forecast_v4`, plus one input adapter
  in `fno/forecast_scoring/v4/`. `calibrated_p` is not used (section 4, item 6).
- **M1:** `cal60` is M1's idea of scaling the market's implied move by realised history, but with a 60-session window
  per name. M1's `VixScaledWeather` needs 500 resolved days, which a new F&O entrant does not have (judge note). The
  weather colour is reported as a regime label, and M1's code is unchanged.
- **S1:** BR1's protocol items in S1's format, frozen with S1's freeze check.
- **Data:** the A3 panel builder already parses both file formats. BR1b widens it from NIFTY to every underlying.

## 8. Open points for the owner and the reviewers

1. **K = 3 (recommended), or K = 12?** K = 12 costs about 30% more months.
2. **The AI subset size** (about 30), after two weeks of F8 minutes.
3. **Stock spot for 2019-2023:** the near-month future (proposed) or a CM back-fill from NSE.
4. **The expectation the owner should hold (some evidence):** a believable edge takes most of a year to prove at 3%,
   and nearer two years at 2%. That is about 5x faster than the indices alone, not weeks.

## 9. What we must NOT do (data snooping)

1. Pick targets, thresholds, the universe, the baseline or the contract-adjustment rule after looking at the
   confirmatory outcomes. The 2024-2026 data was used here only for sizing and for testing the rule on known cases.
2. Count back-fill results as evidence, or tune on history and "confirm" on the same history.
3. Add or drop names, targets, families or hybrid rules after the freeze. That needs a new version and a new clock.
4. Look at interim results outside the two registered looks, or stop early on a good run.
5. Claim the best of many without the whole family's Holm correction, or hide the losers.
6. Let an AI see outcomes or any data after its cutoff. The packs stay point in time.
7. Treat direction calls as breadth: they are mostly one market bet.
8. Read forecast skill as money. Stock option spreads are wide, so a forecast edge becomes a trading edge only when
   E4-style paper fills on liquid names show it.

## Proposed stories (text only after the owner's go)

- **BR1a:** the protocol, including the 2019-2025 regime re-measure as a freeze gate and the baseline choice by rule.
- **BR1b:** the all-underlying end-of-day panel, extending A3, with the contract-adjustment rule.
- **BR1c:** baselines and the rule family, with G7-layout records.
- **BR1d:** BR1 scoring through G8's functions.
- **BR1e:** the hybrid and AI families.

## Answers to judge 165

| # | Finding | Answer | Check |
|---|---|---|---|
| 1 | Corporate actions in the target (blocking) | **Accepted.** The strike rule (section 1) | 0% strikes kept on KOTAKBANK, TATAMOTORS, TRENT and VEDL; 100% on the 27 names of 4 Jun 2024, KAYNES and POLICYBZR; all 64 remaining moves of 15% or more checked as real |
| 2 | N_eff is one pair's number | **Accepted.** The headline is now the realistic pair, about 9 (range 6-42) | my pairs reproduce yours: tilt 8.5 against your 8.6 on your window |
| 3 | The primary baseline was asserted | **Accepted.** Chosen by rule on 2019-2025, and must not lose to the others | cal60 vs trail60: on your window, t -1.64 after the corporate-action rule (your +3.25 was before it); +1.65 on 2024-2026; +3.31 on the top 30. There is no clear winner |
| 4 | Alpha and claim rule | **Accepted.** 0.02 per look in every table; plain Holm on `confirmatory_test`; no `calibrated_p` and no NIFTY gates | months +24% (2%: 13.8 to 17.2) |
| 5 | The AI top 30 is slower | **Accepted.** 6.1 (realistic pair) or 10.5 (your pair); 2% in about 22 months; the rule and hybrid families also on the 30 | 10.5 reproduced |
| 6 | One regime | **Accepted.** A freeze gate on the worst year of 2019-2025. Measured so far: 2024 is the worst (2% in 21.5 months) | also found: lag-1 up to 0.26, now in every months figure (up to 1.7x) |
| 7 | Hybrid rules in flight | **Accepted.** Frozen at the freeze | n/a |
| 8 | K = 3 | **Accepted** as the recommendation; K = 12 is the alternative | 8.5 against your 8.4 on your settings (9.4 with lag-1); 17.2 with v4's alpha and lag-1 on the realistic pair |
| notes | Results days; M1's 500-day window; fetch.py; calendar; setup | All accepted: a results-day split; a 60-session `cal60`, not M1's 500; fetch.py rewritten (clean, no hard-coded path); NSE calendar for scoring; setup line in the README | `ruff check` clean on all three scripts |
