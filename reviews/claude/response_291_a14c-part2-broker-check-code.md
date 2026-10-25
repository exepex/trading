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
| Idempotent: `ok` and `mismatch` are done; `error` is asked again only by a same-day rerun (superseded in round 3: O1 never retries the step, judge 634; only a by-hand run asks again); a damaged earlier record refuses (exit 1) | `BrokerRecord.done` | `test_a_rerun_asks_only_what_is_not_done_and_a_done_day_asks_nothing`, `test_a_damaged_earlier_record_or_a_refused_write_is_a_record_problem` |
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
| A mismatch was not alerted when the record failed, and the line said "not checked" | reproduced | the line says "checked but not saved"; no finding is alerted for data that did not land (superseded in round 3: only a by-hand run asks again, judge 634) | `test_a_record_that_cannot_be_written_or_read_exits_1` |
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

## Round 3: judge 630's five findings (25 Oct 2026; the orchestrator's last round)

I checked each finding and accept all five, each on its own evidence:
- **1 (blocking):** the first test run in this session failed with exactly "Install the Groww SDK first" before
  `routine_setup.sh --groww`.
- **2:** `NseIndexOptionExposure.per_unit` is `rate x level` per short leg, so a 0.12% move flips a correct row at
  0.1% tolerance.
- **3:** the check's lot and the row builder's lot are two reads of `lot_sizes.NIFTY`, and neither is dated.
- **4 and 5:** read, true.

Text first: dbb6607cf. Then code.

| Finding | Fix | Tests (planted bug caught) |
|---|---|---|
| 1. The suite fails without the Groww SDK | `build_broker_check` builds `GrowwProvider` on first use (`functools.cache`), as Drive already is; the dated-lot library likewise | `test_the_wiring_uses_the_row_builder_s_lot_and_needs_no_groww_sdk` (blocks `growwapi` with `sys.modules`; plant "eager Groww" caught); the full suite in a venv with `requirements.txt` only (below) |
| 2. Exposure at one level while Groww charges the live one | NIFTY read before the first basket and after the last (`Levels`). Exposure is judged against the expected figure nearest Groww's at any level between the two (exposure is linear in the level). A rate step at 10% out of the money inside the range is `error`. With no second reading (a failure, or the 14:50 stop), a basket within 0.1% at the first reading is `ok`, otherwise `error`, never `mismatch`. Both readings are in the record (`nifty_before`, `nifty_after`). | judge 630's case, +0.12% during the run: 6 of 6 `ok` (`test_a_move_during_the_run_is_inside_the_range_and_every_basket_is_ok`); the same answers against a still reading are mismatches; a planted 0.2% error is a mismatch on a still and on a moving index; no second reading; a rate step at NIFTY 18,181-18,183 for SF 100's short 20,000 call. Plants "one level only", "rate step ignored", "unclear as mismatch", "no second reading": 4 of 4 caught |
| 3. The lot read twice and undated | One source: `BasketBuilder.lot_size` is the row builder's calculator's lot; the check has no lot field of its own. Before any request, it is checked against NSE's dated lot for the basket's expiry month from A20a's archived `fo_mktlots.csv` of the day, read with the school's `ArchivedLots` (`broker_lot.py`, no second reader), once per run and expiry. A different lot, a missing file or an unreadable one is `error` with no Groww request (when nothing can be sent, not even the NIFTY quote is asked). | `test_a_lot_differing_from_nse_s_dated_lot_sends_no_basket`, `test_no_dated_lot_or_an_unreadable_lot_file_is_an_error_retried_the_same_day`, `test_the_dated_lot_is_read_with_the_school_s_reader_for_the_basket_s_expiry_month`, the wiring test. Plants "lot check removed", "any dated lot accepted", "missing lot read as 65", "BANKNIFTY lot (30) as the basket's", "quote asked with nothing to send": 5 of 5 caught |
| 4. Stale slot and timing text | The step runs third, right after the 14:05 start and before the weather; measured 44.7 s and 60.7 s, about 2.5 min for 40 baskets; `PACE_SECONDS`' comment says so | text |
| 5. No self-review entry | below | - |

Plants: 10 of 10 caught.

**Real read-only check of the dated lot (Drive, 25 Oct).**
- 23 Oct's archived lot file gives NIFTY 65 for November and December, the same as `lot_sizes.NIFTY`.
- 26 Oct's file is not archived yet, so the read gives `lot_unavailable`, as it should.
- **When A20a's lot file really lands (corrected 25 Oct, from the fo-masters runs; strong evidence, three days).** My
  "12 hours late on 21 Oct" above was wrong: 21 Oct 19:46 IST was the job's first run, started by hand
  (`workflow_dispatch`). GitHub starts every scheduled slot about 4.5-5 hours late:

  | Slot (IST) | Started, 22 Oct | 23 Oct | 24 Oct |
  |---|---|---|---|
  | 07:45 | 13:03 | 13:00 | 12:46 |
  | 11:15 retry | 16:09 | 16:01 | 15:18 |
  | 18:45 | 23:29 | 23:22 | 22:05 |

  The day's lot file therefore lands about 13:00 IST, about one hour before the 14:05 check. The 11:15 retry always
  lands after the check, so it never saves the day. If the 07:45 slot is more than about 6 hours late, or fails, the
  check is `error` "no dated NSE lot" for the day: exit 1, one alert from O1, and the day's figure is lost unless the
  check is run by hand before 14:50 (O1 never retries the step, judge 634).
- I chose fail-closed over carrying a lot from another day, following the school's own rule. The cost is a lost
  broker figure on a late-archive day. Moving A20a's lots slot earlier is A20a's owner's call; I put that to the
  orchestrator, not into this branch.

