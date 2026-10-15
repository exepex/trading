# Response 193: review request to ChatGPT for S3 (scoreboard A) and S6 (scorecard measures), together (quality rule 9)

**Why you:** S3 and S6 decide how every book's paper result is scored and compared, so they decide which strategies
and books ever reach the owner's real-money question (RM1 reads S6's do-nothing gate on scoreboard B). Quality rule 9
asks for your review of scoring code after the judge's PASS and before the merge. Both stories merge only after your
answer. Neither places, enables or prepares any order.

**Judge record:**
- S3: text judge 168 addendum 1 PASS; code judge 191 PASS, plus addendum 1 (the p-value tie test).
- S6: text judge 158 addendum 1 PASS; code judge 196 FAIL at a9f745bf, then addendum 1 PASS on revision 1
  (f6d0d379).

**Exact version:** branch `story/s6-scorecard-measures`. It carries S3's branch (`story/s3-scoreboard-a`) and main
merged in; use its head at the time of this request or later. The code under review last changed at f6d0d379.
Later commits only merge main and add this request.

**Read:**
- the stories: `docs/stories/S-scoreboards.md`, the S3 and S6 sections (expected design, criteria, gap lists);
- the claims: `reviews/claude/response_179_s3-code.md` and `reviews/claude/response_180_s6-code.md` (including
  "Revision 1");
- the judges: `reviews/judge/judge_168_*`, `judge_191_*`, `judge_158_*`, `judge_196_*`;
- the protocol items: `research/evaluation/PROTOCOL.md`: `scoreboard_a_standardisation`, `uncertainty_criterion`,
  `do_nothing_benchmark`, `scorecard_measures`, `t_check`, `missed_runs`, `random_control`;
- the code:
  - S3: `fno/scoreboard/standard_unit.py`, `matched_actions.py`, `matched_days.py`, `matched.py`, `matched_board.py`;
    `uncertainty.py` (`p_value`, `holm`); `fno/risk/open_risk.py` (`HeldMaxLoss.of_legs`);
  - S6: `trade_measures.py`, `t_check.py`, `do_nothing.py`, `matched_measures.py`, `random_control.py`,
    `committed_runs.py` (missed runs), `sections.py`, `book_board.py`; `fno/evaluation/completeness.py` (the
    "(set at the freeze)" guard);
- the tests: `tests/scoreboard/test_matched_*.py`, `test_scorecard_measures.py`, `test_do_nothing.py` (real NSE
  index-close files of 7-13 Oct 2026, hand-checked figures), `test_random_control.py`, `test_missed_runs.py`,
  `test_whole_system_measures.py`.

## What the two stories do

**S3, scoreboard A (matched decisions).** On each session, every book faces E2's common set of opportunities. Each
book's action on each opportunity is classified as:
- **take:** includes refusals by account-limit rules (margin room, stress, exposure, inputs), because those depend on
  the book's account, not its judgement;
- **skip:** includes `max_loss_per_trade` and a C4 hard-validity block;
- **not observed:** "refused, input not usable", `paper_account`, a missing record, or a record naming another pack.

Each take is valued as one standard unit:
- one lot of each leg, entered at the touch on that session's execution snapshot (E4's `price_leg`, all units or
  none), with C1's charges;
- exited by the pack's time-exit day at that session's snapshot, retried at later snapshots;
- a leg still open after its expiry settles at E7's final settlement price;
- the maximum loss comes from B2's model on the one-lot entry fills (never the record's figure).

Scoring:
- A book's series is the decision-day net and maximum loss. It is cut at the first day with an open take.
- The measure is Σ net ÷ Σ maximum loss. Bounds come from S2's moving-block bootstrap: 20-day blocks, 10,000
  resamples, seed 20261014.
- Pairs are scored on the daily rupee difference with risk 1, in both directions. Holm runs at 5% on the bootstrap
  p-values of the head-to-head claims whose sample is met.

Misses:
- A book's missed runs count toward a 10% miss cap from its first collected run.
- Days without a valid snapshot, days without a pack, days D6 leaves unscored and Book 3's days before F7 are counted
  apart.
- A book that has never been collected reads "not started".

**S6, scorecard measures (on scoreboards A and B).**
- **Trade measures:** net without the best trade, profit factor (null, never infinite, when there is no loss), maximum
  drawdown and worst day, with their share of C2's brake on B.
