# Response 290: story G13b part A, NIFTY and BANKNIFTY 15:45 price ranges, sealed and scored (builder's claims)

Builder: session_01UkTaDeTRF9ksDgQB9cTU5C · Story: `docs/stories/G13b-price-ranges.md` (text PASS, judge 406.1;
revision 3 PASS, judge 406.2; revision 4 in this branch says what the build does) · Branch: `story/g13b-price-ranges`
(G13 merged to `main` at 4e5c2326 and `main` merged in) · Judge: E · Lane 1 · Scope: part A only (DESK 21 Oct "Scope
freeze"); parts B and C not started.

## Verdict first

Part A is built and tested, not live (`daily.live_from.price_ranges: null`):
- **Issue at 15:45** of each regular session, NIFTY and BANKNIFTY, horizons N1 and N3, five quantiles (5/25/50/75/95%)
  and `P(up)`, from five forecasters (`implied`, `rv20`, `hist750`, `ewma_t4`, `no_change`) plus empty AI/hybrid slots.
- **Sealed** by GitHub's push receipt before 09:15 of the next session, the seal stored once in Drive; a late record is
  counted, never scored.
- **Scored** by the quantile score (5-level pinball, a coarse CRPS), 50%/90% band coverage, Brier of `P(up)`, G4's
  block bootstrap; never pooled across label, method, underlying, issue or horizon.
- **Back-fill** end of day (NIFTY from G13's panel, BANKNIFTY from the archived F&O files, UDiFF and old format) and
  from the 3 pm chains; **reader port** for FL1 (`RangeForecasts`, `RangeScores`, `Outcomes`).
- **O1 step** `price_ranges` after `price_distribution`, G13b's receipts its only pathspecs.

Evidence:
- **Tests:** 73 G13b tests (`tests/price_ranges/`). Full suite on the pushed tree (latest `main`, G13 included, merged in at 30d0d922):
  8,751 passed, 0 failed.
  ruff, format, `check_imports`, `check_records` clean.
- **Mutations:** 14 planted, 14 caught (table below); 2 survived the first pass (special sessions in the
  back-fill, the future's last trade for its settlement) and got tests before this file.
- **Real output:** today's (21 Oct) 1545 records rebuilt from the real canonical chains for both indices (dry run,
  nothing written), and the first end-of-day back-fill scores for both (exploratory, below).

## Criteria: code, test, broken-code proof

| # | Criterion | Code | Tests | Mutation caught |
|---|---|---|---|---|
| 1 | Point in time | `build.py` `RangeBuilder.build` (closes `< d`, CAPTURE), `_reference` | `test_build.py::test_no_close_of_the_day_or_later_is_read_at_15_45`, `test_no_chain_or_no_spot_is_a_missing_issue` | CAPTURE reading `d`'s close |
| 2 | Horizons, τ | `horizons` (G13), `constants.py` `REST_OF_DAY`, `build.py` `_row` | `test_build.py::test_targets_skip_the_holiday_and_tau_adds_the_rest_of_the_day`, `test_past_the_calendar_s_end_is_not_eligible`, `test_a_good_day_...no_n0`; `test_review_fixes.py::test_a_calendar_gap_at_the_stale_check_is_a_reason_not_a_crash` | overnight share 0.393 → 0.5 |
| 3 | Forecasters | `forecasters.py`, `t4.py` | `test_forecasters.py` (8), `test_t4.py` (2.1318 at 95%, 0.7407 at 75%), `test_review_fixes.py::test_the_two_percent_line_is_in_log_terms` | share `(k+tail)/(n+tail)` → `k/n`; spread `sqrt(share)` → `share`; t(4) without `/√2`; `p_big` one tail only |
| 4 | Record check | `records.py` `check_row` | `test_build.py::test_the_record_check_refuses_bad_rows`, `..._accepts_a_point_mass_for_no_change_only_and_known_issues` | (G13's check reused; its mutations in response 262) |
| 5 | Outcomes | `closes.py` (`Outcomes`, `IndexFileCloses`, `TableCloses`), `tables.py` | `test_closes.py` (3), `test_review_fixes.py::test_a_late_index_close_file_fills_its_day_on_the_next_update` | rescan only after the last day; table name without the row count |
| 6 | Sealing | `sealing.py`, `seals.py`, `wiring.py` `deep_enough` | `test_sealing_and_scores.py` (at the deadline sealed, one second later late; no evidence late), `test_review_fixes.py` (stored once and never asked again; unknown waits 7 days then stored late; last 8 days covered) | log reach ×100 |
| 7 | Scores | `scores.py` | `test_sealing_and_scores.py` (hand QS/coverage/Brier, equal close not up, point mass n/a, G4 bootstrap with its own seed, never pooled, per-row scores), `test_review_fixes.py` (methods apart, late counts ok rows only) | late counting every row |
| 8 | Back-fill | `backfill.py`, `bhavcopy_chains.py`, `chains.py` | `test_backfill_and_reader.py` (written once, labelled, rerun no-op, stops before live, failing day skipped), `test_bhavcopy_chains.py` (UDiFF and old format give the same chain; settlement as the future), `test_review_fixes.py` (special session skipped) | special sessions back-filled; future from the last trade |
| 9 | Reader port | `reader.py` | `test_backfill_and_reader.py::test_the_reader_gives_fl1_...`, `test_review_fixes.py::test_overlapping_backfills_count_once_...` | dedupe key → every record |
| 10 | Step and failures | `issuer.py`, `fno/daily/wiring.py`, `constants_operations.py`, `config.yaml` | `test_issuer.py` (6), `test_daily_step.py`, `test_review_fixes.py` (table failure never costs NIFTY; closes failure that underlying only; special session not issued); O1's lists extended, nothing loosened | regular-session check off |
| 14 | No frozen/G7/G13 change | G13b imports G7's `Ewma`/series and G13's code, edits neither | full suite (freeze tests pass) | n/a |
| 15 | Real output | below | dry run and back-fill scripts in the session scratchpad | n/a |

Mutations were planted by a scratch script (`scratchpad/mutate.py`, not committed); each made `tests/price_ranges`
fail and the file was restored.

## Self-review findings and what changed

A review agent read the whole branch before this file. Accepted, with tests:
1. **Blocking: a seal could expire.** GitHub's activity log covers one week; a record scored later would read "no
   evidence" and turn late. Now each seal is read while the log has it and stored write-once in Drive (`seals.py`);
   in a shallow clone the last 10 days of `main` are fetched first (git's first commit adding a receipt is otherwise
   the boundary commit).
2. A close-table or seal failure stopped NIFTY's issue: now contained, a problem line, the other index still issued.
3. A late-archived index-close file left a hole in BANKNIFTY's table: each update rescans every missing session; the
   table file is named by last day and row count so the newest always sorts last (the first fix tied on the name, a
   test caught it).
4. Overlapping back-fills counted a day twice and two methods could be pooled: deduped per (label, method,
   underlying, day, issue), method SHA in every group key.
5. The text said `k/n` for `implied`'s share; the code uses `(k + 0.049)/(n + 0.049)` live and `k/n` at end of day.
   Text updated (rev 4); reasoning: the live distribution must cover the rest of `d`'s session too.
6-11. Regular sessions only (issue and back-fill); bhavcopy three nearest expiries and settlement (text); the 2% line
   in log terms; late counts ok rows only; scores file named by its making time; a calendar gap is a reason, not a
   crash.

## A bug G13's end-to-end run found (fixed here, commit cf858864)

After G13's merge, its own commands ran from a fresh clone of `main` with the Drive settings: `pricedist backfill
--source eod` wrote 1,926 NIFTY days to Drive and `--source 3pm` the 1-20 Oct chains of four indices (receipts on
`main` at 2526b83b). `pricedist score` then stopped: "not a valid archive path: 'data/price_distribution/v1/'". Both
CLIs passed the Drive cache a folder with a trailing "/", which `path_parts` refuses (rightly: an empty part).
G13b's `pricerange score` had the same constant.
- **Root cause in the tests:** G13's scorer test copied files into the cache folder by hand, so `sync` was never run
  with the command's own prefix.
- **Fix:** both prefixes are built from each story's `folders.py` (`DATA_AREA/ROOT`, `drive(ROOT)`); G13's test now
  syncs through the real `DriveCache`, and G13b has the same test. Both fail with the old constant (checked).
- **Real check after the fix** (no file written): the sync verified all 5 Drive files and the scores match response
  262 (implied lowest QS at h1, h5, e1, e2; against rv20: p 0.023 h1, 0.009 h5, 0.053 e1, 0.687 e2).
- This commit touches G13's `fno/price_distribution/cli.py` and its test: it reaches `main` with G13b's merge.

## What the data says (exploratory, not live evidence)

**NIFTY, end of day, 1,918 sessions (Jan 2019 to 15 Oct 2026), CLOSE basis** (QS in log units, lower is better):

| Horizon | Forecaster | n | QS | 50% band | 90% band | Brier P(up) |
|---|---|---|---|---|---|---|
| N1 | implied | 1,908 | 0.00456 | 0.513 | 0.910 | 0.2499 |
| N1 | rv20 | 1,918 | 0.00471 | 0.508 | 0.884 | 0.25 |
| N1 | ewma_t4 | 1,918 | 0.00471 | 0.425 | 0.871 | 0.25 |
| N1 | hist750 | 1,910 | 0.00487 | 0.494 | 0.887 | 0.2487 |
| N1 | no_change | 1,918 | 0.00727 | n/a | n/a | 0.25 |
| N3 | implied | 1,906 | 0.00805 | 0.477 | 0.900 | 0.2483 |
| N3 | rv20 | 1,917 | 0.00841 | 0.473 | 0.868 | 0.25 |
| N3 | ewma_t4 | 1,917 | 0.00843 | 0.385 | 0.852 | 0.25 |
| N3 | hist750 | 1,907 | 0.00857 | 0.491 | 0.899 | 0.2487 |
| N3 | no_change | 1,917 | 0.01311 | n/a | n/a | 0.25 |

`implied` beats every baseline (bootstrap p 0.037-0.044 at N1, ≤0.012 at N3). Implied N1 `P(|r| ≥ 2%)` averages
5.85%, against about 4.1% of days realised: the option-implied tails are too fat by about 40% (the variance risk
premium, reasoning only).

**BANKNIFTY, end of day:** 686 sessions (2 Jan 2024 to 15 Oct 2026; closes from
1,427 archived index-close files 2021-2026, no gap), CLOSE basis. A sample, not the full back-fill (that is the
rule-8 run after the merge, from BANKNIFTY's first archived day):

| Horizon | Forecaster | n | QS | 50% band | 90% band | Brier P(up) |
|---|---|---|---|---|---|---|
| N1 | implied | 682 | 0.00458 | 0.570 | 0.919 | 0.2499 |
| N1 | ewma_t4 | 686 | 0.00470 | 0.459 | 0.864 | 0.25 |
| N1 | rv20 | 686 | 0.00473 | 0.523 | 0.880 | 0.25 |
| N1 | hist750 | 686 | 0.00475 | 0.517 | 0.913 | 0.25 |
| N1 | no_change | 686 | 0.00713 | n/a | n/a | 0.25 |
| N3 | implied | 677 | 0.00784 | 0.532 | 0.905 | 0.2488 |
| N3 | ewma_t4 | 685 | 0.00811 | 0.436 | 0.866 | 0.25 |
| N3 | hist750 | 685 | 0.00816 | 0.533 | 0.917 | 0.2508 |
| N3 | rv20 | 685 | 0.00819 | 0.509 | 0.864 | 0.25 |
| N3 | no_change | 685 | 0.01251 | n/a | n/a | 0.25 |

Same order as NIFTY: `implied` lowest QS at both horizons, but at N1 the gap to the rules is not significant on 682
days (bootstrap p 0.054 against rv20, 0.079 hist750, 0.090 ewma_t4); at N3 it is (p 0.004-0.033). Its 50% band holds
57% at N1 (too wide: the implied range overstates typical moves). Implied N1 `P(|r| >= 2%)` averages 6.2% against
5.5% of days realised. G7's consistency line is NIFTY-only (V6a forecasts NIFTY), so it is empty for BANKNIFTY.

**Today's 1545 records (21 Oct 2026, dry run, real canonical chains, nothing written):** `S_ref` is the 3 pm chain's spot, closes
through 19 Oct (20 Oct was not a session), τ = 1.049 and 3.049. Quantiles in index points:

| Index | Forecaster | Horizon | 5% | 25% | 50% | 75% | 95% | P(up) |
|---|---|---|---|---|---|---|---|---|
| NIFTY (S_ref 22,675.15 at 14:57:49) | implied | N1 (22 Oct) | 22,324 | 22,553 | 22,680 | 22,810 | 23,032 | 0.511 |
| | rv20 | N1 | 22,290 | 22,517 | 22,675 | 22,835 | 23,067 | 0.5 |
| | implied | N3 (26 Oct) | 22,085 | 22,472 | 22,689 | 22,911 | 23,292 | 0.519 |
| BANKNIFTY (S_ref 54,775.40 at 15:02:50) | implied | N1 (22 Oct) | 53,850 | 54,455 | 54,826 | 55,151 | 55,700 | 0.547 |
| | rv20 | N1 | 53,964 | 54,441 | 54,775 | 55,112 | 55,599 | 0.5 |
| | implied | N3 (26 Oct) | 53,266 | 54,290 | 54,921 | 55,478 | 56,423 | 0.566 |

Every row of both records is `ok` (all ten per index in the scratch output `scratchpad/dry1545.txt`); implied N1
`P(|r| >= 2%)` is 5.0% for NIFTY, 6.0% for BANKNIFTY. Not sealed, not scored: a dry run.

## Honest headline (owner's notes, in every report)

- **Strong evidence (1,900 NIFTY days; the same order on 686 BANKNIFTY days, significant at N3 only):** the option-implied range is the best of the five at both horizons and its
  90% band holds 90-91%. The edge over a 20-day volatility rule is small (QS 0.00456 against 0.00471, 3%).
- **No direction skill:** `implied`'s and `hist750`'s `P(up)` Brier is 0.248-0.250, the same as a coin. Only these two
  take a view on direction; `rv20`, `ewma_t4` and `no_change` say 0.5 by construction.
- **`ewma_t4` is too narrow:** its 50% band holds 38-43%, not 50%.
- **Not modelled in v1:** no US-close adjustment (the 15:45 range ignores the night's US session); BANKNIFTY uses
  NIFTY's 0.393 overnight share (reasoning only); the rest of `d`'s session (0.049) is a measured average, not today's.
- **Back-fill is not live evidence:** live scores start when the owner sets `live_from`; 60 sealed live days are the
  owner's calibration mark.

## Before live (owner's step)

1. Build BANKNIFTY's close table in Drive by hand: `python -m fno pricerange closes` (about 2,400 archive files, about
   1.4 s each; the daily step then adds one row a day).
2. Check A4c's BANKNIFTY chains are canonical on the chosen first day (both were today).
3. Set `daily.live_from.price_ranges` in `config.yaml`.

## Not built (scope freeze)

Part B (every contract valued at end of day), part C (the 09:15 issue, after A22), the 09:30 issue, the AI slots'
rows. Questions 1-3 of the story stay open for the owner.
