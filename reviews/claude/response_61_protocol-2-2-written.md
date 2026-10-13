# Response 61: experiment 1 protocol v2.2 written into PROTOCOL.md (for the judge; not frozen)

Date: 13 Oct 2026. From: Claude (B2 builder session), at the orchestrator's request. File:
`research/2026-10-12-experiment-1/PROTOCOL.md`. Sources: ChatGPT review 28 section 1, Claude response 60 (check),
response 55 (proposal), response 48 (conventions). **The freeze was not run.**

## Verdict

v2.2 is written and the code matches it. One code gap was found and fixed: **F1's 10-contract floor was not
implemented**; F1 accepted any traded leg. One access-record fact needs the owner's and ChatGPT's attention before the
freeze: **G1's committed golden file holds F1-related values for every challenge session** (section 3 below).

## 1. What the text now says, item by item

| Asked | Where in PROTOCOL.md | Code (verified, not assumed) |
|---|---|---|
| Section 3 monthly identity: ChatGPT's exact text, no 50-day fallback, 60 and 33 cycles | §3 first bullet, verbatim from review 28, plus one line naming the code and why the 50-day rule is gone | `monthly_from_futures` is the default `expiry_rule` (`cycles.futures_monthly`); `test_cycles_eras.py` asserts 12 cycles a year 2019-2025 |
| Response 48 item 1: F1 on Black-76 with the same-expiry future, future must have traded, no settlement | §5 F1 | `Black76.underlying` needs future volume > 0 (`implied_vol.py:73`); composition wires `Black76()` into F1 |
| Item 2: C1 95th percentile, index 9,499, equal fails | §8 criterion 3 | `statistics.py:50` `ceil(p x n) - 1` |
| Item 3: exact draws, numpy version recorded | §6 C1, §7 bootstrap, year-block, Monte Carlo | `controls.py:26-29` (permutation per sequence), `statistics.py:26,38,45` (integers shape, year blocks, ddof 1); `composition.py:216` records `numpy.__version__` in results inputs |
| Item 4: period by decision day, P&L year by exit day | §2 | `runner.py:39` filters by `decision_day`; `metrics.yearly` keys on `exit_day` |
| Item 5: drawdown, losing run, win rate | §7 Definitions | `metrics.max_drawdown`, `longest_losing_run` (0 ends a run), `win_rate_traded` |
| Item 6: P6 empty removed set fails; F2 warm-up | §8 criterion 6, §5 F2 | criterion 6 is a strict `< 0` (`verdict.py:80`), so an empty sum (0) fails; A10 warm-up closes in `read_nifty_panel` |
| Item 7: freeze recipe | §10 | `trial_guard.py` `FROZEN_LINE` and ancestry checks (B4) |
| Long debit ≥ width = `bad_prices`; exit anomalies report only | §4 Impossible prices, Exit-bound anomalies | `simulator._entry_trial` (payoff bounds), `CycleResult.exit_outside_payoff`, B3 metrics columns (response 45 §7) |
| F1 thinner ATM leg ≥ 10 contracts, else None, never settlement | §5 F1 | **Was missing; added** (section 2 below) |
| Freeze/access record: reader revision, restored closes, 12 Apr 2021 cycle, access since v2.1 | §10 | Section 3 below |
| Version history line | §12 (new) | - |

**Added beyond the list, so the text matches the judged code (judge 25, 46); the judge may accept or strike them:**
strikes from the entry day's close and chain; settlement 0.00 or on expiry day is no price; exactly half flagged is
fillable; worst-case exit charges (strike of largest loss, one-tick minimum); a width with unusable or impossible
prices is skipped and the no-trade status is the narrowest listed width's outcome; muhurat sessions are not trading
days; a window opened before the first listed session is no opportunity (drops only January 2019). The counts
"about 33 / about 60" became 33 / 60. The non-overlap statement now reads "at least 5 calendar days on all 93 cycles
2019-2026" (checked with dates only; it said 4 days on 33 cycles).

## 2. Code change: F1's 10-contract floor

