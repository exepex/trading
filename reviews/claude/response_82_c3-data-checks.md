# Response 82: story C3, data checks before every decision: builder's claims

Builder session, 14 Oct 2026. Branch `story/c3-data-checks`, from `main` 8c5bd5f. Judge first; nothing goes to `main`.

**Verdict in one line:** before every decision, six data checks run on E2's common pack and on the execution snapshot.
- **Any failure:** "no new trade: stale or unverified data" plus an alert to #fno-desk, refused before any leg is priced.
- **A failure that leaves prices unverified:** an exit that is due becomes a pending exit through E4's own exit path.
  It fills at the next valid quotes and never at a stale price.

## 1. The design (`fno/checks/`, wired in `fno/checks/wiring.py`)

| Part | What |
|---|---|
| `DataCheck` (`data_checks.py`) | One class per check. `problems(subject)` returns why it fails. `prices_unverified` says whether a failure makes the snapshot's prices unusable, for exits too. |
| `SnapshotReadable` | The capture is named for the day and can be read: present, the day's, and its file matching the hash in its own sidecar (E4's reader). |
| `SnapshotInWindow` | Captured inside its scheduled window: `started_at` at or after the window's start and `finished_at` at or before its end, both read from the sidecar. No quote age is claimed. |
| `SnapshotMatchesPack` | The pack records this snapshot ID with the same quote-file SHA-256. |
| `SpotNearPreviousClose` | The pack's one spot value is within 2% of the official close of the previous session (A7 calendar), unless the day is flagged as a shock. |
| `LegQuotesValid` | Every leg the decision needs has its own quote valid by A4's rule. |
| `PreviousSessionFile` | NSE's F&O file of the previous session (A7 calendar) is archived. |
| `ExecutionSchedule` (`schedule.py`) | **The interface E3 fills:** which capture the decision executes at, and its window. Until E3 exists, `PackSnapshotSchedule` uses the pack's A4 snapshot and the recorder's 14:55-15:10 window. |
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
2. **"The hash matches the pack" applies to whichever capture the decision executes at.** The pack must record that
   snapshot ID with the same hash.
   - If E3 executes at a capture other than the pack's A4 snapshot (E4's fixtures use a 15:15 capture), E3 must record
     that capture's provenance in a pack. Otherwise every decision fails this check, loudly, by design.
   - This is my reading of the story. The orchestrator should confirm it with E3.
3. **The window is strict.** A capture that starts inside the window but finishes after its end fails.
   - The recorder may start its last retry before 15:10 and finish after. Such a canonical snapshot fails the checks,
     and there is no new trade that day.
   - Conservative; reasoning only.
4. **Which failures stop exits.** Only failures that make prices untrustworthy stop exits: unreadable snapshot, outside
   the window, hash mismatch, or a suspect spot.
   - A missing NSE file of the previous session, or an invalid leg, stops new trades only. E4 handles legs one by one
     (design 9: risk-reducing exits still run).
5. **An unreadable snapshot gets no per-trade pending-exit row.** A desk event needs a snapshot ID and hash, so a file
   that cannot be read is reported by the gate's alert instead.
   - The open trades wait for the next readable snapshot, and their exits are reviewed there.
   - This is a limit of this story, said openly.
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

## 4. Gates

Full suite, `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py` and the 350-line limit: the
results are in the commit message and the message to the orchestrator.
