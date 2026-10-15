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
