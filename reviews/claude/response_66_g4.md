# Response 66: story G4 (forecast scoring and reports) built, claims for the judge

Date: 13 Oct 2026. From: Claude (B2 builder session), at the orchestrator's request. Story:
`docs/stories/G-forecasts.md` G4. Protocols: `research/forecasts/PROTOCOL.md` (v1, sections 7-8) and `PROTOCOL_v2.md`.

## Verdict

Built:
- every resolvable Book 1 and baseline forecast is scored exactly per protocol v1 sections 7-8, with v2's live rules
  (receipts, 15:15 deadline, live and history never mixed);
- a daily GitHub Actions job (no AI) commits `research/forecasts/scores/<as-of>.json` in a stable shape
  (`forecast_scores/v1`), and a Monday job posts a plain-words summary to #fno-desk;
- no confirmatory claim is possible before the protocol allows it (Books 2 and 3 do not exist, so the primary family
  stays p = 1 and its Holm result is withheld).

All four acceptance criteria are met by tests (below).

## Two places where I did not follow the instruction literally (with evidence)

1. **"Wired in baseline_wiring":** not possible without stopping the live capture. `fno/forecast/baseline_wiring.py` is
   in FREEZE_v2.md's byte-checked table (`0df32dbc...`); `require_version_frozen` refuses every live capture if it
   changes.
2. **"New modules" inside `fno/forecast/`:** `tests/forecast/test_freeze_v2.py::test_the_repository_v2_freeze_holds_and_covers_the_v2_code`
   requires every `.py` in `fno/forecast/` to be in the v2 freeze; my first draft there failed it.

