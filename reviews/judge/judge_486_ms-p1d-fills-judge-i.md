# Judge 486: MS-P1d, safety laws, accounts and fills (second judge)

**Scope:** story/ms-p1-fills at 96704ef8 (builder session_014VUoPfMfRWNXyJSnXxB5NL), diff 32fdbdde..96704ef8. Judge I
(session_01MvZneCLZqBuiGyNxawdVee), the second judge under JUDGE.md "Two judges for money pieces". I did not read
Judge B's verdict. Lane 1. Round 1 of 2.

**Verdict: FAIL.** 2 should-fixes, 1 minor. It holds at 7064a030, which only merges a's final: no file under d's packages or tests changed, and both defects are unchanged there. Every criterion passes; both should-fixes are paths where a protection
can quietly stop working.

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Pass at the limit, refuse beyond; stop and brake at `>=` | MET | plants 1, 2, 5, 8 caught |
| 2 | No law changes a proposal | MET | holds by the frozen types, as the builder says |
| 3 | Daily stop: entries refused, exits never; closes need two-sided quotes | MET | plants 21, 22 caught; `exit` uses `closing_quotes`, all legs or none (plant 17) |
| 4 | Brake: pauses, holds, lifts only on a review row, exits go on | MET in code; see finding 1 | plants 3, 5, 6, 33, 34 caught |
| 5 | Quote gate: missing or one-sided quote, size, sell-back | MET | plants 16, 23, 27 caught |
| 6 | No valid seal, no fill; refused after 15:30 | MET | plants 15, 36 caught |
| 7 | Fills at the touch or not at all | MET | plants 16, 17 caught |
| 8 | An exit with a missing quote waits | MET | plant 17 caught |
| 9 | Settlement at intrinsic against `SttlmPric`; no file gives `settlement_needed` | MET; see finding 2 | plants 18, 19 caught. My real run on the archived 29 Sep 2026 file settles all 4 indices from Drive |
| 10 | NIFTY drift: unknown, never a number | MET | plant 20 caught |
| 11 | Conformance | MET | the suite passes; 392 school tests also pass on d merged with a's final 4451a75b |
| - | Gates | MET | full `pytest -n auto`: 10,519 passed, 16 xfailed, 0 failed (the builder's 4 failures do not reproduce); ruff check and format, check_imports and check_records clean; largest file 195 lines |

## The orchestrator's list (checked)
- **13 laws and their split: MET.** Built from the real `config.yaml`: 13 laws. Each refusal reason falls in exactly one of `ACCOUNT_LIMITS` (bucket, open risk, new risk, margin room), `DRIVER_STOPS` (stop, brake) or `TRADE_VALIDITY` (the other 7). `stale_seal` is the fill port's own. a's final adds only a `NoTradeReason`, so nothing here changes.
- **Law 2 takes the largest of three: MET.** Plant 7 (the touch figure dropped) caught. The touch figure scales by lots × lot size.
- **Law 3 fails closed: MET.** Plants 9, 10, 11 caught: NIFTY rows used for another index, held positions ignored, and a missing file passing.
- **BANKNIFTY+FINNIFTY bucket: MET** [some evidence: FINNIFTY's largest weights are banks]. Plants 12, 13 caught.
- **Record-scan privacy (00cc5786): MET.** A real-git commit test, and my plant (the pattern removed) failed 5 tests. The desk's two patterns are unchanged.
- **Accounts outside the desk's space: MET.** The files sit under `journal/school/journal/shadow/...`. The desk's `paper_accounts` lists only `journal/shadow/`, and the Drive names are the repository paths, so the two cannot collide.

## Findings
1. **Should-fix: any review row lifts the brake, even one dated the day after it engaged.**
   - The owner's rule is "Pause till monthly review", and section 6 item 5 says the lift row is written "on or after the first Saturday of the next month". `brake.py:37` accepts any row dated on or after the engagement.
   - My run: engaged 22 Oct, a row dated 23 Oct (or 22 Oct) lifts the brake and restarts the high at the 26 Oct equity.
   - One early or mistaken row turns the month's pause into a one-day pause.
   - Fix expected: a row dated before the first Saturday of the month after the engagement is an error (`ReviewFileError`), with tests for that day and the day before it. [reasoning only; the orchestrator may overrule this as item 11's choice]
2. **Should-fix: settlement with no Drive settings stays "not archived yet" forever, with no alert.**
   - `execution/wiring.py:17-18` passes `build_raw_stores()`, which is `[]` without the service-account settings. My run with them unset: every price is `SettlementUnavailable ... not archived yet`.
   - Expired positions then never settle. They have no mark in the next capture, so they count at minus their maximum loss (`valuation.py:29`), which feeds the daily stop and no alert says why.
   - Fix expected: no store raises, as b's `RawFilesNotConfigured` does, with a test.

**Minor:** `ledger_fills.py:46`, the check that the charges equal C1's, has no test that fails without it (my plant 28 survived).

## Plants
39 planted, 37 caught. Survivors: plant 28 (the minor above) and plant 4. Plant 4 changes the brake's lift window (`day < row.session` to `<=`); it changes nothing through the wiring, because `ReviewFile.lifts` already keeps only rows dated before the session. Neither is a defect on the wired path.

## Notes (no action required)
- [reasoning only] NIFTY-W positions use NIFTY's margin rows (the file has no expiry), and the margin uses `config.yaml`'s NIFTY lot (65), not the road-day's A20a lot. Both are right today; short options' margin on expiry day may be higher.
- The builder says it openly: until MS-P1m's margin rows land, law 3 refuses every BANKNIFTY, FINNIFTY and MIDCPNIFTY entry and most NIFTY structures. The pilot can trade almost nothing until then, so the first sessions will show mainly refusals.
- For j: settlement must run before the session's first `view`, or an expired position counts at its worst case and can trip the stop.
