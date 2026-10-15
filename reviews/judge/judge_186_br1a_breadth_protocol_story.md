# Judge 186: BR1a breadth protocol, story text (judge A)

**Checked:** `story/br1a-protocol` at `8d6b5c3f285ca4895141a666c0a440316eda5bef`, the latest. It replaces fbfa7b7b,
8f14121a and 8ac9182a, which the builder and the orchestrator sent in turn. The story is `docs/stories/BR-breadth.md`
(BR1a) and its claims are `reviews/claude/response_177_br1a-protocol.md`. I read them against:
- ChatGPT review 116 (Q3-Q5);
- the owner's row 7983c880 ("Go, with ChatGPT's two fixes");
- the sizing results `research/2026-10-15-breadth-sizing/results/2024-01-01_2026-10-14.txt`;
- `fno/forecast_v4/confirmatory.py`;
- RM1's code commit 0c28cbed.

Text only, no code. Numbered 186: 182-185 were taken by other judges while this was written.

**Verdict: FAIL, 3 should-fix (all in study 3's procedure and its order), no blocking.** The two owner-required fixes
are in, and the outcome screen, the wording and the freezer plan are sound. But the frozen error-rate check can
still be run more than one way, and the owner asked for exactly that check to be pre-registered.

## The points asked

- **`claim_meaning` and `primary_baseline_rule`: MET.**
  - The only confirmatory claim is "family F beats the primary baseline on T1, end of day".
  - The other two baselines are paired, with 95% intervals, and labelled descriptive. "Beats all" is banned, and
    criterion 3 scans for it.
  - The primary is the lowest mean Brier over 2019-2025, with a fixed tie rule, recorded before the freeze. This
    matches review 116 Q3 and the owner's row.
- **The outcome screen is outcome-side only: MET.**
  - It is computed from t+1's file, never in a pack or a feature, and the same for every family.
  - Counts are disclosed by year, with NSE-list disagreements.
  - The more-than-half-kept limit is stated.
  - Criterion 4 tests a full strike replacement (excluded) and a 20% crash with every strike kept (scored). It also
    sets the BR1b interface contract.
- **Honest wording: MET, and checked against the committed result:**
  - N_eff runs from 6.1 (top-30, cal60 vs tilt) to 41.5 (all, cal60 vs trail60), so "6-42" holds.
  - The tilt case is N_eff 9.0 ("about 9").
  - The tilt lost: mean d −0.0063, t −8.06.
  - The "unknown whether any forecaster beats the primary by 2-3%" line is review 116 Q5's sentence.
- **Study 1 (spot proxy): MET as a method,** with the 128-session overlap and the 97% agreement rule. See SF3 for
  its fallback.
- **Study 2 (regime gate): MET as a method:** per-year SD and lag-1, the AR(1) inflation, and March-April 2020 on its
  own. See SF2 for its order with study 3.
- **Study 3: limits fixed before the run, and no post-freeze tuning: MET.** Limits: 0.025 per look, 0.045 over both
  looks, 0.035 false futility; the ladder (0.015, 0.01, 0.005, then postpone) is fixed. Two gaps remain (SF1, SF2).
- **The freezer generalisation: MET as a plan, with no clash.**
  - S1 stays byte-for-byte unchanged, defaults to `--protocol evaluation`, and the definition comes only through
    `wiring.py`.
  - It must land before S1's freeze, because S1's decided `frozen_files` lists `protocol.py` and `completeness.py`.
    That is correct.
  - RM1 goes first. Its code commit 0c28cbed is on RM1's branch, touches `freeze.py`, adds `gate.py`, and is not yet
    judged.
  - BR1's definition carries `requires_gate = False`. That is right, because a BR1 claim decides no money.
  - F9's names are kept. S6's `REQUIRED_ITEMS` line is rebased by whichever lands second.
  - This is lane 1 code. Its own round must show `test_freeze.py`, `test_real_money_gate.py` and every S1 test
    unchanged and green.

## Should-fix

**SF1. "Both signs" makes the false-claim rate ambiguous, and one reading doubles it.**
- **Evidence:** study 3 runs the procedure "with … both signs of d" and defines false claim as "the share of paths
  with any claim at either look", against a limit of 0.025 per look. The test is one-sided at a Holm level of 0.02.
  Under a centred null each sign rejects at about the nominal rate, so pooled over both signs the rate is about
  twice that.
- **Path:** if the builder pools the signs, the real series show about 0.04 per look. The 0.025 limit fails on the
  arithmetic, not on mis-calibration, and the ladder lowers the rate to 0.01 or postpones claims. That roughly doubles
  the months to a decision, and review 116 Q4 notes that futility feeds the stop decision.
- **Fix (text):** "the rates are computed for each sign separately (d and −d), and each sign must meet every limit".

**SF2. Study 2's look counts and study 3's rate depend on each other, and the order is not fixed.**
- **Evidence:**
  - `looks` sets look 2 as "the count giving 80% power for the minimum effect at the worst year's SD and lag-1"
    (study 2). `sizing.py:months` uses z at (1 − 0.02/K), that is, the rate.
  - Study 3 runs "both looks" at "the rate under test". Its fallback lowers the rate "on the same paths".
  - The text does not say whether a lowered rate recomputes the look counts, which then changes study 3's own
    inputs.
- **Path:** if the rate falls to 0.01, one builder keeps the 0.02 look counts and gets lower power than planned.
  Another recomputes them and must re-run study 3 at the new looks. These are two different frozen protocols from
  one text.
- **Fix (text):** state a single deterministic order. For example: "for each candidate rate in (0.02, 0.015, 0.01,
  0.005), in turn, compute the look counts by `sizing.py`'s formula at that rate (one-sided, z at 1 − rate/3, 80%
  power, the worst year's SD and lag-1, δ = 0.02 × the primary's mean Brier from study 1), run study 3 at those
  looks, and stop at the first rate that passes".

