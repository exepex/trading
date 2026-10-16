# Judge 302: F6/F7 story text, Book 3's engine and matched shadows (story/f6-book3-engine at e1994f0a)

**Verdict: FAIL on the story text: 3 should-fix findings and 2 minor.** The request named 24970758, but the branch
moved to e1994f0a at 11:27, so I judged e1994f0a. Since 24970758 the earlier interface contradictions with F1t are
gone:
- the answer now sits inside F1t's `decision`;
- `Book3Decider(AiBookDecider)` replaces `Book3Engine`, with one commit;
- the registry row's `model` is `registered_model`;
- a bad shape is refused at `seal`.

## Checked myself (strong evidence)
- D5 is not on `main`: `story/d5-constitution-code` at 9a9a1b96 is unmerged, while D4 is merged. F6 correctly
  depends on both.
- Book 3's day record with a null strategy is allowed by D3 at b49abdde (judge 300).
- The private pack reads `journal/book3_ai` and `book3/` (`fno/desk/private_pack.py:20`).
- The cap key `risk.profiles.books.max_loss_per_trade_rs` is 10000 (`config.yaml:53,80`).
- The rule-key reasoning holds: `parameters_sha256` covers the name and version, so an equality test on it can never
  catch a renamed copy. Some evidence: I read the claim, but did not open D1's hash code.

## Findings

**Should-fix 1. Book 3's orders and exits have no owner.** Strong evidence. Fills need an `OrderBuilder` that turns a
committed Book 3 run into entry orders (Book 1's replays D2 on the playbook, `fno/books/book1_orders.py:31-57`; Book
3's must replay with the stored picks against the registered specs), and an `ExitRules` that applies the exit day fixed
at the decision from the spec (Book 1's: `book1_exits.py:34`). F6 puts "fills (E4/E8)" out of scope and lists them
under F1t; F1t only adds dispatch.

Fix: F6 owns `Book3Orders(OrderBuilder)` and `Book3ExitRules(ExitRules)`, since it owns the replay and the spec, with
criteria. The replay of a changed pick must refuse orders, as Book 1's does. Otherwise, name another owner.

**Should-fix 2. The restore rule contradicts F1t.** Strong evidence. F6's "Agreed with F1t" paragraph says "tracked
files to HEAD, new files deleted"; F1t at 2639b915 says "the snapshot, not HEAD, is the reference" (taken just before
`decide()`). `research/ledger.csv` is shared with the research factory, so a restore to HEAD would delete a
factory row written earlier in the day.

Fix: adopt F1t's snapshot rule word for word.

**Should-fix 3. The day sheet's writer is undecided.** Strong evidence. The day sheet is "a private-pack item, built
at the pack step" through "one hook proposed to F5's builder". The register's only row for such a hook is "Book 2
pack rule default" (Book 2 only, planned).

Fix:
- Name who builds the hook for Book 3, put it in Depends, and add a criterion: the day sheet exists before the private
  pack is built, its bytes are in the private pack's hash, and it is computed on the same 15:00 features as D2.
- F6 may simply write `journal/book3_ai/day_sheet/<d>.json` at the pack step through that same hook.

**Minor.**
1. State that proposals are registered only from a promoted answer. This is implied, because the decider runs only
   after F1t accepts the answer. Add one test: a late or invalid day registers nothing.
2. F7: a take naming a width outside the version's set becomes `no_decision`. Good. Also state that the shadow file
   is written even when Book 3's real decision is refused by C2 or C4. That is implied by "never the account", but
   criterion 3 tests only "with and without shadow entries".

## Over-engineering check
The design is small: no Book 3 width or lots choice (a new width is a new spec), no stored pilot label (S2/S3 derive
it), and one selection allocator offered to F5. No layer beyond D2, C2, C4 and D3 is added. Accepted (reasoning only).

## Owner expectations
- Book 3 invents and registers strategies and trades only from d+1: design 12.3, criteria 1-3.
- No override: met through D3.
- Red team and cards never block: criterion 9.
- Pilot: criterion 10.
All traced.
