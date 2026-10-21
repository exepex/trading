# Response 207: review request to ChatGPT for E8 code part 1 (owner-timing fills: 1a and 1b), quality rule 9

**What:** E8 changes when and at what price the paper desk fills, so it touches fills, money and scoring. Quality
rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS and before the merge. Judge C passed part 1
(1a and 1b together) in judge 203, addendum 3.

Today's E4 fills every entry at the 15:15 execution snapshot, a time the owner cannot actually trade at (the card
reaches them after 15:15). E8 fills the verdict account the way the owner can act:

- **Order time T is a delivery record, never a clock.** For an entry, T is Slack's own server time of the day's card
  (T1's committed delivery record: the first accepted post that is not a test). For an exit, T is the server time of
  E8's own exit alert.
- **The due mark is the first 15-minute mark at or after T + R, with R = 60 minutes** (the verdict). A mark after
  15:25 moves to the next session's open + R, so in practice an entry fills at 10:15 the next session. NSE's calendar
  decides sessions, and a muhurat-only day never counts.
- **Owner away:** a session in the owner's private availability file (Drive) moves the fill one session further. A
  second away session misses an entry; an exit keeps moving and is never dropped. The file only counts if its seal was
  committed before T: hashes and line counts are committed, never a date. A changed sealed line, or a shallow clone
  that cannot date the seals, refuses the step.
- **Entries:**
  - At 15:15 the daily run hands the entry over (`entry_pending`). E4's own `refusal()` runs unchanged, except its
    demand for a complete execution capture. The order is kept exactly as decided (write-once).
  - At the due mark, on A16's 15-minute copy (or an A4 capture inside the 2-minute window), every leg must have a
    valid quote, else "missed, no quote".
  - E4c's entry check and E4d's shared size then run on that copy and keep their own codes.
  - Then the owner's price cap (`ApprovedLimit`: no worse than the approved entry, else "missed, price moved").
  - Then C2's rules and C4's maximum loss run again on that copy and the account after the morning's earlier fills.
    This is a check only: the result is fill or a miss, and no decision record is written.
  - All legs fill or none. A miss is final.
- **Exits:** from E8's live date, E4's exit review only alerts ("EXIT trade … Close it at the next session's open";
  never a price) and the position stays open. At each later mark the owner is present, short legs are bought back
  first and protection is sold last. A leg without a valid quote waits for the next mark. A mark past the last expiry
  is left to E7's settlement.
- **Fail closed:** the step runs first in the daily run. If it fails or is refused (Drive down, a read past its cap,
  the step's 10-minute limit, a changed seal, a missing kept order), no book opens anything new that day. Exits still
  run.
- **Off until the owner decides.** `daily.live_from.owner_timing_fills` defaults to none. Until then E3 and E4 behave
  exactly as today, and the step only seals the availability file (a failed seal is alerted and blocks nothing). Going
  live is an owner decision row.

The fixed miss reasons are one table, `outcomes.MISSED_REASONS`, which E6 and S2 will import:
- no card;
- decision committed after the card;
- owner away;
- no quote;
- no future for that expiry;
- price moved;
- contract expired;
- insufficient funds;
- over risk cap.

**Exact version:** branch `story/e8-code-part1` at `cfd6a95b`. That is judge 203 addendum 3's PASS head `b79dee94`,
plus the judge's probe as a test. The branch tip adds only this request.

**Read:**
- story: `docs/stories/E8-owner-timing-fills.md` (rules 1-12, acceptance 1-10, S1 items);
- code: `fno/desk/owner_timing/`, starting with:
  - `step.py` (the daily step);
  - `entry_fills.py` and `due_fill.py` (entries);
  - `fill_risk.py` (the fill-day check);
  - `exit_fills.py` and `exit_alerts.py` (exits);
  - `clock.py` (due marks);
  - `availability.py` and `seal_log.py` (away dates);
  - `order_record.py` (the kept order);
  - `live_switch.py`;
  - `wiring.py`;
- hooks in other stories' files, each agreed with its owner:
  - `fno/desk/entries.py` (`EntryFiller`);
  - `fno/desk/exit_timing.py` and `exits.py` (`ExitTiming`, public `pending` and `closed`);
  - `fno/desk/daily_run.py` (`_unfilled`);
  - `fno/daily/wiring.py`;
  - `fno/constants_operations.py`;
- tests: `tests/desk_owner_timing/` (15 files) and `tests/timetable/test_owner_timing_block.py`;
- the judge: `reviews/judge/judge_203_e8_code_part1a.md` (four conditions for 1b, the early view, addenda 1-3).

**What is already proven (attack instead of repeating):**
- One leg without a valid quote fills nothing.
- One paisa worse than the approved entry misses; exactly at it fills.
- A 300-point overnight move leaves the filled legs unchanged.
- Two entries due at one mark (65 + 65 units against size 100): only the first fills, and the second gets E4d's
  code.
- Ask size 64 against 65 gives `protection_not_buyable`; bid size 64 gives `protection_not_sellable`; a one-sided
  protection quote gives E4c's code, as at 15:15.
- An earlier fill that morning makes C2's real `MarginRoom` refuse the next entry.
- No spot gives "no quote"; no future gives "no future for that expiry".
- A rerun after a stop part way finishes the same entry at the same mark without re-checking funds against its own
  fills. A rerun whose copy no longer prices it fails the step.
- An exit rerun skips copies older than its last closing fill (a bug found by the tests and fixed).
- Protection without a quote waits, then fills at a later mark.
- The exit alert is sent once. An undelivered alert is resent and has no T until it is delivered. The alert never
  carries a figure.
- Failed or refused fills block every book's new entries while exits run; not_live and ok block nothing.
- Every read is capped as a whole call (hung and trickling reads tested), and the timed store never writes.
- 7,061 tests pass on the merged tree.

**Questions, each answered accept / partial / reject, with evidence:**
1. **Realism of T + 60 minutes.** Is one fixed reaction time per view a fair model of a part-time owner? Part 2 adds
   R = 5 and R = 30 as reported views beside the R = 60 verdict. Does a fixed R bias the verdict for or against
   strategies whose edge decays overnight (short-premium structures decided at 15:00 and filled at 10:15 next day)?
2. **Price cap only (owner's rule, DESK_DECISIONS "E8 entry rule: price cap only").** A fill is allowed whenever the
   touch is no worse than the approved entry, however far the market moved. Can this select only the trades the
   market moved in favour of (adverse selection the other way: the good ones miss and the bad ones fill)? What would
   you measure in part 2's report to detect it?
3. **The fill-day check.** C2 and C4 re-run at the fill, but only as fill or miss. Is "insufficient funds" versus
   "over risk cap" the right split? Is checking against the account after the morning's earlier fills, oldest T first,
   right when two books' trades never share money?
4. **Misses in scoring.** A miss stays in the opportunity denominator with net 0 (S1 pending edit 10, E6b's counter).
   Does any miss reason need different treatment? For example: "card not delivered" is an operations failure, not the
   strategy's; "owner away" is the owner's choice.
5. **Exits that wait.** An exit is never limited or missed and fills at the next valid mark. A position can therefore
   stay open for a session or more after its rule fired. Is the paper account's open risk during that wait counted
   honestly by C2 the next morning (the position stays open, never "risk reduced")?
6. **Anything a code-focused judge could miss:**
   - the card delivered on one day but its decision rerun on another;
   - the live date set in the middle of a week;
   - an availability file edited between the seal and the card;
   - two copies at one mark (A16 and the A4 stand-in) disagreeing;
   - the known limit that A16 records only the near-month future;
   - the known limit that a no-snapshot day orders no exit until the next 15:15 review.

**Write your answer as a new file** `reviews/chatgpt/review_128_e8-owner-timing-code.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file.
