# Response 126: story G8, protocol v4 scoring (story text)

Branch `story/g8-scoring`, from main 36d2db8. Text only: `docs/stories/G-forecasts.md` section G8. Code starts after
judge D's PASS.

## What I checked before writing (evidence labels as the project uses them)

- **Every rule G8 needs is already in `fno/forecast_v4/`** except the owner's crash-share cut (strong evidence: code
  reading). `confirmatory.judgeable` has only the 5-day gate; the cut exists only in `tools/v4_crash_cut.py` (a
  study), and the protocol's section 11 E still lists three options. The owner chose option 2 on 15 Oct
  (`DESK_DECISIONS.md`). Proposed to the orchestrator: one function beside `judgeable` and one protocol line, so it is
  frozen with the protocol.
- **The thresholds live in `tools/`, not `fno/`:** V1 and V2 use `claim_threshold` and `futility_threshold`, V6a and V6b
  use `v4_brier_bands.operative_thresholds` (the banded rule of revision 5; `v4_brier_regimes.operative_thresholds`
  is the superseded revision 4). `claim_threshold` takes the look's rate and divides by 15 itself (strong evidence:
  code; calling it with rate / 15 would square the correction).
- **Runtime** (some evidence, one run here): 17 s (V1 claim, n = 125), 7 s (V1 futility), 56 s (V6b, band 5-7), so a
  look of up to 12 judged members takes minutes. V1's claim threshold at n = 125 came out 1.1e-12, as the protocol
  says (effectively unreachable).
- **The 13+ band at n = 125:** 13 / 125 = 10.4% > 10%, so the cut makes it unreachable; usable from n = 130 (strong
  evidence: arithmetic).

## Choices, for the judge

1. **G8 resolves outcomes** for V1-V3, V6 and V7 (one place); asked the G7 builder through the orchestrator whether
   G7 does too. V4 and V5 are out: they need A16 ATM quotes and expiry-settlement wiring (reasoning: no real input
   exists yet).
2. **Calibration slope and intercept** are an OLS of the outcome on the probability, the same function as
   Mincer-Zarnowitz (DRY; reported only, never a verdict). A logistic recalibration is the textbook alternative;
   not chosen because it changes no decision (owner's rule).
3. **Seed words** of non-member comparisons: `16 + crc32(question/forecaster) mod 2^31`, stable when forecasters are
   added (reported sensitivities only).
4. **Futility uses the gate set and its own n** for the threshold (the protocol's 5.5 defines futility on the gate
   set; the tools calibrate at the n they are given). For Brier questions both sets are the same.
5. **Before the freeze nothing is written as a look record**; every output says EXPLORATORY.
