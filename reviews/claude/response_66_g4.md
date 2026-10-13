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

## Addendum (13-14 Oct 2026): judge 58 PASS, then the AI books' scoring (judge 58's list) and live Q5

G4 is **done** (judge 58: PASS, Book 1's Brier recomputed independently to every digit). After the pass, at the
orchestrator's request, these follow-ups are in place.

| Item | What was built | Evidence |
|---|---|---|
| 1. Read the AI books' records | `fno/forecast_scoring/ai_sources.py` reads `research/forecasts/ai_v1/<YYYY>/<d>_<book>_forecasts.csv` with its `_audit.json`. An AI day is scored only on a receipt-verified v2 pack day, and only when every record names that pack | `tests/forecast_scoring/test_scoring_ai.py::test_an_on_time_ai_day_on_a_verified_pack_is_scored_and_its_isolation_reported` |
| 2. Never score `model_mismatch`, `exposed`, a breach, or an unscored day | Scored only when the audit `status` is `on_time` (an allow-list, so any status F1 adds later, such as `breach`, is excluded automatically) and the audit has no `"unscored": true`. Unscored days are listed in the report with their reason | `test_withdrawn_breached_or_mismatched_ai_days_are_never_scored` (6 cases: exposed, model_mismatch, breach, unscored flag, no audit, another pack) |
| 3. Coverage per book (G5 criterion 3) and the isolation label | `coverage.py`: per book (all three), days with a counted forecast out of every v2 pack day from the common start to the as-of day. The report's `coverage`, `ai_isolation` (from the audits; `sealed_same_day` by default) and the weekly summary lines | `test_coverage_counts_from_the_common_start_and_a_missed_day_lowers_it`, `test_the_report_shows_coverage_common_start_isolation_and_unscored_days` |
| 4. `COMMON_START = 14 Oct 2026` | Fixed in `fno/forecast_scoring/wiring.py`; no protocol fixes another date (design 12.8 and protocols v1/v2 name none). A missed day lowers coverage, never moves the start. The review gate opens on 14 Apr 2027 | `test_confirmatory_claims_only_after_six_months_of_common_start_trading` |
| Response 69 item 7: live Q5 against the pack's 15:00 IV30 | `ForecastScorer` takes one resolver per input mode: history (`close_proxy`) uses the panel's close IV30 (unchanged), live (`live_1500_proxy`) uses the IV30 in the day's own verified pack (`score_sources.pack_iv30`). This applies to Book 1 and the AI books alike | `test_live_question_5_is_scored_against_the_pack_iv30_and_history_against_the_panel` (planted disagreement: panel IV30 = next RV - 1 gives "no", Brier 0.81; pack IV30 = next RV + 1 gives "yes", Brier 0.01, same day and p = 0.9); `test_the_pack_iv30_is_read_from_the_pack_and_none_or_unknown_is_no_value` |

This reverses my earlier interpretation 1 (live Q5 against the panel's IV30), which judge 58 had accepted. The change
follows ChatGPT review 30 and response 69 item 7. The protocol text for it is the G1 session's
(`PROTOCOL_v3.md`, not on `main` yet). This scorer change does not depend on it, but v3 must say the same rule.

### Contract proposed to the F1 session (the "unscored" field) and the G1 session (Q5 text)

I could not agree these live: `send_message` blocked on a permission prompt earlier in this session, and the
orchestrator told me not to use it. They are written here for the orchestrator to relay; the code accepts both
forms, so F1 can choose.
- **F1 (`session_01AGpndRQcLERm1xLMNb3Tmj`):** a day counts only if the audit's `status` is `on_time`. To unscore a
  day after the fact (a transcript audit finds a breach), either set `status` to a new value (e.g. `breach`) or keep
  it and add `"unscored": true` with `"unscored_reason": "<who, which session, what>"`. G4 lists either with its
  reason and never scores it. Coverage then shows the day as not counted.
- **G1 (`session_01Ur7pxMsg1quhFZNN7EkmQB`):** v3 should say "live question 5 is scored against the IV30 in the
  forecast's own 15:00 pack (v2 section 2), void when that IV30 is flagged or missing; the history back-fill keeps the
  panel's close IV30 (v1 section 3)". G4 implements exactly this.

Checks: see the commit message (pytest, ruff, check_imports). The report for 13 Oct 2026 is regenerated with the new
fields (`common_start`, `coverage`, `ai_isolation`, `unscored_ai_days`); the scores themselves are unchanged.

## Addendum 2 (14 Oct 2026): judge 62 addendum 1 must-fix, the AI reader now uses F1's scoring gate

**Accepted (strong evidence).** My reader (`f03cb63`) checked only the collection audit's `status`. F1 writes
transcript breaches to a separate `_transcript_audit.json`, so a breached or not-yet-audited day was scored and
counted as covered. Reproduced on the old reader (`f03cb63`'s `ai_sources.py`, run against the new test's planted files): a
`read_other_records` breach for Hybrid left all five of its records scored and nothing unscored.

The fix, in `fno/forecast_scoring/ai_sources.py`:
1. Every AI book-day goes through `fno.ai.scoring_gate.scoring_status(root, day, book, as_of)`, F1's one rule. My own
   status checks and the `"unscored": true` field I proposed are gone; F1's transcript audit replaces them.
2. Only `scored` days are scored. They must also name the day's receipt-verified v2 pack, else they are unscored.
3. The report lists `unscored_ai_days` (never scored) and `pending_ai_days` (audit due, or the week's draw not made
   yet) separately. Neither appears in the scored forecasts, so neither counts in coverage. The weekly summary prints
   both counts.
4. Tests in `tests/forecast_scoring/test_scoring_ai_gate.py`, on files written as F1 writes them (fire log, collection
   audit, `TranscriptAudits.record` / `new_audit`):
   - a planted `read_other_records` breach: unscored with "transcript breach: read_other_records", 0 counted days,
     listed in the report and the summary;
   - a pending audit ("transcript audit due" for one of the first 10 fired days): not scored, 0 counted, and scored
     once a clean audit is recorded;
   - `exposed` and `model_mismatch` are unscored with the gate's reason;
   - a scored day with a wrong or unverified pack is unscored.

**What the tests do not cover end to end:** `score_forecasts` itself, which needs the frozen back-fill, the git
freezes and the panel. It calls exactly `ai_forecasts(root, live.packs)`. The tests run that reader, then
coverage and the report, on the same outputs.

**Collision with F1's same-hour change (fixed):** F1's `0688ad5` (the weekly draw seeded by the week's last official
NIFTY 50 close) removed `today` from `scoring_status(root, day, book)`. My `22ace2f` still passed `as_of`. Both
merged cleanly as text, so merge commit `a31c36f` broke the 4 gate tests (TypeError) for one commit on `main`. I pushed
it after re-running the suite on the merge before that pull, not after it; that was my mistake. The fix drops `as_of`
from `ai_forecasts`, so the reader passes exactly what the gate takes. The G1 v3 session made the same fix in its
protocol commit `904c036`; my identical fix merged into it, and only this note is new. A day whose week has no seed yet is now
`pending` with the gate's reason "weekly audit draw not made yet ...".
