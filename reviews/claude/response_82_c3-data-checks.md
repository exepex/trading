# Response 82: story C3, data checks before every decision: builder's claims

Builder session, 14 Oct 2026. Branch `story/c3-data-checks`, from `main` 8c5bd5f. Judge first; nothing goes to `main`.

**Verdict in one line:** before every decision, six data checks run on E2's common pack and on the execution snapshot.
- **Any failure:** "no new trade: stale or unverified data" plus an alert to #fno-desk, refused before any leg is priced.
- **A failure that leaves prices unverified** (unreadable, outside the window, not the capture its committed record
  names): an exit that is due becomes a pending exit through E4's own exit path. It fills at the next valid quotes and
  never at a stale price.

## 1. The design (`fno/checks/`, wired in `fno/checks/wiring.py`)

| Part | What |
|---|---|
| `DataCheck` (`data_checks.py`) | One class per check. `problems(subject)` returns why it fails. `prices_unverified` says whether a failure makes the snapshot's prices unusable, for exits too. |
| `SnapshotReadable` | The capture is named for the day and can be read: present, the day's, and its file matching the hash in its own sidecar (E4's reader). |
| `SnapshotInWindow` | Captured inside its scheduled window: `started_at` at or after the window's start and `finished_at` at or before its end, both read from the sidecar. No quote age is claimed. |
| `SnapshotMatchesRecord` | The snapshot is the one its committed, hashed capture record names: the same ID, quote-file SHA-256 and sidecar SHA-256 (the sidecar holds the capture times). Judge 81 ruling 2. |
| `SpotNearPreviousClose` | Each chain's spot in the pack (one per monthly chain) is within 2% of the official close of the previous session (A7 calendar), unless the day is flagged as a shock. The spots must agree within `SPOT_AGREEMENT` (0.2%). **New trades only** (judge 81). |
| `LegQuotesValid` | Every leg the decision needs has its own quote valid by A4's rule. |
| `PreviousSessionFile` | NSE's F&O file of the previous session (A7 calendar) is archived. |
| `ExecutionSchedule` (`schedule.py`) | **The interface E3 fills:** which capture the decision executes at, its window and its committed **capture record** (`CaptureRecord`: capture ID, quote-file and sidecar SHA-256, where it is committed). Until E3 exists, `PackSnapshotSchedule` supplies the common pack's A4 record (its provenance; the pack is written once and committed) and the recorder's 14:55-15:10 window. E3 will supply its own execution record without changing C3. |
| `DataGate` (`gate.py`) | Reads the scheduled capture, runs every check, and sends one alert on failure. Returns the snapshot and a `CheckReport`. |
| `ShockFlags` (`shock.py`) | Where the shock flag comes from. **No source exists yet** (details below). |

**Into E4, with no duplicated path:**
- `EntryDesk.enter(..., checks)` refuses on any failure before pricing a leg. Today, a bad short leg would first fill the
  protection and then unwind it at a legging cost.
- `ExitDesk.review(..., checks)`: when prices are unverified, protection is not judged, price rules do not fire, and an
  exit that is due records `exit_ordered` and then `pending_exit` through E4's own event and alert code.
  - The exit is retried at the next snapshot. Expired legs still settle from NSE's settlement file, which is not a quote.
- Both desks **require** the report and raise if it is for another snapshot or day, or if it did not check every leg
  of the order. A caller cannot skip the checks by passing an empty report.

**One A4 rule:** it is now `ExecutionQuote.a4_problem`, used by both E4's pricing and C3's leg check.
- It checks the quote's own numbers (bid > 0, ask > 0, bid <= ask, both sizes > 0).
- It also requires the recorder's `valid` flag, which carries the trade-today evidence (last trade time, or day volume
  for NSE).
- So a hand-edited `valid=true` on a crossed book is refused. Before, pricing trusted the flag alone.

## 2. Choices the orchestrator or owner should check

1. **The shock flag has no source (fact).** I searched the repository. The A6 events file lists *scheduled* events,
   not shocks, and nothing else flags one. So `NoShockFlags` flags none, and any move beyond 2% stops new trades. A
   source (an owner flag file, or an NSE circular feed) is one new class plus one line in the wiring.
   - Owner question: do you want a flag file you edit by hand? (Reasoning only.)
2. **Replaced (judge 81 ruling 2):** the 15:00 pack can never hold E3's 15:15 capture (cutoff, write-once), so
   "matches the pack" would have refused every E3 execution. The check now compares the snapshot with a committed
   capture record supplied through `ExecutionSchedule` (see addendum 1).
3. **The window is strict.** A capture that starts inside the window but finishes after its end fails.
   - The recorder may start its last retry before 15:10 and finish after. Such a canonical snapshot fails the checks,
     and there is no new trade that day.
   - Conservative; reasoning only.
