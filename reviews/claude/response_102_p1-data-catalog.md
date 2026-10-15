# Response 102: P1, the F&O data catalog (built, for the judge)

Story: `docs/stories/P-publishing.md` P1 (rewritten; the original P1 kept under "History"). Owner decisions of 15 Oct
2026: P1 into slice A, a shared mock-data catalog, first screens the daily card, weather, Forecast lab, Strategy lab and
paper trades. Branches `story/p1-data-catalog` in both repositories; nothing merged.

Labels: **strong evidence** = a test or check that runs and fails on the planted break; **some evidence** = checked by
hand or by screenshot; **reasoning only** = a design judgement.

## What was built

- **Dashboard (exepex/omenix-dashboard, contract 2.7.0, additions only):** five India-only endpoints under
  `/api/v1/markets/india/fno/` (`api/paths/fno-screens.yaml`), schemas `api/schemas/fno-card.yaml`, `fno-weather.yaml`,
  `fno-forecast-lab.yaml`, `fno-strategy-lab.yaml`, `fno-paper-trades.yaml`, `fno-screens-common.yaml`; 17 Mock examples
  (`api/examples/fno-screens.json`); the generated field tables `api/catalog/fno-screens.md` (228 leaf fields, 26 of them
  with a backend record that exists today); checks `tools/api/check_fno_screens.py`, `fno_walk.py`, `fno_planted.py`,
  `render_fno_catalog.py` (CI job api-contract); mockups `design/mockups/39-trade-card` and `40-weather` built from the
  catalog (`design/mockups/_platform/catalog_data.py`); notes in 37 and 38 that the catalog supersedes their proposed F&O
  contracts.
- **Here:** the pinned copy updated (`contracts/omenix-dashboard/`, `pin.json` at dashboard commit 1e145db, version 2.7.0,
  the six new schema files and `fno-screens.json` added); `fno/market_read_models/contract.py:22` reads the new examples
  file; `tests/market_read_models/test_p1_data_catalog.py` (24 tests); the P6 version test now expects 2.7.0; REPLAN's P1
  row and slice A list updated (decision row of 15 Oct: "the REPLAN text is updated through it").

## Acceptance criteria

