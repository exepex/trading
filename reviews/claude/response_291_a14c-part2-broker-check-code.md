# Response 291: A14c part 2, the daily Groww broker margin check, code (builder's claims for judge D)

Builder session 01Vm1WnH8i9waM8EJG8zwWqg, 21 Oct 2026. Branch `story/a14c-part2-broker-check`. Text and allow-list:
judge 291 addendum 2 and judge 356 addendum 1 PASS. Lane 1 (Groww, margins, O1's schedule step).

## What it does (strong evidence: the diff and the tests named)

`python -m fno margins stress-broker-check`, run only by O1's `margin_check` step (still behind its `LiveFrom` date
until the owner sets `daily.live_from.margin_check`).

| Rule (text) | Where | Tests |
|---|---|---|
| From 09:30 IST on a session day; otherwise "outside market hours", exit 0, nothing asked | `broker_check.py` `run` | `test_outside_market_hours_nothing_is_asked` [before 09:30, closed day] |
| No broker request starts at or after 14:50:00 IST, whatever the start; the rest are `error` "deadline", exit 1 | `_ask` (the check is before every request, the NIFTY quote included) | `test_no_request_starts_at_or_after_14_50_and_the_rest_are_errors` [14:49:59, 14:50:00, 14:50:01, 14:49:55] |
| One request every 2 s, the NIFTY quote first | `_ask`, `PACE_SECONDS` | `test_every_basket_ok_is_recorded_paced_with_the_index_first` |
| Every A14 row of the day; each basket rebuilt from the same archived SPAN file and proved to be that row (the `source` file and SHA-256, and all three figures to the paisa) | `broker_basket.py` `BasketBuilder` | `test_a_row_its_file_does_not_reproduce_or_a_missing_file_is_an_error_not_a_check`, `test_a_row_whose_source_names_another_file_or_sha256_has_no_basket` |
| SPAN: Groww's `span_required` vs `max(0, scan - NOV)`, within Rs 1 a lot | `broker_compare.py` | boundaries Rs 1.00 and 0.99 ok, 1.01 (both signs) mismatch; `test_groww_s_span_is_compared_with_the_row_s_span_after_its_net_option_value` |
| Exposure: Groww's `exposure_required` vs A14's `NseIndexOptionExposure` at this caller's own NIFTY `get_quote` level, within 0.1% (never implied from Groww's figure) | `compare` | 0.10% and 0.099% ok, 0.101% and a planted 0.2% mismatch; `test_exposure_is_recomputed_at_the_live_level_never_implied_from_groww` |
| Compared to the paisa, so float noise never decides a boundary case; a zero expected exposure (bought-only baskets) needs a zero answer | `_beyond` | the boundary cases above |
| Read-only by construction: `ReadOnlyGroww` with this caller's list `get_order_margin_details`, `get_quote`, `SEGMENT_FNO`, `SEGMENT_CASH`, `EXCHANGE_NSE` | `broker_port.py` | `test_this_caller_s_list_meets_the_positive_rule_and_lets_no_other_name_through`, `test_the_wiring_gives_the_check_only_this_caller_s_read_only_client` |
| Record: one write-once O9 file per run, `data/margins/broker_checks/<as_of>/<HHMMSS IST>.csv`, one row per basket; receipt under `receipts/` | `broker_record.py` | `test_the_record_is_written_once_with_its_receipt_and_read_back_as_done` |
| O1 commits this check's receipts only (`receipt_pathspecs()`), replacing `stress_broker_check.csv` | `fno/daily/wiring.py` | `tests/daily/test_steps.py` (the step's command and pathspec) |
| Idempotent: `ok` and `mismatch` are done; `error` is asked again only by a same-day rerun; a damaged earlier record refuses (exit 1) | `BrokerRecord.done` | `test_a_rerun_asks_only_what_is_not_done_and_a_done_day_asks_nothing`, `test_a_damaged_earlier_record_or_a_refused_write_is_a_record_problem` |
| Mismatch: a finding, exit 0, its own #fno-desk line "...differ beyond tolerance for <baskets>: review the stress factor"; the run log keeps the send result | `_finish` | tolerance tests; `test_a_mismatch_and_an_error_together_alert_the_finding_and_exit_1` |
| Failure: exit 1, the reason last, no own alert (O1 sends the step's line); only an exception's class name is kept | `_failed`, `_one` | `test_a_broker_failure_is_an_error_row_exit_1_and_no_own_alert` [basket, index] (a planted "secret" in the text never appears) |
| No A14 row for the day: "nothing written: ...", exit 0 (O1 records refused) | `run` | `test_no_a14_row_for_the_day_is_a_refusal_o1_records` |
| The Actions jobs' composition root builds no Groww client; no workflow runs the check | `broker_wiring.py` (new root, listed in CLAUDE.md) | `test_the_root_of_the_jobs_github_actions_runs_builds_no_broker_client` |

## Live rehearsal on real data (strong evidence; 21 Oct 2026, 20:13 IST, after the close)

A read-only script (not the command, which is market hours only) ran the same parts on today's real rows:

- 15 of 15 A14 rows of 21 Oct were rebuilt exactly from `nsccl.20261021.i1.zip` (Drive), figures to the paisa.
- NIFTY `get_quote` 22,811.35 against the file's close 22,888.95. Groww's exposure equalled A14's rule at the live
  level to the paisa (59,309.51 for every basket). At the file's close it would have been 0.34% off, beyond 0.1%:
  that is why the level is this caller's own quote.
- SPAN: all 15 within Rs 1 (largest gap Rs 0.50, SC 200: Groww 12,324.50 vs 12,324.00; Groww's figures move in
  steps of Rs 0.25). BF's SPAN after NOV is 0 at both.
- **Request count and time (judge F asked):** 16 requests in 44.7 s, against my estimate of about 35 s (15 x 2 s pacing
  plus about 1 s per answer). A full STR1 set of about 40 baskets would take about 2 minutes, still inside the window.
- **Account after the calls (judge F asked), read-only `get_order_list`, `get_positions_for_user`,
  `get_available_margin_details`:** 0 orders, 0 positions, `net_margin_used` 0.0, `span_margin_used` 0.0,
  `exposure_margin_used` 0.0, `collateral_used` 0.0. The check itself never holds these names. I repeat this after the
  first live day.

## Self-review round (21 Oct, before sending): one blocking and seven minor findings, each checked and fixed

| Finding | Check | Fix | Test |
|---|---|---|---|
| **Blocking:** the margin request had no timeout; the SDK's signature `get_order_margin_details(segment, orders, timeout=None)` waits forever, so a hang held O1's run up to its 10-minute limit and lost the run's answers | read the installed SDK | `timeout=10`, as the quote has | the adapter test asserts both timeouts (mutation caught) |
| A mismatch was not alerted when the record failed, and the line said "not checked" | reproduced | the line says "checked but not saved"; no finding is alerted for data that did not land (a same-day rerun asks again) | `test_a_record_that_cannot_be_written_or_read_exits_1` |
| Drive's and google-auth's exception text went into the line | read | class name only, except this repository's own refusals (`BasketProblem`, `RecordProblem`, `MarginOutsideModel`) | the same test ("503" never printed) |
| An index failure hid a basket's own reason | reproduced | a row whose basket failed keeps its own reason | `test_an_index_failure_keeps_each_basket_s_own_reason` |
| A malformed width or missing Drive settings gave a traceback, not a line | reproduced | keys parsed inside the guarded block; Drive (store, cache, SPAN file) built on first use | `test_a_malformed_row_is_a_failure_line_not_a_traceback`, `test_before_09_30_the_check_needs_no_drive_or_groww_settings` |
| On a mismatch, O1's journal reason was "alert sent" | read `steps.outcome` | the summary line, naming the mismatched baskets, is printed last | the tolerance tests |
| Stale O1 story line and config comment; duplicated "NIFTY" constant | read | updated; `NIFTY_SYMBOL` from `fno/constants.py` | - |

The reviewer also asked for one real Groww reading of a debit basket before going live. The rehearsal above already
answers it: Groww gave SPAN 0.00 for all five BF rows (scan below NOV), equal to the row's `max(0, scan - NOV)`.

## Mutations (strong evidence: 16 of 16 caught, plus 5 in the self-review round)

Stop at `>` instead of `>=` 14:50; start 09:00; pacing removed; mismatch alert removed; errors not failing; done set
ignored; tolerance `>=`; exposure tolerance 0.2%; exposure at the file's close instead of the live level; SPAN without
NOV (caught after adding the direct test); every leg SELL; figure proof removed; source/SHA proof removed (caught after
adding the direct test); `error` counted as done; damaged record accepted; a zero NIFTY level accepted.

## Choices to rule on

- "No request starts after 14:50" is built as: none at or after 14:50:00 (14:49:59 starts; 14:50:00 does not).
- If one basket errs and others mismatch, the mismatch alert is still sent and the run exits 1 with the error reason
  last (the finding is not hidden by the failure).
- A row whose basket the file does not reproduce is an `error` (a data fault to fix), not a `mismatch`.

## Gates

On the merged head 3dc0ab9b: ruff, format, imports and the number check clean; full suite 8209 passed, 18 xfailed,
0 failed.

## Limits (said plainly)

- The comparison's tolerances are some evidence: one basket on 16 Oct, and now 15 baskets on one evening.
- The live run in market hours has not happened yet; the first one is the owner's `live_from` date.
- Groww's symbol form `NIFTY<yy><MON><strike><CE|PE>` is proven for monthly expiries only, which is all A14 uses.

## Round 2 (25 Oct 2026, builder session 01JkD3wtEQbxiE7qLHzQS7jp; the first builder is out of reach)

The owner lifted every pause on 25 Oct, and the orchestrator gave this part to this session. Not judged before: the
code above at ebce3593.

**Merge of main (merge, not rebase; 4,110 commits of main since 21 Oct).** It had six conflicts, all resolved without
changing the check:
- `CLAUDE.md` and `config.yaml`: main's text. Main's composition-root rule is now generic, so the old list entry is
  gone. `daily.live_from.margin_check` stays `null`.
- `fno/daily/wiring.py`: main's steps, plus this check's receipt pathspecs and main's new `locks` argument to
  `CommandStep`, as every other step has. Main's `MARGIN_CHECKS = stress_broker_check.csv` is removed (nothing else
  reads it).