So G4 is its own package, `fno/forecast_scoring/`, with its own composition root, `fno/forecast_scoring/wiring.py`
(added to CLAUDE.md's list), and its own command, `python -m fno forecast-scores`, because the forecast `cli.py` is
frozen too. It reuses the frozen code (comparisons, targets, history, schemas, record files, freeze checks) and edits
none of it.

## Per criterion

| # | Criterion | Evidence | Claim |
|---|---|---|---|
| 1 | Brier and log score match hand values; clipping applied | `tests/forecast_scoring/test_scoring_math.py::test_brier_and_clipped_log_score_match_hand_values` (6 cases incl. p = 0 and 1 clipped to 0.01/0.99, p = 0.995 clipped down); calibration bins and means by hand | MET |
| 2 | Block bootstrap with the fixed seed reproduces a committed interval exactly | `test_block_bootstrap_reproduces_the_committed_interval_exactly`: 60 fixture differences, comparison k = 11, committed mean 0.0016161160872767398, p 0.44815518448155184, interval (-0.002196496847533564, 0.0023129662470145616), equal exactly; an independent loop implementation in the test gives the same; k = 12 differs (own seed). Fewer than 40 dates: not tested, p = 1. Holm step-down by hand | MET |
| 3 | Never scored before its target date is resolvable | `tests/forecast_scoring/test_scoring_resolution.py`: pending the day before the 20th trading day (holiday skipped: 1 Jan to 30 Jan 2025), resolved on it; closes after the as-of day exist but are never read; closes not yet arrived keep it pending; a missing needed close voids it; Q4 resolves before Q1; Q5 waits for the panel; the scorer counts pending and scores none | MET |
| 4 | Every report labels forecasts as secondary to net profit | `test_every_report_says_forecasts_are_secondary_to_net_profit`: the record's `standing` field and the summary's first line; `confirmatory_note` while claims are not allowed | MET |

## What is scored and how (each rule from the protocol, cited)

- **Resolution** (`resolution.py`): outcomes from the official closes (`warmup_closes.csv`, which O6 extends nightly)
  **through the as-of day only**, with the frozen `targets.py`; question 5's IV30 from the panel (v1 section 3).
  States: pending, void, resolved.
- **Scores** (`scores.py`, `scoring.py`): per input mode, forecaster and question, the counts (forecasts, no forecast,
  pending, void, scored), mean Brier, mean clipped log score and the 10-bin calibration table.
  - Question 5 on flagged days is a separate sensitivity (`q5_flagged_iv30`).
  - Baseline (a) on Q1-Q2 is split into flagged and unflagged IV30 days.
  - The period's Q5 flag rate is reported.
- **Comparisons** (`block_bootstrap.py`, using `comparisons.py`'s frozen families, seeds and constants): the primary 10
  with Holm, and the secondary 35 as effect sizes with unadjusted 95% intervals.
- **Gate** (`confirmatory_allowed`): false until six months of common-start trading of the compared books (design 12.8).
  `COMMON_START` is None until Books 2 and 3 exist, so `holm_significant` is null in every report.
- **Freeze checks:** v1's `require_frozen_before` on the back-fill's commit (`5632bfc`: passes), and v2's
  `require_version_frozen` whenever live files exist. A failed check means "not scored", exit 1.
- **Live records:** scored only if `<d>_pack.json` and `<d>_forecasts.csv` hash to the day's capture receipt (v2
  section 5), read from the capture's run summary in Drive's pipeline area (`RunSummaryReceipts`; interface
  `CaptureReceipts`).
  - Without Drive credentials every live day stays "unverified", reported and never scored.
  - Records generated after 15:15 IST are counted as late, never scored.
- **Record shape** (`score_report.py`, `forecast_scores/v1`, sorted-key JSON, byte-identical on re-run): `as_of`,
  `standing`, `confirmatory_allowed` / `confirmatory_note`, `inputs`, `late_live_records`, `unverified_live_days`, and
  per mode `scores`, `primary` and `secondary`.
  - `inputs` holds the file hashes, both protocol commits, the history start and the number of live days.
  - The shape is meant for a P1-style read model for the Forecast lab (screen 37); publishing it is P1/P2's job.

## Interpretations the judge should confirm

1. **Question 5's outcome on live days** uses the panel's IV30(d) (v1 section 3, close-based). Protocol v2 says "outcomes
   stay as v1 defines them". So a live Q5 forecast stays pending until the panel is rebuilt past its day. The live mid
   IV30 is the forecast's input, not its target.
2. **Interval percentiles:** the protocol says "the 2.5% and 97.5% percentiles" without a convention. I used numpy's
   default (linear) and wrote it in the module docstring.
3. **Outcomes come from the official closes file, not the panel's closes.** The two are the same NSE index-close values
   (A10/O6). The closes file is extended nightly; the panel is not.

## Holdout rule (experiment 1's 2019-2023)

- **Back-fill:** rows dated before 1 Jan 2024 are dropped by their date text before any field is parsed
  (`backfill_forecasts`). The test plants an unparsable 2023 row to prove it.
- **Golden file:** never read.
- **Panel:** read for IV30 for 2024 onward only.
- **Index closes:** the resolver loads every official close (2017 onward) to build trading-day offsets. These are NSE
  index closes, not golden or back-fill rows. Only closes up to 20 trading days before 2024 enter any 2024 outcome.

## Results so far (descriptive only, secondary to net profit)

History back-fill, close proxy, 1 Jan 2024 to 12 Oct 2026: 9,948 forecasts scored. Book 1 against the base rate, mean
Brier difference with unadjusted 95% interval (negative favours Book 1):

| Question | Days | Difference | Interval |
|---|---|---|---|
| NIFTY up in 20 days | 669 | -0.0004 | -0.0086 to +0.0080 |
| NIFTY moves 3% in 20 days | 669 | -0.0062 | -0.0135 to +0.0011 |
| Realised vol rises | 669 | -0.0336 | -0.0585 to -0.0031 |
| VIX up in 10 days | 679 | -0.0079 | -0.0173 to +0.0019 |
| Realised vol below implied | 630 | +0.0301 | +0.0097 to +0.0551 |

Reading (some evidence, descriptive):
- Book 1 (the mean of two baselines) beats the plain base rate on "realised vol rises".
- It loses on "realised vol below implied", where the model baseline drags it down.
- The rest is indistinguishable.

None of this is confirmatory and none of it can promote a book.

## Operations

- `.github/workflows/forecast-scores.yml`: daily at 22:41 IST (after O6's 21:11 closes) it scores and commits the
  report; Mondays at 09:11 IST it posts `forecast-scores summary --send` to #fno-desk. Both need the existing Drive and
  Slack secrets, and it alerts on failure.
- The report is about 67 KB a day, about 17 MB a year. If that is too much, the daily file could later keep only
  changed days.

## Checks

`python -m pytest -q`: 1,575 passed. `ruff check fno tests tools` and `ruff format`: clean. `python tools/check_imports.py`:
clean. The real report as of 13 Oct 2026 is byte-identical on re-run (SHA-256 `2a1ac000...0ec24`).

## Judge verifies

To recompute one book's Brier for one month, take `research/forecasts/scores/2026-10-13.json` (mode `close_proxy`).
For a month's back-fill rows of `book1_rules` and one question, compute the outcomes by hand from
`warmup_closes.csv` and average (p - o)^2. Note that the report gives the whole-period mean, not monthly means.
