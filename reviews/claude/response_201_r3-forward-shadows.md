# Response 201: R3, first forward shadows: story text and claims (for the judge)

**Story text:** `docs/stories/R-factory.md`, R3. Branch `story/r3-forward-shadows`. Issue #124, REPLAN slice B. Lane 1.
Text only. Number 201 assigned by the orchestrator.

## Claims

| # | Claim | Evidence |
|---|---|---|
| 1 | Shadow decisions are already evaluated and recorded by Book 1's D2 run, with `mode: shadow`. | Strong: `fno/playbook/loader.py` `shadow_on`; `evaluate.py`; `decision_run.py`; `decision_record.py`. |
| 2 | Nothing fills a shadow decision. | Strong: `fno/desk/daily_steps.py` `fill` and `fno/books/book1_orders.py` read the three books' chosen outcomes only. |
| 3 | The first registered research version would make Book 1's run raise: its shadow account is never opened in production. | Strong: `JournalShadowBooks.account` raises if not started; `start_shadow_books` is called only by `tests/desk/test_shadow_books.py`. |
| 4 | Shadow books receive Book 1's recorded terms. | Strong: `fno/books/book1_wiring.py` `_parts`: `recorded_terms(root, BOOK1_RULES)` is passed to `build_shadow_books`. |
| 5 | No idea passes the cost wall today. | Strong: response 92 (Rs 814-939 per four-leg round trip; zero candidates); weekly weather W1-W5 failed; R2 stopped at the cost wall (`research/ideas/R2.md`). |
| 6 | B0, the monthly short condor benchmark shadow, was offered only as a measurement. | Strong: response 92, verdict and option table. |
| 7 | V1 and V2 cannot start now. | Strong: no v4 feature in `fno/playbook/vocabulary.py`; STR1 codes blocked until STR1b-2 (`fno/playbook/activation.py`). Some evidence: V1's forecaster gives values from about mid-November (A16/G8/G10 builder, assumes no void sessions). |
| 8 | E8's scope already covers shadow candidates, but it defines no order time for a shadow. | Strong: `docs/stories/E8-owner-timing-fills.md` (scope line on shadow candidates; T is the card's delivery time). |
| 9 | Test B of the stop rule waits for R3's closed-trades path. | Strong: `fno/budget/stop_rule_tracker.py` (`path=None`, producing story R3); S3/S6 builder, 16 Oct. |
| 10 | Exercising the whole shadow path with B0 before the V-ideas is worth its one trial. | Reasoning only (question 1). |
| 11 | E8 fills every pending order whatever its account; R3 writes shadow orders in Book 1's format, fills E8's per-account terms lookup and opens the accounts. | Strong for the split (E8 builder, 16 Oct); reasoning only for the interface names until E8's part 1b. |
