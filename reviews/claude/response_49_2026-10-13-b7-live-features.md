# Response 49: story B7 (live 3 pm feature versions and their validation), builder's claims

Builder session for story B7 (GitHub issue #36). Code commit `c68163a` (merged into `main` as `2c5fdcf`). Same session,
before it: judge-28 minors of B3 in `efd480f` (a continuous-P&L C1 golden case that pins index 9,499, and a test that a
total exactly at its threshold fails) and the protocol-conventions proposal `response_48_2026-10-13-protocol-conventions.md`.
Checks on the merged head: `python -m pytest -q` 873 passed; `ruff check fno tests tools` clean; `ruff format` applied;
`python tools/check_imports.py` clean (186 files).

## Read first: two inputs the story assumes do not exist yet

1. **A4 records no India VIX and no futures quote at 15:00** (`fno/quotes/recorder.py`: option quotes and spot only;
   no provider in `fno/providers/` offers an index or VIX quote). So:
   - **Live F2 is always `None` today.** The feature is built and tested with a VIX input; the snapshot reader leaves it
     `None` until the recorder stores VIX. Under the use rule it can never be validated, so no strategy can use it live.
     Fix (outside B7): extend A4 to record India VIX (and the near-month future) at capture. Strong evidence (code read).
   - **Live F1 takes its forward from put-call parity** at the ATM strike, F = K + e^(rT) (C - P) from the call and put
     mids, because there is no 15:00 future. The research F1 uses the future's close (B1). The validation measures the
     difference; if A4 later records the future, live F1 can switch to it (one new class behind `ImpliedVolModel`-style
     input, one line in the composition root). Reasoning only for parity vs future at 15:00; to be measured.
2. **No A4 day is committed yet** (`research/data/quotes/` does not exist in the repository) and the panel ends on
   12 Oct 2026, so the validation command reports 0 days on real data today. The code is proved on fixtures; the real
   report needs 20+ recorded days with a rebuilt panel.

## What was built

| File | What |
|---|---|
| `fno/research_data/quote_snapshots.py` | A4's canonical snapshot read back: capture finish time (IST), spot, VIX (None from A4), each contract's bid, ask, validity; `mid` only for a valid two-sided, uncrossed quote, never the last price |
| `fno/research_engine/features.py` | `ResearchData` gains `snapshots` (empty by default), so the harness changes them too |
| `fno/research_engine/live_features.py` | `LiveFeature` (known at the desk's decision time, 15:00 from `DESK_DECISION_TIME` in the composition root; uses a snapshot only if its capture finished by then); live F1, live F2, live F3 |
| `fno/research_engine/live_validation.py` | `validate` and `ValidationReport`: per recorded day live vs close; mean and largest absolute difference; condition agreement; live availability; `LiveUseRule` (20 days, 90%, 90%) |
| `fno/research_engine/live_gate.py` | `require_validated(strategy, live_features, validated)` raises if any live feature lacks a passing report; `validated_from_reports(folder)` reads the committed reports |
| `fno/research_engine/research_cli.py` | `python -m fno research validate-live <feature>` writes `research/live_validation/<feature>.json` |
| `fno/composition.py` | `build_live_features`, `validation_context`, `run_live_validation` |
| `tests/research_engine/lookahead_harness.py` | `perturb_snapshots` and `LIVE_PERTURBERS` (snapshots finished after the cutoff are changed) |

## Criteria

| # | Criterion | Evidence | Status |
|---|---|---|---|
| 1 | The B1 harness passes for every live feature with the 15:00 cutoff | `test_live_lookahead.py::test_every_live_feature_is_unchanged_by_data_after_15_00`: live F1, F2 (with a VIX in the fixture) and F3 on 4 decision days, each a real value; the harness changes the decision day's own 15:30 closes, every later session, events not yet announced and every snapshot finished after 15:00. `test_a_late_same_day_snapshot_is_changed_and_ignored` (a 15:05 capture is changed and live F1 gives None); `test_the_harness_catches_live_leaks` (a feature using a 15:05 capture and one using today's close both fail) | met |
| 2 | 20 fixture days with known close and live values: report numbers match a hand computation | `test_live_validation.py::test_the_report_equals_the_hand_computation`: 20 recorded days (plus one unrecorded and one the panel lacks, both left out); agreement 17/20 = 0.85; numeric differences 8 x 0.5 + 2.5 + 9 x 0.25 + 1.5 = 10.25 over 19 days (mean 0.5395, largest 2.5); availability 19/20; disagreement days listed; not validated (0.85 < 0.90). `test_the_use_rule_passes_at_twenty_days_and_ninety_percent` (0.95 passes; 19 days fail; a stricter owner rule fails) | met |
| 3 | A strategy whose live features are not validated cannot reach status `paper` (D1 loader check) | `test_an_unvalidated_live_feature_keeps_a_strategy_from_paper`: reports read from a folder, `require_validated` refuses a strategy with an unvalidated or missing live feature and allows a fully validated one. **Partly:** story D1 (the playbook loader) does not exist yet; the check is built and tested, D1 must call it when it loads a strategy with status `paper` | partly met (gate built; D1 wires it) |
| 4 | Invalid or missing quotes give `None`, never a fallback to last price | `test_live_features.py`: invalid quotes, a missing ATM leg, a one-sided book (bid 0), a crossed book (reader test), a missing or late snapshot all give None; `LiveQuote.mid` never reads `last` | met |

Hand value for the judge's recomputation (`test_live_f1_equals_the_hand_calculation`, `tests/research_engine/live_fixtures.py`):
spot 20,000, ATM 20,000, expiry 41 days away (T = 41/365), rate 0.065; call and put mids are Black-76 prices at
forward 20,100 and 17%. Parity: F = 20,000 + e^(0.065 x 41/365) x (C - P) = 20,100.00; both IVs 17.00; realised from
20 returns of +-1% = 0.01 x sqrt(252) x 100 = 15.87; live F1 = 1.13.

## Design choices (decisions, stated)

1. **A capture that finished after 15:00 is not used** (A4's window runs to 15:10): with a 15:00 cutoff, a 15:05
   capture is data after the cutoff. If the desk's decision time moves (story E3 freezes it), `DESK_DECISION_TIME`
   changes in one place.
2. **Live realised volatility** uses the previous 20 sessions' closes followed by the 15:00 spot (the research F1 uses
   21 closes ending with today's close). That tracks the research version best without reading today's close.
3. **The validation context**: the day's farther recorded monthly expiry (A4 records the two nearest monthlies; the
   farther one is the next monthly, 28-62 days out), entry the next trading day, exit the last trading day with 21+
   days to expiry. Days without a snapshot, without panel data, or without a context are left out and not counted.
4. **Availability added to the use rule.** Without it, a live feature that is never computed (live F2 today) would
   "agree" 100% with a close condition that happens to be false on every day. My addition (reasoning only); the owner
   can drop or change it with the other two thresholds, which stay as proposed (20 days, 90%).
5. **Condition used for agreement**: a number counts as "above zero" (F1 > 0, as every policy uses it), a flag as
   itself, `None` as not met.
6. **Live F3 = F3 at the cutoff.** Events are dated by announcement day (story A6), so nothing intraday differs; the
   harness counts an announcement from the start of its day. If an announcement could come after 15:00 on the decision
   day, A6 would need times.

## Not met, limits, asks

- Criterion 3 depends on D1 calling `require_validated`; until D1 exists nothing loads a playbook.
- Live F2 cannot be validated until A4 records India VIX; live F1's forward is parity-based until A4 records the future.
  Ask (orchestrator / owner): extend A4 to record India VIX and the near-month NIFTY future at capture.
- No real validation report yet (no committed A4 days; the panel ends 12 Oct 2026). Once 20+ days exist and the panel
  is rebuilt past them, `python -m fno research validate-live <feature>` writes the first real reports.
- Judge-28's second minor (look-back from index-close files only) waits for story A10; not done here.

## Addendum: judge 44 (FAIL, 2 should-fix, 3 minor) and the items routed to B7's builder

Commit `9f39718` (merged `0364b22`). Full suite 1,128 passed; `ruff check` clean; `check_imports` clean; discovery
results unchanged (SHA-256 `814a79a5...`). Each finding: accepted, with the fix and its proof.

| # | Judge's finding | Accepted? | Fix | Proof |
|---|---|---|---|---|
| 1 (should fix) | Agreement maps live None to "condition false"; policies have three states | **Accepted.** `policies.py` has `Positive`, `NotPositive` and `IsFalse`, so a live None against a close <= 0 is "no trade" against "butterfly" in P5 | `live_validation.decision_state`: above zero / at most zero / unknown for numbers, true / false / unknown for flags; agreement compares states | `test_agreement_compares_the_policys_three_decision_states`: the judge's case (close -1 on 20 days; live None 2, +0.5 2, -1 16) now gives agreement 0.80, availability 0.90, not validated (was 0.90, validated). A never-computed feature now scores agreement 0.0 |
| 2 (should fix) | The gate cannot apply a strategy's frozen rule and trusts a flag | **Accepted** | `require_validated(strategy, features, reports, rule)` recomputes days, state agreement and availability from each report's per-day (live, close) values and checks them against the strategy's `LiveUseRule`; the `validated` flag and summary numbers are never read | `test_the_gate_rechecks_every_report_under_the_strategys_frozen_rule` (a 0.90 report passes the default rule and is refused under a 95% rule; a missing report is refused); `test_a_forged_flag_or_summary_does_not_pass_the_gate` (flag true, agreement 1.0, days 99 in the summary: refused, per-day values give 0.85) |
| minor 1 | Live F2's history including today's close passes all tests | **Accepted** (the code was right; the test was missing) | New test | `test_live_f2_history_ends_at_the_previous_session`: 125 x 10 and 125 x 20 before today, today's close 100, 3 pm VIX 17. Correct: True (median 15). With the judge's break B4 applied I ran it: it fails (median 20), then restored the code |
| minor 2 | Live F1 depends on the concrete `Black76` | **Accepted** | `LiveAtmIvMinusRealised(cutoff, rate, model: ImpliedVolModel)`, no default; the composition root passes `Black76()`. With the recorded future (below), live F1 now uses `model.underlying(spot, future)` exactly as research F1: the parity forward is gone, so nothing in the class is Black-76-specific | `test_live_f1_equals_the_hand_calculation` (17% from the recorded 20,100 future; live F1 1.13); `test_live_f1_needs_the_recorded_same_expiry_future_and_that_it_traded` |
| minor 3 | Late captures give None; report capture time per day | **Accepted** (measurement needs real days) | Each compared day carries `captured_at` (the capture's finish time) in the report | `test_each_compared_day_carries_its_capture_time`. Capture duration cannot be measured until A4 has real days; A4's levels add two NSE requests to each attempt |

### Routed: A4 records India VIX and the NIFTY futures at capture

- `fno/quotes/market_levels.py`: `LevelSource` interface and `NseLevelSource` (NSE's public `/api/allIndices` for
  India VIX with NSE's own timestamp, `/api/liveEquity-derivatives?index=nse50_fut` for every listed NIFTY future:
  last price and volume; no bid or ask exists there). Wired in `build_quote_recorder`. Research data only, read-only.
- The recorder reads the levels inside each attempt (before `finished_at`) and writes `india_vix`, `india_vix_time`,
  `futures`, `levels_failures` and `levels_source` into the meta. A failing endpoint is recorded and never blocks the
  option capture or changes "complete". Built without a level source (A4's golden tests), the bytes are unchanged.
- Checked live from this container on 13 Oct 2026 (after the close): India VIX 14.04 (stamp 15:30), futures 27 Oct
  22,860 (volume 3,932,695), 23 Nov 22,965, 29 Dec 23,109. Whether NSE answers from the routine's network at 15:00
  is not yet proven; a refusal shows in `levels_failures`.
- The snapshot reader passes VIX to live F2 and the futures to live F1 (as `FutureQuote`, last price as close, no
  settlement or open interest at 3 pm).
- Tests: `tests/quotes/test_market_levels.py` (payload parsing, a failing endpoint recorded, the recorder writes the
  levels and the reader returns them, the app wires NSE).
- **Real validation still needs 20 or more committed A4 days with levels** (the first is the next 3 pm run) and a
  panel rebuilt past them. Until then live F1 and F2 cannot be validated and no strategy using them can reach paper.

### Routed: the panel's 30 Mar 2021 gap

- The panel reader now gives a session the panel left out the closes of the index-close file (NSE's
  `ind_close_all_30032021.csv`: NIFTY 50 14,845.10, India VIX 20.65) and still no option or future rows. So F1's
  21-close window and F2's history run through that day instead of breaking for 21 sessions.
- B2's simulator keeps such an entry day unfillable (no entry-day option rows), never a strike condition:
  `test_an_entry_day_with_index_closes_but_no_option_rows_is_unfillable`.
- Tests: `test_a_left_out_session_takes_its_closes_from_the_index_close_file`; the panel README says so.
- I did not rebuild the panel itself: the gap is filled at reading time from the committed index-close file, the one
  source of index closes. If the desk prefers the closes inside the panel's manifest, that is an A3 build change.
