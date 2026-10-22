# Judge 479: MS-P1a, the market school pilot contracts

**Scope:** story/ms-p1-contracts at 756e6545 (builder session_01CmKJ6taCLzfEGg7wt6RC4N). Story MS-market-school.md
sections 3-4 and its Claims; design response 327 rev 2. Lane 1. Round 1 of 2.

**Verdict: FAIL.** There are 4 should-fixes. Criteria 1-6 and 8 are met. Criterion 7 (no order, Slack or Groww import)
is not proven. Three contracts that the parallel parts need are missing, so those parts would define them twice.

## Met (checked)
- **Gates (my run):** pytest -n auto gives 10244 passed and 16 xfailed. ruff check, ruff format, check_imports and
  check_records are clean. The largest file is 200 lines.
- **No forbidden files touched.** The diff touches only `config.yaml` (the `school` block), `fno/config.py` (one
  line), `fno/school/`, `tests/school/` and the story. Nothing touches DAILY_RUN_STEPS, v4 or a frozen file.
- **The `school` block is all off.** `enabled` and `reports` are false and `first_counted` is empty. The limits are
  10,000, 25,000, 1.2 lakh, 5, and 30,000 / 1.5 lakh / 50,000. A test pins them to today's book caps.
- **Write-once and deterministic.**
  - Canonical JSON with sorted keys, no NaN, -0.0 written as 0.0, and an int in a float field written as a float.
  - gzip time is zero.
  - `DashcamStore.seal` is the same for the same records, and other records raise `ReplayConflict`.
- **Seal before fill.** `Seal.covers` requires the same SHA-256 and pushed_at <= the fill time.
  `FillPort.enter`/`exit` take the seal, and `FillResult` is exactly one of filled, refused or state.
- **Banner** has 2 members. **OpportunityCounts** holds eligible >= fillable >= executed >= 0.
- **Records hang together.** A closed road is exactly a `road_closed` decision with the same reason, and a refusal
  carries its proposal.
- **Plants: 13 of my own, 11 caught.** Caught: a seal 5 minutes late, a seal of another file, executed above
  fillable, an open road without a snapshot, an empty fill result, costs above max loss, a law result without a
  reason, gzip time not zero, a bool accepted as a limit, a close without an exit reason, fake fills at mid.

## Should-fixes
1. **The import boundary misses relative and transitive imports (criterion 7).**
   - Defect: `test_boundaries.py` matches only absolute names. `from ...providers.groww import GrowwProvider` and
     `from ...alerts import slack`, planted in `fno/school/roads/`, both pass. The package itself uses relative
     imports (`contracts/roads.py`: `from ...quotes.recorder import DATASET`).
   - Defect: importing `fno.school.contracts` already loads `requests`, `fno.providers` and `fno.intraday.pacing`,
     through `fno/quotes/recorder.py`, just to read a dataset constant. The test's own FORBIDDEN list names
     `requests`, `fno.providers` and `fno.intraday`.
   - Test it must pass: each plant above fails the test. A fresh interpreter that imports every `fno.school`
     module finds none of the forbidden modules in `sys.modules`, or the claim names exactly which ones are allowed
     and why.
   - [reasoning only: resolve each relative import against its file's package; take the dataset names from a
     module that loads no capture code]
2. **The dashcam cannot be asked what is already sealed.**
   - Defect: `DashcamStore` has only `seal(records)` and `read(seal)`. Part j's "a rerun skips sealed decisions",
     part g's sections (a session's records) and part i's two-run comparator each need the seal of a (session,
     slot, kind) without re-deciding. Each would add its own lookup to c's class, outside the contract.
   - Test it must pass: a conformance check that the lookup returns None before `seal` and that Seal after, on the
     fake and on c's store.
3. **Tickets cannot relax "only the account limits" through the contract.**
   - Defect: part f must check tickets with the same laws, with only the account limits relaxed (3.3 and story f,
     including a driver stopped by the daily stop or brake: `TicketReason.DRIVER_STOPPED`). Nothing in `SafetyLaw`
     or the constants says which laws are account limits, so d and f would each decide it.
   - Test it must pass: one frozen definition, tested to be exactly bucket, open risk, new risk a day, margin room,
     daily stop and brake, and never protection, max loss or any quote-gate reason.
4. **No fleet contract for the harness.**
   - Defect: part i must make "the fake fleet" give each planted fault's exact reason code, and part j's real runner
     must then pass the same harness. There is no `FleetRunner` protocol and no fake fleet, so i must write its own
     loop in j's order (roads, gate, drivers, laws, seal, fills, ...), a second definition of j.
   - Test it must pass: a `FleetRunner` protocol (`run(session, mode)`) with a fake that passes a conformance check:
     one sealed outcome per scheduled (road, driver), decisions sealed before any fill.
   - [reasoning only: or the story drops i's fleet run until j exists]

## Notes (no action required)
- `OpportunityCounts` has no scheduled count, so a rate built from it alone would drop `road_closed` and
  `unavailable` from the denominator (3.5). g must count denominators from the decision records; worth a line in
  g's story.
- A refused ticket is a `REFUSED` decision, the same as a refused trade, so only f's counts tell them apart.

**Next:** fixes 1-4 with their tests, then round 2.
