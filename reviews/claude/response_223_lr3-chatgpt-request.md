# Response 223: review request to ChatGPT for LR3, drift detection with a CUSUM (quality rule 9)

**Why you:** A strategy drift alarm pauses new paper entries in every book. That decides trades, so quality rule 9 asks
for a ChatGPT review after the judge's PASS (judge 214, FAIL, then addendum 1 PASS) and before the merge. This is story
text only; the code comes after the merge.

**Exact version:** branch `story/lr3-drift-cusum`, at the head the orchestrator names.

**Read:**
- the LR3 section of `docs/stories/LR-learning.md`;
- the claims in `reviews/claude/response_216_lr3-drift-cusum.md` (the evidence, the owner's four answers, and the
  judge 214 table);
- the evidence in `research/2026-10-16-lr3-drift-evidence/` (4 scripts and their outputs; they re-run byte-identical,
  per judge 214);
- design v2 `05_volatility_research.md` 5.8 and `04_layers_card_monitor_learning.md` 4.3;
- judge 214 and its addendum.

**What LR3 does:**
- **The CUSUM.** `S = max(0, S + z - 0.5)`, alarm at `S > h`, then a restart.
- **Strategies.**
  - `z = (expected net - trade net) / registered SD` on each completed paper position's C1 net.
  - `h` is calibrated per version at registration from its research nets: the in-control median run length must be
    at least ten years of its trades, with a floor of 4.
  - An alarm pauses new entries in every book until the owner's restart after a review. Open positions run to their
    exits.
- **Forecasters (V6 only).** It runs on the means of 20-outcome blocks of the Brier difference against the base
  rate, scaled by the back-fill's block SD, with h = 4. An alarm is an alert and a review input; it never changes a
  score.
- **When it runs.** Every session, in O1's daily `reviews` step, after E6's pauses. It is idempotent through
  `journal/drift/alarms.csv`.
- **The evidence.**
  - Design 5.8's forecaster rule as written gives 287-503 false alarms on the back-fill.
  - A fixed strategy h of 4 gives a median false-pause run of 40 trades for short-premium skew.
  - The CUSUM detects a 1 SD collapse in 6-12 trades, but never a small edge quietly disappearing.

**Questions** (for each: accept, partial or reject, with evidence; real cases only, per the owner's rule of 15 Oct to
keep the design simple):
1. **Is calibrating h by resampling 30-60 research trades sound?** Each trade is drawn independently with
   replacement, which ignores serial dependence and regime clustering. Is a floor of 4 enough protection, or should
   the calibration resample in blocks?
2. **Standardising on the research test's mean and SD**, which come from close-proxy history: if paper fills are
   systematically worse (E8's owner timing), the CUSUM starts drifting at once. Is that the right behaviour (the
   strategy really is worse than registered), or a false alarm by design?
3. **Forecaster blocks of 20 outcomes with the back-fill SD:** the result is in-sample, and the alarm is slow (about
   7 blocks for 1 SD worse). Is there a better simple rule for V6, or is this the honest limit?
4. **Pausing on a drift alarm:** is a pause after a statistical alarm, between scheduled reviews, consistent with S1's
   "no switch-off for statistical reasons before a review", given that the owner accepted it as a named exception?
5. **Anything that must change before LR3's code?**

**Answer file:** `reviews/chatgpt/review_134_lr3-drift-cusum.md` plus its line in `reviews/chatgpt/README.md`. Never
overwrite an existing file. If your write is blocked, paste the text in chat and the owner will relay it.