- `tests/daily/test_steps.py`: main's step order (`quotes`, `owner_timing_fills`, `margin_check`) and this branch's
  command and pathspec checks.
- `docs/WORK_REGISTER.md` and `reviews/claude/README.md`: main's rows plus this part's rows.

**One defect the merge exposed, and its root cause (strong evidence: the test failed on the merge, passes after the
fix).** Main's O9 change 494d97df3 (23 Oct) makes `DriveCache.sync` report a prefix with no receipts as a problem
("a wrong path must never read as all verified"). `BrokerRecord.done` synced the day's folder before anything was
written, so **every day's first run would have stopped on "cannot be read back", exit 1, with nothing asked**. The fix
uses the rule main's `fno/storage/receipted_rows.py` already applies: when no receipt exists under the day's folder,
the day has nothing done, and the empty set is returned without a sync. A receipted record that Drive no longer
returns still refuses ("not returned by Drive", a new assertion in
`test_a_damaged_earlier_record_or_a_refused_write_is_a_record_problem`), so the shortcut cannot hide a lost file.
Mutations: the shortcut always taken, 2 tests failed; the shortcut removed, 1 failed.

**Real read-only sample, Sun 25 Oct about 04:15 IST (what it proves and what it does not):**
- The real command, as O1 runs it: `margin check 2026-10-25: outside market hours`, exit 0, nothing asked
  (closed day).
