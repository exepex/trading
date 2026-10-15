# Judge 173: A14c story text (the stressed-margin factor recomputed from NSE's SPAN files), rule 1

**Verdict on c6c2b97f3df4011a6004f2774f2731e196614a21 (`story/a14c-stress-recompute`, text only): PASS.** No blocking
or should-fix findings and three notes.

Applied: `docs/JUDGE.md` rule 1; the owner's rules "keep the design simple" and "one builder per function".

## The finding the story carries: checked and true

- **The code.** `fno/risk/margins.py` (docstring and `_span`) multiplies only the scanning risk:
  `max(0, k x scan - NOV) + min(0, NOV) + exposure`.
- **My recomputation from response 77's 14 Oct table.**
  - SF 100: unstressed 822.25 + 59,077.07 = 59,899.32; stressed 1.45 x 822.25 + 59,077.07 = 60,269.33, which is +0.62%.
  - SC 300: 71,427.59 / 67,594.67 = +5.67%.
  - Every BF row: 0%, because NOV covers the stressed scan.
- **What it means.** 1.45 was measured on the whole margin (response 77: "today's method", scan plus exposure), but the
  rule applies it to a part that is 1-14% of the margin. Today's crash buffer is about 0-6%, as the story says (strong
  evidence).

## The orchestrator's four points

1. **Criterion 1 (reproduce 1.127 within 0.001): sound, with one dependency to name (note 1).** 1.127 is response 77's
   Sep-Oct 2026 window (29 entries, BF 100). The criterion's "or explain each difference with the files' figures" is
   right for a hand-run reference.
2. **The 2020 short-option minimum: acceptable as written.**
   - SPAN takes the larger of the scan figure and the minimum charge.
   - Response 77's own caveat says 2020's margins "simply tracked the index (+26.5% from 7 Apr 2020)", with the
     minimum binding for all structures alike (1.265). Whenever the minimum binds, the held rise equals the index's
     rise, whatever the exact aggregation.
   - Criterion 4's "by hand" test is written by the same builder as the rule, so it is not independent (note 2).
3. **The four owner questions: fair, each recommendation labelled.**
   - Q1 gives both options with their costs. The report gives both figures until the owner decides. "Recommended: B"
     is marked reasoning only.
   - Q2-Q4 are balanced. Q3 keeps the owner setting every risk value (A for now), and the run lands about a week
     before expiry.
   - One balance point: note 3.
4. **The 13 Nov lapse timeline: correct.**
   - `_factor` refuses when `(day - as_of).days > max_age_days`. With `as_of` 2026-10-14 and 30 days, 13 Nov is day 30
     and still valid; from 14 Nov C2 refuses every trade.
   - The plan (text by about 20 Oct, build and back-fill by 3 Nov, first run 6 Nov, owner and judge by 11 Nov) leaves
     two days of margin. That is tight but stated.

## Notes (one line each where they go)

1. **Criterion 1 needs September 2026 files that are not in Drive yet.** The archive starts on 1 Oct 2026
   (`research/data/manifests/span-bod.csv`, first row 2026-10-01), and response 77's 2026 window has entries from
   September. Say that criterion 1 runs after the back-fill of question 2. If the owner picks "every day since 2020",
   it covers this.
2. **An independent anchor for 2020 and 2024, cheap once the back-fill exists.** Extend criterion 1 to also reproduce
   response 77's 1.265 (Jan-Apr 2020) and 1.407 (May-Jun 2024, BF 300 entered 5 Jun) within 0.001, or explain each
   difference. That checks the 2020 minimum's modelling against a figure the builder did not write. The 2024 window is
   today's binding value.
3. **Q1's option B, its effect said in numbers (for neutrality).** Under B, k = 1.45 on the whole margin raises a held
   SF 100 from about 59,900 to about 86,900 a lot. C2 would then refuse more trades for the same capital. The owner
   should see that cost beside B's benefit before answering.

## Coordination

The work register has A14c's own row (`fno/nse_margins/` later). Owner question 1's option B would be a separate C2
story, not built here. No duplicate with A14 or C2 work in flight.

## Addendum 1 (15 Oct 2026): revision at 83e7f6ef2a454c9832a7daf9ad4f2bd1328b2021 (owner's answers to Q1 and Q2)

**Verdict: PASS.** One note carried over.

- **Q1 and Q2: recorded, and the text follows them.** `docs/DESK_DECISIONS.md` has both 15 Oct rows: "Crash buffer
  applies to the whole margin" and "Stressed-factor recompute uses everything since 1 Jan 2020".
  - The run now measures the held rise of the whole margin C2 counts (`max(0, scan - NOV) + min(0, NOV) +
    exposure`, the "C2 counts" column of response 77's table), the same quantity C2c makes k multiply. The scan's own
    rise is reported for information only.
  - The back-fill covers every session since 1 Jan 2020 (about 1,700 files, about 16 GB).
  - Criterion 6 requires C2c to merge before any value from this run is entered, so the factor is applied as it was
    measured. Q3 and Q4 stay open with their recommendations, to be answered before the first value.
- **My note 1: met.** The full back-fill includes the September 2026 files that criterion 1 needs.
- **My note 3: moved to C2c**, where it belongs. C2c (branch `story/c2c-whole-margin-stress`) is the story that changes
  C2. Its text should state the effect on C2's room, for example a held SF 100 at about 86,900 a lot at k = 1.45 against
  about 59,900 today. I will check that when C2c comes to me.
- **My note 2: still a note.** Reproducing response 77's 1.265 (2020) and 1.407 (2024) as well as 1.127 gives the 2020
  short-option minimum an anchor the builder did not write. After the full back-fill it costs nothing extra.
- **On the builder's doubt about criterion 1.** Response 77's "margin (today's method)" is its table's "C2 counts"
  column, which is the quantity this revision now names. So 1.127 can be reproduced on that definition, and the
  criterion's "or explain each difference" covers any gap in response 77's hand run.

## Addendum 2 (15 Oct 2026): final text at 010adb2152581670de451fd7ff62bae3e9ed53bd (83e7f6e..010adb2)

**Verdict: PASS, with no notes left.**

- **Note 1: met.** Criterion 1 runs after the full back-fill and says why (the archive starts on 1 Oct 2026, and the
  2026 window has September entries).
- **Note 2: met.** Criterion 1 now reproduces all three of response 77's windows within 0.001, or explains each
  difference: 1.127 (2026), 1.265 (2020, the minimum binding) and 1.407 (2024, today's binding value). These are
  anchors the builder did not write.
- **Note 3: met.** Q1 states C2c's effect: a held SF 100 goes from about 59,900 to about 86,900 a lot (today's
  scan-only stress gives 60,269). "About 31% fewer lots" checks out: 1 - 1/1.45 = 0.310.
- **The decision commit.** Criterion 6 cites `d68b1a9c` ("Decision rows: … whole-margin crash buffer, recompute
  windows"), and that commit holds the two 15 Oct rows.
- **Still the owner's.** Q3 (who enters the value) and Q4 (NSE circulars) stay open, to be answered before the first
  value. C2c is with judge G.