**SF3. Study 1's fallback leaves out study 3.**
- **Evidence:** if the agreement is below 97%, "the 2019-2023 years are reported as descriptive only, and the primary
  baseline and the regime gate use 2024-2025 alone". Study 3's null series still read "2019-2025".
- **Path:** in exactly the case where 2019-23's Y is known to be unreliable, the error rates that set the claim rule
  would still be calibrated on it.
- **Fix (text):** add study 3 to the fallback's list (its null series and worst year then come from 2024-2025).

## Notes (one line each, no fix asked)

- Study 3 has no fixed seed. Studies 1-2 must reproduce byte for byte (criterion 5); name study 3's seed too, and the
  judge re-runs it with another seed as planned.
- `frozen_files` lists BR1b-BR1e outputs (the panel, baseline and scoring code, the hybrid rule set, the AI subset).
  The freezer refuses a missing listed file, so BR1 freezes only after those exist. Say so in Known limits.
- The minimum-effect shift in false futility should name its unit: δ = 0.02 × the primary's mean Brier on the
  path's series.
- Coordination: the BR1 register row covers this. RM1, S1's text owner and F9 agreed in scope 3, so there is no
  duplicate.

## Gates

Gates on the trial merge with origin/main a723840d (tree 75f6563, clean merge):
- pytest: 6121 passed and **3 failed**;
- `ruff check`: clean;
- `ruff format --check`: 1127 files formatted;
- `check_imports`: clean.

**The 3 failures are main's, not BR1a's.** origin/main a723840d alone fails the same 3, with 6118 passed (run side
by side):
- `tests/books/test_paper_account.py::test_the_committed_state_is_…` and
  `tests/market_read_models/test_home_blocks.py::test_the_live_wiring_reads_the_repositorys_books_…` both read
  committed paper-account files. E2c's merge step 3 (d9f67c4f) removed those files from the public record.
- `tests/forecast_v4_rules/test_v4rules_series_and_rules.py::test_committed_closes_reproduce_the_disclosed_v6_counts`
  asserts (100, 2409) and gets (100, 2410), so a pinned count broke on a new committed close.
BR1a changes no code, so it neither causes nor fixes these. Main's CI is red: reported to the orchestrator.

**A re-check needs only:** study 3's sign rule (SF1), the rate and look order (SF2), and study 1's fallback list (SF3).
