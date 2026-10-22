# Judge 506: MS-P1a3, unmeasured sizes and the ledger reader (second judge)

**Scope:** story/ms-p1-contracts-a3 at 9ede0d1e (on main 52facc92). Judge I (session_01MvZneCLZqBuiGyNxawdVee), the
second judge (money piece); Judge B passed it (479.3), and I did not read that verdict. Lane 1. Round 1 of 2.

**Verdict: FAIL.** 1 should-fix. No live path is affected today; the contract's own fake contradicts the rule it adds.

## Checked
| Point | Result | Evidence |
|---|---|---|
| `SlotQuote.sizes_measured` | MET | `snapshot.py:27-36`: default True; False requires no sizes; `two_sided` then needs prices only. 3 of 3 plants caught (the size guard dropped, sizes ignored, default False) |
| `SIZE_NOT_MEASURED` sits in `TRADE_VALIDITY` | MET | `constants.py:91`; `TRADE_VALIDITY` is the complement of a's split; `test_law_split.py` updated |
| `LedgerReader` | MET | `accounts.py:105-110`, with `check_ledger_reader` and 5 bad readers caught. d's `SchoolAccounts.entries` (judge 498) fits it |
| Judge B's warning: does a live path now accept an unmeasured quote? | **none today** | Nothing on this tree builds a `SlotQuote` with `sizes_measured=False`: the only producer, `roads/capture.py`, takes the default, and a missing size there stays `two_sided` False. My probe of d's real `SchoolFills.enter` on unmeasured quotes refuses it (with `one_sided_quote`: E4's check sees no size) |
| Gates | MET | full `pytest -n auto` 11,666 passed, 16 xfailed, 0 failed; ruff, check_imports and check_records clean |

## Finding
1. **Should-fix: the reference fake fills an unmeasured quote, and no conformance check says a fill port must refuse one.**
   - `FakeFills._fill` (`fakes.py:149-153`) fills on `two_sided` alone. My probe: `FakeFills.enter` on unmeasured quotes returns filled legs.
   - The contract says such a live fill is `SIZE_NOT_MEASURED`, and design A (orchestrator) says only a practice-flagged rule may map sizes; without the flag, the fill is refused.
   - Parts i and j test against these fakes, so a fleet test would pass on fills that the real port refuses.
   - Fix expected:
     - `FakeFills` refuses a quote with `sizes_measured=False` with `SIZE_NOT_MEASURED` (on entry; an exit waits);
     - `conformance.check_fill_port_unmeasured` pins that the reason is `SIZE_NOT_MEASURED`, for entry and exit, and the fake passes it.
   - **Merge-order condition:** d's real port today answers `one_sided_quote`. It passes the new check only with d's part 4, so d's conformance test against it lands with part 4, and a3 must not be read as "d already refuses by name".

## Plants
3 planted, 3 caught. Plus 2 probes: d's real port refuses, the fake fills (finding 1).

## Notes
- b's quality gate and the drivers also read `two_sided`, so unmeasured quotes from the simulator count as observed and tradeable there. That is intended for practice only, and it is safe only while no live source sets the flag. j should refuse a live run that receives such a quote.