4. **Which failures stop exits.** Only failures that make prices untrustworthy stop exits: an unreadable snapshot, one
   outside its window, or one differing from its capture record.
   - The spot check, a missing NSE file of the previous session, and an invalid leg stop new trades only. E4 handles
     legs one by one (design 9: risk-reducing exits still run).
5. **An unreadable snapshot gets no per-trade pending-exit row**, because a desk event needs a snapshot ID and hash.
   Instead the gate's alert names every open trade whose exit is due without a price: one already ordered, or reached
   by the time rule (`ExitDesk.due_exits`, judge 81 should-fix). Their exits are reviewed at the next readable
   snapshot.
6. **One alert per gate run.** E3 calls the gate once per decision, so a day with several decisions may alert more than
   once with the same data reason.

## 3. Evidence

- `tests/checks/test_data_checks.py` (22 tests), on fake snapshots and packs:
  - each check passes and fails;
  - the window's edges pass, and one second outside them fails;
  - spot at exactly ±2% passes and ±2.01% fails;
  - a flagged shock passes;
  - each A4 condition fails on its own, and the trade is refused with no legging cost.
- `tests/checks/test_exits_and_stale_fixture.py` (5 tests):
  - a time exit that is due on stale data is `pending_exit` with an alert, then closes at the next valid snapshot;
  - a stop loss does not fire on stale prices, and no `protection_unverified` is recorded;
  - a missing NSE file refuses the new trade but still lets the exit close;
  - a report on another snapshot, or one missing a leg, raises.
- **The judge's fixture:** `tests/fixtures/c3_stale/` holds A4's files for a capture taken at 13:31 IST and a pack that
  records it. Run through the real checks with the recorder's window, the one failure is
  "captured 13:31:02-13:31:40, outside its window 14:55:00-15:10:00", with one alert.
- E4's tests now pass a "checks passed" report. Their behaviour is unchanged.
- Mutations (`python -B`, caches cleared): **26 of 26 caught**. The plants covered:
  - every check switched off or loosened;
  - the window's start or end ignored;
  - a doubled spot limit, and a shock always flagged;
  - the previous file read for today instead of the previous session;
  - each A4 condition dropped;
  - the entry or exit ignoring the report, or not checking it covers this snapshot and all legs;
  - the time rule off on stale data;
  - no alert sent;
  - the spot check unwired.

## Addendum 1: judge 81 (FAIL), fixed

Each point was checked against the code before it was accepted.

1. **Two spots per real snapshot: accepted, verified in the code.** The recorder fetches each of its
   `MONTHLY_EXPIRIES = 2` chains with its own provider call (`recorder.py`, the `for expiry in months` loop), and each
   row stores its own chain's spot (`"spot": chain.spot`).
   - So my "exactly one spot" rule would have refused entries every day; the single-spot fixture hid it.
   - Now every spot is compared with the previous close, and the spots must agree within `SPOT_AGREEMENT` = 0.2%
     (about 50 points).
   - Why 0.2%: two index readings seconds apart rarely differ by more than a few points, while a future's price mixed
     in would differ by its basis (about 0.3-1% a month out).
   - Strength: reasoning only. **No real A4 capture is committed yet**, so I could not measure the gap. Today's 14:55
     capture should be checked against it when it lands.
   - Tests: spots +0.05% apart pass, exactly 0.2% passes, 0.4% fails, and agreeing spots +2.09% from the close fail.
2. **The spot check stops exits on big-move days: accepted.** It contradicted design 9, and freshness is already the
   window's and the record's job. The spot check is now new-trades-only.
   - Test: on a +3% day the entry is refused, and the due exit closes with 4 fills.
3. **Should-fix, accepted:** when no snapshot can be read, the gate's alert names every exit due without a price.
   - Test: the time exit is named; a price rule is not, because it cannot be judged.
4. **Ruling 2, root fix done:** `SnapshotMatchesRecord` compares the snapshot with a `CaptureRecord` supplied through
   `ExecutionSchedule`.
   - The record's sidecar hash covers the capture times. `ExecutionSnapshot` now carries `meta_sha256`.
   - Today the record is the common pack's A4 provenance (snapshot ID, `csv_sha256`, `meta_sha256`).
   - E3 will supply the record of its own 15:15 execution capture through the same interface, without changing C3.
   - Tests: a quote file rewritten after the record, a sidecar with later times, a record naming another ID, and no
     record at all each fail by name.
   - The stale fixture's pack now records the sidecar hash too.
5. **Kept as the orchestrator ruled:** strict spot checking without a shock source (entries only), and the strict
   window.

Mutations (`python -B`, caches cleared): **34 of 34 caught**. The new plants:
- each part of the record comparison dropped;
- the record missing, or not supplied by the pack schedule;
- the spot agreement off;
- spots required to be equal (the old bug);
- only the first spot checked;
- the spot check blocking exits again;
- due exits not named;
- the record check unwired.

## 4. Gates

Full suite, `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py` and the 350-line limit: the
results are in the commit message and the message to the orchestrator.
