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

## Revision 1: answer to judge 180 (FAIL; 2 blocking, 3 should-fix)

I checked each point against the code on `main`. All five are accepted, and one premise is corrected.

1. **Blocking 1 (timeline): ACCEPT, with one correction.**
   - Confirmed: `config.yaml` `desk.timetable` has pack 14:58, `decision_deadline` 15:12, `execution_snapshot` 15:15.
     `fno/desk/daily_run.py` records the `decisions` step at 15:12 and the `snapshot` step at 15:15, so a 15:08 card
     would read neither.
   - Correction: there is **no decision-time C3 check** to read instead. The decision run calls no data check.
     `DataGate` is used only by the desk's snapshot, fill and exit steps (`grep` of `fno/`), and the decision-time
     evidence check is C4's.
   - So T2 now reads two outcomes, each with its final time taken from the desk's own `Timetable`, never written in
     code (G10 changes the times in one place):
     - `DecisionOutcome`: the decisions step and the C4 rows;
     - `ExecutionOutcome`: the snapshot step.
   - A record not yet final shows "not yet decided (final at HH:MM)". The last session's execution outcome, which is
     final, is shown too. Criteria 1 and 4; test 1 runs at 15:08, 15:13, 15:16 and at G10's times.
   - The post time stays O1's. Known limits recommends posting after the decisions step (reasoning only).
2. **Blocking 2 (gap list): ACCEPT.** There is now a seven-row table of 7.3's checks:
   - cost wall: out, a new C4 rule when needed (no code anywhere, my grep agrees);
   - evidence label against rung: T2b with T1's trade fields, criterion 13;
   - the other five rows, each mapped to a criterion or an owner.
3. **Should-fix 3 (rung): ACCEPT.** `RungOutcome` is removed. "No version at paper" stays T1's `RegistryStatus`.
   Criterion 7's AST test forbids a registry reader in `rule_checks.py`.
4. **Should-fix 4 (event warning): ACCEPT.** It is now a T2b scope item:
   - source: A6's `events.csv` scheduled rows;
   - window: from the day after the card to the trade's exit (time exit, else expiry), from the trade fields;
   - criterion 12. Built with T1's trade fields: only a TRADE or WATCH card has a window.
5. **Should-fix 5: ACCEPT.** "No run log: not yet decided" is criterion 5.

## Code round: T2 only (text PASS, judge 180 addendum 1; orchestrator's go)

New: `fno/cards/rule_checks.py` (156 lines) and `fno/cards/ruled_status.py` (59 lines). Changed: `fno/cards/wiring.py`
(`build_status`), and one reason code `CARD_HARD_RULE_BREACH` in `fno/constants.py` (now 347 lines, near the 350
limit). Tests: `tests/cards/test_rule_checks.py`, 7 tests.

How it meets the text:
- **Final means recorded.** An outcome is final once the desk's run log has its step (`decisions`, `snapshot`).
  Before that the card shows "not yet decided (final at HH:MM IST)", with the time from the desk's `Timetable`
  (criteria 1 and 4; one test runs the same records under today's and G10's times).
  - Choice made in coding: final is decided by the step being recorded, not by the clock. A restarted or late desk
    then shows "not yet decided" until its step really exists, instead of "no breach" at 15:13 (strong: `RunLog`
    writes a step only when it ends).
- **No run log:** "not yet decided: the desk has not run today" (criterion 5).
- **C4 rows:** only rows dated that day count; the books named late or not committed come from the decisions step
  (criterion 2).
- **C3:** a `snapshot` result with `valid: false` gives `data_check_failed`; the last session's verdict is shown
  while today's is pending (criteria 3 and 4).
- **Unreadable records:** an unreadable run log or failures file gives `data_check_failed` naming the file
  (criterion 6).
- **Reason order:** `data_check_failed`, then `hard_rule_breach`, then T1's own reason. The card stays `NO TRADE`
  (v1).
- **AST test:** `rule_checks.py` imports nothing from `checks` or `playbook` and calls no write (criteria 7 and 8).
  T1's `RegistryStatus` is wrapped, unchanged.
- **Footer:** every file read goes into the card's records-used footer.

Live dry run, `python -m fno card daily --on 2026-10-15`: "Rule checks: not complete", both rules "not yet decided:
the desk has not run today". This is true today: no `journal/runs/` file exists on `main`, because the desk's daily
run is not scheduled yet (O1).
