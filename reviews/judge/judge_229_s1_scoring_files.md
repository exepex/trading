# Judge 229: S1 item 15, the scoring files in `frozen_files` (judge A, lane 1, before S1's freeze)

**Checked:** `story/s1-scoring-files` at `1ca9fe801d86e2e4920d9686da0c155c2521a435` (the R2/G7 builder). The diff is
2 files:
- `research/evaluation/PROTOCOL.md` `frozen_files` gains a "Scoring files" bullet with 25 `fno/scoreboard` modules;
- a new `tests/evaluation/test_scoring_files_frozen.py`.

The orchestrator asked whether the builder's known limit is acceptable before a freeze: scoring's dependencies in
`fno/desk`, `fno/risk` and `fno/accounting` are left unhashed.

**Verdict: FAIL, 1 should-fix, no blocking.** The list and its test are correct for `fno/scoreboard`. But the limit
is not acceptable as it stands, because scoring recomputes figures at score time with unhashed code.

## What is right

- All 25 modules of `fno/scoreboard` except `__init__.py` and `cli.py` are listed by path. This is needed, because
  `frozen_targets` hashes only the backticked paths.
- The test fails when a scoreboard module is added and not listed (the planted removal of `t_check.py` in its third
  test). It also fails when a listed path is not a file.
- Nothing else in S1 changes. The Status stays "decided by the owner on 2026-10-14", which is right, because the item's
  own rule adds "the scoring code of S2, S3 and S6 … before the freeze".
- On the trial merge with main (judge 227's freezer lines and this bullet merge cleanly),
  `python -m fno evaluation check` prints S1 and the gate complete.

## Should-fix

**SF1. Scoring calls unhashed code that computes the scored figures, so an edit after the freeze changes every
counted score while `verify` stays silent.**
- **Evidence:**
  - `fno/scoreboard/standard_unit.py`, S3's standard unit, which is the score's denominator and is shared with F9,
    calls `price_leg` from `fno/desk/pricing.py` (lines 54 and 71), `SettlementPrices` from `fno/desk/settlement.py`
    and `HeldMaxLoss` from `fno/risk/open_risk.py`, at score time.
  - `random_control.py` calls `price_leg` and `HeldMaxLoss`.
  - `book_trades.py` uses `trade_line` from `fno/accounting/ledgers.py`, which charges with `fno/costs.py`.
  - `sources.py` uses `snapshot_marks` from `fno/scorecard/scorecard.py`.
  - `HeldMaxLoss` in turn rests on `risk/trade_costs.py`, `risk/buckets.py`, `risk/inputs.py`,
    `research_engine/cycle_costs.py` and `research_engine/structures.py`.
  - None of these is in `frozen_files`. Only their settings are: `config.yaml:risk` and `:charges`.
- **Path in normal running:** the risk code changes often (C2, C5, and the C2c whole-margin and C2d stress-factor
  rounds of the last two days). A change to how `HeldMaxLoss` computes a held position's maximum loss after S1's
  freeze would change S3's standard unit, and so every book's matched score, for decisions already counted. The
  freeze's hashes would not move, and `verify` would report "unchanged". That is exactly what the owner's option A
  forbids: "code written after decisions are seen could be shaped by them, so the code is hashed with its rules before
  anything is counted".
- **Why "the owner's rule names S2, S3 and S6's scoring code" does not settle it:** these functions are S3's scoring
  computation. `standard_unit.py` only calls them. A literal reading by package leaves the arithmetic out.
- **Cost, said plainly:** hashing them couples S1 to desk and risk code. Any later edit to those files after the
  freeze then needs a new S1 version, by the item's own rule. That is the price of principle 4, but it is a real
  trade-off. The full import closure of `fno/scoreboard` is about 170 modules, which is far too broad to hash.
- **Expected fix** (one of two; the owner's call, through the orchestrator):
  1. **Recommended (reasoning only).** Add the score-time computation modules to the bullet: `fno/desk/pricing.py`,
     `fno/desk/settlement.py`, `fno/risk/open_risk.py`, `fno/risk/trade_costs.py`, `fno/risk/buckets.py`,
     `fno/risk/inputs.py`, `fno/research_engine/cycle_costs.py`, `fno/research_engine/structures.py`,
     `fno/accounting/ledgers.py`, `fno/costs.py` and `fno/scorecard/scorecard.py`. Then extend the test: every
     `fno` module that `fno/scoreboard` imports a function or class from is either listed or in an explicit
     exemption set with a one-line reason. Data shapes and readers (`desk/records`, `desk/snapshot`, `books/versions`,
     storage) can be exempted.
  2. **Or** the owner accepts the limit in a DESK_DECISIONS row that names the unhashed modules and what they can
     change, and the limit is written into the `frozen_files` Reason, not left in a message. As built, the limit is
     recorded nowhere in the repository: the commit touches only the bullet and the test.

## Gates

- On the trial merge with origin/main fb86612c (tree 430a2c0, clean), `-n auto`: pytest 6924 passed.
- `ruff check` is clean, `ruff format --check` shows 1226 files formatted, and `check_imports` is clean.

**A re-check needs the extended bullet and test (option 1), or the owner's row and the Reason line (option 2).**
