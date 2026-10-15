# Response 174: T2 + T3, the devil's advocate on the daily card: story text and claims (for the judge)

**Story text:** `docs/stories/T-cards.md`, section "T2 + T3". Branch `story/t2-t3-advocate`. Issues #104, #105, REPLAN
slice B. Lane 1. No code yet.

## Claims

| # | Claim | Evidence |
|---|---|---|
| 1 | Stale or invalid data is already refused by C3's gate and recorded in the run log's `snapshot` step. | Strong: `fno/checks/gate.py`, `fno/desk/daily_run.py`, `fno/desk/run_log.py`. |
| 2 | Caps, margin room, maximum loss with charges, shape and the version's terms are already refused by C4, one row per failed check in `journal/<book>/validity_failures.csv`. | Strong: `fno/checks/validity_*.py`, `VALIDITY_FAILURES_FILE` in `fno/constants.py`. |
| 3 | So T2 re-checking any of them would be a second version of a rule; T2 reads their outcomes instead. | Strong (the one-builder rule); enforced by criterion 5's AST test. |
| 4 | No code today blocks an entry for an event inside the holding window, for stock-option settlement, or for a variant of a failed idea. | Strong: `grep` on `main` (`FEATURE_EVENT_IN_WINDOW` is a research feature and an entry-condition flag only; no stock options are traded; R1 code is not built). |
| 5 | Every card is `NO TRADE` today and the card is not posted daily until O1. | Strong: `fno/cards/status.py`; orchestrator, 15 Oct 2026. |
| 6 | Weather RED does not block entries in the desk yet. | Strong: M1 story Out list. |
| 7 | T3 needs no new AI caller: `fno/advocate`'s port and `RoutineTrigger` cover it; `ObjectionCheck` needs only its limits as constructor settings. | Strong: `fno/advocate/routine_file.py` (constants `MAX_OBJECTIONS`, `MAX_WORDS`). |
| 8 | The card's subject for T3 must be public lines only (card records are Drive only). | Strong: owner decision of 15 Oct 2026 (`docs/DESK_DECISIONS.md`), `fno/cards/record_store.py`. |
| 9 | About 5 minutes from the 15:00 pack to the post is tight for a fired routine. | Reasoning only; the record will measure it. |
| 10 | Running T3 on `NO TRADE` days adds little. | Reasoning only (question 1). |

## Questions

The three in the story text: when T3 runs (recommend A, trade and watch cards only); new 7.3 rules (recommend A, each
in C4 or R1 when needed, with a warning line now); build order (recommend A, T2 now, T3 after the trade fields and O1).
