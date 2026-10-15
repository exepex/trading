# Response 115: STR1b activation gates (story text; claims follow with the code)

Branch `story/str1b-activation-gates`. Story text: `docs/stories/B-research-engine.md`, section STR1b.

## History of the text

- **53abdc0:** first text. Judge 115 FAIL, with 7 should-fix.
- **0462f71:** revised. The 7 should-fix were met, and addendum 1 added should-fix 8.
- **6b62348:** should-fix 8 added. Judge 115 addendum 2 PASS.
- **This revision:** trimmed under the owner's rule of 15 Oct 2026, "keep the design simple" (`docs/DESK_DECISIONS.md`),
  by the orchestrator's decision 65. Kept: the capital split, per-code approval dates, the margin-row check and the
  activation gate. The five guards that only a hand-made or buggy caller could need are dropped to Known limits.

## The dropped guards and ChatGPT review 100 (for ChatGPT and the owner)

Response 114 accepted all four points of review 100. Each dropped item, whether it traces to review 100, and why the
owner's rule now covers it:

| Dropped guard | Traces to | Why it now falls under "keep the design simple" |
|---|---|---|
| C2 rebuilds the labelled structure from the legs (with the "zero margin reads" spy) | **Yes:** review 100 point 1, the "better follow-up: have C2 derive bought-only status and the structure shape from legs" | A mislabel needs a proposal built by hand. In the normal running of the system, D2 builds every proposal through B2, so its label always matches its legs. If one did not, C4's independent shape check would refuse it, and E3 fills only on a recorded C4 pass. Review 100 itself called C4 "the safety boundary" and asked only that this be documented and tested, which judge 106 did. |
| Binding the C4 pass by hash to the exact proposal, book, version and rule | **Yes:** review 100 point 1, "a recorded C4 PASS bound to the exact proposal hash/legs, margin row and head snapshot" | E3 reads each order from the same committed D3 record that C4 checked, and the record's files are hash-checked against their commit (`DecisionStore.edited`). A different proposal under the same pass needs a hand edit, and the edit check already refuses it. **The margin-row part of the point is kept** (scope 3): A14 really appends rows between decision and fill. |
| A pass object at the fill primitive (`VerifiedPass`) | **Yes:** review 100 point 1, "an integration test that bypass attempts cannot open a trade" | The only code path that records an entry fill is E3's gate, through `EntryDesk.enter`. A bypass means new code that calls the fill directly, which would be reviewed by the judge as a lane-1 change anyway. |
| Static test listing every fill call site | **No:** judge 115 should-fix 6 (it narrows review 100 point 1's bypass test) | Same reason as the row above. |
| `apply_fill` refuses a close or settle that adds risk | **No:** judge 115 addendum 1, should-fix 8 | E4's exits and E7's settlement close only the holdings they read from the account. A risk-adding "close" needs a hand-built fill. |

**Evidence:** reasoning only, from reading the code paths: `fno/desk/daily_steps.py` `_fill_one`,
`fno/desk/recorded_c4.py`, `fno/desk/exits.py`, `fno/desk/execution.py` and `fno/books/account.py`. Judge 106 probed
the C4 boundary (54 planted naked shorts, every mislabelled shape refused).

**If ChatGPT or the owner disagrees:** the guard for points 1 and 3 of the table was fully specified in the text that
passed judge 115 (6b62348), so it can be restored from there.
