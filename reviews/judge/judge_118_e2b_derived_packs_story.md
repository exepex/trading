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

## Addendum 1 (15 Oct 2026): de2830061a845cc366752ab6900da8439ec8abb2

Text only (`git diff dd0be6a de28300`: the E2b section).

| Item | Status | Evidence |
|---|---|---|
| sf 1, the unwind pair | MET | Named as the one stated exception: a failed hedge's `FILL_OPEN` at the ask, its `FILL_UNWIND` at the bid of the same snapshot, and `legging_cost_rs`. It goes to the owner with the fills-to-Drive question (orchestrator's decision 28). Criterion 3 now tests every E4 outcome (opened, partial fill, closed, pending exit, settlement) and finds both sides of one contract only in the unwind pair |
| sf 2, A4b first | MET | A4b is a dependency in criterion 3 and the Depends line, and E2b merges only after A4b (orchestrator's decision 29). E6 reads the 15:15 file from Drive through A4b's hash-checked store |
| Minor 1, the unknown count | MET | The scorecard report prints the number of "touch unknown" fills |
| Minor 2, path tricks | MET | The guard compares resolved paths; tests cover `.CSV`, `../` and a symlink into the Groww folder |

**Code note (I check it when judging the code):** a test that "only the unwind pair reveals both sides" must compare
each pair of rows on the same `snapshot_id` and `quote_contract_id`, across all books' and shadows' fill files, so that
two books filling the same contract in one snapshot on opposite sides is not missed. A buy in one book and a sell in
another at the same snapshot give both sides just as an unwind does. If it can happen, it is a second exception to
state.

**Verdict: PASS for de2830061a845cc366752ab6900da8439ec8abb2** (story text). Code may start. The merge waits for A4b,
and by quality rule 9 the code goes to ChatGPT after my code PASS.

## Addendum 2 (15 Oct 2026): E2b code at b76be4fdf00ab776148d854afde5f69d10782293

Code plus the changed story text (`git diff de28300 b76be4f`). Builder's claims: response 118.

### Gates

| Gate | At b76be4f | Trial merge with `main` b28bc53 |
|---|---|---|
| `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q` | 3,865 passed | 3,919 passed |
| `ruff check` / `ruff format --check` / `check_imports.py` | clean / clean / clean | clean / clean / clean |
| Conflicts | - | `reviews/claude/README.md` only (index rows) |

A4b is not on `main` yet (judge 111 addendum 3: waits for the owner's probe), so this trial merge does not include it.

## Verdict: FAIL (code), 2 should-fix; 3 minor

### Per criterion

| Criterion | Builder's claim | My evidence | Status |
|---|---|---|---|
| 1 No per-contract figure in the pack; spot per chain; two spots refused | `option:` items gone; `spot:<expiry>`, `quote_counts` | On the real 14 Oct snapshot (184 rows), `_spots` gives `spot:2026-10-27` 22,620.00 at the chain's first row (14:55:25.46) and `spot:2026-11-23` 22,621.15. Blanking one chain's spots gives that item with value None. A second level 22,620.05 in one chain is a PackError naming the expiry. 22620.0 and 22620.00 count as one level. No bid, ask or size field in any item. Plants M13, M14, M19 and M20 caught | MET |
| 2 C3 from `spot:` items; one spot per chain | blank or refused `spot:` named | The code names a blank item and a refused item. Plants M11 (refused ignored) and M12 (blank ignored) caught | MET |
| 3 Fill rows carry no touch; exceptions pinned; E6 from the snapshot; unknowns counted | as in response 118 | `FILL_COLUMNS` has no `quote_bid`/`quote_ask`. The cross-account test (`test_public_fills.py:73`) compares across book 1 and book 2 by snapshot and contract, as my addendum 1 note asked. Hand check on the real snapshot: 10 legs at the touch give 5.9325/unit from `half_spread`, and my own arithmetic gives 5.9325. Wrong hash, blank or `../` snapshot ID, absent contract, other contract ID, other day: each is one "touch unknown", no crash. The report prints the count (plant M22 caught). **But a corrupt snapshot and a one-sided quote are untested (should-fix 2)** | PARTLY |
| 4 Capture commits record and sidecar only | `names[1]` | Plant M15 (the CSV re-added) caught | MET |
| 5 Guard: before git, after the add, folders, earlier-staged files | as in response 118 | On real git repositories: a folder, a trailing-slash pathspec and a parent folder are refused after the add, and the add is undone. A file staged earlier is refused and left staged. `.CSV`, `../` and a symlink are refused. A sidecar alone commits. Plants M1-M5 and M21 caught. **But a refusal inside an account write escapes the desk's per-book handling after the fills were applied (should-fix 1)** | PARTLY |
| 6-7 E2 criteria on schema 2; no `option:` reader | existing tests | Full suite green. My grep finds no `option:` lookup left in `fno/` | MET |
| Story text re-check | exceptions 1-3, known channels, kept mids | Exception 3 matches `fno/desk/exits.py:90-106`. The scoreboard B channel matches `daily_values.py:44-55`. All are stated for the owner, not silently kept. One slip (minor 1) | MET |

Plants: 22 of my own. 20 were caught; M16 and M18 survived (should-fix 2).

## Should-fix

**1. A guard refusal during an account write leaves the fills applied but not committed, and escapes the desk's per-book handling.**
- **What happens.** `GitAccountSync.write` runs `apply(journal)` (the fills reach the book's ledger), and only then `commit_paths`.
- **Probe on a real repository.** A raw quote file staged earlier outside the book folder, then one account write:
  - `RawQuoteCommitRefused` is raised. It is a `ValueError`, not `AccountWriteRefused`.
  - `cash_ledger.csv` already holds the new fill row, uncommitted.
  - The next write for that book stops on "uncommitted work in journal/book1_rules/account".
- **Why it matters.**
  - `DailySteps.fill` catches only `AccountWriteRefused` (`daily_steps.py:143`, "never crashes the run before its exits", judge 84). This refusal escapes `fill()`, ends the run step, and the exits step never runs.
  - The paper account then holds a trade that the run log does not record.
  - In `review_exits` the broad handler alerts, but the exit fills are likewise applied and not committed.
  - This is exactly the case criterion 5 was written for ("a quote file staged earlier by anything else"). So when the guard does its job, it breaks judge 84 and splits the account from its record.
- **Expected fix.**
  - Check the whole index in the account write's dedicated check, before `apply`, so a refusal applies nothing.
  - Make the refusal one the desk handles: an `AccountWriteRefused` subclass, or caught and turned into one. The fill step then records "not filled" with an alert, and other books and the exits go on.
  - Test it: with an earlier-staged quote file, the fill step gives "not filled" plus an alert, the journal is byte-identical, and exits are still reviewed. Add the same for an exit write.

**2. "Touch unknown, never a crash" is untested for the two cases that need the code.**
- **M16 survived.** Narrowing `except (SnapshotError, ValueError, KeyError, OSError)` to `SnapshotError` passes all 293 related tests. On a copy of the real snapshot with a corrupt `.meta.json`, the reader raises `JSONDecodeError`, not `SnapshotError`, so without the wide `except` E6 crashes.
- **M18 survived.** Dropping the bid/ask `None` check passes too. `ExecutionQuote.bid/ask` are `float | None`, so a one-sided quote would then crash on `None + float`.
- **Expected fix:** two tests. A corrupt sidecar or CSV gives one "touch unknown", and a one-sided quote gives one "touch unknown"; both still average the other fills.

## Minor

1. **Story text slip.** "**two stated exceptions**" is followed by a list of three. Make it "three", matching criterion 3.
2. **A chain with no rows at all gets no `spot:` item** (the meta's `expiries` lists it, the rows do not). C3's 0.2% agreement then quietly runs on one chain, as it did before E2b. "One spot per recorded chain" could take the chain list from `meta["expiries"]` and give a missing chain a None item. Reasoning only; not a regression.
3. **The guard is path-based by design.** A raw file copied or renamed outside the folder passes. It also refuses a staged deletion of a raw quote file (`diff --cached` lists deletions). That errs on the safe side, but if A4b removes the 14 Oct Groww CSV that is still on `main` (`.../2026/10/nifty_20261014_145500.csv`, public since that day), that removal must not go through `Git`.

## For the merge check (after A4b)

- `fno/scorecard/wiring.py` builds E6's snapshots from the local quote folder. After A4b, it must read through A4b's hash-checked Drive store, or every fill outside the capture's checkout is "touch unknown". The merge must keep one version of `execution_capture.py`.

**Verdict: FAIL for b76be4fdf00ab776148d854afde5f69d10782293** (code) on should-fixes 1-2. A re-check needs only `git_sync.py`, the fill and exit step handling, `touches.py` and their tests.
