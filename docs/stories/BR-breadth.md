# Epic BR: the breadth track (fast evidence across F&O underlyings)

Roles: statistician, quantitative modeller, volatility trader, risk manager, portfolio manager, red team. Goal: evidence
of forecasting skill within months, not years, that is "not because of luck". It comes from many independent daily
bets across NSE's F&O underlyings, scored against a baseline chosen before the data is seen, with every error rate
checked on real history. Design and evidence: `reviews/claude/response_154_breadth-track.md` (revision 1; judge 165
addendum 1 PASS) and `research/2026-10-15-breadth-sizing/`. Second review: ChatGPT review 116 (PARTIAL), answered in
`reviews/claude/response_176_chatgpt-review-116-answer.md` (the orchestrator's answer, on main). BR1a's claims: `reviews/claude/response_177_br1a-protocol.md`. Owner: "Go, with ChatGPT's two fixes" (DESK_DECISIONS,
16 Oct 2026). Story template and definition of done: `docs/IMPLEMENTATION_PLAN.md`.

The epic's stories:
- **BR1a:** this story, the protocol and its freeze gates.
- **BR1b:** the all-underlying end-of-day panel, extending A3.
- **BR1c:** baselines and the rule family, with G7-layout records.
- **BR1d:** scoring through G8's functions.
- **BR1e:** the hybrid and AI families.

Only BR1a is written now.

---

## BR1a. The breadth protocol and its freeze gates

**Repository:** trading · **Lane:** 1: it decides forecast and evaluation records and the claim rule, and it changes
`fno/evaluation/` (the freezer). Quality rule 9 applies: ChatGPT reviews after the judge's PASS.

**Description:** As the statistician, I want BR1's protocol written item by item in S1's format, and its three
pre-registered history studies run before the freeze, so that a BR1 claim means exactly one thing and its false-claim
and false-futility rates are known on real Indian data.

**Context and why:**
- Response 154 sized the track. The owner accepted it with ChatGPT review 116's two fixes:
  1. **The claim meaning.** The only confirmatory claim is "beats the single preselected primary baseline". The
     other two simple baselines are reported, paired, with uncertainty, and never advertised as beaten.
  2. **The error rates.** `forecast_v4.confirmatory.confirmatory_test` takes the larger of a batch-means p and a
     studentized-bootstrap p (`fno/forecast_v4/confirmatory.py:75`). Its size was never checked on BR1's series,
     which are daily cross-sectional mean Brier differences. v4 itself found null rejection inflation in an
     uncalibrated test and calibrated its thresholds (rule E+D). BR1 must check its own before any claim rule is
     frozen.
- The 2019-2023 files have no spot column. Response 154's freeze gate is a regime re-measure on 2019-2025, using the
  near-month future as spot.

**What is measured so far, and how to read it:**
- **Strong evidence, measured on 2024-2026:** the range of effective bets across forecaster pairs, the per-year
  SD and lag-1 of the daily mean, and the strike-replacement screen.
- **Planning assumptions only, not evidence:** the 2% and 3% skills used for months. No forecaster is known to have
  them.
- **A counterexample:** on 2024-2026 the 1.15 volatility tilt **lost** to `cal60` (mean d -0.0063, t -8.06,
  `results/2024-01-01_2026-10-14.txt`). A tilt is a planning case for breadth, not a model of a good forecaster.

**Scope.** In:

1. **`research/breadth/PROTOCOL.md`**, version 1, in S1's item format (`Value`, `Status`, `Reason`, `Evidence`).
   Every item below is a proposal until the owner decides it item by item. The values are this story's proposals:

   - `universe`: every F&O underlying with a traded ATM straddle on at least 80% of the last 60 sessions, and with
     at least 60 resolved outcomes. Entries and exits follow NSE's F&O list by this rule. A delisted name stays
     scored to its last session.
   - `target_t1`: T1, `Y(u, t) = 1` when `|ln(S(t+1) / S(t))|` is at least the ATM-straddle implied daily move of t.
     Spot is NSE's `UndrlygPric`, or the near-month future close in the old file format. The trading-day count uses
     the NSE calendar (A7).
   - `outcome_exclusion`: the corporate-action screen, **outcome-side only**.
     - A (u, t) pair is not scored when fewer than half of u's listed strikes on t, for an expiry listed on both
       days, are still listed on t+1.
     - The flag is computed from t+1's file, so it is never available to any forecaster and never enters a pack
       or a feature.
     - It applies to every family and baseline alike.
     - Every report states the count excluded, by year, and the days where NSE's corporate-action list (archived
       from Oct 2026) disagrees.
     - Dividends below NSE's adjustment threshold stay in the target. Their measured effect is reported, never
       adjusted (judge 165 add. 1 note B: under 0.2% of baseline Brier).
     - **Known limit:** an adjustment that keeps more than half of the strikes would escape the screen. None was
       seen in 2024-2026 (all 64 remaining moves of 15% or more were checked).
   - `forecast_time`: end of day. The forecast for t uses data up to t's close and is committed before 09:15 IST on
     t+1. The 14:30 version is descriptive only.
   - `families`: rule (code only), hybrid (rules proposed by AI, applied by code, the rule set frozen at the
     freeze), AI (direct probabilities on a fixed 30-name subset chosen by option turnover at the freeze). The rule
     and hybrid families are scored on all names and on the AI's 30.
   - `baselines`: `market` (p = 0.3173), `trail60` (the 60-session frequency of Y), `cal60` (the implied move scaled
     by the trailing 60-outcome realised-to-implied ratio). Formulas as in `research/2026-10-15-breadth-sizing/
     sizing.py`.
   - `primary_baseline_rule`: the registered baseline with the lowest mean Brier over every scored (u, t) of
     2019-01-01 to 2025-12-31 is the primary. A tie at 4 decimals goes to the earlier one in the list above. The
     result is recorded before the freeze and never revisited.
   - `claim_meaning`: the only confirmatory claim is **"family F beats the primary baseline on T1, end of day"**.
     - Against the other two baselines, each family's paired mean difference and its 95% interval are reported,
       labelled descriptive.
     - A result is never written as "beats all baselines".
     - A descriptive loss to a non-primary baseline is shown as a caution, never as proven inferiority.
   - `confirmatory_family`: K = 3, one member per family against the primary. T2, direction targets, the residual
     target and the 14:30 version are descriptive only.
   - `test`: for each member, the daily series `d_t` = the mean over names of (Brier of the primary minus Brier of
     the family).
     - p is `confirmatory_test(d, block=5, k)`, one-sided.
     - Holm over the 3 members at **0.02 per look**.
     - A member is judged only with at least 12 whole blocks.
     - v4's `calibrated_p` thresholds and NIFTY gates are not used.
     - **The rate used is the one set by the null/size check (item `null_size_check`), not assumed.**
   - `minimum_effect`: a 2% lower mean Brier than the primary's. This is a planning value, not evidence of a
     reachable skill.
   - `looks`: two, at fixed session counts after the freeze. Look 2 is the count giving 80% power for the minimum
     effect at the **worst** year's SD and lag-1 (study 2). Look 1 is half of it.
   - `futility`: at look 1 only. A member is futile when the plain batch-means p_e for "the true improvement is
     below the minimum effect" is at most 0.025. That is `futility_p` with a threshold of 0.025, or the check's
     fixed replacement.
   - `null_size_check`: study 3 below, with its limits and its fallback written here before it is run.
   - `regime_gate`: study 2 below.
   - `descriptive_reports`: N_eff of each family's errors (rho of d across names), the results-day split, T2,
     direction, 14:30, the non-primary comparisons and the exclusion counts.
   - `reporting`: every member at every look, its p, its decision, the date, and the losers too. Results are per
     protocol version.
   - `frozen_files`: this protocol, the panel code (BR1b), the baseline and scoring code (BR1c, BR1d), the hybrid
     rule set, and the AI subset list.

