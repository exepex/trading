# Judge 127: G7 phase 1 story text (v4 baselines and rule forecasters), rule 1

**Verdict on 992440fc45045706a4fb729e6917201a6dd52773 (`story/g7-baselines`, from main 16ed8e0): PASS.** No blocking
or should-fix findings and one minor. The earlier SHAs eb89d0a, ee1da6b and 6189889 were superseded before I ruled.

Applied: `docs/JUDGE.md` rule 1 (story text before code); the owner's 15 Oct rule (real cases only); the orchestrator's
working rule ("would this change a buy/sell signal, a trade or a stop decision?").

## Checked against protocol v4 (as merged at 597487f) and the committed data

| Point | Result | Evidence |
|---|---|---|
| Point in time, the d-1 reading of 3.1 | Correct | 3.1's header admits only inputs first seen before `d`'s 15:00 cutoff. `d`'s own close and its intraday `RV_s` (15:30 mark) do not exist at 15:00, so "RV ending at `d`" and EWMA's "`h x s2_d`" can only mean the last session first seen before the cutoff, `d-1`. Any other reading would put a post-cutoff value into a forecast. The protocol text could say this itself at the freeze (note, not a finding). |
| V6 outcomes and the disclosed counts | Reproduced | From `warmup_closes.csv` (`session == regular`, to 14 Oct 2026) I get 2,410 sessions, 2,409 returns, 100 with abs >= 2% and 331 of 2,405 five-return windows, the same as protocol 8 and criterion 1. The file has 2024-01-20 as `special` and 2024-11-01 as `muhurat`, so the skip cases are real rows. |
| Base rate, EWMA and HAR rules | Match 3.1 | 750 most recent resolved non-void outcomes, at least 500 (criterion 3). EWMA lambda 0.94, seeded from the mean of the first 250 sessions, eligible after 250 (criterion 4). HAR on the last 750 rows resolved before a monthly refit, minimum 500, forecast `h x prediction`, non-positive missing (criterion 5). V6a resolves at `t+1`'s close and V6b at `t+5`'s, counting only if resolved before the cutoff (criterion 2). |
| V1 start and switch | Match 1.3 and 3.2 | 20 non-void live sessions to start; intraday HAR from 250 live sessions, then primary for good via `eligibility.primary_baseline`. |
| A16b rows never live (decision 56) | Holds on the real paths | `series.py` reads A16's live `research/data/intraday/rv/` rows. A16b writes `rv-candle/`, a different folder, so a reader of `rv/` cannot see them. Criterion 6 also refuses provenance `backfilled` for the 20 and 250 counts and any live input. A16's `rv/` rows carry status `ok`/`void` (`fno/intraday/session_rv.py`); "a void session is never a value" maps to that. |
| File names fixed for the freeze | Yes | Package `fno/forecast_v4_rules/` (series, baselines, rules, records, capture, backfill); wiring in `fno/forecast/baseline_wiring.py` (outside G1's pinned `wiring.py`); records `research/forecasts/v4/<forecaster>/<question>.csv`. Folder ids are `fno/constants.py`'s values (`base_rate`, `trailing`, `ewma_094`, `har_daily`, `har_intraday`), plus two new constants for the rule forecasters. G8's text reads the same layout and ids, so the naming item between the builders is settled. |
| The rule forecasters | Sound, zero fitted parameters | `v6_ewma_t4`: `X = s T / sqrt(2)` with `T` ~ t(4) has variance `s^2`, and `p1 = P(abs(X) >= 0.02)`. Lambda and df are fixed, not tuned on spent data. Decision 70 makes it reported only, since V6's `rules` slot is M1's. `v1_close_blend` takes V1's slot. Neither re-implements `forecast_v4`. |
| Phase 2 deferrals | Consistent | Implied baselines are V2 and V3's primaries and only "also reported" for V1, so phase 1 leaves no V1/V6 primary undefined. |

My own hand values from the committed closes, for checking the code later: EWMA `s2` through 14 Oct 2026 = 7.7224e-05
(s = 0.8788%); `v6_ewma_t4` for 15 Oct: V6a 0.0323, V6b 0.1515; the V6a base rate over the last 750 resolved returns:
0.0267 (20 of 750).

## Minor (one line to fix in the text or the code; does not change a signal, trade or stop)

V1's trailing baseline is written as "the last live non-void intraday `RV_s` before the cutoff". When `d-1` is void,
that takes an older session in its place. Protocol 3.1 says trailing is the RV of the last `h` scored sessions, and that
a value that cannot be computed is "missing that day, never floored or replaced". A16 expects void sessions (its 5%
rule), so this case is real. The fix: trailing for V1 is `d-1`'s `RV_s`, missing when `d-1` is void. Trailing is only
"also reported" for V1, so no decision depends on it.

## Not checked here

The code (it comes as G7's own lane-1 check). The protocol itself (judge 98).
