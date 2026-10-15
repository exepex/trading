# Judge 128: G8 story text (protocol v4 scoring, comparisons and the two looks), rule 1

**Verdict on b987988dcff0415cfb6316487f9ec43c8a8641a6 (`story/g8-scoring`, response 126): PASS.** No findings.

Applied: `docs/JUDGE.md` rule 1; the owner's 15 Oct rule (real cases only); the "signal, trade or stop?" rule. G8's look
feeds Test A, a stop decision, so I checked every rule it names against protocol v4 sections 4-6 and the calibration
file.

| Point | Result | Evidence |
|---|---|---|
| Calls `fno/forecast_v4` and never re-implements it | Yes | Every rule is named as a call: pairs, loss, `calibrated_p`, `futility_p`, `judgeable`, the bootstraps, `judge_family`, `window_regime`, `forecasting_test`, `power_report`, `terms`. |
| Threshold tools and their arguments | Correct | `tools/v4_claim_thresholds.claim_threshold(question, n, rate, ...)` takes the look's rate and divides by 15 itself (its docstring says "rate / 15"), so passing the look rate is right. `tools/v4_futility_study.futility_threshold(question, n)` and `tools/v4_brier_bands.operative_thresholds(question, n, band)` exist with those signatures. |
| Claim on the scored set, futility on the gate set | Matches the protocol | Section 5.3 sets claims on the scored set; `PROTOCOL_v4_calibration.md` section 2 defines F+D "on the gate set". Each threshold is called at its own set's n. For Brier questions the two sets are the same. |
| Both gates at every look; the crash cut (decision 69) | Correct, boundaries right | The owner's item E row (`DESK_DECISIONS.md`, 15 Oct: option 2, more than 10% 2% days gives no verdict) is real. `big_days / n > 0.10` is strict: at n = 125, 12 days (9.6%) are judged and 13 (10.4%) are not; at n = 250, 25 (exactly 10%) are judged and 26 are not. Criterion 4 tests all of these and the 4/5-day gate. A not-judged member gets p = 1 and stays open, never "no", as 5.7 says. Putting `crash_dominated` beside `judgeable` in `confirmatory.py` freezes it with the protocol. The section 11 E line is correctly named as a dependency of the G6 freeze commit. |
| The family, V7, Test A | Match 5.6-5.8 and 6 | 15 members from `terms.FAMILY`, all printed with look, rate and timestamp. V7 is fixed at p = 1. A member closed at look 1 is not judged at look 2. With no registered slot, Test A is "undecided", never "no". Seeds: k is the member's 1-based place; reported comparisons are numbered after 15, as 5.2 says. |
| Outcomes from G7's `series.py` | Consistent with G7 at 992440f | One place per rule. V1 reads A16's `rv/` rows, where status `ok` is an outcome and `void` is void (A16 writes exactly `ok`/`void`). A16b's `rv-candle/` is never read. V7 reads `vix_closes()`, which G7 now provides. |
| The naming item | Settled | G8 looks forecasters up by `fno/constants.py` ids. G7's revision uses the same ids (`ewma_094`). No primary baseline uses EWMA. |
| Before the freeze | Safe | Every output is EXPLORATORY and `look` writes no record. After the freeze, a record is written once and never overwritten (criterion 8). V4, V5 and Test B are out of scope with reasons. |
| Real fixtures | Yes | The 2024 skip cases (20 Jan special, 1 Nov muhurat) are real rows of `warmup_closes.csv`, as I checked for judge 127. |

Not checked here: the code (G8's own lane-1 check). For the freeze, the G7 and G8 file hashes go into the record only
after both codes pass.