2. **Three pre-registered history studies.** These are research scripts under `research/breadth/studies/`, reusing
   `research/2026-10-15-breadth-sizing/extract.py` and `sizing.py`, extended to the old file format. They read only
   the Drive raw archive. Each writes one result file. Their method and limits are fixed by this story text before
   they run, and they are run once.

   - **Study 1: the spot proxy and the primary baseline.**
     - On the 128 sessions where both formats exist (2024-01-01 to 2024-07-05), compare Y from `UndrlygPric` with Y
       from the near-month future close, name by name.
     - Report the agreement rate. If it is below 97%, the 2019-2023 years are reported as descriptive only, and the
       primary baseline and the regime gate use 2024-2025 alone.
     - Then apply `primary_baseline_rule` and record the three baselines' mean Brier with 95% intervals.
   - **Study 2: the regime gate.**
     - By calendar year, 2019-2025: the SD and lag-1 of the daily mean d for each pair of registered baselines and
       for the planning pair (`cal60` vs `cal60` x 1.15), plus the outcome correlation.
     - The worst year sets the look counts (item `looks`) with the AR(1) inflation (1 + lag1) / (1 - lag1).
     - March-April 2020 is reported on its own.
   - **Study 3: the null and size check** (ChatGPT review 116, Q4).
     - **Null series:** each registered baseline pair's daily d over 2019-2025, centred to mean zero, and separately
       for the worst year. This keeps the real skew, heavy tails, crash days and dependence, with no true skill.
     - **Paths:**
       - 2,000 paths per series from a circular block bootstrap with 63-session blocks. The blocks are far longer
         than the test's 5, so dependence beyond the test's block is kept.
       - The real rolling windows, one start every 21 sessions, are reported beside them.
     - **The procedure, as frozen:** run on each path, with K = 3 members taken as the three pairs' paths drawn
       together (their cross-correlation kept), both looks, Holm at the rate under test, and both signs of d.
     - **False claim:** the share of paths with any claim at either look. Limit: at most 0.025 per look and 0.045
       over both looks, overall and in the worst year.
     - **False futility:** the same paths shifted to a true improvement of exactly the minimum effect. The share
       declared futile at look 1 must be at most 0.035.
     - **Fallback, fixed now:**
       - If a false-claim limit fails, the per-look rate is lowered to the first value in (0.015, 0.01, 0.005)
         that passes on the same paths. If none passes, claims are postponed and BR1 reports descriptively until a
         new version.
       - If the futility limit fails, the futility threshold is lowered in the same steps, or futility is dropped.
       - The chosen values are written into `PROTOCOL.md` before the freeze. Nothing is ever tuned on post-freeze
         data.
     - No crash-day gate is added unless study 3 shows a failure that one would fix.

