# Response 285: A20c, macro release dates kept point in time (builder's claims)

**Story:** `docs/stories/A20-rules-and-dates.md` (part c; text branch head 9ed3c071) · **Branch:**
`story/a20c-macro-calendar` · **Builder:** session_013u1Ac2N9eRQ8XCYPjwpaat · **Lane:** 1 (MOSPI, the Fed, Drive,
Slack, a workflow, a new dependency)

## What it does

`python -m fno macro-calendar` (workflow `macro-calendar.yml`, 07:30 IST daily):
- **MOSPI** (`fno/macro_calendar/mospi.py`): reads the latest Advance Release Calendar via MOSPI's API, extracts the
  PDF's text with `pypdf==5.4.0` (pinned; approved by the orchestrator), and parses India CPI, IIP and GDP dates for
  the financial year. It requires exactly 12 CPI and 12 IIP dates and at least 4 GDP dates, otherwise "layout
  changed?". A planned weekend date moves to the Monday, keeping the printed date as `planned` (MOSPI's footnote,
  confirmed by its own "Released on" lines).
- **The Fed** (`fed.py`): FOMC decision days (a range's last day; "Apr/May 30-1" → 1 May) for each year from the
  run's year on, 8 a year or the run fails; a notation vote is not a decision. These are US dates.
- **US CPI and payrolls**: `UnconfiguredCalendar` fails every run, on purpose, until the owner decides on a FRED key.
  BLS refuses GitHub's runners (probe run 38900266338).
- Each calendar read whole becomes one O9 `PartTable` snapshot part `macro-calendar/<source>/...` with every date,
  the run's time and the document's period. The document is kept once in Drive under its SHA-256. The run is stale
  when the last future date is under 30 days ahead. One alert names every problem, and the run exits 1. O10's watcher
  records the failed run (`macro-calendar` to be listed there).
- **Events** (`fno/research_data/macro_events.py`; A6's frozen `events.py` and `events.csv` are not touched):
  - `announced_on` is the IST day of the first snapshot holding a date, and only if before the date.
  - A future date that a later snapshot drops, while the date is inside that snapshot's period, is withdrawn. It
    becomes A6's moved-meeting form (`scheduled=False`, `first_announced_on`, `first_withdrawn_on`, "WITHDRAWN" in
    the description), known through A6's `known_on` only until the withdrawal.
  - Dates outside the new document's period are kept.
  - Past dates dropped stand; a date that comes back is a new announcement.

## Claims per criterion (code, test, broken-code proof)

All mutations were planted and restored by `mutate.py` (this session's scratchpad); every one listed was CAUGHT.

| Crit. | Claim | Code | Tests | Mutations |
|---|---|---|---|---|
| 10 | The real ARC text gives 12 CPI, 12 IIP and 5 GDP dates for FY 2026-27 (exact days asserted); 11 and 13 CPI refused; no title refused; weekend dates moved to Monday with the printed date kept (8 such dates asserted), and a Monday stays; a real PDF (built in the test) is read, while a non-PDF and a PDF without text are refused; the adapter follows MOSPI's latest-calendar answer, refuses a 403 and a non-PDF link, and reports the financial-year period | `mospi.py` | `tests/macro_calendar/test_mospi.py` | count check off; Jan-Mar year; empty PDF accepted; weekend not moved; Friday moved; PDF KeyError escapes; wrong period |
| 11 | The real FOMC page gives 16 decision days for 2026-27 (exact first and last); "Apr/May 30-1" → 1 May 2024; 2025's notation vote excluded; 7 meetings, no panel for the run's year and an empty page refused; period from the run's year to the last listed year; capture stale at 29 days ahead, fine at 30; a failed or unconfigured calendar does not stop the others; Drive errors named; an unchanged document is not uploaded again | `fed.py`, `capture.py` | `test_fed.py`, `test_capture_and_job.py` | first day of range; first month of span; count check off; notation vote kept; stale `<`→`<=`; document stored every run; failure stops others; Drive OSError escapes |
| 12 | `announced_on` is the IST day (20:00 UTC → next IST day); a date first seen on or after its day is dropped; a withdrawn date is known the day before and not on the withdrawal day, and `in_window` sees it before; WITHDRAWN marker; a past date dropped stands; the next financial year's file withdraws nothing from the old year; an older file served again withdraws nothing outside its year; a returning date is a new announcement; sources are separate; A6's `TYPES` unchanged | `macro_events.py` | `test_events.py` | UTC day; late sightings kept; withdrawal off; period ignored; marker removed |
| 13 | Cron `0 2 * * *`, `contents: write`, alert step on `failure() && steps.calendar.outputs.posted != 'true'`, env holds only secret references | workflow | `test_the_workflow_...` | — |
| 14 | Commits only `receipts/` | wiring | `test_the_job_commits_only_receipts` | — |
| 15 | Wired only in `fno/macro_calendar/wiring.py`; tests offline | wiring | all | — |
| 4/9 (job) | One alert names every problem; receipts not committed is a problem; a clean run sends nothing | `job.py` | job test | not-committed ignored |

Removed after mutation testing: a "Released on" filter and a split that changed nothing on the real layout, since
the exact counts already catch drift. They were dead code, so they were deleted rather than kept untested.

## US CPI and payrolls from FRED (added 21 Oct, owner's key)

- `fno/macro_calendar/fred.py`: FRED's release-dates API, CPI (release 10) and Employment Situation (release 50), with
  scheduled dates included; dates from the run's year on; at least one after today, or the run fails. The key goes
  only in the query: no message names the URL, rows cite the public release page, and a kept document has the key
  replaced. Without `FNO_FRED_API_KEY` the wiring keeps `UnconfiguredCalendar` ("set the GitHub secret ...").
- Tests: `tests/macro_calendar/test_fred.py`. The fixture follows FRED's documented answer format; it is **not a live
  read**, because the key exists only as a GitHub secret. Mutations caught: key kept in the document, no future-date
  check, past years kept, non-200 accepted, wiring always unconfigured. The first live run after the secret is set
  proves the real answer.
- The workflow passes the secret; the fallback step follows judge 359 (`if: failure()`, quiet when the job spoke);
  `#` removed from step names (YAML read ` #fno-desk` as a comment and cut the names); `macro-calendar` added to O10's
  `capture-watch.yml` list.

## Real output sample (criterion 16)

The committed classes against the real MOSPI and Fed, with a local folder in place of Drive and dry-run receipts
and alerts, 16 Oct 2026:

```
mospi: 29 dates, last 2027-03-29
fed: 16 dates, last 2027-12-08
receipts: (dry run, local folder)
bls: calendar NOT read: us_cpi, us_payrolls: no source configured (BLS refuses GitHub's runners; a FRED API key awaits the owner)
dry run, nothing sent; would send: (that line, as the alert)
exit 1
45 rows -> 24 forward events; next five: [('2026-10-28', 'india_iip'), ('2026-10-28', 'us_fomc'), ('2026-11-12', 'india_cpi'), ('2026-11-30', 'india_gdp'), ('2026-11-30', 'india_iip')]
moved weekend dates: [('india_iip', '2026-11-28', '2026-11-30'), ('india_cpi', '2026-12-12', '2026-12-14'), ('india_iip', '2027-02-28', '2027-03-01'), ('india_iip', '2027-03-28', '2027-03-29')]
```

## Builder self-review (quality rule 3)

A review agent read the diff (correctness and silent failures):
1. **Blocking, accepted:** a new financial-year file would have "withdrawn" the old file's unreleased March dates,
   and an older file served again would have withdrawn every future date. Fixed: each snapshot carries the
   document's period, and only a date inside it can be withdrawn. Tests and mutation.
2. **Should fix, accepted:** weekend planned dates (4 of the 13 future ones) are not the real release days (the
   footnote; "Released on" lines confirm it). Fixed: moved to Monday, printed date kept. Public holidays are not
   known here (a stated limit).
3. **Should fix, partly accepted:** a withdrawn date uses A6's moved-meeting form (`scheduled=False`), which a reader
   could mistake for an event that happened. A6 has no "cancelled" type and `events.py` is frozen, so the form stays.
   Its description now says "WITHDRAWN ...: no release on this day", and the module says to read these events only
   through `known_on`/`in_window`. Nothing consumes them yet; the first consumer's story must follow that.
4. **Minor, accepted:** FOMC dates are US dates. This is said in the code and the text.
5. **Minor, accepted:** unexpected PDF errors (any `PyPdfError`, `KeyError`, `TypeError`, `AssertionError`) are now
   `CalendarFailed` rather than a crash.
The agent found no silent exit-0 path.

## Gates

On the unshallow clone: 7410 passed; ruff check and format clean; `check_imports.py` and `check_records.py` clean.

## Honest limits

- **The run fails every day until US CPI/payrolls have a source.** That is deliberate (never silent), but it costs a
  daily alert, and under O10's go-live gate it counts as a failure. Options for the orchestrator: the owner's FRED
  key, or remove the unconfigured line and record the gap once as a decision.
- MOSPI public holidays (a planned weekday that is a holiday) are not moved; the real day may be one later.
- The parser fixture is the ARC's text as pinned pypdf extracts it. The record scan refuses binary files, so the PDF
  itself is not committed; the PDF path is tested with a PDF built by hand in the test.
- No consumer reads `macro_events` yet (M1, F3 and the packs read A6's `events.csv`): wiring them in is a separate
  decision, because it changes a scored forecaster.
- `announced_on` is a late bound: the date was public at least by our first snapshot, maybe earlier.
