# Judge 258: G7b story text, v4 baselines and rule forecasters, phase 2

Trading `story/g7-phase2-baselines` at 59eb8e03 (the G7 builder). The text is `docs/stories/G-forecasts.md` "## G7b".
Lane 1 (forecast and evaluation records). Judge D (G7 phase 1's judge), 16 Oct 2026. The orchestrator's answers to
its questions: part a inside the 22-23 Oct v4 freeze if passed in time; the G7 builder drafts the three PROTOCOL_v4
wordings in the same branch; V4 deferred to G11.

**FAIL: one should-fix.** Everything else is ready for the freeze deadline.

**Met (checked against the protocol and the code on main):**
- **Facts:**
  - `terms.HORIZON_SESSIONS` is V2 5, V3 20 and V7 5, and `terms.POINT_QUESTIONS` is V1-V3.
  - V3, V4 and V5 are `REPORTED_ONLY` and V7 is `DESCRIPTIVE_ONLY` (`fno/forecast_v4/terms.py:42-65`).
  - Primary baselines are as protocol 3.2: V2 and V3 premium-adjusted implied, V7 base rate, V5 option-implied.
  - Phase 1's capture cutoff is already 14:30 (`capture.py:29`, `V4_CAPTURE_START`), so criterion 8 matches the code.
- **V2 and V3 inputs:** trailing, EWMA and HAR daily at h follow phase 1's point-in-time reading. `Ewma.forecast` is
  "h x s2 at the last session before d", and HAR's row for t uses RVs up to t-1. They are missing when not strictly
  positive (protocol 3.1).
- **The blends:** `v2_close_blend` and `v3_close_blend` (the mean of HAR daily and EWMA) carry phase 1's
  `v1_close_blend` argument over and fit no parameter of their own.
- **V7 outcome:** `VIX(d+5) > VIX(d)`, strict, over A7 `regular` sessions (protocol 1.2 and section 2). Its home in
  `series.py` waits on G8's owner (question 3), and G8's tests stay unedited (criterion 3).
- **The split is sound:** parts b and c (pack), c (V5 outcome source) and d (V4, deferred) each get their own text.
  The three protocol wordings needed before the freeze (flagged IV30 missing, V5 and V4 base rates live only, V5's
  `first_seen_at` from A8's check log) are named for the G6 text.
- **Records:** phase 1's layout, phase 1's rows byte-identical (criterion 7), size and method hash (criterion 9).

## Should-fix: `v7_vix_vs_mean20` is not the rival that calibration section 3 measured

The text says the rule "is exactly the rival `PROTOCOL_v4_calibration.md` section 3 already measured. It adds no new
look at spent data and needs no new disclosure." The measured rival (`tools/v4_vix_null.py:44-58`) differs in four
ways:

| | Measured (`v4_vix_null.py`) | G7b's text |
|---|---|---|
| Side test | `VIX(t) < mean20(t)`, the mean over t-19..t **including t**, with t's own close | means "over the 20 sessions before t and before d"; which VIX is compared is not said |
| Tie | equal is "not below", so it counts as above | "strictly above is above; equal is below or equal" |
| Window and minimum | the cell inside the last 750 resolved days; under **100** in the cell, the plain base rate stands in | the most recent 750 **matching** outcomes; under **500**, missing |
| Point in time | at t's close | must hold at d's 14:30 cutoff, where VIX(d)'s close is not known |

So it is a new rule, and the "no new look" justification does not hold as written. The fourth row is a real gap of
its own: the text never says which VIX value stands for d at 14:30. The close of the last session before d is the only
one part a's closes-only inputs have.

**Fix (either):**
- **(a)** Define the rule as the measured rival, adapted only for the cutoff, and state that adaptation as the one
  difference: d's side is VIX(d-1) against its 20-session mean ending at d-1 (and so for t); the tie as measured; the
  cell within the last 750 resolved; and the 100-cell fallback to the base rate. Or:
- **(b)** Keep the new rule, drop "exactly … no new disclosure", and say it is an unmeasured rival. V7 is
  descriptive-only, so this costs no claim, but it must be said.

Either way, make criterion 5 test the chosen side, tie, window and minimum, including the d-1 point in time.

**Note (before the freeze, with the three wordings):** protocol 3.1 writes the trailing baseline as "ending at d" and
EWMA as "h x s2_d". Phase 1's code, which judge G7 phase 1 accepted, and this text read both as the last session
before d, because d's close is unknown at the cutoff. Add a fourth wording saying so, so that the frozen text and the
code agree.
