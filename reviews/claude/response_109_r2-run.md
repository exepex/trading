# Response 109: R2 run, stock options around results (branch `story/r2-run`, lane 1)

Builder's claims for the judge. Story: REPLAN item 5 (R2), registered as ledger trial 53
(`research/2026-10-15-r2-stock-options-results/PROTOCOL.md`, frozen at 93a19c3, hash `89947b4c...e40a6b`, unchanged).
Labels: **strong evidence**, **some evidence**, **reasoning only**.

## Order of commits (the freeze holds only if this order holds)

1. `291760c` **Amendment 1** pushed alone, before any code and before any data: judge 97's follow-ups 1-3 and 5 and
   the data details the protocol leaves open. Its hash is in `FREEZE.md`.
2. **Script commit**: `study.py`, `snapshot.py`, `r2study/` (16 modules), amendment 2, tests, the script hashes in
   `FREEZE.md`. Tested on synthetic data only. The judge checks it before the run.
3. **Run commit** (after the judge's PASS): `results.json`, `results.md`, `inputs.csv`, `DATA_SPEND.md` rows, this
   file's results section.

## What was read before the run (said plainly)

- Manifests and file lists (dates, URLs, hashes, row counts). Strong evidence that A12's board-meeting archive covers
  only 2005-2007 (`board-meetings.csv`), so amendment 1 D1 reads NSE's list by month.
- The column names of one January 2025 board-meeting answer, and the last 300 characters of NSE's event-calendar answer
  (two November 2026 meetings) while testing that NSE answers from this container.
- The raw F&O and index-close files were **copied** from Drive to a local cache (4,009 files) and each SHA-256 checked
  against its manifest row; none was parsed. Some evidence (my statement; the commands are in this session).

## Gap list (REPLAN item 5, the protocol, judge 97's follow-ups)

| Requirement | Where | Test |
|---|---|---|
| Point-in-time F&O eligibility (FUTSTK and OPTSTK on the entry session) | `bhav.py` `DaySummary.is_fo_stock`; `events.py` `_event` | e2e `NOOPT` counted "not F&O" |
| Volume and open interest of near strikes | `evaluate.py` `leg_is_liquid` | liquidity boundary tests (50 / 49, 100 / 99.99 OI, exit 49) |
| Lot values against Rs 10,000 | `structures.py` `maximum_loss`; `evaluate.py` | cap at 10,000 exactly / 10,000.01 |
| Cheapest defined-risk structures S1-S7 | `structures.py` `STRUCTURES` | K0 tie, steps, width, condor credit and loss, untradable cases |
| Legacy lot derivation and its 98% validation | `lots.py` | 3-of-5 boundary; exact vs 1%-off turnover |
| Physical settlement: expiry at least 5 sessions after R, pushes counted | `sessions.py` `choose_expiry`; `descriptive.py` | 5 vs 4 sessions, push flag |
| One Groww snapshot, half-spreads, buckets, merge, untradable, p75 pads | `snapshot_capture.py`, `spreads.py` | merge at 29/30, 20%/30% one-sided, p75, window 14:00-15:00 |
| Bid/ask depth per bucket (judge 97 FU1) | `spreads.py` `depth` | depth in lots test |
| Effective clusters, within-week ICC, bootstrap, Kish | `clusters.py`, `moves.py` | ICC = 1 and -1 cases, Kish, determinism |
| Only 2019-2021 moves read | `moves.py` `OutsideCorrelationYears` | 2022 event refused |
| Annualisation of 130 clusters a year (FU2) | `rules.py` `clusters_a_year`; `stages.py` | window length both ends; e2e 1 cluster in 102 days |
| Power note 297 a year (FU3) | `rules.py`; `stages.py` `decide` | 390/130 and 891/297; YES label below 297 |
| Unknown-sector count (FU5) | `descriptive.py` `plan_lines` | e2e |
| Stages 0-4, early failure, cannot-answer cases | `stages.py`, `descriptive.py`, `analysis.py` | each stage's boundary; no snapshot; coverage 0% |
| No P&L on outcomes | exit session: contracts and listed strikes only (`evaluate.py`, `markets.py`) | by construction; reviewers checked |
| Raw Groww quotes to Drive only | `snapshot.py` | not unit-testable (live); stated |

Out of scope: F&O ban days (protocol section 10 limit), point-in-time sectors (limit), P&L (forbidden).

## Results

Not run yet: the run waits for the judge's PASS on the script commit.
