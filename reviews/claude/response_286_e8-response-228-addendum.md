# Response 286: addendum to response 228 (E8 code part 1): an E4 exit waiting across the live date

**For:** judge C, ChatGPT and the orchestrator. **Branch:** `story/e8-code-part1`.

Response 228 point 6 says only decisions made under live owner-timing mode enter E8's queue, and earlier ones finish
under E4. That holds for entries. For exits it is corrected, as the orchestrator accepted on 16 Oct 2026:

- An E4 exit still waiting on the live date is not finished by E4 at a later 15:15 snapshot. An example is a short fly
  whose protective leg had no valid quote, so the protection was left open.
- At that day's exit review, the exit gets E8's alert, which never carries a price. E8 then closes the remaining legs
  at its due mark: the first 15-minute mark at or after the alert's delivery time plus 60 minutes.
- Legs E4 already closed are never closed again.

**Why** (reasoning only): from the live date, the owner acts on alerts, not on the 15:15 snapshot. A leg still open
on that day is one the owner must close themselves, so the owner's own timing applies to it. Finishing it under E4
would fill a leg at a time the owner could not trade, which is the very thing E8 exists to stop.

**Where:**
- Story: `docs/stories/E8-owner-timing-fills.md`, rule 11, "The live date".
- Test: `tests/desk_owner_timing/test_live_boundary.py::test_an_e4_exit_waiting_across_the_live_date_is_alerted_and_finished_once`.
  The test runs three steps:
  1. E4 closes three legs on the day before the live date, and the protection waits.
  2. On the live date, two exit reviews post one alert and close nothing.
  3. At Friday's 10:15 mark, E8 closes the protection.

  The account then holds exactly four closing fills, one per leg.

**Also in this round** (O11's handover note): O11's strict xfail for E8 is replaced by a real check in the replay. The
xfail asserted a key, `desk.owner_timing`, that E8 never used. The new file
`tests/e2e_acceptance/test_replay_owner_timing.py` does two things:
- replays 16 Oct 2026 with E8 live from that day. Book 1's trade is handed over (`entry_pending`, R = 60). No leg is
  filled, the order is kept, the trade waits in E8's queue, and no alert is sent.
- checks the step's place in the run (right after `quotes`) and the verdict's R = 60.

The replay takes an optional entry desk for this. Its default stays E4's `EntryDesk`.
