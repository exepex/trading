# Handover: A20 and A22 builder (session_013u1Ac2N9eRQ8XCYPjwpaat), 21 Oct 2026, about 20:30 IST

## (a) Identity
- Role: builder of story A20 (point-in-time rules and dates) and A22 (pre-open data). Orchestrator
  session_01VG1RqxLFUVdvvPuMRYZtDH; judge: Judge F session_01QLDqmpqUA7gAi7vcijnj5Y.
- Branches (all pushed): `story/a20-rules-and-dates` (text) 9ed3c071; `story/a20a-fo-masters` merged;
  `story/a20b-circulars` a84b3ef2; `story/a20c-macro-calendar` 829d025e; `story/a22-preopen` (this file).

## (b) Done and merged to main
- A20 text: judge 353 FAIL → addendum 1 PASS (at 5a51abe9; later text edits for A20c are on 9ed3c071 and not yet
  judged as text, they ride with A20c's code judging).
- A20a `fo-masters` (ban list under its trade date, lot sizes daily): judge 358 PASS; merged 967eb7fd; claims
  `response_283`; on O10's capture-watch. First live run (manual dispatch) 39615323749: took 22 Oct's list and lots,
  correctly failed "no ban list for today's session 21 Oct" (job was not live that morning), one alert.
- Register rows on main: A20 (06a0855e), A22 (ecd418f1). Conversation log 16 Oct (14f5d282).

## (c) Done, not merged
- A20b `circulars` a84b3ef2 (claims `response_284`): judge 359 FAIL (SF1: fallback step) → fixed, waiting re-judge.
- A20c `macro-calendar` 829d025e (claims `response_285`): MOSPI ARC + Fed FOMC + FRED (US CPI 10, payrolls 50);
  waiting first judging. Needs the GitHub secret `FNO_FRED_API_KEY` (owner adding); without it "not configured" daily.
- When merging b and c: merge main first; keep both sides of CLAUDE.md, README, register; add `circulars` to
  `.github/workflows/capture-watch.yml` (c already adds `macro-calendar`); full gates on the merged tree;
  `tools/check_numbers.py` clean.

## (d) In progress
- A22 story text `docs/stories/A22-preopen-data.md` (5fbc44c9) with Judge F. Code not started (quality rule 1).
- Step 0b needed on a trading morning 09:08-09:15 IST: do `market-data-pre-open?key=NIFTY|BANKNIFTY` answer, and does
  Groww give BANKNIFTY's pre-open 1-minute candle (reuse `fno/intraday/candle_source.py` GrowwCandleSource)?
- Nothing uncommitted.

## (e) Reviews
- Self-review agents (quality rule 3) ran on a, b and c; every finding fixed or answered in the claims files.

## (f) Open questions and agreements
- A19 (session_01Qj3wtYynDoNxVxFcqvZD9b): A19 keeps SEBI RSS minus `/legal/circulars/`; A20b owns NSE and SEBI circulars.
- O10 (session_013YJ5gjXdxtFu6mwXP6v48N): whoever merges second adds the A20 workflows to capture-watch; row per
  failed run is fine; alert steps must start "Alert" and run on `failure()`.
- Owner: FRED secret; NSE terms page unreadable by script (personal-research rule applied); delete branch
  `probe/a20c-bls` (proxy refuses deletes).

## (g) Risks
- Two pre-existing failures on main (not A20's): `tests/forecast_scoring_v4/test_g7_series.py::test_v1_reads_only_the_a16_rows_it_is_given`,
  `tests/market_read_models/test_forecast_history_page.py::test_every_point_is_the_reports_own_scored_count_and_mean_brier`.
- fo-masters cosmetic follow-up (lane 1): its failure line hides that tomorrow's list was taken; its YAML step names are
  cut at `#` (fixed in b and c, not yet in a on main).
- MOSPI holidays are not rolled (weekends are); FRED fixture is documented format, not a live read.

## (h) First three actions for a successor
1. Read Judge F's verdicts on A22 text, A20b (re-judge) and A20c; fix any findings on those branches.
2. On the first trading morning after the A22 text PASS, do step 0b at 09:08-09:15 IST, then build `fno/preopen/`.
3. Check fo-masters' scheduled 07:45 IST run log (should be clean) and cite it in `response_283`.
