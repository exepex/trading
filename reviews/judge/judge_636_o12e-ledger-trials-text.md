# Judge 636: O12e, ledger trial numbers claimed in blocks, story text round 1

Branch `story/o12e-ledger-trials` at `cf62172e4` (section "O12e" of `docs/stories/O12-number-claims.md`, register
row). **FAIL, lane 1** (3 should-fix, 1 minor). Text only; judge session 01BvZZzF4XR48qNHNxLydQhf.

## Criteria

| Item | Verdict | Evidence |
|---|---|---|
| Seeded history equals main's `research/ledger.csv` | MET | my script on main: 108 rows, ids 1-108, no gaps, no duplicates, no non-numeric id; the runs of one experiment are exactly the 16 named (1, 2-17, ..., 100, 101-108) |
| Every path registers inside a claimed block | NOT MET | findings 1 and 3 |
| The Book 3 exemption is safe | NOT MET | finding 2 |
| A full block | MET | the freeze and `register` refuse it; a new block is claimed (criteria 3-5) |
| No write-once record edited | MET as designed, but finding 1 leaves one half-written | the design adds `numbers/` rows and a pin only; `ledger.csv` rows are not changed |
| Doc-reading tests and number check | MET | 932 passed, 13 xfailed; `check_numbers`: clean; only Markdown changed |

## Findings

1. **Should fix: a refused freeze leaves its write-once record behind.** `Freeze.freeze` writes `FREEZE_v<n>.md`
   (`fno/evaluation/freeze.py:160`) before `_register` (line 161). With the new rule ("refused when there is no block"),
   a refused freeze leaves the file on disk, and every retry is refused at line 152 ("exists: a change is a new
   protocol version"). Fix: the text says the trial id is chosen (or refused) before anything is written; add that
   to criterion 5, plus a plant that moves the choice back after the write.
2. **Should fix: the exemption covers every non-numeric id, not only Book 3's.** The text exempts "ids that are not
   whole numbers". `ledger.py` checks no id format (`read_ledger` 141-150, `register` 170-181), so `x109` or
   `edge2:1` would bypass both the guard and the check. Fix: exempt exactly `book3:<strategy_id>` with Book 3's own
   experiment (`book3/registry.py:95`, `TRIAL_FAMILY`). Any other non-numeric id is refused by `register` and flagged
   by the check. Add this to criteria 1 and 4.
3. **Should fix: a trial typed by hand into the ledger still runs outside a block until the merge.** The known limits
   say the check catches a hand-typed id "on the next push". But `checks.yml:10-14` runs only on pushes to `main` and on
   pull requests, and `require_committed` (`ledger.py:183-197`), the gate every run passes, needs only a local commit.
   The latest collision was itself hand-written: the v4 freeze's rows 101-108 came in commit 4c7187c8c with no code
   writing them. So a branch can still run on ids that clash with another branch, which is the failure O12e exists to
   stop. Fix: put the block check in `require_committed` too, for numeric ids not in the seed (or state why not, with
   the owner's acceptance). Add a criterion and a plant. Also reword "every writer goes through it": hand edits do not.
4. Minor: "the experiment starts with the block's name" lets block `edge2-f1` cover `edge2-f10-...`. Require the
   name itself or the name followed by `-`. Test both.

## Plants

None (text round). The text's own plant list should add: the choice made after the freeze file is written (1); a
non-`book3:` non-numeric id accepted (2); the run gate without the block check (3).

## Notes

- Who claimed a block cannot be proven: this is stated plainly in the text, and the claim tool's race handling is
  unchanged from O12.
- 115-120 `edge2-f6` is reserved by the orchestrator, not by a builder. That is fine, since F6's experiment must
  start `edge2-f6`.
