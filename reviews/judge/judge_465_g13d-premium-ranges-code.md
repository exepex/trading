# Judge 465: G13d code, each contract's next-session premium range (caeebfcd, response 317)

Judge B, 22 Oct 2026. Lane 1: a new story with forecast and score records, two O1 steps (null `live_from`), and
G13b's seal code made parameterisable.
- Builder: G13/G13b (session_01UkTaDeTRF9ksDgQB9cTU5C).
- The story text passed in judges 453 and 453.1.
- Number claimed with `tools/claim_number.py`.

## Verdict: PASS (notes only; note 1 should be added before merge)

## Criteria

| Story item | Result | Evidence |
|---|---|---|
| The rule | MET | see "The rule" below |
| Not ranged, counted by reason | MET | no IV, the expiry on or before d+, no distribution, no ATM IV |
| Baselines | MET | `decay_only` and `no_change` are points |
| Outcome | MET | see "Outcome" below |
| Session-first scoring and the verdict | MET | see "Scoring and the verdict" below |
| Sealing | MET | see "Sealing and issue" below |
| O1 steps | MET | both steps placed as agreed with O1's owner; `live_from` null for both; the pinned-order tests are updated |
| Gates | MET | see "Gates" below |

### The rule
- `rule.py`: the forward quantiles are F·exp(-s²h/2 + z·s·√h) with h = calendar days / 365 (G13's `years`).
- Each contract is priced with Black-76 at its own IV (`iv_points / 100`), one step less, at G13's rate.
- A put's values are reversed, so the range is monotone.
- My plants each fail 1 test: the drift term dropped; "one day less" dropped.

### Outcome
- d+'s mid from G13's record of d+, two-sided quotes only, same source only.
- G13's filtered quotes are counted as "no valid two-sided quote". This is disclosed (deviation 3).
- My plants each fail 1 test: one-sided quotes used; a mismatched source scored.

### Scoring and the verdict
- Everything is averaged per session first, then G4's moving-block bootstrap runs over sessions.
- The verdict is the judged rule from judge 453.1, read only at 60, 120 and 250 sessions, each on its first L sessions.
- My plants each fail 1 test: sums instead of session means; a look reading every session.

### Sealing and issue
- G13b's `SealCheck` and `Seals` take `deadline_of` and the path functions, with G13b's defaults. G13b's method hash
  stays 8d7d7301, and its tests pass.
- G13d's deadline is 15:30 on d.
- The issue refuses at or after 15:30 (deviation 1, agreed with O1's owner). My plant (`>=` changed to `>`) fails 1
  test.

### Gates

| Gate | Result |
|---|---|
| `tests/premium_ranges` and `tests/price_ranges` | 117 passed |
| full suite (`-n auto`) | 9,671 passed, 16 xfailed |
| `ruff check fno tests tools` | clean |
| `ruff format --check` | clean |
| `check_imports` | clean |

### The real-data numbers are not a bug
I checked them against the index moves (`warmup_closes.csv`).

| Day | NIFTY move | In one-day sigmas at a 14% IV | The rule's coverage, 50% / 90% |
|---|---|---|---|
| 14 -> 15 Oct | +1.66% (VIX 14.63 -> 14.03) | about 2.3 | 0.00 / 0.14 |
| 15 -> 16 Oct | +0.65% | 0.9 | 0.17 / 1.00 |
| 16 -> 19 Oct | -1.1% over 3 days | 0.87 | 0.25 / 1.00 |

Each day's coverage is what a correct rule gives for that move.

## Notes (one line each)

1. **Sticky strike is untested.** The test builders use one IV for both the contract and the ATM, so replacing each
   contract's IV with the expiry's ATM IV (`build.py`) passes every test. That is half of the stated rule. Add one hand
   case with the contract's IV different from the ATM IV, before merge.
2. **For the owner: a session's coverage is close to all or nothing.** Every contract of a session shares the one index
   move, so its coverage is near 0 or near 1 (see the table above). Its spread across sessions is then near
   √(p(1 - p)), about 0.3 at 90% and 0.5 at 50%, not the 0.2 the story assumed.
   - Under exact calibration, and ignoring autocorrelation, an interval fits inside the bands only from about 96
     sessions (50%) and 138 sessions (90%).
   - So the 60-session look will almost surely say "not yet decided", and the 120 and 250 looks are the real ones.
     This fits the story's own warning; reasoning only.
3. **The step's runtime is not measured yet.** G13d's issue and G13's record share about 11 minutes after the card.
   Measure them before asking for go-live, as the builder says.
4. **The outcome is read from G13's record, not A4's chain directly.** Quotes G13 drops appear as unscored. This is
   disclosed; the counts will show the size.
