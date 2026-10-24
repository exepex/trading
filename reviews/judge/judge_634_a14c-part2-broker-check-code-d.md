# Judge 634: A14c part 2, the daily read-only Groww broker margin check, code round 1 (judge 1 of 2)

Branch `story/a14c-part2-broker-check` at `5f7dc5d7c`; claims `reviews/claude/response_291_...code.md`, "Round 2".
**FAIL, lane 1** (1 blocking, 1 should-fix, 3 minor). Judge session 01BvZZzF4XR48qNHNxLydQhf.

## Criteria

| Criterion (A14c part 2 text, criterion 10) | Verdict | Evidence |
|---|---|---|
| Read-only: only this caller's list reaches Groww | MET | `broker_port.py:16`, `read_only.py:37-50`; `place_order`, `get_order_list`, `get_positions_for_user` refused (test); SDK 1.5 `get_order_margin_details` posts to `/margins/detail/orders` only (read the installed source) |
| From 09:30 on a session day; no request at or after 14:50:00 | MET | `broker_check.py:66,136`; plants P1 (14:51), P15, P17 (09:00) caught |
| Pacing and request count vs Groww's 300/min and sign-in | MET | 1 quote + N baskets, 2 s apart (≤30/min); `providers/groww.py:140-146` signs in once per process, lazily; plant P11 caught |
| SPAN `max(0, scan-NOV)` within Rs 1; exposure at own NIFTY quote within 0.1% | MET | `broker_compare.py:35-42`; P2 (row's exposure), P8 (Rs 1.5), P9 (no NOV) caught; basket proved by source SHA-256 and three figures (`broker_basket.py:63-75`) |
| ffed1c8c1: empty day reads empty; a receipted file Drive lost refuses | MET | `broker_record.py:73-77`; P3 (shortcut always), P4 (incomplete sync accepted), P16 (`error` counted done) caught |
| Write-once O9 record with receipt; O1 commits only its receipts | MET | `DataStore.put`; `daily/wiring.py:144-151`; `CommandStep` commits paths on exit 1 too (`desk/daily_run.py:236`); P14 caught |
| Alert path: a mismatch sends one line, a failure none of its own | MET | `broker_check.py:145-156`; P10 caught |
| Failure lines say what happens next | NOT MET | finding 2 |
| Gates on a trial merge with main 378dbe30f | PARTLY | ruff, format, imports, records clean; full suite 16626 passed, 14 xfailed, 0 failed (with the Groww SDK installed); without it, finding 1 |

## Findings

1. **Blocking: the suite fails where CI runs it.** `build_broker_check` builds `GrowwProvider(cfg)` at once
   (`broker_wiring.py:30`), whose constructor imports `growwapi` (`providers/groww.py:130-133`); CI installs only
   `requirements.txt` (`checks.yml:35`; growwapi is in `requirements-groww.txt`). With `growwapi` blocked:
   `test_before_09_30_the_check_needs_no_drive_or_groww_settings` FAILS ("Install the Groww SDK first"); main's same
   tests pass (204 passed). The test's own claim (no Groww needed before 09:30) is false without the SDK. Fix: build the
   provider on first broker use (inside the client lambda), as Drive already is; prove it with the SDK absent.
2. **Should fix: the lines promise a same-day retry O1 never makes.** `broker_check.py:34,36-39` print "a rerun today
   retries them" / "asks them again", and the story's Idempotent bullet and O1's text say a same-day rerun retries.
   But `outcome()` sets no `retry` key (`daily/steps.py:45-54`), `RunLog.done` treats such a failed step as done
   (`desk/run_log.py:41-43,81-82`), the run skips done steps (`desk/daily_run.py:145`); only exits and marks retry
   (line 84). My script: a failed `margin_check` entry gives `done("margin_check") == True`. O1's alert carries this
   line to #fno-desk. Fix: say the truth (lost for the day; only a by-hand `margins stress-broker-check` before 14:50
   asks again), in the lines, the story and O1's text, with a test on the line.
3. Minor: the story says the step runs "about 14:35 IST, after the weather and the v4 forecasts"; `DAILY_RUN_STEPS`
   runs it third, before `weather` (`constants_operations.py:59-63`), about 14:06. Fix the text.
4. Minor (reasoning only): one NIFTY level at the start serves every basket; the builder's runs took 44.7-60.7 s, and a
   0.1% NIFTY move inside a minute gives a false "review the stress factor" line. Re-quote per basket (about 31
   requests, still far under the cap) or state the drift in the Monday sample.
5. Minor (rule 3): no self-review is stated for round 2's changes (ffed1c8c1, the merge, 5f7dc5d7c).

## Plants

17 planted, one at a time, restored each time: 16 caught. Survivor: P13, the order-verb second line in `ReadOnlyGroww`
removed; unreachable while the positive rule holds (no order name matches `get_*` or UPPER_CASE), as judged in 356.

## Notes

- Open item, not a finding: the market-hours sample (Mon 26 Oct about 10:00 IST) is owed; Sunday's GA000 refusal was
  handled as designed (15 `error` rows, exit 1, no own alert).
- The claims sit in a response file, not the story's Claims section (CLAUDE.md); routed so by the orchestrator.
- Independence: while reading the judge README's format I saw the index row of judge 630 (the other judge). Finding 4
  was in my notes before that; finding 1 I then checked myself with the run above. Nothing else of it was read.
- Gates first failed 2 + 9 errors in a shallow clone (freeze tests); after `git fetch --unshallow` all passed.