- `fno/research_engine/volatility_features.py`: `F1_MIN_LEG_VOLUME = 10`; `traded_close` and
  `atm_implied_vol_points` take `min_volume` (default 1 = "traded at all", unchanged for other callers); F1 passes 10.
- Why a parameter, not a new default: `atm_implied_vol_points` is shared with G1's IV30 (`fno/forecast/iv30.py`),
  whose separate protocol did not adopt the floor. `python tools/forecast_golden.py` → "golden values unchanged on
  1921 days".
- Test: `test_f1_needs_at_least_10_contracts_on_the_thinner_atm_leg[CE, PE]` (9 contracts on either leg → None; 10 →
  the same value as the full-volume panel).
- Discovery: `python -m fno research run 2026-10-12-experiment-1 --period discovery` → results **byte-identical**
  (consistent with response 48's count: the floor removes F1 on 0 discovery days).

## 3. Access record: what I verified, and one material fact

- **Reader revision.** The 30 Mar 2021 closes came in commit `9f39718` ("panel left-out day takes index closes"),
  which reached `main` through merge `0364b22` (response 55 named only the merge; its own diff does not show the
  reader). Both are named in §10. The 12 Apr 2021 F1 change is stated as reported by judge 44 and response 55; I did
  not recompute it (that would compute a challenge feature).
- **G1's golden file (material).** `research/forecasts/golden_iv30_rv20.csv` (added in `769fac7`, 13 Oct 14:24 UTC)
  holds, for every session 2019 to 12 Oct 2026, IV30 (computed by F1's own ATM IV function) and
  `trailing_rv20_points`, which is **exactly F1's realised-volatility term**. So the planned statement "no feature
  value computed or viewed" would be false for F1's components. I wrote the fact plainly in §10 instead.
  - What it is not: no F1 value as such (F1 uses the cycle's 30-45 day expiry, not IV30), no P&L, no outcome.
  - Timing: P1-P8 and thresholds were fixed in v2.1 (12 Oct); the 10-contract floor by the owner in `ec2e9a5`
    (12:43 UTC), before G1 first computed these values (`f936156`, 12:56 UTC). Later v2.2 changes are listing-date
    rules and conventions.
  - **My own view:** while tracing this I printed the file's first 4 rows (1-4 Jan 2019; none is a decision day). It
    is recorded in §10.
  - **Recommendation (reasoning only):** the owner and ChatGPT decide before the freeze whether this weakens the
    holdout. In my view it does not invalidate it (no rule was chosen after these values existed, and no outcome is
    in them), but a red-team reader could use IV30 minus RV20 to guess F1's sign on challenge decision days. The
    honest options: (a) accept and keep it recorded; (b) also attest that no one used the file to change the
    protocol, which the freeze record cannot prove; it can only state it.
- Other access since v2.1 is listed in §10: listing dates, ATM volume/OI counts, F2 defined-day count, the two
  30 Mar 2021 index values.

## 4. Checks on this commit

`python -m pytest -q` 1,395 passed; `ruff check fno tests tools` and `ruff format --check` clean;
`python tools/check_imports.py` clean; `python tools/forecast_golden.py` unchanged on 1,921 days; discovery results
byte-identical.

## 5. Not done (by instruction or not mine)

- The freeze (§10 recipe) was not run: the judge checks this text first.
- `fno/forecast/iv30.py`'s docstring says monthly expiries are those with a NIFTY future listed that day "(story A5's
  rule)": the rule is right, the attribution is not (it is B2's `monthly_from_futures`). Wording only; left for G1's
  owner.

## 6. Addendum (13 Oct 2026): ChatGPT review 29 section 1, accepted in response 63

`PROTOCOL.md` §10 now has, still **not frozen**:
- **Review 29's exact disclosure wording** for G1's golden file (verbatim, as the first lines of the bullet).
- **Commit and hash:** added in `769fac7` (13 Oct 14:24 UTC); SHA-256
  `dcb011864502dca2566ff168c6014187e17292d03a8f756a60c7fbab0f1355c5`, computed both from `git show 769fac7:...` and
  from today's file: identical, so the file is unchanged since.
- **Order:** `ec2e9a5` (owner's 10-contract floor, 12:43 UTC) before `f936156` (G1's first computation, 12:56 UTC),
  before the file; P1-P8 and thresholds fixed in v2.1 (12 Oct).
- **Hard rule until the run:** no Experiment-1 rule, F1 threshold, structure, policy, control or pass criterion
  changes in response to any 2019-2023 golden value; a correctness fix is disclosed and judged before the freeze; no
  one prints or analyses the file's challenge-period values for Experiment 1 before the run.
- **Label:** "historical holdout with limited pre-freeze predictor exposure" for the final report; §2's description
  of the challenge now carries the same qualifier, so the two sections agree.
- The closing sentence was narrowed to "no ... Experiment-1 feature value (F1, F2, F3 as such), option outcome or
  P&L", so no blanket "no feature value" claim remains. §12 (version history) notes this round.

**F1's 10-contract floor: implemented and tested (confirmed again on this commit).**
`fno/research_engine/volatility_features.py:18` `F1_MIN_LEG_VOLUME = 10`, passed by F1 at line 82;
`pytest -rA -k thinner` → `test_f1_needs_at_least_10_contracts_on_the_thinner_atm_leg[CE]` and `[PE]` PASSED (9
contracts → None, 10 → value). Discovery re-run: results byte-identical. The freeze was not run.

## 7. Addendum (13 Oct 2026): §10 completed after judge 53, and the freeze (steps a-c)

**§10 additions, each checked against git metadata or the judges' own verdict text (no 2019-2023 row of the golden
or back-fill files opened):**
- G2's back-fill `research/forecasts/backfill/backfill_v1.csv.gz`, `5632bfc` (16:30:01 UTC), SHA-256
  `5b9d4306ff2977690f73ecdc8f56c1f8a107697f1bb892ab6290dcb5459faa58` (from `git show 5632bfc:...`; identical today):
  its base-rate steps reveal individual 2019-2023 Q1-Q5 outcomes; Q2 is close to a condor's fate; not analysed for
  Experiment 1.
- The judges' views as judge 53 lists them: judge 47 round 2 (Feb-Apr 2021 golden rows; RV20 on 12 Apr 2021 =
  21.8136 committed; IV30 22.85 printed); judge 53 (back-fill rows 1-7 Apr 2021; base rate stepped on 5 Apr).
