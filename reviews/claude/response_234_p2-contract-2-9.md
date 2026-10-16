# Response 234: P2, contract 2.9, the weather history's chances and `forecast_history` (claims for judge D, lane 1)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ, branch `story/p2-contract-2-9` from main at e48abe72 (P2a parts 1 and 2
merged). Contract 2.9.0 is on omenix-dashboard main at e74c9395 (judge 224 addendum 1).

## What changed

1. **Re-pin to 2.9.0.**
   - All the dashboard's `api/` files are byte copies at e74c9395cf98d0698b9a5ba32796400e1d97428b.
   - One new schema file, `fno-forecast-history.yaml`; none removed.
   - `python -m fno market contract-check` compares the pin with the dashboard's main.
2. **`weather_history` gets each session's chances back** (owner, 16 Oct 2026, ad562ca1: the weather levels stay
   public).
   - New fields: `p_big_1d` and `p_big_5d` (the operative model's) and `base_rate_1d` and `base_rate_5d`, each read
     from the record, null when its status is not ok.
   - Still never sent: an input value, a `reaches` colour, a level, the US cue.
3. **New page `forecast_history`** (`forecast_history_block.py`, `forecast_history_inputs.py`):
   - **Source:** G4's committed reports `research/forecasts/scores/<day>.json` dated on or before the session, read
     only. Each point is `scores[].primary`: `scored` as n, `mean_brier` as mean_loss.
   - **Live and back-fill apart:** `live_1500_proxy` is labelled `live`, `close_proxy` `backfill_exploratory`. There is
     one series per forecaster and label, never joined.
   - **One point per report:** none for a day without a report, and none with n = 0.
   - **The back-fill-file rule:** a back-fill series uses only the reports whose `inputs.backfill_sha256` is the
     newest report's.
   - **The question texts** are one table, `forecast_questions.py` (Q1 is the Forecast lab example's own words). The
     Forecast lab page (P2b) will reuse it, so a question is never worded two ways.

## On real data (16 Oct 2026)

- Three G4 reports: 13, 15 and 16 Oct. There is none for 14 Oct, so that day has no point.
- All 15 series are back-fill, three forecasters per question: Q1 and Q2 have `baseline_a_risk_neutral`,
  `baseline_b_base_rate` and `book1_rules`; Q3, Q4 and Q5 have `baseline_b_base_rate`, `baseline_c_model` and
  `book1_rules`. G4 scores no answer for the others there.
- No live series: the live mode first appears on 16 Oct with 0 answers resolved.
- Example: Q1 `book1_rules` back-fill has n 669, 670 and 671, mean Brier 0.2441, 0.2443 and 0.2445. These are the
  report's own numbers.
- `weather_history` for 14 Oct: p_big_1d 0.02, base 0.0267; counts unchanged (2,409 back-fill).

## A deviation the judge should rule on

- **What the contract lacks:** the merged 2.9 has no `backfill_sha256` field on a series (the screens lead's later
  note proposed one; e74c939 does not carry it). It also allows one series per forecaster and label.
- **What I built instead:** when the back-fill file changes, the page keeps only the newest file's points. Two series
  under the same forecaster and label would be indistinguishable.
- **Why it matches the rule's intent:** the screen draws the newest series, and the series is never carried across
  two files.
- **Today it changes nothing:** all three reports share one hash, 5b9d4306…. The test plants a rebuilt report and
  checks that the older file's back-fill points drop while live points stay.

## Tests

| Claim | Test |
|---|---|
| Every point is the report's own `scored` and `mean_brier`, re-read from the files | `tests/market_read_models/test_forecast_history_page.py::test_every_point_is_the_reports_own_scored_count_and_mean_brier` |
| n >= 1 on every point; one series per question, forecaster and label | `test_a_report_with_no_scored_answer_gives_no_point_and_the_live_mode_stays_apart` |
| A rebuilt back-fill drops the older file's points | `test_a_rebuilt_back_fill_drops_the_older_files_points_but_keeps_live_ones` |
| The empty state | `test_no_report_gives_the_empty_page` |
| Weather history chances are the records' own (null when not ok); no input or `reaches` | `test_weather_history_page.py::test_a_row_carries_its_colour_label_and_the_records_own_chances_and_nothing_of_the_inputs` |
| Pin 2.9.0; page counts 1,272 pages, 21 blocks | `test_market_contract_and_run.py`, `test_market_publish_read_back.py` |

## Addendum 1: re-pinned to dashboard main ea75be3 (the orchestrator; 75133fc3 is withdrawn from the judge)

The dashboard's main moved after e74c939 to ea75be313b34c457f9d5e3f5835c4dff6a4e852f. It is still 2.9.0, with the same
files; five files changed. It adds the two fields the screens lead had proposed:

1. **`backfill_sha256` per forecast-history series** (required; a string for back-fill, null for live, through
   if/then/else). This replaces the deviation above.
   - Each back-fill series now names its file, G4's `inputs.backfill_sha256`.
   - A change of file starts a new series for the same forecaster, oldest file first, rather than dropping the older
     points. No series ever spans a rebuild.
   - The test now plants a rebuilt report: Q1 `book1_rules` back-fill becomes two series, the old file holding the
     three real reports' points and the new file holding 17 Oct only.
   - A real-data test checks that every back-fill series names the reports' own hash and every live one names none.
2. **`accounts[].open_risk_cap` on `FnoPaperTrades`.** No page of this branch builds `FnoPaperTrades`; that page is
   P2c. When I build it, the cap comes from the risk settings reader (`fno/risk/profile_settings.py`
   `open_risk_cap_rs`), never a typed number, and the same goes for `brake.pause_at` (judge 224 addendum 3's note).

## Addendum 2: pinned to 2.10.0 at dashboard 38dfee6 (the orchestrator; supersedes ea75be3)

- **Why:** the orchestrator merged the judged version bump, so the shape with `backfill_sha256` and `open_risk_cap` is
  now labelled 2.10.0 (dashboard 38dfee63b1418bce271026c5ad9509552dc40f29). That ends the "two shapes under one
  label" problem.
- **What changed:** the pinned `api/` bytes; `contract_version` 2.10.0; the version test. No file was added or
  removed, and the code is unchanged from addendum 1.
- **The dashboard's main is already at f4f7f40,** which changes only `web/`. `git diff 38dfee6 f4f7f40 -- api/` is
  empty, so `market contract-check` against main reports the pin as the same.
