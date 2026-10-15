# Epic RM: the real-money gate and the small real-money test

Roles: statistician, risk manager, F&O trader, tax and cost accountant, compliance. Goal: the rules that decide when
real money could ever be considered are written and frozen before any counted paper result exists, so no result can
shape them. Nothing in this epic places, modifies, cancels or enables a real order. Story template and definition of
done: `docs/IMPLEMENTATION_PLAN.md`.

---

## RM1. Real-money gate, frozen before the first counted paper decision

**Repository:** trading · **Issue:** #107 · **Lane:** 1 (the real-money gate; JUDGE.md rule 9: judge, then ChatGPT,
then the owner)

**Description:** As the owner, I want the real-money pass mark and the small test's rules fixed and hashed before the
first counted paper decision, so that I can never be talked into real money by a pass mark written after seeing the
results.

**Context and why:** Design v2 8.3 and 8.4; owner decision 8 (15 Oct 2026, accepted) and its amendment ("B ... =>
I accept": selection-adjusted evidence always; a paired real-vs-paper test with a prediction interval); principle 4
(14 Oct 2026: "a pass mark for real money is written before results and never lowered because time passed");
decision 168 (do-nothing gate); ChatGPT reviews 97 and 98 (the exact sample, statistic, interval and execution
constraints belong in RM1's frozen text before counted evidence); judge 158 (RM1 must say how several books'
`beats_index_after_tax` values combine).

**Scope.** In:
- `research/evaluation/REAL_MONEY_GATE.md`: the seven conditions of 8.3 and the test of 8.4 as items in S1's item
  format, each with an exact value or rule (draft on this branch);
- the gate listed in S1's `frozen_files`, so S1's freeze hashes it and S1's `order` check proves it precedes every
  counted decision (one freeze, one order check; no second freeze tool);
- the gate's evidence is only Book 1 positions counted under the protocol version that holds the gate (the
  decision's commit has that freeze as a strict ancestor); pilot and shadow positions are shown, never counted
  (judge 171 SF1);
- S1's freeze refuses while the gate is incomplete or any gate item is not decided by the owner; `python -m fno
  evaluation check` also checks the gate.

Out:
- computing the gate (eligibility report) and recording real fills: RM2, after a version reaches the gate;
- any order, broker call or setting that could place one;
- S6's `beats_index_after_tax` and E8's fills (read by the gate, built by S6 and E8);
- the crash-replay engine (condition 3(b) names the windows and data; the replay is built with the first version
  that reaches the gate).

**Expected design (after a text PASS):**
- `fno/evaluation/gate.py` (new, small): `GATE_FILE` and the gate's required items (the 12 keys of the draft).
- `fno/evaluation/completeness.py`: `completeness_problems` and `undecided_items` take the required-item list as a
  parameter (default S1's), and `completeness_problems` takes `require_version` (default true; false for the gate),
  so one checker serves both documents (DRY). The gate has no version line of its own: it is versioned and frozen
  with S1.
- `fno/evaluation/freeze.py`: `_checked_text` also checks the gate (complete and decided) and refuses by naming each
  problem. `cli.py`'s `check` prints the gate's result as a second line.
- `research/evaluation/PROTOCOL.md`, `frozen_files`: adds `research/evaluation/REAL_MONEY_GATE.md` and
  `fno/evaluation/gate.py`. This changes an owner-decided item's list (as the scoring-code addition already
  foresees), so it goes to the owner as question Q10. S1's text owner (session 0185gR5DmoDh2zBAvgRU4CEB) makes that
  one-line edit; RM1 does not edit `PROTOCOL.md`.
- No new composition root: no outside service is touched.

**Acceptance criteria:**
1. The gate file has an exact value or rule for each 8.3 condition (1-7) and each 8.4 element (account, cap, lot,
   duration, paired pass, prediction interval, slippage, drawdown stop, slippage stop), each traceable to its source
   row (judge checks the table in response 163).
2. `python -m fno evaluation check` reports the gate complete; it rejects a missing gate item, an empty field, an
   evidence label outside the three, or "to be decided" and its kin, naming the item.
3. `python -m fno evaluation freeze` refuses while any gate item's status is not "decided by the owner on <date>",
   naming the items; the refusal writes no record and no ledger row.
4. A freeze with a complete, decided gate writes the gate's SHA-256 into `FREEZE_v<n>.md`; `evaluation verify`
   reports a later edit of the gate as changed.
5. The gate's two owner numbers of 8.4 (account size, per-trade cap) carry the owner's written decision and date
   before the freeze (decision 8): criterion 3 enforces it mechanically.
6. The gate's terms define the evidence record by S1's version rule (Book 1 only, decisions after the freeze) and
   measure every slippage from the paper price before pad (judge 171 SF1, SF2); `real_test_sample` keeps 8.4's
   registered number (SF3). Checked by reading, traced in response 163.
7. No code path reads the gate to place, modify or cancel an order, and no broker write is imported (the
   `check_imports` rule and a test that `fno/evaluation/` imports no provider or broker module).
8. Files stay under 350 lines; `fno/evaluation/freeze.py` stays one class with one job.

**Test plan (each criterion with a broken-code proof, rule 4):** completeness on a fixture gate (missing item, empty
field, bad label, "tbd"); freeze refused on an undecided gate (no record, no ledger row), freeze written on a decided
gate with the gate's hash; `verify` flags a one-byte gate edit; the import test; the real draft gate passes
`check` (complete) and fails `check --decided` (not decided) until the owner answers.

**Judge verifies:** the text against 8.3, 8.4 and the decision rows (criterion 1's table); each owner question is
asked with options, never answered by the builder; the freeze refusal by planting an undecided status.

**Known limits:**
- The gate is frozen with S1, so changing it later is a new S1 protocol version (the intended cost: no quiet edit).
- S1 v1 cannot freeze before the owner answers RM1's questions; a slow answer delays counted paper evidence (Book 1
  keeps trading as pilot evidence meanwhile).
- Shadow records never count toward the gate until a later story extends S1's order check to them.
- `fill_honesty` needs A16 snapshots, which cover only the nearest weekly and monthly NIFTY expiries.
- The gate's conditions read data that does not exist yet (E8 fills, S6's benchmark, A16 snapshots); missing data
  counts as "not met", never as a pass.

**Depends:** S1 (draft built), S6 (text on main), E8 (story) · **Size:** S · **Status:** story text and draft gate
revised for judge 171's three should-fixes; code waits for a text PASS, ChatGPT and the orchestrator's go
