# Judge 224: dashboard contract 2.9.0 (story/fno-contract-2-9 at be3629c)

**Verdict: PASS on the content, merge after one step.** be3629c does **not** contain main 1972241
(`git merge-base --is-ancestor` fails). The screens lead must merge main in first. The merged head needs
`check_contract` and `check_fno_screens` again, plus a look at the `examples` file, the one big file both sides
touch. On be3629c itself, `check_contract` and `check_fno_screens` exit 0 ("10 pages, 32 Mock examples").

## Against the owner's decision (trading `docs/DESK_DECISIONS.md`, 16 Oct, ad562ca1)

- **"Weather levels stay public":** `weather_history` gets `p_big_1d`, `p_big_5d`, `base_rate_1d` and
  `base_rate_5d` back, required. The 2.8.0 strict-form `x-never-sent` line is removed, and the input values and
  `reaches` stay never sent. This matches the decision exactly ("Screens still never send the levels themselves, but
  `weather_history` may carry each session's chances beside its colour in contract 2.9"). Judge 217 should-fix 1 was
  a rule pending the owner, and the owner has now answered it.
- **"Field A only":** `FnoForecastHistory` carries each forecaster's running `mean_loss` and `n` per G4 report. Its
  `x-never-sent` keeps "single forecasts and their outcomes (field B)" out, as the owner decided.

## `forecast_history` against G4's real reports (my read of `research/forecasts/scores/2026-10-16.json`)

- **The modes:** the report holds `close_proxy` (2024-01-01 to 2026-10-12, the back-fill) and `live_1500_proxy`
  (2026-10-15), each with 20 forecaster-and-question summaries. The contract's `label` maps `live_1500_proxy` to
  live and `close_proxy` to `backfill_exploratory`, and the series are "never joined". That is right.
- **The fields:** each summary has `counts.resolved` (671 for baseline A's back-fill) and `primary.mean_brier`
  (0.2476) with `primary.scored` (671). These are the contract's `n` (x-record `score_summary:scored`) and
  `mean_loss`. They exist under those names.
- **One point per report (`as_of`), not per session:** right, since G4 writes one report per day (13, 15 and 16 Oct
  exist; 14 Oct has none, so it has no point).
- **`primary_baseline` dropped,** with the yardstick taken from the Forecast lab page: one copy, which is right.
- **The text says that `n` counts answers as they resolve** (up to the horizon), so a period average is over answers
  that came in during it, mostly forecasts made earlier. That is honest.

## `MOCKUPS_ALSO`

The check now also compares a mockup's `data.json` `also` block with the catalog's examples for each listed
operation. **I planted a mismatch myself** (emptied one `getFnoForecastHistory` state in 37's `also`):
`check_fno_screens` reported "37-forecasts/data.json: its data differs from the catalog's getFnoForecastHistory
examples" and exited 1. The rule works. The orchestrator described a committed planted "also" break, but I found none
in the checks (only my manual plant). Add it to the planted-breaks list so it stays caught.

## Notes (not should-fix)

- **The period-average formula** `(n2·m2 − n1·m1)/(n2 − n1)` holds only if a later report's scored set contains the
  earlier one unchanged. That is G4's design (resolved answers are never re-scored). If the back-fill is ever rebuilt
  (a new `backfill_commit`), the two reports straddle different data. The screen should not difference across a
  change of `inputs.backfill_sha256`. The contract could carry a per-point input hash, or say so.
- **`mean_loss` for v4 (QLIKE):** "G8 adds it; the record named holds only Brier today". It is honest that the v4
  series will be empty until G8 publishes it.

## Addendum 1: head 709cb8c (main 1972241 merged in)

**PASS.**

- 709cb8c contains 1972241 (`--is-ancestor` passes). `api/` and `tools/` are unchanged from be3629c, so the content
  judged above stands.
- **Gates:**
  - `check_contract` and `check_fno_screens` exit 0;
  - re-running `sync-design` leaves the tree clean, so the fixture is exact;
  - `npm test` gives 499 passed, 0 failed, 0 skipped. W3a part 2 still passes on the 2.9 fixture: it reads only the
    2.8 fields.
- **Still a note, not a block:** the planted "also" mismatch is a manual check (yours and mine), not a committed
  planted break. Add it to the checks' planted list when next touching `check_fno_screens.py`.

## Addendum 2: head cf9692e (judge 224's points done)

**PASS.**

- **The planted "also" break is committed.** `planted_also` copies each `MOCKUPS_ALSO` mockup's data into a scratch
  folder, empties one example of each further operation, runs `check_mockups` and requires the mismatch to be
  reported. `check_fno_screens` exits 0 with it in place.
- **Back-fill rebuilds are handled.** Each series requires `backfill_sha256`, enforced by `if`/`then`/`else` on its
  label: a string for `backfill_exploratory` (G4's `inputs.backfill_sha256`, which exists in the real report), null for
  live. The text says a rebuilt back-fill starts a new series and the period difference is taken only within one. Two
  new probes (a rebuilt series without the hash, a live one with it) are refused.
- **The check change is accepted.** The closed-object rule now also skips `/then` and `/else`, as it already skipped
  `/if`. Those nodes only add conditions to their parent object, which is still checked closed (opening the series
  item is still reported, as the lead showed).
- **Gates:** `check_contract` ("every planted break caught") and `check_fno_screens` exit 0 on cf9692e.

## Addendum 3: head 07c8683 (`accounts[].open_risk_cap` added)

**PASS.**

- **The new field:** `FnoPaperTrades.accounts[].open_risk_cap` is a required INR (Paper) field, from C5's
  `risk.profiles.books.open_risk_cap_rs`. Trading's `config.yaml:55` reads `open_risk_cap_rs: 150000`.
  `open_max_loss`'s description now says "against open_risk_cap" instead of naming Rs 1.5 lakh in the text.
- **Not a strategy rule:** it is a book limit, like `brake.pause_at`, which judge 217 accepted. It reveals no
  strategy's rules.
- **It removes a copied owner number:** mockup 41's `2-books.js` drew `cap = 150000` hard-coded and now reads
  `a.open_risk_cap`. It also unblocks W3c's cap bar (judge 225's accepted deviation): the screen can now draw it from
  the payload.
- **Gates:** `check_contract` and `check_fno_screens` exit 0 on 07c8683. The examples, catalog and fixture all carry
  the field.
- **Note:** P2c must fill this field from config through the existing risk settings reader, not a typed 150000, when
  it builds the `paper_trades` page.
