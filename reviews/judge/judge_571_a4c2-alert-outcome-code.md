# Judge 571: A4c-2, the 3 pm index alert names each index's outcome, code (story/a4c-alert-outcome @ ba821e5d7)

**FAIL (round 1 of 2 for the code; 2 should-fix, 3 minor). Lane 1** (an alert to #fno-desk, the 3 pm record).
Judge F's role, taken over for this item. Text passed in judge 568 addendum 1. Labels: strong, some, reasoning only.

## Criteria

| # | Criterion | Result | My evidence |
|---|---|---|---|
| 1 | 14:38: every line and the one alert say "not started: too early (before 14:41)", no "canonical none", no marker | MET | `indices.py:62` carries `TOO_EARLY_REASON`; `indices_cli.py:49` adds `CLOSED_NONE` only outside `DONE_WITHOUT_ATTEMPT`; my replay at 14:38: 3 lines, 1 alert, exit 1, no file written |
| 2 | 14:41:00 waits and records; 14:40:59 too early | MET | `indices.py:61` keeps `>`; plant `>=` caught |
| 3 | an index closed none keeps "canonical none" | MET | close_day runs on the same condition (`indices.py:76-77`, `indices_cli.py:49`); two tests; plant caught |
| 4 | a quiet day sends no alert | MET | `QUIET_STATUSES` unchanged; tests at `test_index_recording.py:100,107,179`; plant caught |
| 5 | the unsent-alert test prints the new text | MET | `test_unsent_alert_text.py:73-75` |
| 6 | too early: exit 1, exactly one alert | MET | test asserts `code == 1 and len(sent) == 1`; plants (quiet, one alert per index) caught |
| 7 | the weekly slot gets the same wording | MET | `test_weekly.py:171`; one `IndexRecording` for all slots |
| 8 | `earliest_waiting_start` gives 14:41 and 14:35 | MET | `recorder.py:50-53`; test; plant (+60 s) caught |
| 9 | gates; no file over 350 lines | MET | trial merge with main (09d12bc9): 15,114 passed, 15 xfailed; ruff, format, imports, record scan clean; recorder.py 327 |
| QR2-6 | gap list, self-review, broken-code proof, cases, real sample | PARTLY | rule 3 missing (SF1); the rest present and true (sample reproduced word for word) |

## Findings

1. **Should fix: no builder self-review (quality rule 3, `docs/JUDGE.md`).** The Claims (`A-data-foundation.md`, A4c-2)
   have planted bugs but no section on independent code-review agents run on the diff, what they found and what was
   fixed. Same ruling as judges 181 and 188 [strong: the section is absent]. Fix: run the review on the diff and add the
   section to the Claims.
2. **Should fix: the new too-early alert still points to sidecars that do not exist.** `INDEX_ALERT`
   (`indices_cli.py:17-19`) ends "the sidecars in research/data/quotes/groww/ say why". A too-early run writes no
   sidecar and no file at all (my 14:38 replay: `rglob("*")` empty). This story exists because the alert's fixed
   wording was false for "too early"; this tail is the same kind of false fixed wording, so a reader looks for a file
   that is not there [strong]. Fix: say "the sidecars say why" only for indices that were attempted (or name the
   reason inline and drop the pointer for not-started ones), with a test that the 14:38 alert has no sidecar pointer.

## Minor

1. The result line of a closed-none index never says "canonical none" (`_line` and `_why` still build their text
   apart), though the story says "the line and the alert cannot disagree". Not a criterion; say so or align them.
2. The too-early decision (`indices.py:61`, `recorder.py:146`) still compares `(start - now) > MAX_EARLY_WAIT_SECONDS`
   instead of using `earliest_waiting_start`; today they agree (plants 4 and 5 both caught), but the text and the
   decision are two expressions of one rule [reasoning only].
3. `recorder.py:52` says "the one place this subtraction lives"; on `main` `fno/daily/quote_parts.py`'s
   `EARLIEST_START` still subtracts on its own until the O1 switch below lands.

## Plants

13 planted, 13 caught, none survived: canonical none always; never; no too-early reason; `>=`; limit +60 s; "too early"
dropped from `DONE_WITHOUT_ATTEMPT` (marker written); "(canonical none)" back in `INDEX_ALERT`; too early quiet;
reason dropped from the line; calendar check off; one alert per index; "already recorded" not quiet; 15:10 in the hint.

## Notes

- **O1 and the second merge.** Both trial merges are clean (with main, and then with `story/o1-r1r2-step-safety`).
  Whichever of A4c-2 and O1's R1 merges second must change `fno/daily/quote_parts.py` `earliest_start` to
  `return (datetime.combine(date.min, earliest_waiting_start(window_start)) + START_MARGIN).time()`, import
  `earliest_waiting_start` from `..quotes.recorder` and drop the then-unused `MAX_EARLY_WAIT_SECONDS` import (keep it
  in the docstring). I made exactly this change on the triple merge: `EARLIEST_START` 14:38:00, `INDEX_EARLIEST_START`
  14:44:00, ruff clean, tests/daily, tests/quotes and tests/timetable 388 passed. If A4c-2 merges first, R1 must
  switch its own `earliest_start`; on main today the duplicate is the old `EARLIEST_START` expression.
- Holidays, muhurat and special sessions: unchanged paths (the calendar check runs before the too-early check). IST
  has no daylight saving. The new text holds times only, no level (public-record rule holds).

## Addendum 1

**Round 2 of 2 at story/a4c-alert-outcome @ 8fb3e8a9e: PASS. Merge go.** Trial merge with main 404452481 (b46dad9d):
full suite **15,135 passed, 15 xfailed**; ruff, format, `check_imports`, `check_records` clean; recorder.py 338 lines.

| Item | Answer | My check | Result |
|---|---|---|---|
| SF1 rule 3 | two review sessions, 11 findings, each answered in the Claims | read; the answers match the diff (A5/B1 status lists once in `indices.py`, B2 helpers in `index_fakes.py`, B5 quiet-line test) | **Accepted** |
| SF2 pointer | `SIDECAR_POINTER` only for status `ATTEMPTED` | 14:38 alert word for word with no pointer and no file (`test_index_recording.py`); 15:12:40 names BANKNIFTY only; plant "window closed counted as attempted" caught | **Accepted** |
| Minor 1 | one `outcome()` for line and alert; `closes_none` for marker and words | `indices.py:78,89`, `indices_cli.py:54`; plants (no canonical none, line without outcome, quiet tail) caught | **Accepted** |
| Minor 2 | `earliest_waiting_moment(day, start, wait)` called by both decisions | see below | **Accepted, the deviation too** |
| Minor 3 | docstring says O1's copy remains until the switch | `recorder.py:58-63` | **Accepted** |
| Criterion 3 | "beside a too early one" cannot occur in one run | `indices.py:62-63` returns too early for every index at once, before any attempt | **Accepted** |

**Minor 2's form.** One rule in one place: `recorder.py:155` and `indices.py:62` call `earliest_waiting_moment`;
`earliest_waiting_start` is that function on `date.min` (`recorder.py:64`). `now < start - wait` equals the old
`now < start and start - now > wait` for every wait of 0 or more, and `window.py:50` refuses a negative wait, so no
case changes. I reproduced the `OverflowError` from `date.min` with a 900-minute wait; the real-day form is right.
Times kept to the second: 14:41 and 14:35 printed; 14:41:00 waits, 14:40:59 too early; v4 14:00:00 waits.

**A1 (put to me): not a finding that blocks; a minor against the passed text.** "a rerun from 14:41 to 15:13 records
it" over-promises late in the window (from 15:12:40 one index gets an attempt, the others close none). The alert is sent
at the too-early moment (before 14:41), when a rerun soon after records all; and O1's R1 removes the case. Keep it now;
when the text is next touched, say "a rerun from 14:41 records it; started late, only the indices reached by 15:13"
[reasoning only].

**Shared scratchpad.** My worktree at 8fb3e8a9e equals the head in `fno/` and `tests/`; none of my 25 plant strings
nor the builder's (`<=`, `date.min` in a decision) is in the code. One stray: a blind rename left
`test_an_unreadable_nse_file_is_reported_once_per_index_andalerted` (`test_index_recording.py:66`); harmless, minor.

**Plants (round 2):** 12 of 12 caught, none survived: window-closed index pointed to; no "canonical none"; the window's
own wait ignored; recorder `<=`; a complete index closed none; "incomplete" for every status; tail on quiet lines; index
rule 1 s early; "too early" closes none; no too-early reason; "too early" quiet; line without outcome.

**Second merge (unchanged instruction).** Whichever of A4c-2 and O1's R1 merges second sets O1's `earliest_start` to
`(datetime.combine(date.min, earliest_waiting_start(window_start)) + START_MARGIN).time()`, imports it from
`..quotes.recorder`, drops the unused `MAX_EARLY_WAIT_SECONDS` import and removes the note in `recorder.py:58-63`.
The R1 trial merge now conflicts only in `docs/WORK_REGISTER.md` (keep both rows).
Note: the round-2 builder session is the orchestrator's own; I share no context with it.
