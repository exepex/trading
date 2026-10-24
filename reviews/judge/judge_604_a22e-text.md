# Judge 604: A22e story text (Amendment 3, index parts' last read at 09:10:45), story/a22e-last-read at 0846f0876 (judge J, round 1 of 2)

**PASS** (text), lane 1, 1 minor. Diff: only `docs/stories/A22-preopen-data.md` (+85). Doc-reading tests with
`FNO_SLACK_BOT_TOKEN` set: 864 passed, 14 xfailed.

## Criteria
| Item | Verdict | My evidence |
|---|---|---|
| Evidence | MET | Read 23 Oct's day row through the verified Drive cache (`data/preopen/day/2026/10/2026-10-23.csv`, SHA-256 290d6382..., equal to its committed receipt). Results: nifty `incomplete`, 3 reads, seen 09:10:59; banknifty `incomplete`, 3 reads, seen 09:11:01. Also gift `ok` (08:40:00) and fo_list `ok` at its first read (09:08:30) |
| Root cause | MET | `run.py:52`: ties go to the earliest `next_at` in list order (gift, fo_list, nifty, banknifty), read one after another. `run.py:76-83`: last read = close - `LAST_READ_BEFORE_CLOSE` (1 s), `ok` only when `seen_at < close`. `seen_at` is the candle answer's `received_at` (`parts.py:92`). The paced source spaces call starts by 0.5 s (`candle_source.py:18`) |
| The rule | MET | `next_at = min(now + 30 s, last_read)` with a 15 s margin gives 09:10:00, 09:10:30, 09:10:45. The default 1 s keeps GIFT at 08:44:59 and the F&O list at 09:10:59. The windows and `seen_at`'s meaning are unchanged |
| Alternatives | MET | Parallel reads would need threads around the paced source. Request-time judging would change `seen_at` for every part. Widening the window moves the 09:12 commit margin. Each is weighed with its reason |
| E1-E4 | MET | each testable on the injected clock; good, bad, boundary (09:10:59 vs 09:11:00) and empty (margin wider than window) cases; 5 plants |
| Out of scope | MET | the rehearsal's "late" is a replay artifact: only the last answer is archived, so REH1c can serve only 09:11:01 |

## Findings
**m1 (minor) The F&O list's last read now waits behind the index reads.**
- Before A22e, all three parts were due at 09:10:59 and the tie went to `fo_list` first.
- After it, the index reads at 09:10:45 run first. Each Groww candle call can take up to `CALL_TIMEOUT_SECONDS` = 30
  (`candle_source.py:21`).
- So if the F&O list were still incomplete after 09:10:30 and both index calls hung, its 09:10:59 read could start
  after 09:11:00.
- This is narrow: on 23 Oct the list was `ok` at 09:08:30.
- Fix: one sentence in the rule saying so, and an E1 or E2 boundary case with the F&O list incomplete and slow index
  calls, so the outcome is a test result, not an assumption.

## Plants
0 (text round). The builder's 5 plants are noted for the code round.
