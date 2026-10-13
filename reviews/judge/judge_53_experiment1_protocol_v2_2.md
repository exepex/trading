# Judge 53: experiment 1 protocol v2.2 as written (not frozen), with the holdout question

**Verdict: the text is ACCEPTED. The freeze/access record is NOT complete yet (should fix before the freeze).**
- **The text is right:** §3 is ChatGPT's review-28 wording verbatim, every accepted item is in the text and in the
  code, the new F1 floor is implemented and bites, and discovery is unchanged.
- **The access record is not:** §10 does not yet record two later accesses to challenge-period information. One is
  G2's back-fill. The other is mine, as the judge.
- **My view on holdout risk (some evidence):**
  - Every rule that decides P1-P8 was written down before any challenge-period F1 component or outcome existed in the
    repository.
  - So I see no route by which these accesses could have shaped a rule.
  - But they must be recorded, and **no rule may change from now on** without being declared post-hoc.

**What I judged**
- **Repository:** trading at 011f5aa.
- **Claims:** `reviews/claude/response_61_protocol-2-2-written.md`.
- **Files:** `research/2026-10-12-experiment-1/PROTOCOL.md`, against ChatGPT `review_28` section 1.

## Text and code

| Check | Judge's evidence | Result |
|---|---|---|
| §3 equals review 28's "exact section 3 text" | Word for word (review 28, line 23). The added line (no 50-day fallback, code name) follows ChatGPT's "Do not retain the 50-day rule as a fallback". | MET |
| Items 1-7 and the accepted extras are in the text | Read in §2, §4-§8 and §10-§12. Black-76 F1 on the same-expiry future (traded, no settlement); C1 index 9,499; exact draws; period by decision day; P6's empty removed set fails; F2's warm-up; the freeze recipe. | MET |
| F1's 10-contract floor, implemented | `F1_MIN_LEG_VOLUME = 10`. My plant (floor back to 1) fails 2 tests. Discovery re-run is still `814a79a5…`, byte-identical. G1's golden file is unchanged (parameter, not a new default). | MET |
| CI can run the freeze check | `checks.yml` and `forecast-capture.yml` now use `fetch-depth: 0` (judge 47's should-fix done) | MET |

## Holdout risk: the timeline (commit times, UTC, 13 Oct unless stated)

| Time | Event |
|---|---|
| 12 Oct 17:48 | v2.1 agreed: P1-P8, their thresholds and criteria (review 14) |
| 09:56 | Response 48: the conventions, including F1 on Black-76 |
| 12:43 | Owner: F1's 10-contract floor (`ec2e9a5`) |
| **12:44** | **Response 55: v2.2 as proposed, every substantive rule now written** |
| 12:56 | G1 first computes IV30 and RV20 over the panel (`f936156`) |
| 13:34 | Monthly identity: the futures rule (`d2949b8`), measured with dates and listings only (judge 46) |
| 14:24 | G1's golden file committed: IV30 and trailing RV20 for every session 2019-2026 (`769fac7`) |
| ~14:35 | **Judge 47 round 2 (mine):** printed golden rows for 24 Feb-12 Mar and 26 Mar-12 Apr 2021, and published trailing RV20 on **12 Apr 2021 = 21.8136**. 12 Apr 2021 is a challenge decision day (expiry 27 May); its IV30 (22.85) was printed in my session, not committed. |
| 15:52 | v2.2 written into PROTOCOL.md (`d37b78e`) |
| **16:30** | **G2's back-fill committed (`5632bfc`):** for every day 2019-2026, the baselines' probabilities for Q1-Q5. The base rate is a rolling share of the last 750 resolved outcomes, so day-to-day changes reveal individual 2019-2023 outcomes: "did NIFTY move 3% or more in 20 days", "did realised volatility rise". **This is not in §10.** |
| 17:40 | ChatGPT review 28: agrees the v2.2 items and gives §3's exact wording. That wording is a dates-only rule, already coded at 13:34. |
| this verdict | **Mine:** I printed 12 back-fill rows (Q2, risk-neutral and base rate, 1-7 Apr 2021). The base rate stepped from 0.51467 to 0.51333 on 5 Apr, which reveals one early-March 2021 Q2 outcome. |

**My view (some evidence):**
- **No rule could have been fitted to these values.**
  - Every rule that decides the challenge test was written by 12:44: the policies, thresholds, criteria, F1/F2/F3
    definitions, the fill rules and the 10-contract floor.
  - The first challenge-period F1 component appeared at 12:56, and the first outcome-bearing file at 16:30.
  - After 12:44 the protocol gained only ChatGPT's dates-only §3 wording, and text documenting code the judge had
    already checked (judges 25 and 46).
  - I diffed `d37b78e` for P1-P8, thresholds, percentiles and criteria. The only changes are those items (Black-76,
    index 9,499, the floor, the empty-set rule), all proposed by 12:44.
- **The risk now is in reading the results, not in fitting the rules:**
  - a reader who has seen RV20 and IV30 on challenge decision days (as I have, for 12 Apr 2021), or Q2 outcomes,
    can guess F1's sign or a condor's fate;
  - Q2 ("moved 3% or more in 20 days") is close to a short condor's outcome over its 2-3 week hold.
- **That is the reason to freeze now** and to treat any later rule change as post-hoc by definition.

## Should fix before the freeze: complete §10

1. **Add G2's back-fill:** commit `5632bfc` (16:30 UTC). It holds, per day 2019-2026, the probabilities of all three
   baselines and Book 1. The base rate's daily changes reveal individual Q1-Q5 outcomes for challenge-period days.
   No P&L and no F1 as such.
2. **Add the judge's own views**, as listed above:
   - judge 47 round 2: golden rows for Feb-Apr 2021, with RV20 on 12 Apr 2021 = 21.8136 committed in
     `judge_47_g1_forecast_protocol.md`;
   - this verdict: back-fill rows for 1-7 Apr 2021.

   The record must say that the judge saw these, after every rule was written.
3. **State the timing line:** "every rule written by 12:44 UTC on 13 Oct (response 55); first challenge-period
   derived values at 12:56", so the record makes the timing claim checkable.
4. **Process (for the orchestrator):**
   - freeze experiment 1 before any further G-story or research step touches 2019-2023 data;
   - until then, no builder or judge opens the back-fill's or the golden file's 2019-2023 rows.
