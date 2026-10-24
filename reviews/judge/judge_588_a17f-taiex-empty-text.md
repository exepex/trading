# Judge 588: A17f, an empty answer in part B, story text (story/a17f-taiex-empty @ 028d7de02)

**FAIL (text round 1 of 2; 4 should-fix, 3 minor). Lane 1** (Yahoo and TWSE, the private pre-open table, alerts).
Judge F, own session (session_01A8XfbTUVgeeEpqatHaWbtP). Labels: strong, some, reasoning only.

## Facts and rules checked

| Item | Result | My evidence |
|---|---|---|
| 23 Oct: TWSE did not trade (unscheduled) | TRUE | `MI_5MINS?date=20261023`: "很抱歉，沒有符合條件的資料!", total 0; 22 Oct: stat OK, 3,241 rows; `MI_5MINS_HIST` Oct: last row 115/10/22 |
| Holiday file: 27 rows, SHA-256 `7644c1a8…2117`, no 23 Oct | TRUE | fetched today: HTTP 200, 3,774 bytes, same SHA-256 in full; 23 Oct absent |
| 18 weekday closures; 26 Oct a closure (25 Oct Sun, made up Mon) | TRUE | my parse (drop weekends and "交易日" names): the exact 18 dates of the text |
| Mechanism: empty `quote` → KeyError → "not Yahoo's chart answer"; archive after parse | TRUE | `yahoo_source.py:134-139`; `preopen.py:98-99` (parse before `_archive`); alert text `preopen_cli.py:35` |
| Calendar CSV plus test against TWSE's file | SOUND | the parser output equals the hand list for 2026; a fixture per year keeps it honest |
| A listed closure: no request, `market closed`, exit 0 | RIGHT | rule 1 and criterion 1 say so; nothing to read, nothing failed |
| Empty answer on an unlisted day: `no session data`, exit 1 | RIGHT | at 08:50 a typhoon closure and a Yahoo gap cannot be told apart; owner 24 Oct: problems warn. Part B's exit 1 changes nothing else in A22's routine (CLAUDE.md, pre-open step 4) |
| Criterion 6 after Monday | ACCEPTABLE | 26 Oct is a scheduled closure (criterion 1); no open row exists today (23 Oct wrote none: it failed) |
| Gap list, cases, plants, sample | PRESENT | each criterion has good/bad/boundary/empty; P1-P10 cover criteria 1-6; sample promised in the Claims |
| Doc-reading tests on a trial merge with main | PASS | 853 passed, 15 xfailed; record scan clean (9,091 files) |

## Findings

1. **Should fix: settlement from `taiex_yahoo` is circular.** Rule 3 settles from "TWSE's `taiex` first, `taiex_yahoo`
   otherwise". When that fallback is used, a Yahoo gap is likely to be missing from Yahoo's daily series too. So "absent
   while a later session is present" settles a Yahoo gap as `closed (unscheduled)`, and the text then says to add a hand
   `unscheduled` row to the calendar from it [reasoning only, strong on the logic]. Fix: settle only from TWSE's own rows
   (the reader returns the cue, `wiring.py:185`). Otherwise the row stays open and becomes `unsettled`. Add a bad case
   for this.
2. **Should fix: settlement rows back-date the record.** "same `seen_at` day as the original" puts a row written days
   later under the original morning. Any reader that takes rows as known at `seen_at` then sees the settlement early.
   That is look-ahead in a recorded dataset. Fix: `seen_at` is when the settlement ran, and `settles` names the date it
   settles. Add a test that no settlement row has `seen_at` earlier than its run.
3. **Should fix: settlement for the other six indexes is undefined.** Rule 2 makes an empty answer `no session data` for
   any index. But rule 3 names only taiex's tables. For Nikkei or KOSPI it does not say which table settles the row, or
   whether it is left to become `unsettled` with an alert after 10 days. Fix: name the table for each index, or say that
   only taiex settles and what an open row of another index becomes. Add a criterion case.