**Self-review of rounds 2 and 3 (quality rule 3).**
- **Round 2's first-run shortcut** (`BrokerRecord.done`) skips the sync only when the receipts folder in git has no
  receipt for the day. The receipts are the index (O9 rule 4), so "none" is the truth. A receipted file that Drive lost
  still refuses (tested).
- **Round 2's REH1j test edits:** the example changed meaning only; the REH1 owner was told.
- **Found and fixed in round 3:** `RawFileLibrary` keeps no copy, so a lot read per basket would have downloaded the
  lot file from Drive 15 times a run. `NseDatedLot` now reads once per run and expiry; a failed read raises and is not
  remembered, so a by-hand run reads again (tested).
- **Checked, no change:**
  - The second quote is paced and stopped at 14:50 like every request. A run started at 14:49:5x gets "deadline"
    for it, and then the first-reading rule applies.
  - `checked_at` is still taken after each answer.
  - Error rows from a failed basket carry no levels (empty cells).
  - The record's two new columns break nothing: no record has ever been written, since the check was never live, and
    `done()` reads columns by name.
  - The rate-step test compares `exposure / level` rounded to 6 places. That is the summed rate times the lot, so float
    noise cannot fake a step.
- **Limit, said plainly:** a range read over about a minute (more with 40 baskets) loosens the exposure check by
  NIFTY's move in that minute, typically a few hundredths of a percent [reasoning only]. A stale exposure rule
  (2% to 2.5% is a 25% change) is still caught. A per-basket bracket would be tighter, at the cost of 15 more quotes;
  I kept the orchestrator's accepted design.

### Judge 634's new should-fix: the failure lines promised a same-day retry O1 never makes

**Accepted (strong evidence: the code read).** `fno/daily/steps.py` `outcome()` sets no `retry` key. `RunLog.done`
counts a failed entry without `retry: true` as done (`fno/desk/run_log.py:41-43`, `_retried`). So a same-day
`daily run` skips a failed `margin_check`; only exits and marks are retried (owner, 24 Oct). A by-hand
`margins stress-broker-check` does ask again, because `BrokerRecord.done` skips `error` rows.

**Fix (no retry added: that rule is the owner's).**
- Text 7288035b9 (A14c part 2 and O1's story).
- The two lines now end "today's broker figure is lost unless `python -m fno margins stress-broker-check` is run by
  hand before 14:50". When the 14:50 stop is among the reasons they end only "today's broker figure is lost": after
  14:50 no run can ask again, so naming one would be a second false promise (found while fixing).

**Tests.**
- `test_the_failure_line_promises_no_retry_because_o1_never_reruns_the_step`: the check's real failure output goes
  through O1's `outcome()` into a `RunLog`. The entry is `done`, `retried_steps` is empty, and the reason names the
  by-hand run and no "rerun".
- The deadline and record-failure line tests.
- Plants: the old promise put back, 2 failed; the by-hand hint after 14:50, 4 failed.

### Follow-up after judge 630 addendum 1 (test-only, the two surviving plants; for after the merge)

- `test_a_basket_charged_at_the_first_reading_under_a_moving_index_is_ok_at_that_level`: plant `nearest = last`,
  1 failed.
- `test_the_record_keeps_both_nifty_readings_and_an_empty_cell_for_a_missing_one`: plant "both readings written
  empty", 1 failed.
- The lot paragraph above is corrected: no same-day rerun, and A20a's real slot times.

### Judge 634 addendum 1 (round 2 FAIL: one should-fix, one minor), answered on this follow-up branch

Both points are accepted, checked against the code.
- **Point 1.** The response 291 line 634 saw was on c2ed049e6; this branch had already fixed it (3dfaa02f4). The two
  earlier mentions of a same-day rerun (rounds 1 and 2) are now marked as superseded. The story's lot paragraph gives
  the measured times, names the loss risk, and names the fix: A20a's 06:00 IST slot on `story/a20-lots-early-slot`.
- **Point 2.** `NOT_SAVED`, like `FAILED`, now picks its ending through one rule (`_then`):
  - at or after 14:50 (by the clock, or with the 14:50 stop among the reasons), only "today's broker figure is
    lost";
  - before then, the by-hand run *and* "its receipts (receipts/data/margins/broker_checks/) committed", since O1
    commits them only for its own step.

  The story says the same. Tests: `test_after_14_50_no_line_names_a_by_hand_run` (a record failing after the stop;
  a run ending past it) and the exact not-saved line. Plant "the clock ignored": 1 failed.

### The owner's Groww rule (25 Oct, refined the same day): the by-hand path kept, as a rerun of the same command

- **The rule:** no hand-run Groww command from 09:15 to 15:35 IST, except that a scheduled command that failed or
  stopped early may be rerun by hand, in market hours too (DESK_DECISIONS, 25 Oct).
- **Which form, and why:** a rerun of `daily run` does NOT cover a failed `margin_check`. Its step sets no `retry`
  key, so `RunLog.done` holds the failed entry and the rerun skips it (judge 634; tested in
  `test_the_failure_line_promises_no_retry_because_o1_never_reruns_the_step`). So the path stays, worded as the owner's
  exception: "unless this same `python -m fno margins stress-broker-check` is rerun by hand before 14:50 and its
  receipts (receipts/data/margins/broker_checks/) committed". At or after 14:50 the line still says only "today's
  broker figure is lost".
- **History:** 371f308ed briefly removed the path under the first form of the rule; this commit reverts it.
- **The story** says the same, and that any other hand-run Groww command from 09:15 to 15:35 stays forbidden.
- **Monday's sample** stays after 15:35 IST: it is a different command (a rehearsal), not a rerun of a failed step.
