# Response 102: P1, the F&O data catalog (built, for the judge)

Story: `docs/stories/P-publishing.md` P1. It is rewritten; the original P1 is kept under "History". The owner decided
on 15 Oct 2026: P1 moves into slice A, it is a shared mock-data catalog, and its first screens are the daily card,
weather, Forecast lab, Strategy lab and paper trades. The owner's answer on the source of truth was "contract A": the
dashboard's `api/` is the single master contract, and exepex/trading keeps the pinned copy and the drift check.

Branches are `story/p1-data-catalog` in both repositories; nothing is merged.
- **Dashboard head:** 3cf4baa (pushed).
- **Trading:** the head commit holds the pin at 3cf4baa. It is committed locally, but **the push was refused**: this
  session has no push access to exepex/trading. See the orchestrator message.

Evidence labels:
- **strong evidence:** a check or test that runs and fails on a planted break;
- **some evidence:** checked by hand or by screenshot;
- **reasoning only:** a design judgement.

## What I reused from the existing catalog and what I added (orchestrator, message 1)

| Reused as is | Added, and why |
|---|---|
| The bundle (`tools/api/bundle.py`): one OpenAPI document. The new files are `api/paths/fno-screens.yaml`, `api/schemas/fno-*.yaml` and `api/examples/fno-screens.json`. | The tag `fno-screens`, not `blocks`. The `blocks` checks map every field to an element of a signed-off mockup's notes.md. For new screens the catalog comes first and the mockups follow, so those checks point the wrong way here. The new checks run in the same CI job (api-contract). |
| `x-catalog` {publisher, source, freshness, story, status}, inherited the same way; `x-unit` on every leaf. | `x-visibility`: public or owner. Cards are kept in Drive only (owner, 15 Oct), so live card details may be shown on the dashboard but never committed to a repository. |
| The `FnoBlockMeta` envelope (`product`, `publication_id`, Paper). | `x-fill` (built or not_built) with `x-record` `<record>:<field>`: the owner's "what kind of data do we need", and "never faked". |
| `x-status: planned` and the 501 response. | `x-never-sent`: the strategy internals each page must never carry. |
| `check_contract.errors` (the same validator); `walk.resolve`. | `x-provisional`: v4 fields wait for G6 (finding 2). |
| The P6 pin and drift practice in exepex/trading. | Mock examples tagged `x-case` (positive, negative, empty), and generated field tables. |

**Direction of the single copy (finding 5): kept for the signed-off mockups, reversed for the new ones (reasoning only).**
- `examples.py --check` still keeps mockups 30-34 as the source of their examples.
- Mockups 39 and 40 are new, and the catalog is their source: `build.py` writes `data.json` from the examples, and the
  check fails if the two differ.
