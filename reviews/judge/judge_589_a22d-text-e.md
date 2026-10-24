# Judge 589: A22d story text, the flat 09:15 pre-open candle (story/a22d-flat-candle @ 5e2dfff03), judge E

**FAIL (round 1 of 2, text; 1 should-fix, 2 minor). Lane 1** (Groww, the A22 routine's record). Judge E, own session.
Text only: one file, `docs/stories/A22-preopen-data.md`, +118. Judged by reading. Doc-reading tests with the token
kept: 853 passed, 15 xfailed.

## Evidence (my own read of the record; differences and shapes only, no value)

| Claim, 23 Oct | Result | My evidence |
|---|---|---|
| Live answers: one candle of the day each, stamped 09:15, flat, `null` volume | **Reproduced** | `nifty_091059.json` and `banknifty_091101.json`, each read from Drive and hashed against its receipt: 1 candle, 09:15, open = high = low = close, volume field None |
| Its close minus NSE's Open Index Value | **Reproduced: 0.00 and 0.00** | `ind_close_all_23102026.csv` from Drive, SHA-256 equal to its manifest row |
| Minus Groww's 09:09 history close; the real 09:15 candle not flat | **Not reproduced** | Needs live Groww (`growwapi` is not installed here; no 23 Oct 1-minute archive in `groww-candles/`). Accepted as the builder's claim, marked one session |
| Today's outcome: "candles only from 09:15" | True | `answers.py:82-83`; O10 rows 12-13 |

## Rulings asked for

| Choice | Ruling |
|---|---|
| Flat candle only alone, read 09:10:00 to before 09:15:00 | **Accepted.** From 09:15 a 09:15 candle can be a traded minute. The lower bound is after step 0b's final 09:08-09:09 value. The answer's `received_at` is `seen_at` (`parts.py:86-91`). A stale placeholder (yesterday's close) would pass every shape test, so the next-morning check is the real guard |
| `flat_0915_unverified`, kept not blocked, usable from Monday on n=1 | **Accepted, with reasons.** No reader uses the value today: my grep for `nifty_preopen` and the day folder outside `fno/preopen/` finds none, and the forecast lab's GIFT section reads only `early_file`. The label leaves the choice to a future reader. Five matches is a label, not proof [reasoning only] |
| Open check before 08:40 never delays the 09:12 commit | **Not accepted as written** (finding 1) |
| One tick (0.05), A16b's `beyond` | **Accepted.** `minute_check.py:18-20` rounds before comparing; 0.00 seen on both indices |
| Mismatch alert and O10 row carry no value | **Accepted.** The difference stays in the Drive check file |
| NSE `key=NIFTY` out of scope | **Accepted.** The reason is true: no morning answer is archived, so its layout is unread |

## Findings

1. **Should fix: nothing bounds the open check's time, so a slow Drive can push GIFT's read out of its window.**
   - The check runs "at the start of `preopen record` ... before the GIFT window". The routine starts at 08:36 and
     setup takes part of that, so there are about 2-4 minutes before 08:40:00.
   - It syncs Drive folders for up to 10 sessions. D7 covers Drive down or an unreadable file, but not Drive slow (each
     call waiting for its timeout).
   - A check still running at 08:40 delays GIFT's first read. A run that reads only after the window has closed is
     `late` (`run.py:1-4`), and the 08:50 morning edition needs GIFT's receipt at about 08:41.
   - Fix: give the check a hard stop before 08:40:00 (sessions not reached are left for the next morning, never counted
     as a match), or run it after the 09:12 commit. Test it with a slow fake store and an injected clock: GIFT's read
     still starts at 08:40:00. Plant 14 then needs restating to match.

## Minor

1. Day rows written before A22d (23 Oct) have no basis columns. Name that header in D4 and D5's cases: the open check
   and any reader accept it, and a row with no value is skipped.
2. The Evidence heading says "[strong, one session]", but two of its five rows rest on a Groww read that the
   repository cannot replay. Mark those two rows "the builder's read".

## Plants

None (text round). The 14 planned plants cover the rule's bounds, the label count and the check's source.
