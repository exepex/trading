# Judge 84: story E5, Book 1 by pure rules (branch, before merge)

Date: 14 Oct 2026 (UTC). Branch `story/e5-book1` at c12308c (from `main` 5a41a99). Claims:
`reviews/claude/response_85_e5-book1.md`. Story: `docs/stories/E-paper-desk.md` E5.

## Verdict: FAIL, two must-fixes, both shown by probe

The decider is right. Its runs replay, it uses no AI, and C4's gate holds. But the two seams it fills into E3's daily
run can **raise**, and E3's run has no per-book guard. One raise stops the whole run: snapshot, fills and **every
book's exits**. Both raises are reachable in normal use.

## Gates (my runs, `python -B`, caches cleared)

- Full suite: 2,664 passed.
- `ruff check`: clean. `ruff format --check`: 602 files formatted. Imports: clean (610 files).
- `git merge-tree` with current `main` (961d535): clean.

## Must-fix 1: a version with a stop-loss in words is approved, decided and filled, and then the exit step crashes

The orchestrator asked: does a version with a text stop-loss "not trade, or trade with no stop"? Neither. **It
trades, and then it breaks the desk.**
- Nothing on the entry path calls `time_exit_only`. It is called only in `PlaybookExitRules.rules`, at the exit review.
- My probe uses the E5 end-to-end test (`run_days`) with C4 passed and the paper version's exits set to
  `loss: "stop at 2x credit"`.
  - Day 1: Book 1 decides, and the 15:15 fill **opens the trade** (4 legs, e.g. `NIFTY26112725600CE` bought at
    45.13).
  - The same run's exit step then raises `ExitNotApplicable: sc-a-v1.yaml: exits code cannot apply (loss: stop at 2x
    credit)`.
- The consequences, read in the code:
  - `DeskSteps.review_exits` builds one dict over all books, so the raise also stops the other books' exits.
  - `DailyRun.run` never records the `exits` step, so every later run of that day and of every later day raises at
    the same place while the trade is open.
  - So the trade's stop is not enforced, its time exit is not enforced, and no other book's exit runs. That is the
    worst direction for risk.

**Fix (risk manager, reasoning only):**
- **Refuse at entry, not at exit.** A version whose exits code cannot apply must never be ordered. Check this at Book
  1's decision or orders. Better still, check it in D1's approval to `paper`, so it can never be approved. A test must
  show that such a version's chosen trade produces no order.
- **The exit review never raises for the run.** If one trade's rules cannot be built, alert, still apply its time
  exit, and review every other trade and book. A test must show that one bad version leaves the others' exits running.

I agree with the orchestrator that a strategy must never fill unless every one of its exits can be enforced by code. A
D1 format change is needed only to **use** stops or targets. To be safe now, the entry refusal above is enough.

## Must-fix 2: a replay refusal at 15:12 stops the whole run

- `D3CommittedDecisions._decision` calls `ReplayedOrders.orders`. That calls D3's `replay`, which raises
  `ReplayRefused` when the working tree's `fno/` or `config.yaml` differs from the run's `code_commit`. It also raises
  `OrdersRefused` on any difference.
- The collector pulls `main` first (`PlaybookGit.observed`: `git pull`). Any code or config merge landing between Book
  1's 15:00 commit and the 15:12 pull therefore changes the tree. Main gets merges at any hour: ChatGPT pushes, and
  judge-passed branches are merged.
- My probe: the same end-to-end run with a code tree that does not match. Result: `ReplayRefused: 2026-10-13-r1 was
  decided with code cccc…; the running fno/ and config.yaml differ`, raised out of `collect_decisions`. So no
  decisions record, snapshot, fills or exits for any book that day.
- The same applies at the fill step, which rebuilds the orders again through `recorded`.

**Fix:** per book, fail closed for **entries** only:
- a refused build records "not filled: <reason>" with an alert (#fno-desk);
- the run continues, and exits always run;
- add a test for each of `ReplayRefused` and `OrdersRefused`.

Keeping the decision's own code (a worktree of the recorded commit) is the fuller answer. Losing one day's entry is
acceptable; losing the exits is not.

## The orchestrator's five questions

| # | Question | Finding |
|---|---|---|
| 1 | Exits | Must-fix 1. The version trades with no stop and then halts the exits |
| 2 | `decided_at` and judge 82's on-time rule | **Not weakened.** `decided_at` is the commit time the collector observed. The fill step still checks `decision.committed_at` against the snapshot start on its own, and only runs recorded by the decisions step are filled. My plant setting `decided_at` to midnight is not caught, but only because of that duplicate check. Information, not a defect |
| 3 | Market vs C4 and C3 | **Spot:** the snapshot's `spot` is `chains[0].spot` (recorder), one of the pack spots C3 checks. Consistent. **Names:** legs are named by the recorded `contract_id`, which C4's round 3 (bf0d4af, `validity_market.py`) compares with the snapshot's listing. Consistent. **Mid:** Book 1 requires A4-valid, `bid > 0`, `ask >= bid`. C4's `QuoteRow.mid` takes any two-sided quote, so it is looser. Book 1 cannot choose an invalid leg, so no E5 defect. But C4's put-call-parity forward can use invalid or crossed quotes: a note for C4. **Forward:** Book 1 uses the same-expiry future, C4 uses parity. They are independent by design; tolerance is C4's matter |
| 4 | No-AI proof | **MET.** My plant adding `import fno.ai.wiring` inside the lazy `_features` is caught |
| 5 | Not run on real data | True. No real 3 pm snapshot is committed yet (`research/data/quotes/` is empty on `main`). The only committed 13 Oct snapshot (forecast golden case_b) is a fixture with empty `contract_id`, so it would give an empty market. Run the first real day by hand after the must-fixes |

## Per criterion

| # | Criterion | Check | Result |
|---|---|---|---|
| 1 | Book 1 equals D2 (replay, fixture days) | **I replayed the three runs myself** (D3 `replay`, same code): 0 differences on 13, 14 and 15 Oct. The records hold `trade`/`trade` on 13 Oct and `no trade`/`no trade` on 14 and 15 Oct (chosen = rule default) | MET |
| 2 | No AI reachable | Static closure plus run-time fakes; my plant is caught | MET |
| 3 | "No approved strategy" each session day | Tests pass. My plant dropping the file from the commit is caught. My plant reading `approved()` instead of `approved_on(day)` is **not** caught (should-fix) | MET |
| 4 | Committed before the deadline | Tests pass on fixture days. But a code merge before 15:12 crashes the collector (must-fix 2) | PARTLY |
| 5 | C4 failure never fills | Null and failed C4: no fill (tests). C4 passed fills. But a passed version with a text stop fills and then halts the exits (must-fix 1) | PARTLY |

## My plants (11, `tests/book1`, `desk`, `timetable`, `playbook`, `decisions`)

| Plant | Result |
|---|---|
| AI import on the lazy path | caught (1) |
| A quote with no IV kept | caught (1) |
| **Forward = spot instead of the same-expiry future** | **not caught** |
| Pack quote-file SHA-256 not checked | caught (1) |
| **No-approved check reads `approved()`** | **not caught** |
| Exit day `<` to `<=` | caught (2) |
| **Private pack hash not read (a missing private pack passes)** | **not caught** |
| `recorded_terms` reads every record | caught (1) |
| `decided_at` set to midnight | not caught (duplicate check, see question 2) |
| Exit expiry `min` to `max` | not caught (every fixture trade has one expiry; information) |
| "No approved strategy" file not committed | caught (1) |

**Should-fix (tests only):**
- forward from the future (a test where spot and future differ);
- `approved_on(day)` for the no-approved record (a version approved on the day);
- a missing private pack is refused.

## Claims vs reality

| Claim | Reality |
|---|---|
| "A version whose profit, loss or event exit is free text … is refused, never silently ignored" | It is refused only at the exit review, after it has filled, and the refusal halts every book's exits (must-fix 1) |
| "18 of 18 mutations caught" | Not re-run. 3 of my 11 plants survive that matter (should-fix) |
| Replay gives no difference on three days | Confirmed by my own replay |
| C4 needs no E5 change | Consistent with C4's round 3 naming check |
| Not run on real data | True, and stated |

## Project rules

- New package `fno/books/` with its own composition root; CLAUDE.md is updated.
- Constants are in `fno/constants.py`. Files are within 350 lines. No orders, no AI, no secrets.
- The `OrderBuilder` port change is small and justified.
- The `desk` CLI is extended in its single parser.
