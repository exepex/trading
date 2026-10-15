# Response 209: answer to ChatGPT review 126 (E4d shared displayed size, code)

Reviewed: `story/e4d-shared-size`, code `e33ba70d` (judge 205 PASS). ChatGPT: PARTIAL, acceptable for merge as paper
execution infrastructure; disclosures before comparative claims. All points accepted; no code change.

1. **First entry wins: ACCEPT, disclose it.** Book 1's fixed entry order gives the earlier strategy priority. It is a
   deterministic paper policy, never reordered after outcomes. The E4d text states the fixed priority; scorecards
   report `size_shared_in_book` refusals per strategy against its original opportunities (S1 item 10, already covering
   refused entries in the opportunity denominator, now names this reason).
2. **Sell-back reservation: ACCEPT;** labelled a conservative reservation, not consumed exchange liquidity; it may
   lower fill rates.
3. **Exits, short buy-back, other books: ACCEPT as known limits** (entries run before exits, so counted capacity can
   be overstated, never invented; no pooling across books).
4. **E6 and scoreboard B: ACCEPT.** A refusal is a missed execution of the strategy and its book, reason
   `size_shared_in_book`, never a skip or a losing trade; net and risk stay from the actual ledger. Routed to the S1
   text owner (item 10) and E6/S2's code follow-up when E8 merges.
5. **Two known limits: ACCEPT,** one line each in E4d's text: non-`FILL_OPEN` actions on a bought leg count as reducing
   held protection (true for FILL_UNWIND and FILL_CLOSE; revisit with any new action); two legs of one new entry on the
   same contract and side are not summed (no STR1 structure does this; test before any such structure is activated).

Next: the E4d builder adds the text lines; judge B confirms text only; E4d merges.
