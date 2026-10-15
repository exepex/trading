# Response 199: answer to ChatGPT review 125 (RM2 real-money test record, story text)

Reviewed: `story/rm2-real-money-record`, text at `694b8a2f` (judge 198 addendum 2 PASS). ChatGPT: PARTIAL, one
stop-integrity change before code. All points accepted after checking against the RM2 text and `REAL_MONEY_GATE.md`.

1. **One-lot pairing: ACCEPT, plus a settlement fixture.** 4 orders x Rs 23.60 = Rs 94.40 and the Rs 260 pad are the
   judge's figures. Add a fixture with an E7-settled leg: C1's settlement charges, never an invented closing order.
2. **Two times per leg: ACCEPT.** The screenshot's capture time and the order-submission time (from the order
   confirmation or contract note) are stored apart; quote age = order time minus quote time; negative or over 5 minutes
   is "unknown", never zero. A16's fallback uses the latest observed fetch time at or before the order. Test: a 10:00
   screenshot with a 10:07 order is unknown; with a 10:04 order it is valid. No OCR, no Groww call.
3. **Late or missing exit reports: ACCEPT (the one change before code).** A stop is only as timely as its recorded
   exits. RM2's status becomes "records pending, no further test trade" when an entered real trade has no reported exit
   or settlement by its due exit time, or a Drive write failed. Before the next real-test card counts as placeable, open
   exits are reconciled and stops evaluated in actual exit-time order; a crossed stop takes effect at that exit, and any
   trade placed after it is flagged a protocol breach and never counts toward a pass. Fixture: an exit at 10:00 of
   -Rs 21,000 reported at 15:00 and a card at 12:00: the card is "do not place, unreconciled" and the stop is dated
   10:00. This is an instruction and a status for the owner, never an order block (nothing here touches orders).
   Unknown legs are excluded from the five-trade stop's mean but their count is shown beside it; the 10% unknown rule
   applies to the pass only.
4. **Strictly after: ACCEPT** as built; a missing 10:30 quote is unknown, never taken from 10:45.
5. **Privacy and interrupted writes: ACCEPT.** `record-entry` and `record-exit` never write prices or amounts to the
   public repository; an interrupted Drive write never marks an exit as recorded (test it).

Next: the RM2 builder writes 1-5 into the text; judge A re-checks only these; then RM2's code.
