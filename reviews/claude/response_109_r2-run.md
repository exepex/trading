# Response 109: R2 run, stock options around results (branch `story/r2-run`, lane 1)

Builder's claims for the judge. Story: REPLAN item 5 (R2), registered as ledger trial 53
(`research/2026-10-15-r2-stock-options-results/PROTOCOL.md`, frozen at 93a19c3, hash `89947b4c...e40a6b`, unchanged).
Labels: **strong evidence**, **some evidence**, **reasoning only**.

## Order of commits (the freeze holds only if this order holds)

1. `291760c` amendment 1, pushed alone before any code or data. **Judge 109: FAIL** (should-fix 1: the study must not
   be its own NSE downloader; should-fix 2: the lot must be the traded contract's; two minors). All four accepted
   after checking them (the owner's 13 Oct one-downloader rule is real; NSE revises lots by contract month).
2. `9bfa0ad` work-in-progress script (pushed only because the session's stop hook requires pushed work; marked not
   frozen, not for judging).
3. `425b693` amendment 1 revision 1: D1 through A12's own day-list librarian (judge's option b), D3/D4 the chosen
   expiry's own lot and adjustment test, legacy rows read no R price, D5 calendar sessions after the archive, D10
   filed_at share; `DATA_SPEND.md` results-dates row names the real source.
4. **Script commit** (this one): code, amendment 2, tests, script hashes in `FREEZE.md`. The judge checks it.
5. After both pass: A12's board-meeting fill (archiving), the snapshot (14:00-15:00 IST), the one run.

## What was read before the run (said plainly)

- Manifests and file lists (dates, URLs, hashes, row counts).
- The column names of one January 2025 board-meeting answer, and the last 300 characters of NSE's event-calendar answer
  (two November 2026 meetings) while testing that NSE answers from this container.
- The raw F&O and index-close files were **copied** from Drive to a local cache (4,009 files), each SHA-256 checked
  against its manifest row; none parsed by the study.
- `snapshot.py --ready` (a readiness check of the snapshot's own inputs) parsed the 14 Oct 2026 F&O file and NSE's
  event calendar and printed one line: "72 F&O stocks with results in the next 10 sessions". No price, volume, lot,
  spread or move was printed. The 14 Oct file is the snapshot's registered input (section 6.2: previous session's
  contracts); it is also the decision window's last session. Some evidence (my statement; the command is in this
  session).

## Self-review (quality rule 3): two independent review agents, and what I did

| Finding | Severity (theirs) | Done |
|---|---|---|
| Missing cached file silently becomes a wrong exclusion reason | blocking | `MissingFile` stops the run; `--run` refuses if any raw file is not cached |
| Lot from the near-month future, not the chosen expiry (also judge 109) | should-fix | the chosen expiry's own lot; adjustment test on that contract |
| Sessions after the archive's last file not counted for the expiry rule | should-fix | calendar sessions after the last file (amendment 1 D5); this also exposed a calendar-end crash in `snapshot.py` (120 days ahead passes 31 Dec 2026), fixed to 60 days capped at the calendar end |
| 12-month part counts missing | should-fix | `clusters_by_part` per structure, in the report |
| "Lot unknown on R" counted as corporate action | should-fix | its own reason |
| Missing previous-session rows silently 0 | should-fix | counted (history: a note; snapshot: >20% stops the capture's use) |
| Snapshot stocks and error legs vanish; one Groww error loses the capture | should-fix | per-stock and per-leg errors counted, never one-sided; capture continues |
| NSE answers checked only for JSON | should-fix | board meetings via A12's `check_day_list`; event calendar must be rows with symbol and date; no candidates exits 1 |
| Missing Drive copy does not stop the run | should-fix | snapshot refuses without the owner's Drive; meetings only from A12's archive |
| Run commit can hide uncommitted code | should-fix | `--run` refuses unless every script hash is in `FREEZE.md` and the folder is clean |
| Correlation drops uncounted | should-fix | counted by reason, reported |
| Filing of an older quarter can set `filed_at` | nit | period end at most 120 days before D (amendment 2 item 4a) |
| Lot "0" crashes; crossed quotes give negative spreads; quote answered after 15:00 kept; `results.md` unprotected; condor credit at the wing; thin margin not printed; stage-0 reasons; unknown sector over all years; reschedule chaining | nits | all fixed (chaining stated in amendment 1 D1) |
| Legacy lot on R reads R prices | nit (also judge 109 minor 1) | legacy rows use the K0 test and the corporate-actions file only |

## Broken-code proof (quality rule 4)

57 planted bugs, one per criterion's code line, each run against its named test: **57 of 57 caught**. The first
mutation run showed 7 misses: a stale-bytecode flaw in my mutation script (fixed: no bytecode, only exit code 1
counts), and real gaps fixed since (a middle-tercile merge test; a quote answered at 15:00; the period filter; the
calendar sessions; a stronger lot-formula mutation) plus **one code bug the mutation exposed**: the 20% one-sided
boundary computed as `1 - 8/10` = 0.1999..., so exactly 20% could never be tested; now computed as a count ratio.

## Judge 109 addendum 2 (FAIL on adccf53): what I checked and did

All three should-fixes and four minors accepted after checking them against the code (each was true: no test bit
judge D's eight plants; `previous_contracts` is 0.0 for both "no row" and "0 contracts"; nothing named the snapshot).
- SF1: tests for M3 (EN <= 0 adds no cluster), M30 (pre-window events never decide), M17 (condor wider wing with
  unequal steps), M18 (with-pads cap at 10,000.00 and just above), M23/M24 (stage 0 exactly 10% and 80%), M10 (S7 tail
  on the costed loss), M16 (Kish on |m|). All eight are in `mutations.json`; 68 of 68 caught.
- SF2: `r2study/snapshot_legs.py` rebuilds the legs from the raw Drive file plus the previous session's F&O file,
  counts legs with no previous-session row, and the run uses the snapshot only at or below 20%.
- SF3: `--snapshot PATH SHA256`; the run refuses a raw file whose SHA-256 differs; `results.json` gets a `snapshot`
  record (Drive path, SHA-256, time, counts, used or not).
- Minors: protocol and amendments in `check_frozen`; muhurat-day filings after-hours; cache outside the checkout;
  the `--ready` parse noted in `FREEZE.md`.
- The snapshot is taken from a worktree pinned at adccf53 (its 27 `FREEZE.md` hashes checked: all match), as judge D
  ruled; `snapshot.py` and `snapshot_capture.py` are byte-identical in the fix commit.

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