- A rehearsal ran with the command's real parts:
  - all 15 of A14's real rows for **Mon 26 Oct**;
  - their own `nsccl.20261026.i1.zip` read from Drive;
  - live Groww through this caller's `ReadOnlyGroww`.

  The clock was pinned to 26 Oct 10:00 IST. The record went to an in-memory store, never Drive, so no dated record
  exists for a run that did not happen. Alerts were printed, not sent.
- Results:
  - All 15 baskets were rebuilt and proved to be their rows.
  - The NIFTY quote answered.
  - Pacing gave 15 margin requests 2-3 s apart, 60.7 s in all.
  - **Every margin request was refused by Groww: `GrowwAPIException`, code `GA000`, "Margin cannot be fetched at this
    time."** Groww's calculator does not answer on a weekend. On 21 Oct, a weekday, it answered at 20:13 IST, after
    the close (above).
  - The check did what the text says: 15 `error` rows ("Groww: GrowwAPIException", the class name only), the
    "not checked ... a rerun today retries them" line last, exit 1, and no alert of its own.
- The account afterwards, read-only (`get_order_list`, `get_positions_for_user`, `get_available_margin_details`):
  0 orders, 0 positions, `net_fno_margin_used` 0.0, `span_margin_used` 0.0, `exposure_margin_used` 0.0.
- **Still owed:** a matching sample in market hours, Mon 26 Oct about 10:00 IST (09:30-14:00, clear of 14:27 and
  14:55). It will be added here with the request count, the duration and the account check. Until then, the
  tolerance evidence is the 21 Oct evening run above (some evidence).

**Finding for the owner (strong evidence, one Sunday reading).** On a closed day the check never asks, because A7's
calendar says no session. But a special weekend session, or a weekday Groww outage, would give 15 `error` rows and
exit 1. O1 then marks the step and alerts once, which is the designed outcome: a lost day is recorded as lost, never
retried later.
