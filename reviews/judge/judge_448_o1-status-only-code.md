# Judge 448: O1-status-only code (story/o1-status-only at 6e5f4330)

**Verdict: PASS. Lane 1. The builder may merge after the full gates pass on the exact pushed tree.** The text is judge
443 (addenda 2-3).

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Default-deny every leaf by type, whatever its key | MET | `PublicResult.public`: bool and None kept; int only under `COUNT_KEYS`; str only in `WORDS` or `VOCABULARY`, otherwise a template code, `raised:<Type>` or `unlisted`; anything else (floats) becomes None; `lines` and `stderr` dropped |
| 2 | Identifier rule (judge 443 add. 3) | MET | `(?!.*\d{3})[A-Za-z][A-Za-z0-9_:-]*`. I ran it: `NIFTY26OCT25000CE`, `Rs12345` and `22811` become `unlisted`; `t1` and `shadow:b0-monthly-sc-v1` pass |
| 3 | Whole-skeleton matching; a template with no literal is refused | MET | `ReasonRegistry._compiled`: anchored `fullmatch`, placeholders as `.*?`, `TemplateRefused`; the codes import the producers' constants, never retyped (`reason_codes.py`) |
| 4 | One boundary, always present | MET | E3's `StepRecorder` port with the `AsGiven` default; O1's `PublicRecorder` is wired in `fno/daily/wiring.py`; the e2e normal day asserts the built run carries the policy |
| 5 | Child stderr kept apart | MET | `processes.py`: `Process.errors()`; never in the public log; the unsent line is relayed once (real-child test) |
| 6 | The private full log | MET | `journal/runs/.full/` is git-ignored (I checked `git check-ignore`); one Drive copy per run attempt with its receipt; a data-area outage gives one alert and still ends "day done" |
| 7 | Scope inside the owners section | MET | O1's files; E3's `daily_run.py`, `daily_wiring.py` and the new `step_recorder.py` (the agreed `build_daily_run` parameter); O8, T1 and S2 untouched (they already read with `.get`) |
| 8 | Gates on a trial merge with main | MET | 9261 passed, 16 xfailed, 0 failed; ruff and check_imports clean |

## The builder's deviations ("As built")
1. **The identifier rule:** yes. This is judge 443 addendum 3.
2. **Codes as `<area>:<NAME>`:** accepted. They pass the identifier rule, and a rerun re-records them unchanged
   (tested).
3. **Drive copy only on a run that did not stop:** accepted. The recovering rerun copies the whole local log, and a
   stopped run's receipt commit would only fail again.
4. **Receipt in the run's own `<root>/receipts/`:** accepted, and better. The default `receipt_folder()` points at the
   real repository, so the e2e checkout would have written into it.
5. **`not filled` in the word list:** accepted (it is pinned by `test_never_starts`).

## Planted mutations
| Mutation | Result |
|---|---|
| Integers kept under any key | caught (1 failed) |
| A loose identifier (dots allowed, digit runs allowed) | caught (1 failed) |
| Floats kept | caught (1 failed) |
| `lines` and `stderr` kept | caught (4 failed) |
| `fullmatch` replaced by `match` (start-anchored only) | **survived** |

The survivor costs no privacy: a code never carries a value. It means a text that starts with a template's skeleton
and continues gets that template's code. A registry test with a template ending in a literal (filled, plus a suffix,
expecting no match) would pin the end-anchoring.

## Notes (not should-fix: no producer writes these into the log today)
1. **Dict keys are not filtered.** `PublicResult.public` filters values only. I ran it:
   `{"NIFTY26OCT25000CE": True}` passes through whole. Today every keyed result uses book, account or trade-id keys,
   which pass the vocabulary anyway. Apply the same vocabulary to keys (an unlisted key becomes `unlisted:<n>`) so
   the boundary does not depend on producers.
2. **A string of 7 or more decimal digits passes as a hex hash** (`"1234567"` stays), because `[0-9a-f]{7,40}`
   accepts digits only. No producer writes a bare digit string. Requiring at least one `a-f` letter would refuse a real
   short hash about 4% of the time, so leave it and note it.
3. The known limit stays: two-digit tokens beside letters (`VIX15`) pass.
