# Judge 631: F5 text revision for Q11, Book 2's tradable versions (story/f5-book2-q11 at a369d4f0b)

**PASS, lane 1.** Round 1 of 2. Judge I (judge 1 of 2; judge B is the other), own session
(session_01CHtddAzFcEdQh4HFiz3mqU), 25 Oct 2026. Text only (`docs/stories/F5-book2.md`). Judged by reading, against
the owner's Q11 (DESK_DECISIONS line 345) and the code and stories on `main`.

## The three questions asked

| Question | Answer | My evidence |
|---|---|---|
| Can a research rule reach Book 2 without the label? | No, by two checks | F5 writes `served["strategy_status"]` from the registry row at the decision's base commit, in every D3 record that chooses a trade; criterion 13 tests `research`. F1t revision 2 refuses a promoted run whose chosen trade lacks it (`F1t-ai-trading-runner.md:373-377`, criterion 17b) and labels the outcome "strategy not yet passed". Nothing on `main` writes `strategy_status` yet (grep), so both halves are code to come; the text binds both |
| Can the 1-open-trade limit be bypassed? | Not through Q11 | Every research version is unproven. The limit is checked at D2 (`fno/playbook/allocation.py`) and again at C4's own `unproven` check in `EnvelopeMode` (Part 3 step 4, line 179-182). That check's input is the version's completed and open paper trades from E5's records, plus same-day picks that passed C4. The count is Book 2's own fills (`fno/desk/trade_counts.py`: a book's desk records), so shadow evaluations never count toward 20. Criterion 13 tests a second pick failing both checks |
| Do C4 and the sheet use the same set? | Yes, one function | `book2_tradable(playbook)` in `fno/book2/tradable.py` is named as the only definition, read by the sheet (Part 1) and by C4's `approved` (Part 3 step 3) at the decision's base commit. Book 1 never calls it; Book 1 byte-identical is criterion 13 |

## Other checks

| Check | Verdict | Evidence |
|---|---|---|
| Matches the owner's words | MET | "registered research candidates": a row in `playbook/registry.csv` (an unregistered research file never included, criterion 13); "each trade labelled": as above; "D2's unproven limit": unchanged; "Book 1 unchanged": criterion 13; "Paper only": unchanged |
| Criterion 6 revised only on the owner's word | MET | the only changed passed criterion; nothing else passed is changed |
| Envelope prerequisite | MET | the version's envelope must be registered in D6 (Q9 approved v1) |
| Doc-reading tests at a369d4f0b, FNO_SLACK_BOT_TOKEN kept | MET | 922 passed, 14 xfailed; record scan clean |

No finding.

## Notes (not findings)

- Line 46 says "`PlaybookMode`'s `permitted` check" for Book 2's C4, but Part 3 makes Book 2's C4 mode `EnvelopeMode`
  (line 180). Say "`EnvelopeMode`'s checks (with `permitted` from `book2_tradable`)" so the code judge reads one mode.
- The limit is per version. With several registered research versions, Book 2 could hold one open trade in each, and
  a new version number starts at 0 completed trades. That is D2's design, and Q11 adds only one version
  (`b0-monthly-sc` v1) today. Worth one line in the Claims so the owner sees it before more research rows are
  registered.
- A `paused` version is labelled "strategy not yet passed" by F1t's rule (status not `paper`). That is conservative,
  and correct for the owner's purpose. F1t's rule, not F5's.
- F1t revision 2 (the label and the run check) is "for the code judge" (`F1t-ai-trading-runner.md:651`). F5's label
  depends on it; F5's Depends names F1t.
