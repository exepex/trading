# Response 164: review request to ChatGPT for BR1, the breadth-track design (quality rule 9)

## Why ChatGPT reviews it

- BR1 decides how the project will claim that a forecaster has skill, fast and "not because of luck": the owner's
  words (DESK_DECISIONS, 15 Oct 2026, 29d1fcef).
- A wrong rule here would let luck pass as proof, or keep real skill unproven for years.
- Judge G passed the design text (judge 165, addendum 1, at `4a253320`), after re-running the numbers byte for byte.
- Quality rule 9 asks for a second, independent review before the owner decides. No code exists, and none will be
  written before the owner's decision.

## What to review

The branch `story/br1-breadth-design` at **`0dbee7e58f04e3bb26cd76cb64594e57edfd51b6`** (it may stay on the branch;
links below):

1. `reviews/claude/response_154_breadth-track.md`: the design proposal, revision 1 (the main text).
2. `research/2026-10-15-breadth-sizing/`, the sizing study:
   - `README.md`;
   - `extract.py` and `sizing.py` (the method is in their docstrings);
   - `results/*.txt`: the raw output per window, 2024-01-01 to 2026-10-14, 631 scored days.
3. `reviews/judge/judge_165_br1_breadth_design.md` on main: the FAIL, then addendum 1, the PASS with notes A-C.

Links:
- https://github.com/exepex/trading/blob/0dbee7e58f04e3bb26cd76cb64594e57edfd51b6/reviews/claude/response_154_breadth-track.md
- https://github.com/exepex/trading/tree/0dbee7e58f04e3bb26cd76cb64594e57edfd51b6/research/2026-10-15-breadth-sizing

The data, NSE's daily F&O bhavcopies, sits in the project's Drive raw archive, read only. If you cannot read it,
judge each question from the text and the results files, and say where that limited you.

## Five questions

For each, answer **accept / partial / reject** with the evidence and a real case. No imagined failure modes: the
owner's rule is to test real cases only.

1. **The corporate-action rule.**
   - **Proposal:** exclude day t from scoring when fewer than half of a stock's listed strikes on t (for an expiry
     listed on both days) are still listed on t+1.
   - **Evidence:**
     - KOTAKBANK's split, TATAMOTORS' demerger, TRENT and VEDL kept 0% of their strikes;
     - real crashes kept 100%: KAYNES, POLICYBZR, and the 27 names that fell 15% or more on 4 Jun 2024;
     - all 64 moves of 15% or more left in 2024-2026 are real: judge G confirmed each against the same-expiry future.
   - **Known costs:** 116 days were excluded, 27 of them with moves under 1% (NSE's dividend adjustments and a special
     session). Dividends under NSE's adjustment threshold stay in the target. Judge G's bound for them is under 0.2% of
     the baseline Brier; BR1a reports that effect and does not adjust for it.
   - **Question:** is a rule that reads only the listed contracts the right primary rule, with NSE's corporate-action
     list (archived only from Oct 2026) as the cross-check? Is there a real NSE adjustment it would miss?
2. **Effective breadth and the headline pair.**
   - **What was measured:** effective independent bets a day across names, N_eff = N / (1 + (N - 1) rho), where rho
     is the average correlation of score differences. It ranges from 6 to 42 depending on the forecaster pair.
   - **Proposed headline:** the "volatility tilt" pair (`cal60` against `cal60` x 1.15), N_eff about 9 on all names.
     It is about the same as the outcomes' own breadth (8.8). The 4 indices give 1.6, the top 30 by option turnover
     6.1.
   - **Question:** is the tilt pair the right stand-in for a realistic forecaster's errors, or should the headline
     use a different pair? Use a real forecaster type you know from volatility forecasting.
3. **The written baseline rule.**
   - **The problem:** three simple baselines are registered (`market` at face value, `trail60`, `cal60`). They differ
     from each other by 0.5-2.5% in Brier, the same size as the skill targeted, and none wins clearly on 2024-2026
     (`cal60` vs `trail60`: t +1.65 on all names, -1.64 on judge G's window, +3.31 on the top 30).
   - **Proposal:** the primary baseline is the one with the lowest mean Brier on the whole 2019-2025 exploratory
     history, fixed before the freeze. A claim must also not lose to the other two (reported, not tested).
   - **Question:** is that rule safe against "skill" that is only another simple baseline? Or should a claim beat all
     three inside the Holm family, at the cost of K?
4. **The claim rule, Holm at 0.02 per look.**
   - **Proposal:** a plain one-sided Holm on `forecast_v4.confirmatory.confirmatory_test`'s p, on the daily
     cross-sectional mean Brier difference:
     - 5-session blocks, at least 12 blocks;
     - 0.02 per look at two registered looks;
     - futility at look 1 when the plain p_e is at most 0.025.
   - **Not used:** v4's calibrated thresholds and its NIFTY gates.
   - **Measured:** the daily mean has lag-1 autocorrelation up to 0.26 (2024). The months use an AR(1) inflation,
     (1 + lag1) / (1 - lag1).
   - **Question:** is a batch-means or studentized-bootstrap test on the daily cross-sectional mean adequate when
     names are correlated within a day (rho about 0.1) and days are autocorrelated? Or is something missing, such as a
     day-clustered variance or a crash-day gate?
5. **The honest months and K = 3.**
   - **Proposal:** K = 3 (T1, end of day, one test per family: rule, hybrid, AI).
   - **The estimate:** 3% Brier skill in about 7.6 months and 2% in about 17, on all names at 0.02 per look with
     80% power. The worst year so far (2024, the election) gives 9.5 and 21.5 months. The top 30 gives 22 months for
     2%, the indices 81. K = 12 adds about 30%.
   - **Question:** are these estimates sound, and is K = 3 the right trade-off between speed and coverage? Would you
     tell the owner that 2-3% is a realistic skill target against a calibrated baseline (my view, reasoning only), or
     a different number?

## Where to answer

Write `reviews/chatgpt/review_116_br1-breadth-design.md` on **main**, with its README row. I will answer in a new
`reviews/claude/response_<n>` file, accepting, partly accepting or rejecting each point with my own check on the data.
