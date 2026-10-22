# Judge 491: MS-P1m, the roads' margins per proposal (second judge)

**Scope:** story/ms-p1m-margin-rows at 0499f885 (builder session_01Vm1WnH8i9waM8EJG8zwWqg). The diff is
origin/main...0499f885; the claims are response 328. Lane 1, money limits, two judges: I am the second and did not
read the first judge's verdict. Round 1 of 2. Judge J (session_01Qg4Gxun1NvGRrtS9C68Dc1).

**Verdict: FAIL.** There is 1 should-fix: the expiry-day refusal freezes whole control accounts, and nothing measures
or labels that cost. There are also 3 minor findings. Everything else is met with my own evidence.

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | SPAN on the actual legs from the archived file (SHA-256, before 09:00, no new NSE read) | MET | I ran the real wiring on Drive's archive. NIFTY SF 100 (23 Nov, lot 65) equals `margins.csv` on 21 Oct (635.05 / -6100.25 / 59511.27) and on 22 Oct (244.40 / -6181.50 / 59309.51). BANKNIFTY, FINNIFTY and MIDCPNIFTY PCS and the NIFTY weekly PCS on 21 Oct equal my own arithmetic from the parsed arrays (max of 16 scenario sums, signed prices, 2%/3% exposure) to the paisa. Only Drive is read |
| 2 | Named fail-closed cases | MET | each case has a test with its message. Plants caught: SHA, manifest row, missing file, 09:00 (in the adapter and `<=`), Drive catch narrowed, Drive text kept, the model and bad-file wraps, plain terms, history mode. C2's manager turns `ValueError` into a refusal (`fno/risk/manager.py:65`) |
| 3 | Structure-shape checks | MET | lot, index, width, sold leg, one unit, condor order, fly body and wings-inside plants caught |
| 4 | One factory for terms and units | MET | `road_proposal` and `road_open_trade` take lot, legs and units from the terms; the "lot 1" and "units without lots" plants caught |
| 5 | C2, C4 and `margins.csv` unchanged | MET | the diff names no file under `fno/risk/`, `fno/checks/` or `research/data/margins/`. A14's job and A14c's run only move to `SpanFile.written_in_time` (same `<` rule; both "inclusive" plants caught) |
| 6 | Labels on every record | MET | the real `trade_record` holds the method, `factor_label`, `broker_check_label`, the factor row, the file and its SHA-256, legs, lot and the per-lot figures; the plants that drop each label caught. See minor 1 |
| 7 | Reproducible gap measure | MET | my rerun of `tools/ms_p1m_margin_gap.py` gave 13,736 rows, 760 not listed and 304 `MarginOutsideModel`, and every cell of the story's table (share below, minimum ratio) |
| - | Gates (my run) | MET | pytest -n auto: 10,320 passed, 16 xfailed. ruff check and format, `check_imports` and `check_records` are clean. Largest new file 123 lines |

## Findings
1. **Should-fix: the expiry-day refusal stops whole control accounts on every weekly expiry day, unmeasured and
   unlabelled.** The claims ask the judges to rule on this.
   - Why it happens: C2's `MarginRoom` asks the margin of every open trade before the proposal
     (`fno/risk/rules.py:143`). The calculator refuses an expiry on its own day (`calculator.py:62`).
   - The cost: REF drives all five roads in one account, with `min_dte: 2` and no exit, so it holds to expiry
     (`research/school/cards/REF_v1.yaml`, MS-P1e PASSed). It therefore holds a NIFTY weekly position on every weekly
     expiry day. On that day it can open nothing on any of the five roads, about one session in five, for a modelling
     gap rather than a risk. RC1 is the same, so the two controls lose their monthly-road entries on those days.
   - Why it matters: the rule drivers (20-45 days, monthlies) rarely carry an expiring position, so the comparison the
     pilot exists for is biased. "Conservative" is right about money but silent on that bias.
   - Expected, one of these:
     - (a) model the expiring trade's margin on its own expiry day (P0 probe 4's extra 2% ELM) behind the same
       calculator, with tests;
     - (b) the orchestrator's recorded decision naming this effect, a label on every refusal it causes (the record
       says "open trade on its expiry day", not just law 3), and a count per driver in the claims.
   - [reasoning only on the share; strong evidence on the mechanism]

**Minor:**
- (1) `nov_per_lot_rs` in `trade_record` is untested: writing the scan there passes every test.
- (2) `road_wiring`'s refusal when `risk.stressed_margin.factor_file` is unset is untested: a plant returning a
  default 2.1 row passes.
- (3) `self.source.manifest()` runs outside the named-refusal wrap in `_file`. A failure reading the local manifest
  folder would raise its own error, not a named `RiskInputError`. The cause is local and unlikely.

## Plants
37 planted, 35 caught. The survivors are minors 1 and 2. One plant (the sold leg inverted) failed a fixture at
import, which counts as caught.

## Notes
- The beginning-of-day file prices a 15:00 decision, as A14's rows do. Any Drive failure is a named refusal by class
  only. Both accepted as stated.
- MS-P1d must build every school proposal and open trade through `road_proposal` and `road_open_trade`. That is d's
  acceptance test, not checked here.