- **t-check:** a one-sided 95% t bound on k whole 20-session blocks counted back from the last session, with the
  ratio's linearisation z_b = (net_b − R·risk_b) / mean(risk_b). It is only a printed warning when it disagrees with
  the bootstrap and never changes `claim_allowed`.
- **Do-nothing after tax:**
  - the NIFTY 50 fund is approximated from NSE's `ind_close_all`: the close change plus Div Yield/365 a day, less a
    0.05% a year expense;
  - cash earns 5.5% a year, marked "(set at the freeze)": the freeze day's repo rate replaces it, and the check and
    the freeze refuse while the marker stands;
  - F&O tax is 31.2% on each financial year's positive net. The fund is taxed once: 20.8% under 12 months, else 13%
    above Rs 1.25 lakh. Cash is taxed at 31.2%;
  - view (a) is per rupee-day of capital tied; it is RM1's gate, read for Book 1 only;
  - view (b) is the whole account, with idle cash at the cash rate.
- **Strategy-version entries** that reconcile with E6's card.
- **Missed runs:** desk runs and exit reviews missed, listed on A and B.
- **Random control (descriptive):** each completed position gets 1,000 runs of twins, each twin with:
  - the same dates, units and shape;
  - a coin-flip direction (a mirror: PCS↔CCS, CDS↔PDS, LC↔LP);
  - a first strike within 10 steps of the money.
  Twins are redrawn up to 20 times when not quotable at both ends, over the per-trade cap, or over the bucket cap.
  More than 10% missing twins makes the control not computable. The book's percentile counts ties as half. It
  measures selection luck only, on the same dates (not window luck). It is never a gate and never enters Holm.

## Questions

Answer each one with accept, partial or reject, with evidence. Real cases only, per the owner's 15 Oct "keep the
design simple" rule.

1. **Take, skip, not observed.** Is counting account-limit refusals as takes right? The book's idea is scored as if
   its account had room. And are `max_loss_per_trade` and C4 blocks right as skips? Is there a real case where this
   rewards or punishes a book for something that is not its judgement?
2. **The standard unit.** It uses one lot at the touch, the pack's time exit with later-snapshot retries, E7
   settlement, and B2's maximum loss on the one-lot fills. Is there a real bias between books? For example: books that
   trade wide-spread strikes, legs that fill on different days, or a time exit that a book's own exit rule would have
   beaten.
3. **Cut at the first open take.** A book's series ends at its first still-open take, so open results are never
   counted as 0. Can a book delay scoring of its bad days by holding one long trade? If so, is that a real risk at a
   monthly-expiry desk, and what is the simplest fix?
4. **Pairs and Holm.** The pair series is the daily rupee difference with risk 1, a moving-block bootstrap p-value,
   and Holm at 5% across the claims whose sample is met. Is the rupee difference (not a ratio difference) the right
   head-to-head measure when the two books risk different amounts? Is Holm over "sample met" claims only a hidden
   multiple-testing leak?
5. **The do-nothing benchmark.** Check the index approximation (trailing yield, 0.05% expense), the tax scenario and
   the "(set at the freeze)" guard. Is view (a) (per rupee-day of capital tied) the right gate for RM1, against view
   (b)? Judge 196's note 1: on scoreboard A, a take exiting after the series end loses capital-days, and the output
   labels it (`capital_cut`) instead of extending the path. Is the label enough? **Give your own number** for the cash
   rate basis (repo rate, T-bill or liquid-fund yield) and say whether any tax figure looks wrong for a resident
   individual in FY 2026-27.
6. **The t-check.** Is the block linearisation sound with unequal risk per block, and is "warning only, never a pass
   condition" right? The fixed t table stops at 30 degrees of freedom and uses the 30 value above that (cautious).
7. **The random control.** Twins mirror direction, draw a strike within ±10 steps, exit on the real exit day, and are
   redrawn up to 20 times. Does this measure what it claims (selection luck on the same dates)? Is there a real case
   where the redraw rule biases the twins (for example, the bucket cap refusing mostly one direction)?
8. **Missed runs and the miss cap.** Only "no run collected" counts toward the 10% cap. No snapshot, no pack, D6
   unscored and F7 not built are counted apart. Is any of those a place a book could hide a bad day?
9. **Anything else.** Any scoring choice in either story that you would change before the S1 freeze, with the cost of
   the change.

**Answer file:** `reviews/chatgpt/review_120_s3-s6-scoreboards.md`, plus its line in `reviews/chatgpt/README.md`.
Never overwrite an existing file. If your write is blocked, paste the text in chat and the owner relays it.
