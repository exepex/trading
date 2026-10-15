# Response 178: story C2d code, C2 and C4 read the stress factor from A14c's file (claims for the judge)

**Branch:** `story/c2d-stress-factor-file`, built on `story/c2c-whole-margin-stress` (C2c's code is with the judge;
C2d merges after it). **Text:** judge 176 addendum 2 PASS (`da699ce8`). **Lane 1** (money and risk).

## What changed

- **`config.yaml` `risk.stressed_margin`:** `method: multiplier`, `factor_file:
  research/data/margins/stress_factor.csv`, `max_age_days: 30`. `multiplier`, `source` and `as_of` are gone, and are
  refused at start-up (`fno/risk/settings.py`, `FACTOR_MOVED_TO_FILE`), so two sources can never disagree. The config
  comment states the owner's 15 Oct decisions (whole margin; automatic with an alert; any fall waits for the owner).
- **The seed row** `research/data/margins/stress_factor.csv`, exactly as the text says:
  `2026-10-14,1.45,,,applied,"owner seed: response 77, decision 14 Oct",,` under A14c's eight columns
  (`fno/constants.py` `STRESS_FACTOR_COLUMNS`, `STRESS_FACTOR_STATUSES`).
- **C2:** `fno/risk/stress_factor.py` (new, 52 lines): `factor_in_force(path, day, max_age_days)` returns the latest row
  with `as_of < day`, refusing by name a missing file, a wrong header, no row before the day, a factor below 1, an
  unknown status, or a row older than `max_age_days`. A held row's `factor` (the old one) is read as written.
  `MultiplierMargin` reads k through it; `StressedMarginSettings` holds `factor_file` instead of the three values.
- **C4:** `fno/checks/validity_factor.py` (new, 37 lines): its own reader by the same rule (story C4 forbids C2 code
  in `fno/checks/validity*.py`, and a shared reader would let one bug pass both checks). `MarginSettings` holds
  `factor_file`; `multiplier()` turns a `FactorProblem` into C4's `MarginProblem`.
- **The record:** `MultiplierMargin.record(day)` adds the row used (`as_of`, `multiplier`, `status`,
  `evidence_sha256`) to the margin-room verdict of every decision; without a day (the decision record's static
  block) it names the method, what is stressed and the file. `ScenarioLookupMargin.record` takes the same optional day.
- **Dead code removed:** `_optional_date` (C2 settings) and `_date` (C4 settings), now unused.

## Criteria

1. **Point in time** (`tests/risk/test_stress_factor.py`, C2 and C4): rows 14 Oct (1.45) and Sun 8 Nov (1.50);
   6 Nov and 8 Nov use 1.45, 9 Nov uses 1.50; the 8 Nov row is not used on 8 Nov itself.
2. **Fail closed by name** (C2 and C4): no file, wrong header, no row before the day, below 1, unknown status, day 31.
   **Boundary:** 13 Nov (day 30) passes, 14 Nov (day 31) refuses. A held row keeps 1.45 in force.
3. **The seed row:** the repository file is byte-checked; C2 and C4 read it (the quoted `peak` parses).
4. **Single source:** `multiplier`, `source` or `as_of` under `stressed_margin` is refused at start-up.
5. **No figure changes at the switch:** with the repository seed, a 15 Oct decision on NSE's real 14 Oct rows gives
   C2c's figures in C2 and C4 (SF 100 86,854.01; SC 300 98,012.27; BF 300 85,661.75; CCS 300 52,260.42).
6. **The record names the row:** `tests/risk/test_manager.py` pins the static block and the margin-room row.

**Mutations** (each alone, reverted; each caught): `<=` for `<`, no age check, and newest row ignoring the day, in C2
and in C4 (6 of 6).

## Test changes (no assertion loosened)

- The tests that set k in config or settings now write a one-row factor file (`tests/stress_factor_files.py`), dated
  the day before their decision day, because a row on the decision day itself is no longer used (the C2d rule). The
  figures they check are unchanged.
- `test_margins.py`: "unset, expired or future" becomes "expired (day 31), same-day or future" plus "no factor_file",
  each with its named reason; the record test reads `record(DAY)`.
- `test_manager.py`: the repository-factor tests read the repository's file by absolute path; their first valid day is
  15 Oct (was 14 Oct, the seed's own date), and day 30 (13 Nov) and day 31 (14 Nov) are unchanged.
- `test_validity_limits.py`: "multiplier is not set" is now a missing `factor_file`.
- `test_rules.py`: the test double's `record` takes the optional day.
- `tests/checks/validity_sources.py` (shared by the checks and decisions tests): the factor is dated the day before
  `FILE_DAY`, the decision day of those tests.

## What this means for the owner (reasoning)

Nothing changes in any figure today. From A14c's first weekly row, k moves without anyone editing config: a rise
applies the next session, and any fall waits for the owner.

## Gates

On the final tree: `python -m pytest -q` 6,186 passed (12 min 50 s); `ruff check fno tests tools` and `ruff format
--check` clean; `python tools/check_imports.py` clean; `python tools/check_records.py` clean (6,016 files). A first
full run found 5 `tests/decisions` failures: their shared source dated the factor on the decision day itself, which
C2d no longer uses; `tests/checks/validity_sources.py` now dates it the day before, and the rerun is the one above.
