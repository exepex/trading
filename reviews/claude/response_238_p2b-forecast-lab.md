# Response 238: P2b, the Forecast lab page (`forecast_lab`, contract 2.10.0 `FnoForecastLab`)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (P2 page builder), branch `story/p2b-forecast-lab`. Story:
`docs/stories/W3-fno-screens.md`, Part 1, build step 2. Lane 1 (what a screen reads). For judge D.

## What the page is built from (strong evidence: the files and the tests)

- G4's latest daily score report dated on or before the session (`research/forecasts/scores/<day>.json`), used as is:
  nothing is re-scored, re-verified or recomputed.
- The session's committed forecast records: protocol v2's live file (`research/forecasts/live_v2/<YYYY>/<day>_forecasts.csv`,
  Book 1 and the three baselines) and the AI books' files (`research/forecasts/ai_v1/<YYYY>/<day>_<book>_forecasts.csv`).
- Code: `fno/market_read_models/forecast_lab_inputs.py` (reader), `forecast_lab_forecasters.py`,
  `forecast_lab_questions.py`, `forecast_lab_block.py`; wired in `wiring.py` (`build_forecast_lab_inputs`), a new
  `SessionRows.forecast_lab`; the block is the 22nd in `build_market_blocks()` (1,273 pages a day).

## Mapping decisions (agreed with the screens lead, 16 Oct 2026; each checked against G1's protocol)

1. **The yardstick is Book 1, not a baseline (strong evidence: `research/forecasts/PROTOCOL.md` section 8, unchanged in
   v2 and v3).** G1's only confirmatory family is Book 2 and Book 3 each against Book 1. Every book against a baseline
   is secondary and descriptive. So `primary_baseline` = `book1_rules` and `comparisons` = G4's `modes[].primary` rows
   for the question. The contract's own Mock examples showed the base rate as v3's yardstick and a "better" before any
   review; the screens lead is correcting them in the next contract change.
2. **Comparison fields:** forecaster = `first`, baseline = `second`, n_pairs = `n`, mean_diff =
   `mean_brier_difference`, interval = `interval_unadjusted_95`, p_value = null when `tested` is false (G4 writes 1.0
   there), min_effect_met and futility_upper_bound null (v4 only).
3. **Verdicts:** not_tested when not tested (fewer than 40 paired dates); before_review while G4's
   `confirmatory_allowed` is false (design 12.8: six months of common-start trading); only then better / worse /
   no_difference from `holm_significant` and the sign. No verdict can show "better" before the review.
4. **Live only:** scores, comparisons and coverage from G4's `live_1500_proxy` mode. The back-fill appears only on
   `forecast_history`, labelled. Today every question has 0 scored live days (the first live day resolves in 20
   sessions; Q4 in 10).
5. **v4:** listed in `protocols` as a draft (frozen_commit null, its eight ids V1-V5, V6_1d, V6_5d, V7); no V question in
   `questions` until G6 freezes it, so no draft number and no invented `n_needed` reaches a public page. A test fails
   once `research/forecasts/FREEZE_v4.md` exists, so the page cannot stay silent about a frozen v4.
6. **Left out for now:** the card's "house" forecast (no source yet) and the weather as a forecaster (it waits with v4).
   `settle` is not_measured with nulls, even past 60 scored days, until a story measures r (the screens lead rewords
   the enum in the contract).
7. **Small fixed mappings:** n_needed 40 (2L); per forecaster n = `primary.scored`, n_missing = `counts.no_forecast`,
   mean_loss = `primary.mean_brier`; the question's n_scored and n_void are Book 1's (the yardstick's) resolved and void
   counts.

## Today's values and AI statuses (some evidence: real data, 14-16 Oct)

- Each forecaster's own record of the session, its probability as recorded; a recorded "no forecast" (an empty
  probability, e.g. the risk-neutral baseline on Q3-Q5) is left out, never imputed.
- Book 1 and the baselines: late when generated after 15:15 IST; counted only once G4 verified the day against its
  capture receipt; pending while G4 has not reached the day or could not verify it (test).
- An AI book: G5's gate as G4's report gives it (`pending_ai_days`, `unscored_ai_days`): late; model_mismatch; breach
  for "exposed" or "transcript breach"; left out for no_submission, not_fired, not_revealed, and for other reasons
  (invalid, a pack problem: the contract has no status for them; they count as unscored in coverage).
- **Found on real data and fixed before the first commit:** G4's 15 Oct report ran before the AI books' 15 Oct files
  existed, so they are in neither of its lists. A first version called such a day "counted" with no probability. Now
  a day G4 lists nowhere is counted only when its record holds a probability; otherwise it is pending.
- `answer_on` = the session `horizon` NSE sessions later (calendar A7). Known limit: in late December, if the next
  year's holidays are not in the calendar yet, the build stops, named (as the 3 pm recorder already does).

## Coverage (strong evidence: the real 16 Oct report)

- Books only: G4 measures none for the baselines, so theirs is null (the contract allows null).
- pack_days and counted_days are G4's. The rest of the pack days are split by why they did not count:
  - late: Book 1's records generated after 15:15 IST; an AI book's G5 reason "late";
  - unscored: a live day that did not match its receipt; an AI book's other gate reasons;
  - missing: no forecast at all;
  - AI days still waiting for their audit are none of these.
  If the split does not add up to G4's pack days, the build stops, named (test).
- Real, as of 16 Oct: Book 1 has 2 pack days, 1 counted and 1 late (14 Oct, generated 19:27 IST). Book 2 and Book 3
  each have 2 pack days, 0 counted, 1 missing (14 Oct, no submission) and 1 late (15 Oct).

## Never sent (criterion 4)

The AI books' reasons ("attempted" texts), versions (`sha256:`, `isolation:`), sessions (`claude.ai`, `cse_`) never
reach the page: only the forecaster id, probability and status (test over three real days). Isolation is
`sealed_same_day` with the owner's label "sealed same day (not full F1)"; an AI book is never shown as code.

## Tests (`tests/market_read_models/test_forecast_lab_page.py`, 21)

Every score and comparison against G4's live mode; coverage against G4's numbers and the split; today's values against
the 15 Oct records; each AI reason; a planted pending day and a planted on-time AI record (counted); an on-time live record of an unverified day
(pending); every verdict
case; v4 as a draft; the empty state before any report; coverage that does not add up; never-sent; a bad G4 figure
named by path and rule, never by value (criterion 3).

## Known limits and doubts

- A G4 report always lags the 15:00 records by about seven hours (G4 runs at 22:41 IST); the 07:10 publish reads the
  session's report, so this only matters for a manual run between them (then the AI books show pending).
- Two isolation labels in one AI book's audits are shown as the weaker one (sealed same day), never full F1.
- The question-level n_scored is Book 1's count; another forecaster's own count is in `per_forecaster`.
