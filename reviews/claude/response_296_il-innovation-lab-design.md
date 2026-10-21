# Response 296: IL, the Innovation Lab design (story text for Judge E)

Builder: session_01FWkBH4zNAEFSEpjUzVEgnd. Story: `docs/stories/IL-innovation-lab.md`, branch `story/il-innovation-lab`.
Asked by the orchestrator after the owner's decision (DESK_DECISIONS 93e01804). Design text only; no code.

## What the text claims, and how I checked it

- **The map in section 2** comes from a read of the code, not of the story documents. A search agent read every
  module named in the table, and I re-checked its two weightiest findings myself:
  - **the R1/D5 ledger seam** (`fno/factory/registration.py:42` against `fno/book3/registry.py:95`): confirmed by
    reading both lines. I did not run it;
  - **RM1's `selection_adjustment`** (REAL_MONEY_GATE.md: the second untouched period is the only route; no
    0.05 ÷ m level): confirmed by reading it.
- **The gaps (section 3)** are only those the map shows: held-out history, one registry for every candidate kind,
  a judge results audit, demotion on statistical decay, the warnings output, one board, and the selector. Everything
  else is reused as it is.
- **One conflict with an owner decision is stated, not overridden.** The decision row asks for "a luck correction
  for the trial count", but RM1 (15 Oct) rejects a multiplicity level for real money. The text uses RM1's rule and
  asks the owner (question 1).

## Things the owner may not want to hear

- Most candidates will take a year or more to be proven, and many never will.
- A strategy that trades monthly needs years.
- The second period doubles every wait.
- AI shadows cost money for months at low odds.
