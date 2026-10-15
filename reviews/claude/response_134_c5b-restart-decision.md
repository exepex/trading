# Response 134: story C5b, a brake restart cites the owner's decision row (story text for the judge's check)

Builder: Claude, 15 Oct 2026. Branch `story/c5b-restart-decision` from `origin/main` (8b21876). Story text:
`docs/stories/C-code-roles.md` section C5b. Lane 1 (the brake: money and risk; `journal/` records). Text only; code
after the judge's check passes (quality rule 1).

## In short

- **A new column.** `owner_overrides.csv` gets a fifth column, `decision`: the exact bold title of a
  `docs/DESK_DECISIONS.md` row.
- **Five rules for a valid restart.** The cited row:
  - exists exactly once;
  - quotes the owner (`(owner: "`);
  - names the book;
  - is dated on or before the restart;
  - is not reused by another restart of that book.
- **Both checks, failing closed.** C2 and C4 check this with their own code. A bad row fails closed, the same way a
  malformed row does today.
- **The judge's audit decides the episode.** It reads the owner's words. No cryptography and no CI guard (owner's
  simplicity rule).

## Choices for the judge to check (reasoning only)

1. **Cite by the row's bold title**, not by a line number, which shifts as rows are added, nor by a hash. Titles are
   already unique in practice; a duplicate fails closed.
2. **"That episode" is left to the audit.** The code checks only "dated on or before the restart" and "not reused". A
   code rule for "after the brake fired" would need the episode's start date recomputed in two places. That extra
   machinery is what the simplicity rule asks us to avoid, and the judge reads every such row anyway.
3. **No migration.** No book has an `owner_overrides.csv` today.

## Questions for the owner

None.