3. **The freezer for a second protocol.**
   - `fno/evaluation`'s freeze and completeness check are generalised from S1's fixed file and item list to a
     protocol definition (path, required items, freeze-record template), passed in by the composition root
     (`fno/evaluation/wiring.py`).
   - S1's behaviour and records are unchanged.
   - BR1's protocol is frozen to `research/breadth/FREEZE_v1.md` and registered in the research ledger (B4), as
     S1's is.
   - `python -m fno evaluation check|freeze|verify` gains a `--protocol breadth` choice, with `evaluation` the
     default.

4. **Wording** (owner, 16 Oct). Every BR1 text and report states the following:
   - breadth as the measured **range of 6 to 42** effective bets a day;
   - **about 9** only as the common-tilt planning case;
   - the months as normal-approximation planning projections, never deadlines;
   - and the line: "whether any forecaster beats the frozen primary baseline by 2-3% is unknown".

Out (with reasons):
- **The panel, forecasters, scoring, the hybrid and AI families:** BR1b-BR1e.
- **Any live run, schedule or Slack message:** none is needed for a protocol.
- **v4:** unchanged. BR1 does not touch v4's members, thresholds or records.

**Gap list:**

| Requirement (source) | Where |
|---|---|
| Single preselected primary; the other baselines descriptive, never "beats all" (ChatGPT 116 Q3; owner 16 Oct) | items `primary_baseline_rule`, `claim_meaning`; criterion 3 |
| Pre-registered null/size check, both directions, both looks, worst regime, false claim and false futility, fixed fallback, no post-freeze tuning (ChatGPT 116 Q4; owner) | study 3; criteria 6-7 |
| Corporate-action screen outcome-side only, counts disclosed (ChatGPT 116 Q1) | item `outcome_exclusion`; criterion 4 |
| Breadth as the range 6-42, about 9 as a planning case; 2-3% hypothetical; the tilt lost (ChatGPT 116 Q2, Q5) | scope 4; criterion 9 |
| K = 3; T2, direction and 14:30 descriptive (ChatGPT 116 Q5; judge 165 should-fix 8) | items `confirmatory_family`, `forecast_time` |
| Worst-regime re-measure as a freeze gate, future as spot for 2019-23 (judge 165 should-fix 6) | studies 1-2; criterion 5 |
| Own futility level (judge 165 add. 1 note A); dividends reported (note B) | items `futility`, `outcome_exclusion` |
| Freeze with S1's freezer (response 154 section 7) | scope 3; criterion 8 |

