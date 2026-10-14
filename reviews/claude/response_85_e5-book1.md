# Response 85: story E5, Book 1 by pure rules: builder's claims

Builder session, 14 Oct 2026. Branch `story/e5-book1`, from `main` 5a41a99 (E3 merged). Judge first; nothing goes to
`main`.

**Verdict in one line:**
- **What it does:** Book 1 decides by code alone (D2 through D3's decision run on its approved versions, committed),
  and E3's two seams are filled. Orders come from replaying the committed run through D2; exits are the version's time
  exit.
- **Commands:** `desk book1` and `desk run` exist.
- **Not live:** until C4 merges and writes `validity.c4`, **no Book 1 order can fill** (E3's `RecordedC4Pass`). That
  is the intended safe state, and the tests show it.

## 1. The design (`fno/books/`, wired in `fno/books/book1_wiring.py`)

| Part | What |
|---|---|
| `book1.py` `Book1.decide(day)` | Session days only (A7). D3's `DecisionRun.decide` runs over D2's evaluator with Book 1's inputs, and the run is committed. With no `paper` version, it also commits `no_approved_strategy.json` beside the run; D2 still runs, so registered candidates are shadow-tested. A rerun with the same inputs decides nothing twice (D3's duplicate check). |
| `book1_inputs.py` | Reads the **two packs** (both hashes go into the record) and the canonical A4 snapshot, which must be the one the common pack records (same ID and quote-file SHA-256); otherwise refused. Also reads B7's live features, Book 1's own account through C2's `load_risk_book`, E6's trade counts and the shadow books. |
| `book1_market.py` | C2's and D2's `Market` from the canonical snapshot. A valid two-sided quote enters at its mid, named by the provider's recorded symbol (now carried on `LiveQuote.contract_id`), with an IV from B1's Black-76 on the same-expiry future. A quote with no mid, symbol or IV is left out, never guessed. |
| `book1_orders.py` `ReplayedOrders` (E3's `OrderBuilder`) | Replays the committed run through D2's evaluator (D3's `replay`, refused under other code). It must give exactly the stored records, and its **chosen book outcomes** then carry C2's decision with the exact proposal it judged, so the order is never rebuilt from JSON. `decision_id` is the D3 opportunity ID, and `decided_at` is the run's commit time (the port gained that argument). |
| `recorded_terms` | Open trades' structure, width and lots, read from Book 1's committed records (C2's view of the book needs them; nothing else stored them). |
| `book1_exits.py` `PlaybookExitRules` (E3's `ExitRules`) | Each open trade exits on its version's **time exit, the day D2 computed** (`OpportunityFinder.exit_day`, now one method shared by D2 and Book 1; new `ExitOnDay` rule behind E4's `ExitRule`). E4 applies it, including C3's pending exit when prices are unverified. A version whose profit, loss or event exit is free text other than "none…" is **refused** (`ExitNotApplicable`), never silently ignored. The repository's example version passes ("none beyond the bought wings"). |
| `book1_cli.py` | `python -m fno desk book1 [--day]` and `python -m fno desk run [--day]` (E3's `DailyRun` with Book 1's orders and exits). Paper only, and no routine starts them. |

**C4:** Book 1 calls C4 only through D3's decision run (`build_decision_run`). When C4 merges, its `validate_chosen`
inside the run writes `validity.c4`, and E3's `RecordedC4Pass` reads it at the fill. E5 needs no change for that.

## 2. Evidence

- **Criterion 1 (replay):** on three fixture days, every run replays through D3's `replay` with no difference (same code
  commit). The day's chosen list equals D2's direct evaluation on the same inputs, and every record's
  `chosen_action == rule_default`. At least one day trades.
- **Criterion 2 (no AI):**
  - **Statically:** the closure of everything Book 1's modules import (lazy imports included, followed through all
    `fno` modules, 187 modules) holds no `fno.ai` and no AI SDK. It does reach the market-data providers (Groww, NSE)
    through the composition root: data, not models. That is stated in the test.
  - **At run time:** every AI module and SDK is replaced by a fake that fails on any use, and Book 1 still decides and
    orders.
- **Criterion 3:** with only a research candidate, each fixture session day commits `no_approved_strategy.json` with its
  run, and a Sunday decides nothing.
- **Criterion 4:** end to end through E3's real daily run and real D3 reader. Book 1 commits at 15:00, and the 15:12
  collector records its run on every fixture day (none late).
- **Criterion 5:** end to end, three ways:
  - `validity.c4` null (today's reality): no fill;
  - C4 failed: no fill;
  - C4 passed (simulating the merged C4 writing it): the order opens at the 15:15 capture with `sc-a-v1` and the
    opportunity ID. Exits then hold until the time exit.
- **Parts:**
  - the market (only valid, named quotes with an IV; no spot refused);
  - inputs refused with no pack or a pack recording another file;
  - recorded terms (chosen trades only);
  - only D2's chosen book trades become orders (a shadow candidate does not), and a run edited after commit is
    refused;
  - the exit day is D2's, including a holiday (expiry 10 Nov: exit 19 Oct, because 20 Oct is Dussehra);
  - text exits are refused.
- Mutations (`python -B`, caches cleared): **18 of 18 caught**.
  - The first run left 4 survivors, each a missing test: a non-replaying run, shadow outcomes ordered, the exit-text
    check skipped, and the exit day not D2's. Tests were added. A fifth plant (exit day not a session) needed the
    holiday case.

## 3. What the owner or orchestrator should know

1. **No Book 1 order fills until C4 merges.** This is by design (judge 83). Until then `desk run` records decisions, the
   capture, "not filled: no completed C4 pass" and exits.
2. **Not run against real data here.** `desk book1` and `desk run` need the day's committed packs, the canonical
   snapshot, the panel and git on the routine's own checkout. The tests use fixtures and fakes at the git and clock
   seams only. The first real day should be run by hand and its run file read.
3. **Exits are only the time exit**, because the playbook's other exits are free text. A version that states a profit or
   loss exit in words is refused at the exit review. To use one, the playbook format needs a machine-readable exit
   (a D1 change, reasoning only).
4. **The live features reload the research panel each day** (about two years). That is acceptable at one decision a
   day, but it is a cost.
5. Book 1's whole path is deterministic code, and its records replay. The AI books (F5/F6) will need their own
   `OrderBuilder`.

## Addendum 1: judge 84 (FAIL), fixed

Both must-fixes were checked against the code and are right.
- **Exits:** `PlaybookExitRules` raised on a text exit, and `review_exits` was one dict over all books inside an
  unrecorded step. One such version halted every book's exits every day.
- **Replay at the deadline:** `D3CommittedDecisions` built the orders, and so replayed, inside `collect_decisions`. A
  `ReplayRefused` there stopped the snapshot, the fills and the exits for every book.

1. **Exits, at the root.** One rule, `fno/playbook/exit_terms.unenforceable_exits`, says which stated exits code cannot
   apply (today any text exit other than "none…"). It is used three ways:
   - **(b) D1:** the new approval check `ExitsEnforceable`, wired in `build_playbook_loader`, refuses `paper` for such
     a version. The loader and the status change run the same checks.
   - **(a) Book 1's orders:** `ReplayedOrders` refuses (`OrdersRefused`) a run that chose such a version. That is a
     backstop for a hand-edited file.
   - **The exit review never raises:** such a trade still gets its time exit, with an alert naming the exit nobody
     applies. Exit rules read the committed files without D1's checks (`snapshot_playbook`), so a refused playbook
     cannot halt exits. `review_exits` now reviews book by book: a failure is recorded (`reviewed: false, error`) and
     alerted, and the other books are still reviewed.
2. **Replay at 15:12.**
   - The decisions step no longer builds orders. It records the run ID and holding commit only (`CommittedDecision`
     lost its `orders`).
   - Orders are built **at the fill, per book**, through the `OrderBuilder` that `DeskSteps` now holds.
     `ReplayRefused` (code merged after 15:00) and every other refusal become `OrdersRefused`. That book's entries
     fail closed, with "not filled: the committed decision gives no orders (...)" and an alert. The snapshot, the
     other books' fills and every exit review still run.
   - **On the judge's suggestion (replay in a worktree of `code_commit`), partly agreed.** It would save Book 1's day
     after a same-day merge, and fail-closed stays the fallback either way.
   - But it cannot be done in process: the running process cannot import another commit's code. It needs a
     subprocess `python -m fno` in that worktree returning the orders, a new protocol that serialises C2's decision
     and proposal across processes.
   - I propose it as its own story. Meanwhile, an operating rule closes most of the gap: no merge to `fno/` or
     `config.yaml` between 14:55 and 15:20 IST. Reasoning only; the orchestrator's call.
3. **The three surviving plants now have tests:**
   - the IV is Black-76 on the same-expiry future, compared with the spot-based value;
   - a version approved on the day gives "no approved strategy" that day (`approved_on(day)`, not `approved()`);
   - a missing private pack is refused. Both packs are now checked before any other input is read.

Tests added:
- an unenforceable version, and a code merge after the decision, each fail closed for entries only, the day running
  to its exits;
- D1 refuses `paper` with a stop text and loads the "none" form;
- one book's failing exit review leaves the other's and the run intact;
- the playbook fixture's loss text now reads "none (the bought wings cap it)", because "wings" alone is now rightly
  refused.

Mutations (`python -B`, caches cleared): **27 of 27 caught**, including the judge's three.

**Ruling (1) per trade (commit after 3f61f0b):**
- A trade whose playbook version cannot be read gets no rule: E4 holds it and alerts, and the alert names it.
- Every other trade of the book keeps its time exit. Before this change, one unreadable version cost the whole book its
  exits that day.
- Test added; its plant is caught.

## Addendum 2: judge 84 addenda 1 and 2, fixed (replaces 8423594's per-trade approach)

Both must-fixes were checked against the code and are right:
- `startswith("none")` let "none until day 10, then stop at 2x credit" through;
- exits re-read today's playbook files, so a broken unrelated draft halted them all, and 8423594 left an unreadable
  version's trade with no exit at all.

- **A) "none" is the whole value.** `unenforceable_exits` now accepts only exactly "none" (trimmed, any case).
  - The repository's example version now reads `none` with the notes as YAML comments. Comments do not change the
    fingerprint, and the file is unregistered.
  - The fixtures say "none".
  - Tests: "none until…", "none; stop at…" and "None (but stop at 2x)" are each refused; "none", " None " and "NONE"
    pass; the example version passes.
- **B) The time exit is fixed at the decision** (`fno/books/book1_records.py`).
  - Each chosen trade's exit day is computed from its committed run: the version file as the run read it
    (`inputs.json`), and the expiry from the opportunity ID, through D2's `OpportunityFinder.exit_day`.
  - `PlaybookExitRules` takes its rule only from there. Today's version file (that one file only) is read just for the
    per-trade alert, when it is unreadable or states an unenforceable exit. A trade with no committed record is left to
    E4's hold, with an alert.
  - Tests:
    - the exit is the decided one;
    - an unreadable, empty or deleted version file, and an edit that would move the exit, leave it unchanged and alert;
    - today's file stating a stop alerts while the decided exit runs;
    - through the real wiring, an unrelated broken draft leaves the exit applied;
    - no record means no rule and an alert.
- **Found while merging C4 (not in the judge's list): the order replay now runs C4's validator.**
  - With C4 merged, every record holds its C4 result, so `ReplayedOrders` without the validator would find every run
    "does not replay". In the real wiring, no Book 1 order could ever have filled.
  - `build_book1_orders` now passes `build_trade_validator(cfg, book1_rules, root)`, the same one D3's decision run
    uses.
  - Orders are made only for opportunities whose committed record says "trade", so a choice C4 blocked is never
    ordered.
  - Tests: with C4 passing, orders are made; with C4 failing, none; without the validator, the run is refused.
- **Merged `main` (dafbebe, C4) into the branch.** In `CLAUDE.md`, both roots are kept.

Mutations (`python -B`, caches cleared): **31 of 31 caught**. The new plants:
- "none" as a prefix;
- the exit taken at expiry instead of the decided day;
- untraded records counted;
- no alert from today's file;
- no alert without a record;
- the C4 validator not replayed;
- a C4-blocked choice ordered.

## 4. Gates

Full suite, `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py` and the 350-line limit: the
results are in the commit message and the message to the orchestrator.
