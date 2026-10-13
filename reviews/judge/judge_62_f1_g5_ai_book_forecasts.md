# Judge 62: stories F1 (forecast part) and G5, Hybrid and AI team daily forecasts

Date: 13 Oct 2026 (UTC; 14 Oct early IST). Claims: `reviews/claude/response_67_f1-g5.md` (ad5de1a) and its
addendum 1; owner decision in `docs/DESK_DECISIONS.md` (14 Oct, `sealed_same_day` with three conditions).
No live run exists yet (the first is 14 Oct about 15:10 IST), so nothing live could be checked.

## Verdict: PASS for the sealed-answer mechanism as built; the owner's conditions 1 and 2 are NOT yet enforced or recorded anywhere; G5 criterion 3 NOT MET

## The owner's three conditions: enforced, audited, or only written?

| # | Condition (DESK_DECISIONS, 14 Oct) | What exists | Result |
|---|---|---|---|
| 1 | Every session transcript audited for the first 10 session days, then 2 random sessions a week; a breach makes that book's day unscored; two breaches in 20 days stop the book | **Nothing beyond the sentence.** No place records an audit (who, which session, result), no random selection, no `breach` status in the audit file, no code that unscores a breached day, no stop rule. The audit file holds the session link (`fire.session`) so an audit is possible, but none is defined. G4 does not read the AI records at all yet (judge 58), so "unscored" has no consumer | **NOT MET** (written, not enforced or audited) |
| 2 | Label "isolation: sealed same day (not full F1)" on every record and every report | Audit JSON carries `"isolation": "sealed_same_day"` (`fno/ai/record_writer.py`). The forecast CSV (frozen v2 schema) has no such field. G4's report has no isolation text. Not the agreed words either | **PARTLY** |
| 3 | Trading decisions (slice 4) still need full F1 | Written in F1's status line and in DESK_DECISIONS; no slice-4 code exists to enforce | MET (as a written rule; nothing to enforce yet) |

Why it matters (statistician, red team): condition 1 is the only control on the open gap (the routine has the public
repository and network: it can re-run the baselines, read old records, or look at the market after 15:00). Without
a recorded audit, the first 10 days pass unaudited by default and the scores later cannot show which days were
clean. It is cheap now: an audit record per session (for example a row in a file next to the audit JSON with the
auditor, the time and the result) and a G4 rule that skips breached days.

## F1 criteria (forecast part only)

| # | Criterion | My check | Result |
|---|---|---|---|
| 1 | Real isolated session: reads of other books' data fail | Not built: the routines have the repository and network. The owner accepted `sealed_same_day` instead for forecasts only | NOT MET, accepted by owner decision for forecasts (not for trading) |
| 2 | Export lists only allowed items; a planted file is refused | Tests in `tests/ai/test_inputs.py` (planted file, edited prompt refused) pass | MET |
| 3 | Output after the receipt deadline ignored | Receipt time is GitHub's push timestamp from the activity log, not the commit's own date (`fno/ai/receipts.py`); unknown receipt fails closed as late. Planted `elif False:` for the deadline: caught | MET |
| 4 | A served model different from the registered one gives unscored and pauses scoring | Audit status `model_mismatch` (plant caught). It relies on the model the session **reports about itself**, not the session record; and no scorer pauses (G4 does not read AI records) | PARTLY |
| 5 | Failed or limited session gives "AI unavailable" | `no_submission`, `not_fired`, `not_revealed` statuses, five "no forecast" rows, never imputed | MET |
| 6 | No secret in the session; export and prompt scanned (O5) | Pushes go through the O5 hook (`GitMainTransport`). The routine environment's setup (no variables, no connectors) is the owner's; I cannot see it | Not verified by me |
| 7 | Pack hashes match the committed pack | `brief` refuses a pointer whose hash differs; `collect` rebuilds the export and refuses a different `export_sha256` | MET |

**Seal mechanism, checked:** salt `secrets.token_hex(16)` (128 bits), commitment SHA-256 of salt and canonical
answer; a reveal must hash to it. A book whose commitment GitHub received after the other book's reveal is marked
`exposed`; my plant reversing that comparison was caught. All 31 `tests/ai` tests pass.

## G5 criteria

| # | Criterion | Result |
|---|---|---|
| 1 | Five probabilities per session day, or a recorded "no forecast" | MET by tests; no live file yet ("judge verifies: one week of files" impossible today) |
| 2 | Late forecasts ignored | MET (above) |
| 3 | G4's report shows each AI book's coverage | **NOT MET**: `fno/ai/coverage.py` computes it ("for G4's report") but G4's report does not include it |

## Claims vs reality, other

- Timing (reasoning only, from the response's own table): the pack exists at about 15:10-15:13 and the commitment is
  due by 15:15:00. Two to five minutes to start a cloud session, pull, read, reason and push is tight; expect `late`
  days. The builder says so. The first week will show it.
- Hybrid sees Book 1's number (Book 1 is the mean of the baselines it gets). Stated openly by the builder; true.

## Project rules

New package `fno/ai/` with two composition roots; frozen v2 code untouched (the freeze test passes in the suite);
no secret in files; prompts versioned by hash. Clean.