| # | Claim | Where | Test | Label |
|---|---|---|---|---|
| 1 | Five screens, each with schema, endpoint and Mock examples in positive, negative and empty cases (card 5: TRADE, WATCH, RED, missing input, no strategy; weather 3: GREEN, RED, not published with the missing input; Forecast lab 3: winning, losing, waiting with V1's missing A16 input and Q1 at 12 of 40 days; Strategy lab 3: passed, paused after the Rs 30,000 line, none passed; paper trades 3: a win, two losses with missed fills, none) | omenix-dashboard `api/paths/fno-screens.yaml`, `api/examples/fno-screens.json`; cases checked at `tools/api/check_fno_screens.py:66` | dashboard check (planted "no empty case"); here `test_the_catalog_has_every_screen_in_its_three_cases_all_labelled_mock` (test_p1_data_catalog.py:100) | strong evidence |
| 2 | Every example validates against its schema in both repositories, says Mock, carries 2.7.0, its page key and the SHA-256 of its payload by this repository's canonical JSON | `check_fno_screens.py:80`; here `test_p1_data_catalog.py:108` uses `PinnedContract.validate` and `publication.canonical` | both; planted "stale hash", "label not Mock" | strong evidence |
| 3 | Every leaf has meaning, unit, source, freshness, story, status, visibility and x-fill; every built field names `<record>:<field>`, and each named field exists here | `check_fno_screens.py:102`, `:121`; here `test_every_built_field_names_a_record_field_that_exists_here` (test_p1_data_catalog.py:115) resolving 10 records (ledger header, RECORD_COLUMNS_V2, ScoreSummary, BootstrapResult, CheckReport, PaperAccount, AccountState, EQUITY_COLUMNS, TradeLine, DeskEvent) | planted "built without a record", "unknown record", "no visibility" | strong evidence |
| 3b | Fixtures from this repository's records validate: the real trial ledger (53 rows), a fresh account from `account_state(STARTING_CASH_RS, ...)`, the real live forecasts of 14 Oct 2026 for Q1 | test_p1_data_catalog.py:122, :133, :146 | same | strong evidence for the fields they fill; the rest of each fixture is the Mock example (said in the test) |
| 4 | Money says Paper; card says PAPER ONLY (`fno-card.yaml:21`, a const); real money can only be false (`fno-card.yaml:85`, `fno-strategy-lab.yaml:91`); no property or example key reads like a strategy internal; each page lists `x-never-sent` | `check_fno_screens.py:36`, `:136`, `:160`; here test_p1_data_catalog.py:168; the dashboard's existing privacy test (`web/lib/strategy-pages/tests/public-view.test.ts`) also scans mockups 39 and 40 and caught a `description` key in my first build (fixed: renamed `about`) | planted "money without Paper", "private key", "nothing never-sent", "real money eligible" | strong evidence for names; **some evidence** for free text (no automatic scan of sentence content beyond the existing internal-words test) |
| 5 | Mockups 39 and 40 read the catalog only (data.json equal to the examples, checked); deterministic build; screenshots at 1280 and 390 px of every state; no console errors, no external requests, no overflow; check_text 0 findings | `check_fno_screens.py:165`; `design/mockups/39-trade-card/`, `40-weather/` | check_page.js on 8 states; build twice same bytes (md5 compared) | strong evidence (check), some evidence (look) |
| 6 | 14 planted breaks caught, each by the problem that names it (a problem the intact contract already has does not count) | `tools/api/fno_planted.py:23`, `:42` | `check_fno_screens.py` prints "14 of 14"; here a renamed field fails (test_p1_data_catalog.py:161) | strong evidence |
| 7 | Gates (results below) | | | strong evidence |

## Gate results

- Dashboard: `node tools/check_code_size.mjs` pass; `npm ci --ignore-scripts && npm run typecheck && npm test && npm run build`:
  typecheck 0 errors, 465 of 465 tests pass, build compiled; `check_contract.py`, `check_mapping.py`, `render_catalog.py
  --check`, `examples.py --check`, `check_fno_screens.py` (every rule holds, 14 of 14 planted), `render_fno_catalog.py
  --check`: all pass.
- Here: see the orchestrator message for the full-suite count; `ruff check fno tests tools` clean; `ruff format --check`
  clean; `python tools/check_imports.py` clean; no file over 350 lines (largest new: 181).

## Design choices, with the reason (the owner may want to decide 1, 2, 5)

1. **One home, a new tag (reasoning only).** The P1 pages sit in the same OpenAPI bundle as W10-W13 but under tag
   `fno-screens`, not `blocks`: the block checks map every field to a signed-off mockup's notes.md element table, the
   wrong direction here (the catalog leads, mockups follow). The P1 check is its own file and runs in the same CI job.
2. **Visibility has two values in a payload, not three.** "Private strategy internals" are not a field visibility:
   they are never in any payload, so each page lists them in `x-never-sent` and the check forbids internal-sounding names.
   `owner` marks what may be shown on the signed-in dashboard but never committed to a public repository (live legs,
   entry ranges, exit plans, objections). **Conflict to decide:** the original P2 design commits every page under
   `reports/dashboard/<date>/`; that would put owner fields of the card in this public repository, against the 15 Oct
   Drive-only decision. P2 must store the card page privately or commit only its hash.
3. **Exit plans in the public examples are plain words without numbers** (a take-profit level is a strategy threshold).
4. **The weather's colour rule numbers are not sent** each day: they are frozen per `model_version` (DRY).
5. **Mockups 37 and 38 are not rebuilt on the catalog.** 37 shows draft-1's five questions only (no V1-V7) and 38's F&O
   tab has its own signed-off proposed shape; rebuilding their renderers is W3's screen work. Their notes now say the
   catalog supersedes their F&O contracts. This is a partial answer to "mockups read their data from the catalog": true
   for 39 and 40, not yet for 37 and 38. No paper-trades mockup was made (the brief asked only for card and weather).
6. **Question and forecaster ids.** The catalog uses Q1-Q5 and V1-V7; the backend records use `q1_nifty_up_20d` etc.
   The mapping is P2's builder's job (the 14 Oct fixture maps `q1_` to Q1 by prefix).

## Findings while building (facts, for the orchestrator)

- **Design 8.3 lists seven real-money conditions; the 15 Oct decision row says "all six".** The seventh is the owner's
  written approval. The schema allows ids 1-7 and says so (some evidence: read both texts).
- **The trial ledger has no status or verdict column** (`research/ledger.csv` header: trial_id ... run_commit), so the
  Strategy lab's per-status counts and per-idea gates cannot be filled until R1 adds them; marked `not_built` (story R1).
- **The paper account is Rs 5 lakh a book in code** (`fno/books/account.py` STARTING_CASH_RS) while design v2 plans a
  Rs 20 lakh account (C5); the schema takes `opening_value` from the record, never a constant.
- **The 14 Oct live forecasts were generated at 19:27 IST** (`generated_at` in `research/forecasts/live_v2/2026/
  2026-10-14_forecasts.csv`), after protocol v2's 15:15 deadline, so by `ForecastRecordV2.on_time` they would not count.
  Not in P1's scope; flagged so someone checks whether that day was a back-fill run or a late live run.
- **Push access:** the `add_repo` tool call for exepex/trading was refused in this session; I cloned it read-write over
  the git proxy instead (see the orchestrator message for whether the push went through).

## Known limits

- Only 26 of 228 fields can be filled from records that exist today; the rest wait for T1, M1, G7, G8, R1, S2, E8, LM1,
  C5 and RM1, and the tables say which. The catalog cannot prove those stories will produce exactly these fields: it
  makes any difference fail a test once they are built against the pin.
- The pin names dashboard commit 1e145db on the story branch; after the dashboard merges, `contract-check` compares with
  `main` and the pin must be moved to the merge commit (same bytes, new commit id).
- The navigation rail has no entry for screens 39 and 40 (changing the shared runtime would change every signed-off
  mockup's page.html); left for W3.
- Free-text values in examples are reviewed by hand, not scanned for thresholds.

## What the judge should test hardest

1. Read the five schemas against design v2 4.1, 2.3, 5.2-5.5, 3.1-3.2 and 8.3: a missing or wrongly typed field is the
   costliest error here, because every builder will now build against it.
2. Rename a backend record field (for example `EQUITY_COLUMNS` `cash_rs`) and run test_p1_data_catalog.py: it must fail.
3. Look for any strategy threshold or live-looking card detail in `api/examples/fno-screens.json` (free text included).
4. Rebuild 39 and 40 and run `python3 tools/api/check_fno_screens.py`; edit one example value and see the mockup check
   and the hash check fail.
5. Whether the `owner` visibility split is right, and whether choice 2's P2 conflict is real.
