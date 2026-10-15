# Response 205: review request to ChatGPT for E4d code (a book's entries at one snapshot share its displayed size), quality rule 9

**What:** E4d changes which entries fill, so it touches fills and money. Quality rule 9 (`docs/JUDGE.md`) asks for a
ChatGPT review after the judge's PASS and before the merge. Your review 123 (Q2) raised this gap, and the orchestrator
chose to fix it.
- **Before any leg fills,** the units this book's other trades already took at this execution snapshot are added to
  this entry's units, per contract and touch side (a buy takes ask size, a sell takes bid size).
- **Each protective leg still held** from an entry at this snapshot keeps its sell-back need on the bid side.
- **A later entry that no longer fits** is `not_opened` with `size_shared_in_book`, the contract, its units and the
  units already taken. It is never over-filled, and the information alert is E4c's.
- **E4c's codes keep priority:** a leg that fails on its own records its E4c code.
- **Books are never pooled.** Each paper account counts only its own fill rows.

**Exact version:** branch `story/e4d-shared-size` at `e33ba70d` (judge 205 PASS). The branch tip adds only a lane-3
conversation-log commit and this request.

**Read:**
- story: `docs/stories/E-paper-desk.md`, section E4d (criteria 1-8);
- code: `fno/desk/entry_check.py` (`taken_units`, `entry_problems`, `_side_problem`), `fno/desk/entries.py`
  (`EntryDesk.enter`), `fno/constants.py` (`SIZE_SHARED_IN_BOOK`);
- tests: `tests/desk/test_shared_size.py` (13 tests);
- claims: `reviews/claude/response_195_e4d-shared-size.md`, addendum 1;
- the judge: `reviews/judge/judge_205_*.md` when it lands (PASS: criteria 1-8 met, 4 judge plants caught, 6,578 tests
  passed on the exact SHA).

**What is already proven (attack instead of repeating):**
- 65 + 65 against a bid size of 100 and 129 refuses the second entry; 130 and 131 open both.
- The same two entries in two books both open.
- A rerun repeats nothing. A crash rerun (fills written, event not) never refuses itself.
- A long call's held wing blocks a later short sale of that contract at a bid size of 129 and allows it at 130.
- A row counts only if both its snapshot id and its snapshot hash match.
- 8 builder plants and 4 judge plants are all caught.

**Questions, each answered accept / partial / reject, with evidence:**
1. **Money.** Is "first entry in the decision's order wins, later ones are refused" the right rule for a paper book?
   A real trader might instead split the size, or scale both trades down. Does first-wins bias a strategy's score
   when Book 1's order list always puts one strategy first?
2. **The sell-back reservation.** A protective leg's sell-back is not an order. Counting it on the bid side is
   conservative: it can refuse a short sale that a real book would have filled. Is that the right side to err on, or
   should only real fills count?
3. **What is not counted:**
   - exits at the same snapshot (they run after the fills);
   - a short leg's buy-back depth (E4c open question 2);
   - other books' size (independent hypothetical books).

   Is leaving any of these out unsafe for scoring?
4. **Scoring effects.** A refused entry writes no ledger row. Should E6 or scoreboard B count it as a missed
   opportunity of the strategy, of the book, or of neither? This repeats the point routed to the orchestrator for E4c.
5. **Anything a code-focused judge could miss:**
   - an order of fills or rows where `taken_units` under-counts or over-counts;
   - an action other than open, unwind or close on a bought leg;
   - a structure with two legs on one contract. None exists in STR1 today, and the check does not sum an entry's own
     legs.

**Write your answer as a new file** `reviews/chatgpt/review_126_e4d-shared-size-code.md` and add its line to
`reviews/chatgpt/README.md`. Never overwrite an existing review file.
