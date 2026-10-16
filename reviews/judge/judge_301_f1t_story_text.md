# Judge 301: F1t story text, the AI books' trading runner (story/f1t-ai-trading-runner at 2639b915)

**Verdict: FAIL on the story text (quality rule 1): 4 should-fix findings and 2 minor.** Code may start after the
fixes are pushed and re-checked. The request named e59b50be, but the branch moved to 2639b915 at 11:27, so I judged
2639b915. Since e59b50be the text has adopted the orchestrator's ruling (model "unknown" means no trade), the analyst
cards in the pointer, Book 2's rule default inside its private pack, and the write-path snapshot and restore. Those
are accepted below.

## What I checked myself (strong evidence)
- **Code facts cited by the text: all true on `main`.**
  - `RoutineTrigger` (`fno/pipeline/trigger.py:36`).
  - `Commitment`, `reveal_text`, `open_reveal` (`fno/ai/seal.py:33,61,65`).
  - `GitMainTransport` (`fno/ai/transport.py:30`) and the `PushReceipts` interface (`fno/ai/receipts.py:34`).
  - The stop rule: 2 breaches in the last 20 session days, under one version (`fno/ai/stop_rule.py:13-21`).
  - `PACKED_BOOKS = (BOOK1_RULES,)` (`fno/desk/pack_wiring.py:16`).
  - `collect_decisions` (`fno/desk/daily_steps.py:90`).
  - `--self-timed` (`fno/budget/cli.py:31`).
  - The private pack's per-book allowed folders (`fno/desk/private_pack.py:17-21`).
  - O1 is on `main`, with `book1` between `pack` and `decisions` (`fno/constants_operations.py:44-55`).
  - Timetable: pack at 14:58, retried until 15:10; decision deadline 15:12 (`config.yaml:157-163`).
- **Forecast routine audits** (`research/forecasts/ai_v1/2026/*_audit.json`): the facts are mostly right, with two
  errors (finding 1).

## Findings

**Should-fix 1. The "unknown model means no trade" rule would have blocked 5 of 6 real book-days.** Strong evidence.
`model_reported` was `"unknown"` on 15 Oct (both books) and 16 Oct (Book 2). Only 16 Oct Book 3 reported
`claude-opus-5-5`, with `model_check: match`. The text says "Book 3's model `unverified`", but it was Book 2. Under the
ruling, the forecast record shows 1 usable book-day out of 6, not "one of three days". The text also says the routines
were "fired at 15:10:20 IST", but 14 Oct fired at 19:27:47 IST and failed at the setup script.

Fix:
- Correct both facts.
- Add a way for the decision session to report its served model reliably, plus a criterion. For example, the
  bootstrap prompt has the session read its own model (the session's identity line or its session-description tool)
  and write that exact ID into `model_reported`.
- Measure it on the go-live non-counted fire. Otherwise the fail-closed rule turns most days into
  `model_unverified`, a silent cap on Books 2 and 3 that nobody chose.

**Should-fix 2. Step order cancels the AI books whenever `book1` is slow.** Strong evidence for the order; reasoning
for the effect. O1 runs its steps one after another.
- `ai_fire` sits after `book1`, but needs only the packs. Every second `book1` takes is lost from the AI's window
  (`latest_fire` 15:07).
- `ai_collect` must take observation 1 at 15:10:00, and its "started over 30 s late, so every book is `late`" rule
  fires whenever `book1` runs past 15:10:30. The text allows `book1` up to 600 s.

Fix:
- Place `ai_fire` right after `pack`, before `book1`.
- Either bound `book1` so that `ai_collect` starts by 15:10:30 and show the measured duration, or take observation 1
  independently of the step order.
- Add a boundary test with a slow fake `book1`.

**Should-fix 3. Nobody owns Book 2's and Book 3's fill and exit rules.** Strong evidence. The text adds per-book
`OrderBuilder`/`ExitRules` dispatch only.
- Book 1's `ReplayedOrders` (`fno/books/book1_orders.py:31`) replays D2 against the playbook.
- Book 1's `PlaybookExitRules` (`fno/books/book1_exits.py:34`) takes the time exit decided from the playbook.
- A Book 3 run needs a replay with the AI's picks against registered specs (D5), and exits from the spec. Book 2's
  run needs the envelope choice.
- F6's text (e1994f0a) lists "E4/E8 fills" under F1t. F1t lists the books' decisions under F5 and F6. So both
  implementations fall between the stories.

Fix: name the owner of each book's `OrderBuilder` and `ExitRules` (the natural owners are F5 and F6, who own the
replay), add them to the port table, and make criterion 8 use the real ones once they land.

**Should-fix 4. The public reveal can leak the private account.** Strong evidence for the facts; reasoning for the
risk.
- E2c moved fills, positions and marks to Drive (owner, 15 Oct, "A: move to Drive"): public fills let bid prices be
  rebuilt. The public record keeps per-book daily totals only.
- F1t prints the private pack (account files with fill prices) to the model, then publishes the model's answer
  (`reason` up to 600 characters, Book 3's proposals and shadow reasons) in the public repository as the reveal.
- `.gitignore` covers `.ai_book/` but not the new `.ai_decision/` working folder.

Fix:
- Either keep the reveal in Drive with its hash committed (as O9 does for data), or refuse at `seal` any number token
  in the answer that appears in the private pack's account files. The text should state which.
- Add `.ai_decision/` to `.gitignore`, with a test.

**Minor.**
1. The shape-check name is inconsistent: the design says `check_decision(decision) -> list[str]`, while open question
   1 says Book 2's is `check_answer(obj)`. Pick one name for the port.
2. Depends should list the private-pack hook that writes Book 3's day sheet and Book 2's rule default before the pack
   step (register row "Book 2 pack rule default"; F6 relies on the same hook). Also measure the O5 scan on a full
   fixture pointer: account files that the scan flags would make every day `not_fired`.

## Interfaces with F6, F5 and F2
- Agreed and consistent in both texts: the answer is `{"model_reported", "decision"}` with Book 3's keys inside
  `decision`; `AcceptedDecision` and `DecidedRun`; the registry `model` is `registered_model`; one commit for the
  registration and the run.
- `analyst_cards` comes from F2's `CardsOfDay` with a 30 s bound: consistent with F2 at 47fcb523.
- One contradiction remains, on F6's side (judge 302 should-fix 2): F6 restores "tracked files to HEAD"; F1t restores
  to a snapshot taken just before `decide()`. F1t's rule is the right one, because `research/ledger.csv` is shared
  with the research factory.

## Owner expectations covered
Fail closed on every miss, an alert and a record for each (rows 246-247), and no AI answer reaches a fill without C2
and C4: covered by the judging table and criteria 6, 8 and 10.
