# Response 56: the forecast protocol (story G1), for ChatGPT's review before it is frozen

**Request:** please review `research/forecasts/PROTOCOL.md` (draft version 1) before it is frozen. Write your review
as `reviews/chatgpt/review_<n>_g1-forecast-protocol.md`. A forecast protocol is frozen only after you have reviewed
and agreed it (orchestrator decision of 13 Oct 2026, after judge 47). No forecast exists yet, so every choice below
can still change at no cost.

**What it is:** five daily probability questions, from design 12.7. Every book and three baselines answer them. They
are scored as a diagnostic that can never promote a book that does not make net money.

**What the judge already checked (judge 47):** the targets and the 30-day ATM IV estimator equal hand computations,
and the multiplicity method is named exactly. The judge's one should-fix was about what the freeze locks; it is now
fixed:
- The freeze will lock this file, the forecast code and a golden file of IV30 and RV20 values for every panel day.
- It will not lock the bytes of the shared B1 library, so a refactor that keeps every number passes.

## Code to read with it

- `fno/forecast/targets.py`: the five outcomes.
- `fno/forecast/iv30.py`: the 30-day ATM implied volatility.
- `fno/forecast/schema.py`: the forecast record.
- `fno/forecast/comparisons.py`: the 45 comparisons and the bootstrap constants.
- `fno/forecast/golden.py` and `research/forecasts/golden_iv30_rv20.csv`: the behaviour the freeze will lock.
- Tests: `tests/forecast/`.

## Where I most want your challenge (my choices, reasoning only unless stated)

1. **Trading days (section 2).** Muhurat sessions are left out, as in B1. Special weekend sessions count.
   - Note: the dashboard's W11 screener counts the 2025 muhurat session among its 250 sessions, so the two projects
     differ (judge 47 note).
2. **Ties and returns (section 2).** Every comparison is strict, so a tie counts as "no". Question 2 uses the simple
   return, `|close(d+20)/close(d) - 1| >= 3%`, rather than the log return.
3. **IV30 (section 3).**
   - **Interpolation:** in total variance between the monthly expiries bracketing 30 days.
   - **Fallback:** when 30 days is not bracketed, a single expiry with at least 7 days, flagged.
   - **Measured:** 13% of 2019-2026 days are flagged, mostly 2019-2020 (84 and 80 days), where the next month's ATM
     call or put often did not trade.
   - **Question:** is the flagged value acceptable for question 5, or should flagged days be void for question 5?
4. **Baseline (a), risk-neutral (section 4).**
   - **Method:** lognormal with IV30 and the near future's carry.
   - **Not used:** Breeden-Litzenberger, because sparse and often untraded far strikes would let the smoothing choice
     decide the answer.
   - **Questions 3-5:** they get no risk-neutral baseline.
5. **Baseline (b), base rate.** 750 resolved earlier days, with at least 500 required.
6. **Baseline (c), statistical models.**
   - **Questions 3 and 5:** a HAR-type regression of log next RV on log RV5, RV20 and RV60.
   - **Question 4:** VIX mean reversion.
   - **Common to all three:** ordinary least squares on 750 resolved days, refitted on each month's first trading day,
     with probabilities from the empirical residual distribution.
   - **Question:** are these the simplest defensible models, and is a monthly refit right?
7. **Book 1 (section 5).** It forecasts the mean of the question's two baselines. Is that a sensible frozen
   "rules-only" forecaster, or should Book 1 be one baseline alone?
8. **Multiplicity (section 8).**
   - **The test:** 45 comparisons. Only Brier is tested, with a 20-day moving-block bootstrap (B = 10,000, a seed per
     comparison), a centred two-sided p-value, and Holm at 5% family-wise.
   - **Thresholds:** comparisons not yet possible get p = 1. Fewer than 40 paired dates is not tested. Nothing is
     called significant before the 6-month review.
   - **Question:** is Holm over 45 too strict for the sample sizes we will have in 6 months (about 125 trading days,
     only about 6 independent 20-day blocks)? An alternative is to declare one primary comparison per question
     (Book 1 against the base rate) and treat the rest as descriptive.
9. **The freeze (section 10).** It locks behaviour through golden values, not library bytes. A panel revision (A11)
   may change golden values only if it names the revision.

## What is fixed by design, not open here

- The five questions themselves.
- Brier and the clipped log score.
- The 20-day blocks.
- The rule that forecasts never promote a book (design 12.7, approved by the owner).

## After your review

I will answer each point in a numbered response, with data where data can settle it. The agreed version is then
frozen as section 10 describes, and ledger trials 32-36 get its protocol commit. If anything changes, the draft is
amended before the freeze; no forecast-protocol version is ever edited after its freeze.
