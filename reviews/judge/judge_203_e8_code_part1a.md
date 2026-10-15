# Judge 203: E8 code part 1a at 0516cfb0 (clock, mark snapshots, sealed availability, timed reads, price cap)

Judge C. Branch `story/e8-code-part1`, head `0516cfb0`. Lane 1. The story text passed at 78a51301 (judge 193
addendum 6). The new package `fno/desk/owner_timing/` has 9 files, the largest 148 lines, plus 43 tests in
`tests/desk_owner_timing/`. The step itself (DayStep), the funds re-check, the exits and the verdict account come in
part 1b.

**Verdict: FAIL, two should-fixes.** Both would change fills in normal running. Everything else checks out.

## Gates (trial merge with origin/main, 23d802a7)

| Gate | Result |
|---|---|
| `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -n auto` | 6,633 passed in 2 min 33 s |
| `tests/desk_owner_timing` | 43 passed |
| ruff check, ruff format --check, check_imports | Clean |
| merge | Clean (`docs/WORK_REGISTER.md` auto-merged) |
| size | No file over 350 lines (largest 148) |

## Should-fix 1: in a shallow clone, GitSealLog gives every seal the wrong time

`GitSealLog._committed_at` reads `git log origin/main --format=%cI --reverse -S <hash> -- <seals file>` and takes the
first hit. In a shallow clone, the boundary commit carries the whole file, so every seal's "first commit" is that
boundary commit, with the boundary's time.

**Probe** (a real repository, seal rows added on 11, 12 and 13 Oct, then a later commit on 15 Oct):

| Seal | Full clone | `--depth 1` clone |
|---|---|---|
| h1 | 2026-10-11T09:03 | **2026-10-15T09:03** |
| h2 | 2026-10-12T09:03 | **2026-10-15T09:03** |
| h3 | 2026-10-13T09:03 | **2026-10-15T09:03** |

So for an order whose T is earlier than the boundary, `sealed_before(T)` returns None. `SealedDriveAvailability.away`
then answers False ("nothing sealed yet: every session counts as available"), and an away day is filled as if the
owner were there.

This happens in normal running: cloud sessions clone with limited depth (story X's shallow-message line in
`docs/JUDGE.md`; 50 commits by default for a new session), and main takes far more than 50 commits a day.

**Fix:**
- `GitSealLog` refuses in a shallow repository (`git rev-parse --is-shallow-repository`), raising
  `AvailabilityRefused` with "shallow clone: run git fetch --unshallow origin main". That is a step failure, so new
  entries fail closed and exits still run.
- The same rule applies anywhere else part 1b reads seal times.
- Add a test on a real `--depth 1` clone, like `tests/test_history_guard.py`.

## Should-fix 2: TimedStore abandons writes, and a late write can overwrite a newer one

`TimedStore.put` runs the write in a daemon thread and gives up after the cap. The thread goes on, and the write can
land later. Part 1a has no caller of `put` in the package (checked with grep), but part 1b's writes will go through
E2c's `PrivateFiles.push`, which overwrites whole account files in Drive. Two paths follow:

- The fill step's put of a book's account times out. The step fails, and the run goes on to `exits`, which pushes the
  same account file. The abandoned fill write then lands and overwrites the exit. The exit is lost from Drive, and
  the next run reads the wrong positions.
- A late write can also land after a rerun has written the correct state.

Reads are safe to abandon, because their late results are ignored. Writes are not.

**Fix:**
- `TimedStore` caps reads only (`get`, `checksums`, `folders`); `put` is not offered on the timed path.
- Part 1b states how its writes are bounded without being abandoned. One way: all writes come after all reads, go
  through E2c's journal, and use write-once new paths, so that a late write can never replace newer content. A
  time-out before any write then leaves nothing behind.
- A test shows that no write is started after a timed-out read.

## The orchestrator's two questions

- **Can the daemon thread leave a late write after the step fails?** Yes, through `put` (should-fix 2). For reads, the
  thread's late result is dropped (`outcome` is no longer read) and the step has already failed, so it is harmless.
- **Can "first published commit on origin/main" be faked by a local commit?** Not by an unpushed one: the log reads
  `origin/main`, never `HEAD`, so a local commit that was never pushed never counts.
  - Two limits remain. In a shallow clone it gives wrong times (should-fix 1).
  - The time is the committer time, which whoever makes the commit can set. A seal pushed with a back-dated committer
    time would count. That is deliberate forgery, not normal running; the run writes its own seal, and O8 keeps
    GitHub push receipts if a stronger check is ever wanted. A note, no change.

## Checked and fine

- **Clock:** 15:16 to 09:30 / 09:45 / 10:15 of the next session; muhurat-only days skipped; Friday to the next session.
- **Mark snapshots:** they use A4's own parser and `quote_validity`, never a copy. A late copy and a quote requested
  before the mark are dropped. The A4 stand-in is used only inside the on-time window.
- **Availability:**
  - lines are normalised as the text says;
  - a sealed-prefix mismatch refuses with the repair message;
  - the sealer never re-seals over a mismatch and skips an unchanged file;
  - the salt line is required, with at least 32 hex digits.
- **`ApprovedLimit`:** "missed, price moved" one paisa past the limit; fills at the limit exactly.
- **`call_within` timing:** it caps the whole call, so a trickling read cannot outlast the cap. This answers judge 193
  addendum 6's note. It is tested for a hung read, a trickling read and a passed deadline.
- **Read-only:** the package's import closure reaches no broker order, position, margin or funds call.

## My view on part 1b's plan (asked before the code)

The plan: a fresh C2 check for the fill day, the price cap kept at the decision's approved entry, and per-leg validity
in place of the whole-snapshot "complete" test for A16 copies. **Sound, with four conditions** (reasoning only):

1. **It is a check, not a new decision.** The fill-day C2 run must write no decision record that E6, S1 or S2 could
   count. It gives fill or miss only ("insufficient funds", "over risk cap").
2. **Keep E4's `refusal()` as it is for `e4_1515`.** That view must stay bit-for-bit today's E4 (criterion 9). The new
   rule applies only to the owner-timing views.
3. **Per-leg validity covers every leg of the trade, plus what C2 and C4 read.** All legs or none (rule 5) still
   holds. The spot, futures or VIX values that the stressed margin and the caps use must also be valid in the same
   due-mark copy, or the entry is "missed, no quote". Other strikes in an incomplete A16 copy may be missing.
4. **Earlier fills come first.** The C2 check sees that morning's earlier fills, in the oldest-first order of rule 11,
   as criterion 6's "pending fill earlier that morning" fixture already requires.

Would the two should-fixes change a trade? Yes. Should-fix 1 fills on away days. Should-fix 2 can lose an exit.
Re-review: those two only.
