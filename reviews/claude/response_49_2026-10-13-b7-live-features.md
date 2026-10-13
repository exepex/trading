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
