# Response 177: story S3, scoreboard A code (claims for judge G)

Branch `story/s3-scoreboard-a`, head **3e626db71cc3d10522aefaad7ed4f554fe35d3dd**. The text passed in judge 168
addendum 1. Builder: session 0185gR5DmoDh2zBAvgRU4CEB, 15 Oct 2026. Lane 1.

## What was built

| Story part | Code | Evidence |
|---|---|---|
| Design 1: actions | `fno/scoreboard/matched_actions.py` (take, skip, not observed) and `matched_days.py` (common set, pack hash, the reasons a day is not observed) | strong: real record fields and rule names checked |
| Design 2: standard unit, shared with F9 | `fno/scoreboard/standard_unit.py`: one lot, E4 `price_leg`, C1 `Order` charges, time exit from the pack's `exit_day`, retry at later snapshots, E7 settlement | strong (tests) |
| Design 3: scores | `fno/scoreboard/matched.py` and `matched_board.py`: Σnet ÷ Σmax loss by decision day, series cut at the first open take, pairs both ways with risk 1, Holm on the head-to-head claims, pilot and D6 segments | strong (tests) |
| Design 4: output | `python -m fno scoreboard a`; the board goes to `research/scoreboards/A/<date>.json`, which is git-ignored and pushed to Drive by E2c's `PrivateFiles` | reasoning only (wiring) |
| Design 6: miss cap | 10%, counted from the book's first collected run. Days with no snapshot, no common pack, D6-unscored days and pre-F7 days sit outside the cap | strong (tests) |
| Judge G note (a) | `uncertainty.holm(p_values)` takes a plain list; F9 can pass its own | strong (test) |
| Judge G note (b) | `uncertainty.py` is split into `resampled_ratios`, `lower_bound` (same bytes of output), `p_value` and `holm`; no S2 test edited (`git diff` on `tests/scoreboard/test_*` shows only new `test_matched_*` files) | strong |

## Signatures F9 imports (orchestrator: tell F9 if they change)

- `StandardUnit(snapshots, sessions, settlements, held: HeldMaxLoss, charges, lot)`.
  `.value(legs: Sequence[DeskLeg], entry_day, exit_day, on) -> StandardResult(status, net, max_loss, exited_on, note)`.
  The status is one of `closed`, `open`, `not filled` or `maximum loss unknown`.
- `uncertainty.resampled_ratios(series)`, `p_value(series)` and `holm(p_values, alpha=0.05) -> list[bool]`.

## Decisions made in code (judge, please check)

1. **One-lot maximum loss** is B2's held-position model (`HeldMaxLoss.of_legs`, new public method, behaviour preserved).
   It includes the Rs 1 a unit exit pad and the exit order's brokerage even at zero value. For one long call bought at
   100 x 75 it gives Rs 7,615, not the 7,595 I first wrote by hand. It is conservative, the same figure C5 uses for held
   positions, and stated here.
2. **Criterion 8's example was wrong in the story text.** It now matches design 3: an open take ends the series
   before its day. The text change is in this branch.
3. **"inputs" (the same trade already open in the book)** is an account limit and counts as a take. This is found by
   self-review, and the story's list did not name it.
4. **"No common pack"** is its own not-observed reason, outside the cap. The story did not name it. A day with a
   snapshot but no pack is the desk's failure, not the book's.
5. **Pairs both ways.** "X beats Y" and "Y beats X" are separate claims, and both enter Holm.
6. **A book with no collected run yet is "not started",** not "undecided, operations" (Book 2 today).
7. **Lot size** is `config.yaml` `lot_sizes.NIFTY`, the desk's own figure.

## Gates (on the branch merged with main as of 71a1de30)

- **pytest:** 6,174 passed, 3 failed. All 3 fail identically on a clean origin/main worktree:
  - the G7 count test, fixed on `fix/g7-v6-counts-fixed-date` (4b9309dd, merging as lane 2);
  - two tests that read accounts moved to Drive by E2c (routed to E2c's builder).
- **ruff check and format:** clean. **check_imports:** clean. Every file is under 350 lines (largest:
  `matched_board.py` 160).
- **Broken-code proof:** 20 mutations, all caught.
  - The first set: account-limit rules, the C4 block, paper_account, exit side, settlement, unfilled entry, the open
    cut, pair risk, the Holm boundary, the miss-cap boundary, the pack hash, Book 3 via F7, and late runs.
  - Added after self-review: the pair sample in positions, pairs both ways, unscored days outside the cap, not
    started, inputs, the settlement error, and pairs in Holm.
  - Three survived at first (C4 block, late run, then unscored, inputs and settlement error); the tests were
    strengthened until all were caught.

## Self-review

One independent agent found 1 must-fix and 7 should-fix points, all applied:
- the pair sample counted days;
- unscored days were inside the cap;
- "not started";
- pairs were one-way;
- "inputs" was read as a skip;
- a missing pack was labelled as no snapshot;
- duplicated sign and charge logic (now C1's `Order`);
- a settlement error crashed the board.

It confirmed the record fields, rule names, pack hash (sha256 of the file bytes, as `book1_inputs` reads it) and cash
signs against the code.

## Known limits

- Book 3 is "undecided, F7 not built" until F7 exists, and F7's entries must name the structure and the pack hash.
- Daily differences are in rupees and not risk-normalised (response 144 item 23); the per-book ratio is beside them.
- No real board yet: no paper fill exists. The run on today's records gives every book "not started" or F7.
