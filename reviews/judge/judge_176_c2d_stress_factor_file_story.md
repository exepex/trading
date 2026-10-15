# Judge 176: C2d, C2 and C4 read the stress factor from A14c's file, story text (judge G)

- **Judged:** commit `9857460d` on `story/c2c-whole-margin-stress` (builder session 01Vm1WnH8i9waM8EJG8zwWqg): the C2d
  section of `docs/stories/C-code-roles.md` and one work-register row. The branch head `6e280a4a` adds only response
  163. This is lane 1 (C2's and C4's margin input), at quality rule 1. The orchestrator gave the go; 176 was the next
  free number on main.
- **Owner decisions, relayed 15 Oct** (DESK_DECISIONS rows to follow):
  - the factor is applied automatically, with an alert;
  - every fall is held;
  - a factor below 1.0 is refused;
  - a shrinking archive is refused.
- **Cross-read:** the A14c text on `origin/story/a14c-stress-recompute` (lines 1118-1192), today's `config.yaml`
  `risk.stressed_margin` and `fno/risk/settings.py`.
- **Verdict: FAIL (text).** One should-fix (the seed row would poison A14c's first incremental run), plus 3 minor.
  The rest is right and simple.

## The orchestrator's points

1. **C2 and C4 agree.** Both read one file by one rule. Criterion 4 pins the switch to today's figures on every 14 Oct
   row. Criteria 1 and 2 run each test on both C2 and C4. That is enough.
2. **Point-in-time read for replays.**
   - "The latest row with `as_of <= d`" is a true point-in-time read, provided `as_of` is the day the row became
     available. A14c defines `as_of` as the run day, and the run is the Sunday 10:00 IST job, a non-trading day. A
     weekday decision therefore never shares its date with a row written after it.
   - The 7 Nov / 8 Nov replay test is right.
   - A manual weekday re-run is the only exception (note 3).
3. **Fail-closed paths.** All of these refuse by name:
   - no file;
   - a wrong header;
   - no row on or before the day;
   - a factor below 1;
   - a row older than `max_age_days`.

   A `held` row uses its stored `factor`, which A14c defines as the old factor kept ("the row keeps the old factor").
   The two stories agree. `config.yaml` with `multiplier`, `source` or `as_of` is refused at start-up (criterion 3),
   so there is one source.
4. **The 30-day lapse.** The seed 2026-10-14 plus 30 days gives today's lapse after 13 Nov, as the A14c timeline
   says. A weekly row leaves three missed Sundays before refusal (A14c). See minor 4 on the exact boundary.
5. **One reader or two for C4?** One shared reader is enough; I do not need two.
   - C4's independence matters for computation: the formula and the margin check, which stay duplicated, with C2c's
     C2 = C4 agreement test and mutations in both copies.
   - `k` is an input that both must read identically. A second reader of the same file by the same rule would only
     add code and a way to drift (row 156).
   - The shared reader's own tests (criteria 1-2) cover point in time and fail closed.

## Findings

### Should fix

1. **The seed row's `computed` and `unrounded` would feed A14c's incremental rule.**
   - A14c: an incremental run "computes only the entries whose holding ended since the last run's newest entry and
     takes the larger of that and the last `unrounded`".
   - The seed row puts `unrounded` = 1.45, a hand value (response 77's binding window was 1.407, under the scan-only
     method), and it has no "newest entry".
   - **Path:** the first automatic run, about 6 Nov. Taking the larger of a fresh max and the seed's 1.45 makes 1.45 a
     permanent floor of the measured series. The weekly result then never shows the true whole-margin maximum, and A14c
     criterion 8 (incremental = full) fails on real data.
   - **Fix:** in C2d's seed row, leave `computed` and `unrounded` empty and mark the row as the owner's seed. For
     example, `peak` = "owner seed: response 77, decision 14 Oct". C2's reader needs only `as_of`, `factor` and
     `status`.
   - A14c then states that its first run, or any run whose last row has no `unrounded`, is a `--full` run. One line in
     each story, plus a criterion: "the seed row is read by C2 and C4 and ignored by A14c's incremental rule (test)".

### Minor

2. The seed row's `peak` text contains a comma ("three windows, owner decision"), so it must be quoted in the CSV.
   Otherwise the header and column check fails on the seed itself.
3. A manual A14c run on a weekday would write `as_of` = that day, which a replay of that day's 14:30 decision would see.
   That run is not part of normal running, so this is a note. One line would close it: C2 uses rows with
   `as_of < d`, or the job always dates rows to the run's own day and runs only on non-trading days.
4. Criterion 2's 30-day lapse needs its boundary: day 30 passes and day 31 refuses, as today's
   `(day - as_of) > 30` does.

## Project rules

- **Scope:** this changes only where `k` comes from. C2c's judged formula is untouched. There is no order path and no
  secret.
- **Order and register:** the register row names the right files (`fno/risk/settings.py`,
  `fno/checks/validity_settings.py`, `config.yaml`). The order (after C2c, before A14c's first run and STR1b-2) is
  right.
- **Simplicity:** a single data file read by one function is the simplest design that keeps any job from editing
  `config.yaml`.
