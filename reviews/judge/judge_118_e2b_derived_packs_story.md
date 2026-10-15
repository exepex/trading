# Judge 118: story E2b text, derived quote figures only in the committed packs and desk records (quality rule 1; judge C)

Date: 15 Oct 2026 (UTC). Branch `story/e2b-derived-packs` at **dd0be6a1015eea8de880b1a0cc43f9049fcd21cc** (text only:
`docs/stories/E-paper-desk.md`, E2b). Checked against:
- the owner's "8 A" and "6 A";
- the orchestrator's decisions 26-27;
- the code on `main` (c428867 and later): `snapshot_inputs.py`, `market_checks.py`, `execution_costs.py`,
  `records.py`, `entries.py`, `execution_capture.py`, `live_pack.py`;
- A4b (judge 111).

## Verdict: FAIL (text), 2 should-fix; 2 minor

**The design is right:**
- **Decision B is right.** The builder's 648/648 finding means per-contract mid plus spread is the raw quote in another
  form, so leaving per-contract figures out is the only way to honour "8 A" in substance.
- **The reader table is complete.** My grep over `fno/` and `tools/` finds exactly the readers it names:
  - `quote_bid`/`quote_ask` in `fno/scorecard/execution_costs.py:61-63` only;
  - pack `option:` items in `fno/checks/market_checks.py:38` only (C3's spot);
  - the forecast v2 pack (`fno/forecast/live_pack.py:133-139`) reads `spot` from the A4 quote rows, not the desk pack,
    so E2b does not touch it.
- **C3's per-chain spot is right.**
  - The recorder writes one `chain.spot` on every row of a chain (`fno/quotes/recorder.py:270`), and C3 today takes the
    set of distinct spots across option items. So `spot:<expiry>`, one per chain, gives C3 the same set by
    construction.
  - Refusing a chain whose rows carry two spots is a correct new guard (today two spots inside one chain would pass
    unnoticed into C3's set).
  - Criterion 2's boundary list (2% and 0.2% at, under and over; none; one chain) is the right regression.
- **No frozen file.** No file it names is in experiment 1's `FREEZE.md`, the G1 v1-v3 freeze records or S1's draft
  list (S1 lists `fno/desk/timetable.py`, which E2b does not touch).

## Should-fix

**1. The unwind publishes both sides of one contract, so criterion 3's "no other column" is false for it.**
- On a failed hedge E4 buys the protective leg at the **ask** (`FILL_OPEN`), then unwinds it at the **bid** of the
  **same** snapshot (`FILL_UNWIND`, `fno/desk/entries.py:147-153`). Both rows go to `desk_fills.csv` with their prices,
  so that contract's bid and ask are both published.
- The event row's `legging_cost_rs` carries the same information: (ask − bid) × units plus charges.
- **Fix:** either name this as the one exception (a failed-hedge day, one contract, both sides) and put it to the owner
  with the orchestrator's fills-in-the-journal question, or keep unwind pairs out of the public journal. Then add a
  test that only an unwind pair can reveal both sides.

**2. Before A4b, E6 cannot read the touch it now depends on.**
- E6's half-spread would read the 15:15 execution snapshot "through the hash-checked store". Before A4b merges, that
  CSV exists only in the run's local quote folder, uncommitted by E2b's own criterion 4.
- So any E6 run outside that checkout (a later session, CI, the scorecard job) reports every fill "touch unknown". The
  reported half-spread would be empty, quietly, for as long as A4b is open.
- **Fix:** make A4b (or the Drive store) a stated dependency of criterion 3 and merge E2b after A4b. Or state that,
  until A4b, the scorecard runs only in the capture's checkout, and that the count of "touch unknown" fills is printed
  on the scorecard so an empty figure is never silent.

## Minor

1. Criterion 3: the scorecard's own output (`fno/scorecard/report.py`) should print the number of "touch unknown"
   fills next to the half-spread, so an excluded fill is visible to the owner, not only in a test.
2. Criterion 5: also test a `.CSV` case variant and a path reached through `..` or a symlink into the Groww folder,
   since the guard matches paths.

## The A4b fit

- Both stories change `fno/desk/execution_capture.py` the same way, and the story says the later merge keeps one
  version.
- Criterion 4 tests the behaviour (record and sidecar, never the CSV), so either merge order is checkable.
- With should-fix 2 the order becomes A4b first.

**Verdict: FAIL for dd0be6a1015eea8de880b1a0cc43f9049fcd21cc** (story text) on should-fixes 1-2. A re-check needs only
criterion 3, the dependency line and the A4b paragraph.