4. **Should fix: the uncovered year contradicts itself and is not defined.**
   - Criterion 1's empty case wants "the alert" to name `TWSE calendar has no 2027`. Criterion 4's empty case says a run
     with no problem sends no alert. Rule 4 gives the uncovered year no exit code and no O10 kind. "From 1 Dec ... in
     that day's alert line" has the same gap.
   - Nothing says how the CSV "declares the years it covers": its columns have no such field.
   - Fix: define coverage (for example a `covers` row per year, or a year with a parser-checked fixture). State whether
     an uncovered year is a problem, with its alert, O10 kind and exit code.

## Minor

1. Line references: "no 5-minute level" is `preopen.py:67-68`, not 66; parse-then-archive is `preopen.py:98-99`, not
   94-96; the shape check is `yahoo_source.py:137`.
2. Criterion 1's bad CSV row is "refused at load", but the text does not say what then happens. It could stop every
   index (`build_preopen` fails) or only taiex. Say which; only taiex is my suggestion.
3. Older Drive parts read through `DrivePartsRowLog` (`csv.DictReader`) have no `reason` or `settles` key at all, rather
   than blank values. The code must read them with a default.

## Plants

None (a text round). The builder's P1-P10 are checked at the code round, together with my own plants.

## Notes

- Deadline: findings 1-3 touch only rule 3 (criterion 6, after Monday). Finding 4 touches criterion 1. A one-paragraph
  fix of all four lets criteria 1-5 start at once; round 2 is by reading.

## Addendum 1

**Text round 2 of 2 at story/a17f-taiex-empty @ efa332d49: PASS (text). Lane 1.** Judged by reading the round-2 diff
(`028d7de02..efa332d49`, one file). Doc-reading tests on a trial merge with main: 853 passed, 15 xfailed; record scan
clean (9,093 files).

| Item | Answer | My check | Result |
|---|---|---|---|
| SF1 circular settlement | official tables only, read straight from the cue's table; Yahoo-only copy leaves the row open; P11 | rule 3 and criterion 6's bad case say so; official sources exist on main: `asia_sources.py:41-42` (sse_composite, CSIndex), `:58-59` (taiex, TWSE), `:73-74` (nikkei225) | **Accepted** |
| SF2 back-dated rows | `seen_at` = settlement run time, `settles` names the date, empty level fields; test and P12 | rule 3, criterion 6 | **Accepted** |
| SF3 other indexes | nikkei225 and sse_composite settle; kospi, asx200, hang_seng, sti final (named "not settled" in the morning line, no later alert) | matches `wiring.py:68-85`: these four have no official cue | **Accepted** |
| SF4 coverage | one `covers` row per year (TWSE file's SHA-256, fixture-checked); uncovered year: alert, O10 `failure`, exit 1; from 1 Dec: O10 `incomplete`, exit 1; P13 | criteria 1 and 4 now agree (criterion 4's empty case lists coverage) | **Accepted** |
| Minor 1 | `preopen.py` lines fixed; pushback on `yahoo_source.py` | on origin/main `chart_result` is line 117 and the shape check line 121; my "137" was wrong | **Pushback accepted** |
| Minor 2 | a broken calendar fails `taiex` only, still read from Yahoo; the other six untouched | "A broken calendar" paragraph; criterion 1's bad case | **Accepted** |
| Minor 3 | older parts read with `""` defaults | rule 4 | **Accepted** |

## Notes for the code round (not findings)

- The 1 Dec warning exits 1 on every session day until the next year's `covers` row lands, so December could bring
  about 20 alerts. That is the owner's "problems warn" rule and acceptable, but the code round must show that one
  CSV commit stops it.
- A `covers` row shares 1 Jan with that day's `holiday` row. The loader must key rows by date and kind, never by date
  alone.
- Criterion 6 may land after Monday. The commit that holds it gets its own code verdict, with P9-P12 and my own plants.
