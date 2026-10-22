# Judge 495: R1 follow-up, cards anywhere

**Scope:** story/r1-cards-anywhere at 6fcbd6dc (one commit on main). The story's "R1 follow-up: cards anywhere" section
in `docs/stories/R-factory.md` and its Claims. Lane 1 (research records). Round 1 of 2. Judge H
(session_01KNkZVoWvXMkoihKrrXk5Xa).

**Verdict: PASS**, with 2 minor notes.

## Criteria
| Check | Result | Evidence |
|---|---|---|
| Ideas folder first, unchanged | MET | `card_paths.card_path`; plant (ideas lookup removed) caught |
| Else the ledger row's `protocol_path` if it holds a ```factory block | MET | Every protocol path on main's ledger holds no block (my scan of all 37 paths), so none is mistaken for a card. Plant (block check removed) caught |
| A named card that can't be read is an error | MET | `read_card` raises, including the id-versus-file-name check (`card.py:58`); test plus plant (stem match removed) caught |
| `factory report` lists CARD_P1 as a measurement | MET | On 6fcbd6dc merged with the registration branch 8106871b (scratch only): `CARD_P1 v2 (measurement): trial 99 of 99`, `measurement trials left out: 54, 55, 95, 96, 97, 98, 99`, false passes over 92 trials. `factory status CARD_P1` finds it. The real-report test then runs and passes |
| Gates | MET | On the merged tree: pytest -n auto 11,183 passed, 1 skipped, 16 xfailed. ruff check/format, check_imports and check_records are clean. `card_paths.py` is 43 lines |

## Findings
None blocking or should-fix.

**Minor:**
- (a) **A missing ledger-named card is ignored, not refused.** If the ledger names a card that is no longer there,
  for example `research/school/CARD_P1.md` moved, `ledger_card_paths` drops it silently (a test asserts it). The
  report then counts trial 99 as a test again, one more expected false pass, with no error. Every ledger path exists
  today. A ledger-named `.md` that is missing could fail `factory report` instead.
- (b) **One id found in two places is read twice.** `card_path` prefers the ideas folder, but `read_all_ideas`
  returns both cards: my run, with X1 in ideas and `research/school/X1.md` named by the ledger, gives `[X1, MEAS, X1]`.
  It needs a misconfiguration (two cards with one id). `all_card_paths` could refuse a duplicate id.

## Plants
6 planted, 5 caught. The survivor drops the ideas-folder exclusion in `ledger_card_paths`. It is equivalent, because
the set union in `all_card_paths` removes the duplicate path.

## Notes
- Merge order, as the orchestrator says: registration (judge 493) first. Until then the trial-99 report test skips.
