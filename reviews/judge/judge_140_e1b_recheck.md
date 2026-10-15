# Judge 140: E1b re-check on today's main: `story/e1-topup` 5e3e5bf840c83f83353a47907c67ffca39990114 (on top of judge C's PASS at ddcefcc, judge 110 addendum 2), judge A

**Number note.** `judge_110` is judge C's file, so I used 140, the next free number.

**Why there is a re-check.** E1b was merged onto today's `main` and 4 tests failed:
- `fno/constants.py` went over 350 lines after P1;
- P1's catalog test named `starting_cash`, which E1b renames to `capital`.

## The changes since ddcefcc (main merges aside)

| Commit | Change | Check |
|---|---|---|
| ee8ba24 | The budget constants move from `fno/constants.py` to a new `fno/budget/constants.py`. Seven budget modules and two tests import from it. P1's fixture reads `state.capital`. The story adds review 111's wording | The 20 removed lines and the added ones are identical, the same names and values: a pure move. No module imports a moved name from `fno/constants.py` any more (I searched `fno`, `tests` and `tools` for every moved name). It is CLAUDE.md's "module-specific constants at the top of their module" case. `fno/constants.py` is now 331 lines |
| 4fac898 | Re-pin to dashboard a696b4d. Three files change: `fno-paper-trades.yaml` (`opening_value` maps to `account_state:capital`), `blocks-home.yaml` and `blocks.json` (the books at Rs 20 lakh, judge 136) | All **33 pinned files**: the SHA-256 at dashboard a696b4d equals `pin.json`, and the trading copies are byte-identical (0 mismatches). The contract version stays 2.7.0 |
| 5e3e5bf | Merge of main f2ec754 | — |

**The story wording (review 111).** "Only capital is cut at the decision time: fills are not, so rebuilding a whole
account from the ledger as of a past time is not supported."
- This states a limit; it changes no behaviour.
- It is consistent with Book 1 replaying from stored inputs: no decision reads a past account state rebuilt from the
  ledger.

## Gates, run myself on a trial merge of 5e3e5bf with origin/main as of now (510d98f)

- `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`: **5565 passed, 0 failed**. The builder's one failure, the A16b
  verifier test, is fixed on main by c791051 and is included here.
- `ruff check fno tests tools`: clean;
- `ruff format --check fno tests tools`: clean;
- `python tools/check_imports.py`: clean.

### Verdict: PASS for 5e3e5bf840c83f83353a47907c67ffca39990114

- The constants move is a pure move.
- The re-pin is consistent with dashboard a696b4d.
- The fixture follows E1b's rename.
- The full suite passes on today's merged tree.
- Judge C's code verdict (110 addendum 2) stands for the rest.
