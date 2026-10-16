# Response 228: answer to ChatGPT review 128 (E8 owner-timing fills, code part 1)

Reviewed: `story/e8-code-part1` at `cfd6a95b` (judge 203 addenda PASS). The head has since moved to `03c53ba6`, with O1
merged in; the E8 code is unchanged. ChatGPT: PARTIAL; the fill and risk model is acceptable, with one boundary to test
before activation. All six points are accepted. The tests below either already exist (the builder cites them) or are
added before merge.

1. **Fixed T+60: ACCEPT.** R=60 stays the frozen verdict. R=5 and R=30 are diagnostics on the same decision cohort,
   never separate trials. Part 2 shows fill rates, opportunity nets and overnight-gap cohorts per view.
2. **Price cap only: ACCEPT the reporting; no new filter.** The cap can select trades adversely after an overnight gap.
   That is a property of the owner's approved policy, not a bug. Part 2 reports:
   - every original eligible opportunity, by the sign and size of the overnight NIFTY move;
   - opened versus missed_price_moved;
   - net per filled trade and net per original opportunity;
   - the direction and structure of each trade.
   Missed trades are never booked as realised profit or loss. No ±0.5% filter is added without evidence.
3. **Fill-day risk and separate books: ACCEPT.** Within one book, entries are filled in server-T order and each is
   persisted before the next check, so earlier entries use funds first. Books never share cash. Equal T values use
   the existing deterministic order, which the story states.
4. **Misses in scorecards: ACCEPT.**
   - A miss after reaching the fill step adds zero to realised profit or loss but stays in the denominator.
   - MISSED_NO_CARD (delivery) and MISSED_OWNER_AWAY (availability) stay in the owner-achievable denominator but are
     reported apart from market-execution misses.
   - Gate refusals stay outside the denominator; pending entries are in neither count until they resolve; a partial
     unwind counts its real cash.
   This matches response 221 (E6b).
5. **Exits waiting: ACCEPT, with a test.** Integration test: after a short leg closes while its protective leg is still
   pending, the next morning's real RiskBook counts the remaining exposure and refuses a new entry that breaches the cap.
   The same test covers a wholly unfilled exit. A delivered alert never marks an exit closed.
6. **Cross-day, go-live, seals and copies: ACCEPT.**
   - **Live boundary (the most important):** only decisions created under live owner-timing mode enter E8's queue;
     earlier ones finish under E4. A fixture checks that a decision made before live_from and due after it is filled
     exactly once, never twice and never dropped.
   - **Prior-day orders:** a prior-day order recovered later keeps its original card T and due mark, or records its
     original miss.
   - **Seals:** a row appended after T never excuses a miss. A missing seal defaults to "available", the documented
     rule, and is labelled as such.
   - **Two copies:** MarkSnapshots.at takes the canonical A16 copy, or refuses when it disagrees with the A4 copy. It
     never chooses the copy that favours the trade. A planted fixture with disagreeing copies tests this, and the
     snapshot hash binds the chosen source.
   - **Missing future:** a missing further-month future is reported as missing, never synthesised.
   - **No exit review:** a day with no exit review leaves the book exposed and flagged, with no backdated exit. This is
     a known limit.

Next: the E8 builder adds or cites these tests and the part 2 reporting text. The judge confirms the delta. E8 part 1
then merges. The live switch stays off until the owner's date.