- Either way there is one copy. The original brief allowed both directions ("generated from or replaced by catalog
  examples").

## Gap list (orchestrator, message 3, item 1)

| Requirement | Where it comes from | Covered by |
|---|---|---|
| A schema per screen in the dashboard's contract | REPLAN P1 row; owner | criterion 1 |
| Mock examples in the positive, negative and empty cases (RED weather, a loss, "no strategy has passed", "not enough data yet" for V1, a missing input named) | brief | criterion 1 |
| A plain-words field table: field, meaning, unit, backend record, freshness, visibility | brief | criterion 3; `api/catalog/fno-screens.md` |
| Every mock labelled Mock; money Paper; PAPER ONLY on the card | brief | criteria 2 and 4 |
| Mockups read the catalog, never a second copy | brief | criterion 5 (39 and 40). **37 and 38 are out** (see below) |
| New mockups for card and weather, with data.json, template, deterministic build, notes, rationale, shots at 1280 and 390 | brief | criterion 5 |
| Drift fails a test on both sides; the pin updated | brief | criteria 2, 3 and 6 |
| Fields the backend cannot fill are documented, never faked | brief | criterion 3 (`x-fill`) |
| No strategy internals in public examples | brief | criterion 4 |
| How the UI consumes the mock data | owner's description | criterion 5: the mockups render every state |
| Forecast lab 37 and Strategy lab 38 brought into the contract | finding 1 | criterion 1 (FnoForecastLab, FnoStrategyLab) |
| G1 v3 apart from v4; v4 marked "planned, depends on G6" and not frozen | finding 2 | `protocols[]`; `x-provisional` on the v4-only fields |
| 38's F&O facts updated for design v2: Rs 20 lakh, books 2-3 after a pass, shadows, fills at 5/30/60, after tax beside the index fund and cash, stop rule | finding 3 | in the schema: opening_value from the record, `trading` and `why_not`, exploratory_shadow, `fills[3]`, `net_after_tax`, `vs_index_fund`, `vs_cash`, `real_money`. **38's mockup itself is out**: its changes.md says the catalog supersedes it, and the owner signs off again when W3 rebuilds it |
| No mockup existed for card or weather | finding 4 | 39 and 40 |
| Paper-trades screen | finding 4 | schema and examples only; **no mockup** (the brief asked for card and weather only) |
| Extend the existing catalog, not a parallel one | message 1 | the table above |
| Source of truth: one canonical copy, plus a pin and a drift check | messages 4 and 5 | story text and REPLAN row ("contract A"); field-table header |

## Acceptance criteria, each broken on purpose (orchestrator, message 3, item 3)

The dashboard planted breaks are in `tools/api/fno_planted.py`. A break counts only if it raises a new problem that
names it (`fno_planted.py:planted`). Result: 21 of 21 caught.

| # | Claim | Where | Broken on purpose, and the result | Label |
|---|---|---|---|---|
| 1 | Five screens, each with schema, endpoint and Mock examples in its three cases: card 5, weather 3, Forecast lab 3, Strategy lab 3, paper trades 3 | `api/paths/fno-screens.yaml`, `api/examples/fno-screens.json` | plant "no empty case": caught. Here: `test_the_catalog_has_every_screen_in_its_three_cases_all_labelled_mock` | strong evidence |
| 2 | Every example validates in both repositories, says Mock, has version 2.7.0, its page key, and the SHA-256 of its payload by exepex/trading's canonical JSON | `tools/api/check_fno_screens.py` `check_examples`; here `test_every_catalog_example_validates_here_and_carries_this_repositorys_hash` (page_key asserted) | plants "extra field", "missing field", "label not Mock", "stale hash": all caught | strong evidence |
| 3 | Every leaf has its meaning, unit, catalog entry, visibility and x-fill. Every built field names a record field that exists here, **with a matching type where the record is typed** | `check_leaves`, `check_record`; here `test_every_built_field_names_a_record_field_that_exists_here` and `test_every_built_field_has_the_type_of_its_typed_record_field` | plants "built without a record", "unknown record", "no visibility": caught. Renaming `EQUITY_COLUMNS` `cash_rs` failed the test (`['equity_history:cash_rs']`). Against the earlier pin, the type test failed on `trade_line:charges` (a dict) mapped to a number; that mapping is now removed | strong evidence |
| 3b | Fixtures built from real records validate: the ledger row count (53), a fresh account from `account_state(STARTING_CASH_RS, ...)`, and the 14 Oct live forecasts for Q1 | `test_p1_data_catalog.py` fixture tests | a renamed field fails (`test_a_renamed_field_fails_validation`, which matches the field's name) | strong evidence for the fields they fill. The rest of each fixture is the Mock example, and the test says so |
| 4 | Money says Paper; the card says PAPER ONLY; real money can only be false; no internal-sounding key in any schema or example; each page has `x-never-sent`; every object is closed | `check_leaves`, `check_privacy` (now on the contract it is given), `check_card` | plants "money without Paper", "card not PAPER ONLY", "real money eligible", "private key", "private property", "open object", "nothing never-sent": all caught | strong evidence for names. **Some evidence** for free text: two reviewers read it by hand |
| 4b | Design rules the schema enforces: a TRADE card is rung 3, never in RED, never on failed checks or a breach; NO TRADE has a reason; RED blocks; intraday upgrades only AMBER to RED; a missing weather blocks; under 60 outcomes there is no settle date; a paused version names its reason; net equals gross minus costs | `fno-card.yaml` allOf; `fno-weather.yaml`; `fno-forecast-lab.yaml`; `fno-strategy-lab.yaml`; `check_sums` | plants "TRADE at rung 0", "TRADE in RED", "RED without the block", "NO TRADE without a reason", "net not gross minus costs": all caught | strong evidence |
| 5 | Mockups 39 and 40 read the catalog only; build twice gives the same bytes; 8 states shot at 1280 and 390 px; no console errors, no external requests, no overflow; check_text finds 0 | `check_mockups`; `design/mockups/39-trade-card`, `40-weather` | plant "mockup drift": caught. The dashboard's existing privacy test (`web/lib/strategy-pages/tests/public-view.test.ts`) also caught a `description` key in my first build; it is now `about` | strong evidence (checks); some evidence (look) |
| 6 | Planted breaks | `fno_planted.py` | 21 of 21 | strong evidence |
| 7 | Gates | below | | strong evidence |

## Independent code review (orchestrator, message 3, item 2)

Two review agents ran, one per repository; neither edited files. Every finding with what I did about it:

**Dashboard (11 findings):**
1. The privacy and closed-object scan read files on disk, so no plant could reach it. **Fixed.** It now reads the
   contract it is given; two new plants prove it.
2. A `$ref` could downgrade visibility from owner to public. **Fixed.** owner is never downgraded (`fno_walk._context`).
3. The internal-word list was short. **Partly fixed.** Added trigger, lookback, signal, setting, condition. Not added:
   `cutoff`, because it is the envelope's and the card's real cut-off time. Free text is still not scanned (a limit).
4. An impossible TRADE card validated. **Fixed:** rung 3, GREEN or AMBER, checks passed, no breach; WATCH at most rung
   2; `weather_red` needs RED; `advocate_hard_rule` needs the breach.
5. Net per unit of risk and the fill error were missing. **Added** `net_per_risk` {value, lower_bound} and
   `fill_error_per_unit` (S2 and E8, not built).
6. Unenforced rules. **Fixed:** intraday AMBER to RED only; settle under 60; pause reason; sums. **Changed:** a missing
   weather now fails closed (blocks entries). `mean_loss` now says its record holds only Brier today.
7. Answer dates were off by one session, and the 8 Nov muhurat session was missing. **Fixed.** Fno examples are still
   outside `check_calendar` (a limit).
8. Contradictions between examples. **Fixed:** card and lab lower bound (+0.01, above zero); settle only from 60
   outcomes; the 0.026 skill now meets the minimum effect; failed, not retired; the `why_not` text; the 15:10 retry;
   max loss 3984 and 5296; breakeven at the top of the range, 61.3 and 81.5; Budget replaced by an RBI decision.
9. Free-text hints of exits and entry filters. **Fixed:** plainer exit plan and idea titles.
10. Mockup nits. **Fixed:** a zero shadow net; the limit taken from `max_share`; credit labels. **Not changed:** green
    Buy and red Sell legs. The design system uses those colours for Buy and Sell, and the word and glyph are always there.
11. No Paper label on each money figure. **Fixed:** a Paper tag on each money section.

**Trading (9 findings):**
1. The pin was one commit behind. **It was already fixed** in my next commit (the reviewer read an earlier working
   tree). It is now pinned at 3cf4baa, and all 33 files are byte-identical to the dashboard (checked file by file with
   sha256sum).
3. Record names were checked by name only. **Fixed:** a type check for typed records.
4. The fixtures used records only lightly. **Partly fixed:** the account fields now name `AccountState`, which the
   fixture uses. Still true: no fixture builds a closed `TradeLine`, `DeskEvent` or score report (a limit).
5. and 6. The test name overstated, and page_key was not asserted. **Fixed.**
8. The claims file gave no pytest count. **Fixed** below.
2, 7 and 9 were clean or nits.

## Sample output (orchestrator, message 3, item 4)

These lines come from `api/catalog/fno-screens.md` (generated). Columns: Field | Meaning | Unit | Source record |
Freshness | Visibility | Backend today.

Card (61 fields; 1 fillable today):
```
| `label` | Every card is for paper trading; no card ever tells the owner to place a real order | text | the day's card record (T1's CardBuilder ...) | once a session day at card_sent_at (target 15:08 IST) | public | no: T1 |
| `trade.legs[].strike` | The strike price | index points | the day's decision record (D3) and the risk manager's sizing (C2, A14) | ... | owner | no: T1 |
| `trade.max_loss` | Most it can lose, charges included, fixed at entry (at most Rs 10,000 a trade, owner 14 Oct 2026) | INR (Paper) | ... | owner | no: T1 |
| `data_checks.passed` | Every check passed (C3's CheckReport.ok) | yes/no | the session's data-check record (C3, C4) | ... | public | yes (`check_report:ok`) |
```
Forecast lab (43 fields; 10 fillable today):
```
| `questions[].waiting_for[].story` | The exepex/trading story that provides it (e.g. A16) | id | the forecast records (G3, G5; v4: G7) and the score reports (...) | after the close of each NSE session ... | public | no: G8 |
| `questions[].today.values[].probability` | The chance it said (probability questions; null for variance) | probability 0-1 | ... | public | yes (`forecast_record_v2:probability`) |
| `questions[].today.values[].variance` | The variance it said, annualised on 252 sessions | annualised variance (vol squared) | ... | public | no: G7; provisional: protocol v4 (G6) is not frozen or merged yet ... |
| `questions[].settle.status` | not_measured = under 60 scored outcomes; beyond_2_years = ... cannot be settled in useful time | enum | ... | public | no: G8; provisional: ... |
```

## Gate results

**Dashboard at 3cf4baa:**
- `node tools/check_code_size.mjs`: pass.
- typecheck: 0 errors.
- `npm test`: 465 of 465 pass.
- `npm run build`: compiles. It was run at 1643b71; the later commits change no TypeScript.
- `check_contract`, `check_mapping`, `render_catalog --check`, `examples --check`: all pass.
- `check_fno_screens`: every rule holds; 231 leaves, 25 built; 21 of 21 planted.
- `render_fno_catalog --check`: current.
- check_text: 0 findings on both pages.

**Trading:**
- Full suite: **3187 passed** (at the pin 01a6d57, 5 min 50 s). An earlier full run showed 17 failures, all in
  market_read_models. That run overlapped my re-pin of the contract files mid-run; the clean rerun passed.
- At the final pin 3cf4baa: `tests/market_read_models` 178 passed.
- `ruff check` clean; `ruff format --check` clean; `tools/check_imports.py` clean.
- No file over 350 lines (largest new file: `test_p1_data_catalog.py`, 239 lines).

## Design choices the owner may want to decide

1. **The P2 conflict.** The original P2 design commits every page under `reports/dashboard/<date>/`. That would put
   the card's owner-only fields in a public repository, against the Drive-only decision of 15 Oct. P2 must keep the
   card page private, or commit only its hash.
2. **Mockups 37 and 38 are not rebuilt on the catalog.** W3 rebuilds them, and the owner signs off 38 again.
3. **Visibility has two values.** Strategy internals are never in a payload: they are listed in `x-never-sent`, and
   internal-sounding names are refused.
4. **The weather colour rule's numbers are not sent each day.** They are frozen per `model_version`.
5. **A missing weather blocks new entries (fails closed).** This is now an owner decision (15 Oct 2026, "4 A";
   DESK_DECISIONS row "Missing weather blocks new trades").

## Findings while building (facts)

- **Real-money conditions:** design 8.3 lists seven; the 15 Oct decision row says "all six". The seventh is the
  owner's written approval.
- **Strategy lab statuses:** `research/ledger.csv` has no status or verdict column, so the per-status counts wait for
  R1.
- **Account size:** the paper account is Rs 5 lakh a book in code (STARTING_CASH_RS); design v2 plans Rs 20 lakh (C5).
- **Late forecasts:** the 14 Oct live forecasts were generated at 19:27 IST, after protocol v2's 15:15 deadline
  (`ForecastRecordV2.on_time` would not count them). This is not P1's scope.
- **Push access:** exepex/trading is not in this session's authorised repositories, so the push was refused (403 from
  the git proxy).

## Known limits

- Only 25 of 231 fields can be filled from records that exist today.
- The fno examples are not checked against NSE's calendar.
- Free text is not scanned automatically.
- The fixtures do not cover closed trades or score reports.
- The navigation rail has no entry for 39 and 40.
- After the dashboard merges, the pin must move to the merge commit.

## What the judge should test hardest

1. Read the schemas against design v2 4.1, 2.3, 5.2-5.5, 3.1-3.2 and 8.3. A wrong field here costs the most, because
   every builder now builds against it.
2. Rename a typed record field and retype one (for example, make `TradeLine.gross` a `str`): both must fail.
3. Look for any live-looking detail or strategy threshold in the example free text.
4. Edit one example value: the mockup check and the hash check must both fail.
5. Whether the owner and public split, and conflict 1 (P2), are right.
