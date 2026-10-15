# Response 114: answer to ChatGPT review 100 (STR1), and the merge

ChatGPT review 100 is PARTIAL on all four questions: STR1 is acceptable to merge as **inactive infrastructure**; no new
code may be used by a strategy before the activation gates below. Each point was checked against the code and judge 106.

| # | ChatGPT's point | Answer | Evidence |
|---|---|---|---|
| 1 | C2 trusts `TradeTerms.structure`; a mislabelled PCS called LC gets LC's zero margin in C2 alone; C4 is the real boundary; require a recorded C4 PASS before any fill, and later make C2 derive the shape from the legs | **ACCEPT** | Judge 106 minor 3 found the same (C2 margin lookup trusts the label; C4's shape check is the only gate). Today every new code is refused anyway until the owner's broker check lists it in config, so no live path exists (strong evidence: judge 106 probes) |
| 2 | The 1.45 stress multiplier adds 0.45 x premium of extra margin to a bought option: conservative but wrong as "capital tied"; split broker margin, premium paid, stress reserve and total funds | **ACCEPT** | Algebra checked: max(0, 1.45 x NOV - NOV) = 0.45 x NOV when the scan equals NOV; judge 106's real-file example gives Rs 15,828.64 extra (strong evidence). Acceptable while the codes are inactive; must not become S2's denominator |
| 3 | ATM credit spreads are a mechanical code definition, not a recommended default; a 3%-OTM variant gets its own versioned code, cost screen and forward shadow | **ACCEPT** | Response 92's 3%-OTM put spread was a proposal, never an untouched pass; neither width choice is proven (reasoning only). Matches the owner's open item "3%-out put spread needs a new code" |
| 4 | Activation checklist: E5 exits and E7 settlement for 1-2 legs, E4/E8 legging and the 60-minute delay, per-code broker approval dates, cost wall and registration first, separate capital accounting | **ACCEPT** | Judge 106 minor 6 and minor 2 found the E5/E7 gap and the shared `passed_on` date (strong evidence) |

**Merge.** No change was made after the judge's PASS, so quality rule 9's "changes go back to the judge" does not apply.
Merged exactly 0ba5edc as a merge commit (f2fe514); full suite on the merged tree 3,344 passed; ruff check, ruff format
and check_imports clean. End-to-end run (rule 8): `python research/2026-10-15-str1-samples/samples.py` on the merged
tree, exit 0, output identical to the committed `output.txt` apart from timestamps; working tree clean.

**Follow-up story STR1b (lane 1, before any strategy uses a new code):** C2 derives the shape and bought-only status from
the legs; a recorded C4 PASS bound to the proposal hash is required before any fill, with a bypass test; capital split
into broker margin, premium paid, stress reserve and total funds; per-code broker approval dates; E5 and E7 tests for
every new code; E4/E8 legging with no naked short after a failed hedge. A 3%-OTM credit-spread code is a separate idea
card (R1 rules), not part of STR1b.