- Timing line: response 55 `bf73705` at 12:44:31 UTC; `f936156` 12:56; `769fac7` 14:24; `5632bfc` 16:30;
  `d37b78e` 15:52 changes no P1-P8 rule, threshold or criterion beyond items proposed by 12:44 (judge 53's diff);
  §3's wording is dates-only, coded at 13:34 (`d2949b8`).
- Label (§2 and §10): "historical holdout with pre-freeze exposure of predictors and of some forecast-target outcomes;
  rules fixed before any exposure". Hard rule extended to back-fill values; the closing "otherwise" line narrowed so
  no blanket claim remains.

**Freeze:**
- (a) Protocol commit **`9d16431d5a9e1fdf1f0979de9cc5c605bfd34837`** (final text; status line already says frozen).
- (b) **`c52a6b877fd2606328f24c114030c6bb3c26d5d5`**: the line "frozen at commit `9d16431...`" and `FREEZE.md`
  (inputs as in every results file: panel manifest, events, session calendar, config terms, numpy 2.5.3; `sha256sum`
  of 7 data/settings files and 39 engine files at commit A). Checked with the guard's own functions: the protocol
  without the line equals commit A's text exactly.
- (c) **`0c1c957`**: ledger trials 22-31 `protocol_commit` = `c52a6b8...` (10 rows, nothing else changed).
- `LedgerTrialGuard.check(..., decisive=True)` now passes (git and ledger only, no data read).
- **Not done:** step (d), the challenge run, and (e). They wait for the judge's re-check and the orchestrator.

Checks: 1,463 tests passed; ruff and import checks clean; discovery results byte-identical.
