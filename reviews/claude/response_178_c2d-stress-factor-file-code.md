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

## Judge 188 note 1 (fixed)

Of two rows with the same `as_of`, the later one in the file wins: the file is append-only, so it is the correction.
C2 and C4 both use a stable sort on the parsed date and take the last row. Test
`test_of_two_rows_with_the_same_date_the_later_one_wins` covers the later row first in the file and last in the file.
Planting the old `max` fails it in each reader.

## Builder self-review (quality rule 3)

One independent review agent, given only the diff (`6353bf68..1fbcb2ff`), the passed text and these claims. It ran
the full suite on its own worktree (6,191 passed) and probed both readers with 16 planted files. What it found, and what
I did after checking each:

1. **Must-fix, accepted.** An unreadable row (empty factor, a bad or date-time `as_of`, a short row) raised a raw
   `ValueError` or `TypeError`. In C4 that escaped the whole check run, because `multiplier()` catches only
   `FactorProblem` and `_run` only `MarginProblem` and `PricingProblem`. In C2 it was refused without the file's name,
   and a short row escaped `RiskManager.evaluate`. A14c appends this file unattended, so this is a real path.
   **Fixed:** both readers parse every row first, and any unreadable row refuses by name ("stress_factor.csv row N").
   Tests: 7 bad-row cases in C2 and C4, plus one end-to-end test each through C4's `check()` and C2's
   `RiskManager`. The 19 new cases fail on the old readers.
2. **Should-fix, accepted:** a NaN or infinite factor passed `< 1`. **Fixed:** `math.isfinite` in both readers, tested.
3. **Should-fix:** a same-date tie took the first row. Fixed as judge 188 note 1 (above).
4. **Should-fix, accepted:** the latest row was picked by comparing date text, and `fromisoformat` also took
   `20261020`. **Fixed:** only `YYYY-MM-DD` is accepted (`STRESS_FACTOR_DATE`, `strptime`), and rows are ordered by
   the parsed date. The compact and date-time forms are tested.
5. **Minor, accepted:** the record said `multiplier` and mixed the row's `as_of` and `status` into the margin
   figures. **Fixed:** the margin-room verdict carries `stress_factor_row: {as_of, factor, status,
   evidence_sha256}`, the story's names, pinned in `test_manager.py` and `test_margins.py`.
6. **Should-fix, accepted:** stale text. **Fixed:**
   - `research/data/margins/README.md` now describes the C2c formula and k from the file, with a section on
     `stress_factor.csv` (columns, append-only, YYYY-MM-DD, the later same-date row wins, any bad row refuses);
   - C4's module text;
   - the register row ("strictly before").
7. **None:** no other code reads the old config fields.
8. **Note, stated here:** a decision dated 14 Oct 2026 has no factor (the seed is dated 14 Oct, and the rule is
   strictly before). No decision record exists for that day, so nothing changes. "The switch changes no figure"
   holds from 15 Oct.
9. **Minor, accepted:**
   - `fno.risk.stress_factor` is now named in the C4 independence guard's list;
   - the test helper's temporary folder is removed at exit. It stays module-level, because module-level settings
     need the files at import, so `tmp_path_factory` cannot be used.
10. **Note:** `fno/constants.py` is at exactly 350 lines (the limit), so the next constant needs a split. I did not
    split it here.

## What this means for the owner (reasoning)

Nothing changes in any figure today. From A14c's first weekly row, k moves without anyone editing config: a rise
applies the next session, and any fall waits for the owner.

## Gates

On the final tree after judge 188's note and the self-review fixes: `python -m pytest -q` 6,209 passed (11 min 55 s);
`ruff check fno tests tools` and `ruff format --check` clean; `python tools/check_imports.py` clean;
`python tools/check_records.py` clean (6,022 files). The first round (8c0c9fdc) gave 6,186; the new cases are the
tie, bad-row, NaN/inf and end-to-end tests.
