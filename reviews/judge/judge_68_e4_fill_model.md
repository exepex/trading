# Judge 68: story E4, fill model and exits (after-the-fact review)

Date: 14 Oct 2026. Code: trading bed6ca8 (E4), tip 0f955c6. It reached `main` **without a PASS**, the third
breach of the owner's rule (the builder had not read it). Claims: `reviews/claude/response_71_e4-fill-model.md`.

## Verdict: FAIL until the entry limit lands (the orchestrator's must-fix, branch `story/e4-entry-limit`), plus one should-fix on expiry. Criteria 1-6 as written are MET

## Per criterion

| # | Criterion | My check | Result |
|---|---|---|---|
| 1 | Fill = ask (buy) or bid (sell), snapshot hash in the row | The builder's hand case recomputed: fly premium (150 + 140 - 71 - 60.5) x 65 = Rs 10,302.50, mine equal. Plant: the closing side made equal to the opening side (shorts "bought back" at the bid): 9 failed. Plant: size taken from the wrong side of the book: 1 failed | MET |
| 2 | A failed short after protection unwinds, legging cost recorded, not opened | Tests pass; the builder's mutation "no unwind" is caught | MET |
| 3 | Missing exit quotes: pending exit plus alert, never a stale fill | Tests pass; protection held while a short is open | MET |
| 4 | Unquotable protection: `protection_unverified`, no new risk for that book, closed only when every exit fills | Tests pass; Book 2 not blocked | MET |
| 5 | Exit rule reached: closed at the next valid quotes | Target, stop and time; threshold crossing by Rs 0.01 tested | MET |
| 6 | No order function called | AST scan plus a trap provider; nothing in `fno/desk` imports a broker | MET |

`tests/desk`, `tests/books` and `tests/risk`: 151 passed. My plant comparing the touch size with **lots** instead of
units is caught (2 failed). That answers the builder's doubt 3 on the safe side for the check itself; whether Groww's
quantities are units is still unverified against a live response.

**E1 refactor: behaviour unchanged.**
- `csv_text` and `complete_lines` in `fno/books/files.py` are AST-identical to the old private functions.
- `drop_partial_line`, `append_durably` and `write_atomic` contain the same truncate, `fsync` and `os.replace` calls
  the old `AccountWriter` methods had inline.
- `require_lock` is the old `_check_lock`, unchanged.
- E1 and C2 tests pass.

## Must-fix (the orchestrator's decision, which I agree with): an entry price limit

C2 approves on the decision snapshot's mids with a Rs 1 pad. E4 fills at ask/bid up to about 15 minutes later. The
builder's own estimate: 4 legs x Rs 2 x 65 = Rs 520 beyond what C2 approved. Today nothing stops a fill that pushes the
worst case past C2's Rs 10,000 limit.

The fix: a limit price per entry (net premium no worse than the approved one plus a stated tolerance), refusing the
fill otherwise and recording "not opened: price moved". It is on `story/e4-entry-limit`, and I judge that branch before
it merges.

## Should-fix: expired legs (the orchestrator's question 3)

**Is it in E4's scope?** Partly. E4's scope is "exits", and expiry is how a leg exits if no earlier exit fills. The
story text does not name settlement, so the builder stopped at reporting it. That is honest, but it leaves two money
risks:

1. **The result can be overstated.** A leg still open after expiry is never priced (`settlement_needed`). E1 keeps
   marking it at its **last valid mark, flagged stale**, which is the mid before expiry. A short option that ends in
   the money on expiry day would show the pre-expiry value, not the settlement loss. The flag exists, but the equity
   number carries the stale value.
2. **`settlement_needed` does not block new risk.** Only `protection_unverified` blocks the book
   (`entries.refusal`). A book with an unsettled expired trade keeps opening trades, and C2 still sees the dead
   contract as open at its stale mark.

**Fix (reasoning only):**
- (a) Now, in E4: treat `settlement_needed` like `protection_unverified`, so that book takes no new risk.
- (b) A small follow-up story: settle expired legs at NSE's final settlement price. It is already in the archived
  UDiFF F&O file (`SttlmPric`), so no new data is needed.
- (c) Until (b) exists, D1's loader should refuse a `paper` playbook whose exits do not include a `TimeExit` before
  expiry.

## The orchestrator's question 2 (shared displayed size across books)

Confirmed optimistic for scoreboard B (reasoning only): each book can take the full displayed size at the same
snapshot, so three books together could take three times what was shown. With one lot (65 units) per trade and typical
NIFTY sizes, the effect is small. Record it as a stated limit on scoreboard B rather than couple the books (design
12.6's firewall). It is not a must-fix.

## Project rules

New package `fno/desk/` with its own composition root (in CLAUDE.md); C1 charges reused, not re-implemented; files
under 130 lines; no order capability. Process: a third push to `main` without a PASS.
