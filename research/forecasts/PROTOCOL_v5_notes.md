# Protocol v5 notes: changes waiting for the next protocol version

Changes found while protocol v4's freeze is in force. Each one touches a file v4 checks byte for byte, or one
recorded in a freeze, so it cannot be made until v5 is written. This file is not a rule: v5's own text decides.

Opened 22 Oct 2026 by the OSS1 review (`docs/OSS_REVIEW_2026-10-22.md`, `reviews/claude/response_319_oss1-findings.md`).
Each note names its files, the freeze that holds them and what to do.

## 1. One Brier score, not two

- **Files:**
  - `fno/forecast_scoring/scores.py` `brier(p, outcome)` is `(p - o)^2`, with no range check.
  - `fno/forecast_v4/loss.py` `brier(probability, outcome)` is the same square, but refuses a probability outside
    [0, 1] (`LossInputError`).
- **Held by:** both are in v4's `BYTE_CHECKED_GLOBS` (`fno/forecast_scoring/v4/freeze_check.py`).
- **For v5:** keep one function, the checked one from `loss.py`, and import it in `scores.py`. Then re-run G4's
  golden scores to prove that no number moves. They should not move, because the checked version only refuses
  inputs that should never occur.

## 2. One implied-volatility inverter for spot Black-Scholes

- **Files:**
  - `fno/analytics.py` `implied_vol(...)` is a spot-BS bisection, with bounds 1e-4 to 5.0 and a stop at 1e-6.
  - `fno/research_engine/implied_vol.py` has `ImpliedVolModel.implied_vol` (B1), with bounds 0.01 to 2.00 and a stop
    at 1e-9, and `SpotBlackScholes` already prices with `analytics.bs_price`.
- **Use:** `analytics.implied_vol` has **no caller** in `fno/`, `tests/`, `tools/` or `research/` (checked 22 Oct).
  It is dead code.
- **Held by:** `analytics.py`'s SHA-256 is recorded in `research/2026-10-12-experiment-1/FREEZE.md`, and
  `implied_vol.py`'s in v1's and v2's freezes and v4's `RECORDED_NOT_CHECKED`.
- **For v5:** delete `analytics.implied_vol`, and record the new SHA-256s in v5's freeze.

## Not a duplicate: C4's own Black-76 (keep it)

- `fno/checks/validity_pricing.py` has its own `norm_cdf`, Black-76 and bisection on purpose. Judge 83 (must-fix 3)
  required C4 to recompute stress "with C4's own Black-76", and `tests/checks/test_validity_independence.py` forbids
  it from importing B1.
- What keeps it equal to B1 is a test, not shared code. `tests/checks/test_pricing_reference.py` holds B1, C4 and
  spot BS to vollib's prices within 1e-9 rupees on a 288-row grid (OSS1 part a).
