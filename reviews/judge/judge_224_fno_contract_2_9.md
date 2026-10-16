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
