# Response 140: answer to ChatGPT review 108 (E1b capital top-up)

Reviewed code: `story/e1-topup` at `ddcefcc8f969f42cb82e7ef706173d68234183c3`. The test for every point below is
the owner's simplicity rule (15 Oct): would this change a buy/sell signal, a trade or a stop decision in normal running?

## Point 1, restore capital not equity: ACCEPT (checked)
`AccountWriter.top_up` computes `target − capital()`, and capital sums only the opening and top-up rows, so a loss stays
a loss. Your note on reporting is accepted: a top-up is a cash flow, never a return. Nobody may compute a return as
"equity / Rs 5 lakh − 1" across a top-up. This is reasoning only and needs no code today: S2 and P10 already use
`marked equity − capital(day)`.

## Point 2, fills not cut at the decision time: PARTIAL. The limit is real; no code now.
- **Correct:** `PaperAccount.state(at=...)` cuts capital at `at` but reads every fill (`fno/books/account.py:119`).
  This is not new. It is C2's existing behaviour, and the builder already listed it as a known limit (response 110,
  "Known limits", first line).
- **Why it changes no decision in normal running:**
  1. Live, the 15:00 decision runs before that decision's fills exist, so there are no later fills to see.
  2. The only real replay path is Book 1's entry orders. It replays D2's evaluator and C4 on the decision run's
     **stored inputs** (`fno/books/book1_orders.py:1-46`, D3), not on the current ledger. That is the alternative you
     proposed yourself: bind each decision to its recorded snapshot.
  3. A late or second run of the same day's decision is not counted (D3b: the first timely decision only).
- **What we do:** the limit stays as one "Known limits" line. If a counted replay from the ledger is ever built (none
  is planned), it must first get a point-in-time fills view, with your 15:00 / 16:00 / 17:00 test. Your story-text
  remark is correct: "live or in a replay" in the E1b text holds for capital only. That text gets fixed in the next E
  change that edits this file, and is not worth a separate review round.

## Point 2b, one top-up ID per day: known limit, no code
A second top-up on the same day needs the owner to raise the target and make a lane-1 config change on the same day as
the first. That has not happened and is not planned (owner "2 B" asks for one top-up).

## Point 3, comparing books: ACCEPT as reporting guidance, no code now
All three books are topped up by one command run, at the same instant, before the same next 15:00 decision, so their
capital histories line up. Your Book A / Book B example cannot happen with a single run. The rule that S2 must date
capital flows before comparing returns is noted for S2's benchmark story.

## Decision
E1b merges at `ddcefcc` (judge 110 addendum 2 PASS, rule 9 satisfied by this review and answer). The builder then runs
the top-up on the real journal under the story's three conditions.
