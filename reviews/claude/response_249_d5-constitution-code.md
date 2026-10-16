# Response 249: story D5 code, Book 3's constitution and strategy registry (code round, lane 1)

Builder: Claude, 16 Oct 2026 (IST), branch `story/d5-constitution-code`. **It is built on D4's branch**
(`story/d4-envelope-code`, response 247, with judge B), because D5 uses D4's changes to C4: `validity_modes(root)`,
`RegisteredComponents`, and the proposal's new fields. It merges after D4. Owner, 16 Oct (DESK_DECISIONS row 239):
built, judged and switched off. **Nothing is switched on:** no `book3/` folder exists, so every Book 3 trade fails C4
("no constitution file matches the registered D6 component").

## Files

- New:
  - `fno/book3/constitution.py`: allowed keys, references instead of numbers, the hash of the bytes;
  - `fno/book3/spec_rules.py`: a spec against the constitution;
  - `fno/book3/registry.py`: `register`, `require_registered`, `edited_rows`;
  - `fno/book3/wiring.py`: a new composition root, listed in CLAUDE.md;
  - `fno/checks/validity_constitution.py`: `ConstitutionMode`.
- Changed:
  - `fno/checks/validity_proposal.py`: the field `strategy_id`;
  - `fno/checks/wiring.py`: Book 3 maps to `ConstitutionMode`;
  - `fno/checks/validity_modes.py`: `WaitsFor` removed, now that no book uses it (no dead code);
  - `fno/research_engine/ledger.py`: one B4 helper, `Git.commits_touching`.
- Tests:
  - `tests/book3/`: 24 tests, on temporary git repositories;
  - `tests/checks/test_validity.py`: "Book 3 waits for D5" becomes "Book 3 fails closed without a registered
    constitution".

## Criteria

| # | Where | Test | Evidence |
|---|---|---|---|
| 1 | `require_registered`: committed at the checked commit, proposed before the decision day | same session refused; written but not committed refused; next session passes; an unregistered id refused at C4 | strong (tests) |
| 2 | spec hash, the on-disk copy against the committed one, and **the spec's git history** | an edit on disk refused; a committed edit refused, **even one that keeps the rule's hash** (a comment) | strong |
| 3 | `constitution_problems` at registration; `_holding_problem` at C4 on the trade's own exit | a structure outside the list refused; a spec window over the limit refused; a trade exiting 10 days after entry against a 9-day constitution refused at C4 | strong |
| 4 | `served`/D6 component `constitution`; C4 picks the file whose hash D6 names | a constitution not matching its D6 component refused | strong |
| 5 | `edited_rows` over every committed version of the registry | a committed rewrite of a row is found and the strategy refused | strong |
| 6 | `parse_constitution` | an extra key; a number for `risk`; another scoring path, underlying, expiry, sources or code; 30 days | strong |
| 7 | `ConstitutionMode.checks(proposal, evidence)` | its signature has no objection input, so an objection cannot block (by construction) | some: a test of the interface, not of a decider (F6 owns the decider) |
| 8 | `register` adds a `book3:<id>` row to the research ledger's `book3_ai strategies` family | two variants both count | strong for the family. The confirmatory-claim gate is the scoreboard's, not D5's |

Mutation checks, run and restored. Each of these makes tests fail:
- the same-session rule removed (2 tests);
- the spec-history check removed (1);
- C4's own holding check removed (1);
- the edited-row check removed (1).

## Deviations from the passed text (for the judge)

1. **There is no `registered_in_commit` column.** A row cannot name the commit that adds it. The registering commit
   is read from git: the row must be in the registry as committed at the checked commit. Strong evidence: that is how
   B4 proves registration.
2. **C4 checks against HEAD.** C4 runs before the decision is committed, so "committed at HEAD" means strictly before
   the decision's commit. D6 repeats the strict check at scoring. The text's "strict ancestor of the decision commit"
   is met by the pair.
3. **The holding limit is checked twice:** on the spec's window at registration (`max_days - exit_days_before_expiry`)
   and on the trade's own exit at C4. The text named one check; the trade-level one is needed because D2's window is
   not checked again at C4.
4. **"non-NIFTY" and "weekly" cannot be written at all.** D1's format has no underlying field and accepts only
   monthly expiries today. The constitution's own checks stay as the second guard.
5. **Criterion 7 is met by construction** (C4 has no objection input). Testing that a decider ignores objections is
   F6's.
6. **Criterion 8:** D5 makes the trial family complete. Refusing a single-trial confirmatory pass is the
   scoreboard's job, when one exists.

## Changes to other owners' files

- C4's `validity_proposal.py` and `wiring.py`;
- B4's `ledger.py`: one read-only `Git` method.

Both go through the orchestrator.
