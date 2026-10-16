# Judge 307: F5 story text, Book 2's decider (story/f5-book2-decider at 6d2b6331)

**Verdict: FAIL on the story text: 2 should-fix findings and 2 minor.** The core design is right:
- the sheet is computed by code inside the private pack;
- `rule_default` and `eligible` come only from the sheet, never from the AI;
- F6's `SelectionAllocator` is reused, with a rebuild for width and lots;
- C4's `EnvelopeMode` re-checks independently, and the unproven limit is re-checked at C4 (D4 option 2, judge 260
  addendum 2);
- the estimand label is named.

The interfaces with F1t do not match yet.

## Checked myself (strong evidence)
- D4 is merged: `EnvelopeMode` is in `fno/checks/wiring.py:85-91`.
- `eligible` = the versions that reached C2, as judge 260 addendum 2 settled.
- F1t at f1204a5a, the latest text that passed (judge 301 addendum 1):
  - `seal` checks F1t's base first: "`decision` is an object with `action` (text) and `reason` (one line)";
  - then it calls the book's shape check, named `check_decision(decision) -> list[str]`, "the port's one name", with
    F5's in `fno/book2/answer.py`;
  - the port block says "Owners: F5 (Book 2), F6 (Book 3)" for each book's `OrderBuilder` and `ExitRules`.

## Findings

**Should-fix 1. The answer shape and the check's name contradict F1t's port.** Strong evidence.
- F5's shape is `{"slots": [...], "reason": str}`. It has no top-level `action`, so F1t's base check would refuse every
  Book 2 answer at `seal`.
- F5 names its check `check_answer(obj, sheet=None)`; F1t's port names it `check_decision(decision)`.

Fix: put `action` (`follow_rule`, `no_trade` or `trade`, for example the day's summary, or `trade` when any slot
trades) and `reason` at the top of `decision`, with the slots inside it. Name the check `check_decision(decision)`;
the decider's sheet-aware check can be a second function. Confirm the result with F1t's builder.

**Should-fix 2. Book 2's orders and exits are missing.** Strong evidence. F1t's port makes F5 the owner of Book 2's
`OrderBuilder` and `ExitRules`, but F5's scope and criteria do not mention them. Fills need two pieces:
- an order builder that replays a committed Book 2 run, with its stored `selection` picks and any width or lots
  rebuild, and orders only the committed "trade" records (the shadow-only default case included);
- exit rules that fix each trade's exit day from the playbook version as the run read it.

Fix: add both, as F6 did (`Book3Orders` and `Book3ExitRules` reuse Book 1's `ReplayedOrders` and `PlaybookExitRules`),
with criteria: a changed pick or sheet refuses every order; a C4 block is never ordered; editing today's version file
moves no exit.

**Minor.**
1. **The shadow-only path.** When the account "takes the rule default", say that the default itself went through C2
   and C4 in the same run (it is the rule default, so it reached C2, but C4 must still pass it). A C4 failure of the
   default must then give no trade, with both records written.
2. **The unproven re-check at C4.** Name the C4 file and mode it changes (`EnvelopeMode` only, or every mode), and
   confirm that Book 1's C4 behaviour is unchanged by a test, since C4 is shared.

## Open questions (for the orchestrator; my view)
1. **F4 is not built, and has no owner.** F5 recommends that Book 2 waits for F4 (design 12.2: the judge can block).
   That blocks Book 2's go-live on a story that has no owner, and the O11 plan (judge 305) talks of folding F3 into T3
   and leaving F4 aside. This is the owner's decision: wait for F4, or switch on with `judge: "not built"` and C4 as
   the last gate, labelled. Put it to the owner before Book 2's go-live; it does not block F5's code.
2. **One slot per default trade:** this matches D4's one-choice-against-one-default check, and is simpler. I agree
   (reasoning only).
