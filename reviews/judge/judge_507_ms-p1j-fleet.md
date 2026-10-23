# Judge 507: MS-P1j, the fleet join-up (first judge)

**Scope:** story/ms-p1j-fleet at 7f757504 (builder session_01CmKJ6taCLzfEGg7wt6RC4N); the MS-P1j section and its
Claims. It covers `fno/school/fleet/*`, `fno/school/wiring.py`, `fno/school/cli.py`, two lines in `fno/cli.py`, the
tests, and two touches of f (`OwnedFill.is_exit`; `TicketBook.price`/`open`/`close`). Lane 1, money piece (fills,
exits, records): first of two judges, independent of judge K. Round 1 of 2. The builder's round-3 list (already ruled
by the orchestrator) is not re-raised.

**Verdict: PASS.** Nothing blocking, no should-fix. Notes below.

## Gates (my run)
- pytest -n auto: 11795 passed, 9 skipped (the real acceptance test until d's `entries` merges), 16 xfailed.
- `ruff check`, `ruff format`, `check_imports` and `check_records` (8372 files) are clean.

## The three checks asked for
1. **A crash anywhere between the seal and the counts' commit is completed once.**
   - A sealed session is never decided again: `dashcam.find(DECISIONS)` leads to `_finish`.
   - `_finish` is rebuilt from the sealed records and the ledgers (`Recorded`). A recorded opening or closing is read
     back, never re-priced. A recorded position is never opened again. Outcomes and drift are each sealed once. The
     counts are write-once, so other text raises `ReplayConflict`, never a silent overwrite. A crash after the counts'
     write only commits.
   - The size allocation is seeded by (session, slot, road), so a rerun serves exactly what one clean run would.
2. **Entries before exits.** `allocate` ranks (is_exit, is_ticket, seeded owner). An account entry it cannot serve
   is `size_shared` and stays in the denominator. A ticket it cannot serve is not opened. An exit it cannot serve
   fills nothing and waits. No ledger holds an unservable fill.
3. **Pairing and settlement.** A decision of another driver, road or session, or a position of another driver or
   reviewed on another road's snapshot, makes that driver's whole slot `unavailable: driver_error`, never an exit.
   Expired positions settle before the session's first `view`, and the settlement exit records are sealed with the
   decisions.

## Plants: 11 on the fleet, 8 caught
- **Caught:** recorded entries re-priced; recorded entries opened again; an exit closed without size; an unservable
  entry recorded; exits ranked with entries; the counts never written; settlement after the first view; a rerun
  skipping the finish.
- **Survived, equivalent today:**
  - Recorded exits re-priced: a closed position is no longer in `still_open`, so the recorded fill is used anyway.
  - Outcomes sealed every run: sealing the same records again is a no-op, and outcomes are rebuilt deterministically
    from the ledgers.
  - The commit-only branch removed: before 15:30 the counts' write is a same-text no-op that then commits.
    - After 15:30, refused entries would re-price as `stale_seal` and the write would raise `ReplayConflict`, so the
      branch matters there. Round 3's "rerun after 15:30" test should also kill this plant.

## Notes (no action in this round)
- **Margin time inside the first driver's limit.** The first margin check of a session downloads and parses the SPAN
  file inside the first driver's 60-second limit. I measured it on 21 Oct: download 9.1 s for 9.1 MB, and 2.3-2.6 s
  to parse each of the four indices, about 19 s in all. That is inside the limit, but a slow Drive day could time out
  the first driver alone. Warming the margin before the driver loop would remove the case [reasoning only].
- **Unmeasured sizes (a3, for SIM-c).** `_displayed` reads a missing size as 0, so a quote whose sizes were not
  measured can never serve a fill in `allocate`. That is correct for live fills. The simulator must not route its
  unmeasured history through this allocation, or every simulated fill becomes `size_shared`.
- **The real acceptance test** (9 cases) skips until d's `SchoolAccounts.entries` (judge 488.4) merges. I did not
  see it pass. That should be shown before j merges.

## Addendum 1

**Scope:** MS-P1j "round 3" (the builder's numbering), story/ms-p1j-fleet at cb059340, main merged in. It applies the
orchestrator's rulings on round 2 and judge I's note, and touches a, f, g, i and the lab's reserved line on purpose.
This is my round 2 of 2 (first judge, independent of judge K).

**Verdict: PASS.**

- **Gates (my run):** 12087 passed, 16 xfailed. `ruff check`, `ruff format`, `check_imports` and `check_records`
  (8426 files) are clean.
- **Real acceptance on the real wiring: 9 of 9 pass** (`test_acceptance_real.py`, run by me). My round-1 note 3 is
  met.
- **The new pieces, checked.**
  - **Settlements.** `LedgerEntry.recorded_for` is a session date, kept in d's canonical position records. The
    session's settlement exit records are rebuilt from every expiry closing recorded for that session, so a crash
    between a settlement and the seal still seals its exit and outcome, and an earlier session's settlement is never
    sealed again.
  - **Late rerun.** A rerun that finishes after 15:30 writes the "rerun after 15:30, fillable may differ" mark;
    counts already written only commit.
  - **Accounts.** Every account and ticket-ledger call goes through `account_call`, so an unreadable account stops
    the run by name with nothing sealed, and `school run` exits 1.
- **Plants: 15 of my own re-run here, 14 caught.**
  - From round 1, now caught: the commit-only branch removed (the 15:30 test kills it, as round 1 asked) and
    recorded exits re-priced.
  - New, caught: every session's settlements sealed; an account settlement without its session; a late rerun never
    marked; the view unguarded.
  - Survived, equivalent: "outcomes sealed every run" (re-sealing the same records is a no-op).
  - One round-1 plant no longer applies, because the code changed.

**Notes.**
1. `recorded_for` joins `LedgerEntry`, and the position records decode strictly, so a line written before this field
   fails to decode. No school account exists yet (the school is off). If one ever does before this merges, it needs
   a schema step.
2. My round-1 note 1 (the SPAN download inside the first driver's limit, about 19 s of 60 s) and note 2 (`allocate`
   reads a missing size as 0, so practice fills must not go through it) still stand.

## Addendum 2

**Scope:** the delta `7f757504..1da5ffcd` on story/ms-p1j-fleet, as the orchestrator asked. Round 3 (cb059340) is
already judged in addendum 1. This covers round 4 (1da5ffcd): the builder's answers to my notes, and judge 506's live
guard.

**Verdict: PASS.** My round-1 notes 1 and 2 are closed at their root.

- **Gates (my run):** 12097 passed, 16 xfailed; real acceptance 9 of 9. `ruff check`, `ruff format` and
  `check_imports` are clean.
- **Only the driver's code is timed.** The builder rejected my "warm-up" suggestion with a better root cause: the
  60-second limit timed the fleet's own laws.
  - `DriverStep` now isolates and times only the driver's code: its decisions (real, plus the hypothetical ones on
    roads where it holds a ticket), then its exit reviews, each with its own limit. The laws run untimed between
    them, so a slow margin read is never a driver's deadline.
  - A law that throws unexpectedly is now the fleet's loud error, never the driver's. A failed SPAN read still
    refuses each entry by name inside C2's law.
  - I accept this. It is the right fix, and mine was a patch.
- **A road is never ticketed twice.** A ticket on a road where the driver already holds one stands only if the
  driver, deciding again with its tickets, still trades. That answer is now asked inside the timed driver call.
- **Live guard (judge 506).** `plan_slot` closes any road whose capture holds an unmeasured quote
  (`sizes_not_measured`), so the live fleet never trades on one. That makes my note 2 (missing sizes read as 0 in
  `allocate`) moot for live runs until d's QuoteRules reaches it.
- **Plants: 4, 4 caught.** An unmeasured road left open; exit reviews untimed; the laws timed with the driver; a road
  ticketed twice.

## Addendum 3

**Scope:** 8d4d6fb2..5395948a on story/ms-p1j-fleet. Most of it is main merged in (d's part 4, judged in 488.6). The
builder's own change is 5395948a: `allocate` and f's shared size read sizes through d's `QuoteRules`.

**Verdict: PASS.** My note 2 is closed.

- **Gates (my run):** 13511 passed, 16 xfailed. `ruff check` and `ruff format` are clean.
- **The rule.** `_displayed` reads each size through `rules.sizes`.
  - Under LIVE, a missing or unmeasured size serves nothing: it is no fill and no ticket, never unlimited.
  - Under PRACTICE, an unmeasured size has no limit (`inf`).
  - The fleet passes `LIVE` by name; the default is also `LIVE`.
- **Plants: 4, 4 caught.** The rules ignored (raw size); bid and ask swapped; a missing size made unlimited; the fleet
  passing practice rules (caught by the practice-isolation test).

## Addendum 4

**Scope:** 5395948a..fec42868 on story/ms-p1j-fleet, answering judge K's judge 512. The composition root is split so
a replay cannot build a real store.
- `fleet_wiring.fleet_on` wires what both roots share, over the stores handed in.
- `wiring.build_fleet` is the record root: the Drive dashcam, the account sync and the committer.
- `replay_wiring.build_replay_fleet` uses a local dashcam, accounts and counts under its folder, with no commit and a
  fixed clock.
- `cli.py` picks the root. Tests are added; no fleet logic changed.

**Verdict: PASS.**

- **Gates (my run):** 13535 passed, 16 xfailed. `ruff check`, `ruff format` and `check_imports` are clean.
- **A refactor only.** The removed `build_fleet` body is the same wiring, now in `fleet_on`. The record root builds
  the same three real stores as before, and the replay root imports none of them. The mode switch is gone, so a
  replay is a different root, not a flag.
- **Plants: 2, 2 caught.** The replay root using the Drive dashcam; the replay writing accounts at the repository
  root.

## Addendum 5

**Scope:** MS-P1j follow-up, the instructor wired into the fleet: story/ms-p1j-ins-wiring at eb5ec57a, which is
MS-INS part e (63cabe67) merged with main. It merges after part e. Judged on the fleet side only (part e has its own
judges): `SchoolFleet.after_outcomes`, `IsolatedSessionStep`, `UnfilledEntries`, `SealedDayInputs.why` and the
record root's wiring. First of two judges, independent of judge K.

**Verdict: PASS.**

- **Gates (my run):** 14026 passed, 16 xfailed. `ruff check`, `ruff format` and `check_imports` are clean.
- **The step after the outcomes.** It runs after the outcomes' (and drift's) seal and before the counts are written
  and committed, and again on a rerun's commit-only path.
  - The step is isolated: an exception or its 300-second limit gives one alert naming only the class, and the
    school's own counts are still written and committed.
  - Only the record root wires it. The replay root and the tests use `no_step`, and the replay root imports nothing
    of `instructor.wiring`.
- **`UnfilledEntries`.** Every sealed trade or ticket whose position neither ledger ever opened, derived read-only
  from the dashcam and the two ledgers.
- **Plants: 6, 5 caught.** Caught: the rerun skipping the step; the step not isolated; a failure not alerted;
  tickets left out of unfilled; unfilled always empty.
  - Survived, equivalent: the step run before the drift seal. Part e reads no drift (grep), so the order between
    the two does not matter.

**Note.** A step past its limit keeps running. If it is still writing when the counts are committed, part e's
temporary file (`.<name>.part`, in the counts folder) could be caught by the commit's `git add` of that folder. The
write is one small file, so the window is tiny, and `.gitignore` has no rule for `*.part` there [reasoning only]. An
ignore rule for `research/school/counts/**/.*.part` would close it.