**Acceptance criteria** (each with a test on committed data or a hand-made fixture):
1. `research/breadth/PROTOCOL.md` parses with `parse_protocol` and is complete for BR1's required items. The
   freezer refuses it while any item is a proposal (test with a fixture protocol).
2. S1's tests pass unchanged. A BR1 fixture protocol freezes to its own record, and verify detects a changed hashed
   file.
3. `claim_meaning` and the report template contain no "beats all" wording. A test scans BR1's templates for it.
4. The outcome screen: a fixture where t+1 replaces all strikes is excluded, and a fixture with a 20% crash and
   every strike kept is scored. The screen's input is t+1's file only, and no forecaster interface receives it (a
   test on the BR1b interface, written here as the contract).
5. Studies 1-2 reproduce byte for byte from the Drive files listed in the manifests (SHA-256 checked first). Their
   result files are committed with the per-year table and the look counts. The formula is checked by hand on one
   year.
6. Study 3 on a hand-made null with known dependence (an AR(1) of lag 0.3, Gaussian): the false-claim rate is
   within 2 standard errors of the procedure's rate. On a hand-made true effect at the minimum effect, false
   futility is within 2 SE of its target.
7. Study 3 on real data writes the false-claim rates (per look, both looks, both signs, overall and worst year), the
   false-futility rate, and the fallback decision by the rule above, with no free choice.
8. `python -m fno evaluation freeze --protocol breadth` refuses an undecided protocol and freezes a decided one.
   `--protocol evaluation` behaves exactly as before.
9. The wording of scope item 4 appears in `PROTOCOL.md` and in the README of `research/breadth/`.
10. Engineering: no file or class over 350 lines; constants in `fno/constants.py`; the gates pass.

**Test plan:** `tests/evaluation/` for the generalised freezer (S1 unchanged, BR1 fixtures);
`tests/research/test_breadth_studies.py` for the screen and the study-3 procedure on synthetic series.

**Judge verifies:**
- re-runs study 1's agreement on the overlap months;
- recomputes one year's SD, lag-1 and look count by hand;
- re-runs study 3 on one pair with a different seed and checks the rates agree within 2 SE;
- checks that no forecaster interface can see the outcome screen.

**Known limits:**
- The rates of study 3 come from 2019-2025 only. A regime never seen there can still break them, and the per-year
  report will show it.
- A bootstrap from history cannot create crashes that history does not contain.
- With seven years, the primary baseline rule rests on 1,736 sessions of history.

**Depends:** the Drive raw archive (read only), S1's protocol format and freezer, G8's `confirmatory_test` and
`futility_p` (`fno/forecast_v4/confirmatory.py`).

**Size:** M · **Status:** story text for the judge's check. Code and studies start only after its PASS and
ChatGPT's review.
