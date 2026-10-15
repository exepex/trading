# Judge 116: A17b story text, guards before any consumer reads a global cue: `story/a17b-cue-guards` ba95c561e0b841f3fb99758d0951bdd854548923 (quality rule 1, text only)

**What I checked:**
- The A17b section of `docs/stories/A-data-foundation.md` at this SHA, the only file changed.
- It against my judge 103 minors 1-5, judge 100's A15 minors and the orchestrator's design points.
- The US 10-year table's dates, against the stock-market calendar the story proposes.

## What is right

- **Coverage of the findings.** Every judge 103 minor (1, 3, 4, 5) and judge 100 minor maps to a scope item and a
  criterion. FBIL stays an owner item, recorded.
- **The shape of a reading.** `reading_for` returns a status, an age and an expected date. Callers must refuse `stale`
  and `none`, and a `behind` must be stated in a caller's own rules. That is the right contract, and `value_for` stays
  unchanged for research.
- **The 4-day US limit.** It covers a Monday holiday (Friday's close read on Tuesday) and Good Friday (Thursday's
  close read on Monday).
- **Muhurat in the label.** Muhurat is not an open, and every committed row stays `backfilled`, so no past label
  changes.
- **`adopt`.** It cross-checks Drive's creation time within 10 minutes, refuses when the store cannot give it, and
  does one real check on the four copies.
- **Failed attempts capped at 3 a day,** with times and outcomes only in the log.
- **The unscheduled NYSE closures listed** (2 Jan 2007, 29-30 Oct 2012, 5 Dec 2018, 9 Jan 2025) are the ones I know
  of since 2007. Each must carry its source, as the story says.

## Should-fix (text)

1. **The US 10-year is not on the NYSE calendar.** The story gives the S&P 500, the Nasdaq 100 *and* the US 10-year
   their expected date from NYSE rules. The Treasury follows the bond market (SIFMA) calendar instead. The committed
   `us10y.csv` shows the difference both ways:
   - **No value on days NYSE trades:** Columbus Day (14 Oct 2024, 13 Oct 2025) and Veterans Day (11 Nov 2024,
     11 Nov 2025).
   - **A value on days NYSE was closed:**
     - Good Friday 3 Apr 2015, 2 Apr 2021 and 7 Apr 2023;
     - 29 Oct 2012 (Hurricane Sandy, day 1);
     - 2 Jan 2007 (President Ford);
     - 9 Jan 2025 (President Carter).

   So the US 10-year would read `behind` after every Columbus and Veterans Day, and on those Good Fridays its value is
   *newer* than the NYSE expected date. Fix: give the US 10-year its own calendar (SIFMA's recommended closes, sourced),
   or treat it like USD/INR, a stated simplification that can only read `behind`. Check its archived dates against
   whichever calendar it uses.
2. **The statuses overlap, and one case has no status.**
   - **`current` vs `stale`.** "`current`: the value is the expected date's" and "`stale`: older than `max_age_days`"
     can both hold. After Hurricane Sandy, Friday 26 Oct's close is the expected value on Wednesday 31 Oct, at
     **5 days**, above the 4-day limit. After Ford's mourning day, 29 Dec 2006's close on 3 Jan 2007 is also 5 days.
   - **A Tuesday after a US Monday holiday is exactly 4 days.**
   - **Fix:** state the precedence. A value of the expected date is `current` whatever its age; `stale` applies only to
     a value older than the expected date and beyond `max_age_days`.
   - **Newer than expected:** the US 10-year on Good Friday, or USD/INR when RBI publishes on an NSE holiday, gives a
     value newer than the expected date. The text gives it no status. Name it, for example as `current`, and record
     that the expected date was wrong.
   - **Brent** has "no expected date; age only". Say which statuses it can take (`behind` or `stale`, never
     `current`), so a caller cannot mistake an 8-day-old Brent for a fresh one.
3. **The archived-calendar test cannot read the private tables.** "A test checks the archived US tables against the
   calendar", but the S&P 500 and Nasdaq 100 tables are in Drive only (owner decision a927390), and CI has no Drive.
   Say how this runs:
   - as a command against Drive, with its result (dates and counts only) recorded in the claims; or
   - from a committed dates-only list. Trading dates are public facts, but the owner's Drive-only rule covers the
     tables, so a dates-only list needs the orchestrator's call.

   The US 10-year can be checked in CI from its committed table.

## Minor (text)

1. USD/INR's expected date says "the previous NSE weekday". Say whether that means an NSE *session* (the A7 calendar)
   or Monday to Friday. The two differ on NSE holidays.
2. FBIL trails a week, so with an NSE-day expected date it reads `behind` almost always. Say so, since it only fills
   RBI's 2018-2022 hole.
3. Criterion 1's 27 Nov 2026 case needs the US calendar to cover 2026, including Thanksgiving week. Fine, but name
   that dependency.

## Verdict: FAIL for ba95c561e0b841f3fb99758d0951bdd854548923 (story text)

Three should-fixes, all in the text:
- the US 10-year's calendar;
- the status precedence and the newer-than-expected case;
- how the private-table calendar check runs.

Code may start once they are fixed. The re-check needs only the A17b section.
