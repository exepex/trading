# Judge 642: EDGE2 F1 and F6, story/edge2-f6-participant-oi at a5cc130f (judge J, round 1 of 2)

**FAIL**, lane 1: 2 should-fix, 4 minor. The "no edge" results stand, reproduced by my own reruns. Trial merge with
main 82ad1586 (381bf7d0): 16,686 passed, 1 skipped, 13 xfailed; ruff, format, check_imports (2,790), check_records
(9,344) and check_numbers clean. The 44725e7e merge was run too: 16,628 passed.

## Criteria (the orchestrator's checks)
| Item | Verdict | My evidence |
|---|---|---|
| F1 (1) freeze before the run, code hash | MET | GitHub push log: 270959dd at 23:09:31Z; the discovery commit b9b23f9d at 23:10:22; results pushed at 23:20:21Z. `code_hash()` = 9cbe34ce at 47c01637, 270959dd and a5cc130f; protocol SHA-256 2105e363 unchanged |
| F1 (2) held-out unread, rows fresh | MET | `seal.allowed` refuses FINNIFTY and MIDCPNIFTY unless opened, and `nominated_for_held_out` refuses with no nominee (R1-R3 caught). No `heldout.json`. The new FINNIFTY and MIDCPNIFTY weekly rows are `fresh`: `research/` holds FINNIFTY prices only in the Aug-Sep 2026 modelled backtest |
| F1 (3) costs, pads, -Rs 105 | MET | My rerun gives discovery.json identical except `head`. -105.44 = 230.79 - 162.55 - 173.67 (pads 4 x Rs 1 x mean lot 43.4). I priced three trades by hand from the closes with `fno.costs`: gross equal; charges within 0.22, the STT on the padded sell (0.15% x pad x lot x 2). The G1 rows reproduce exactly from the cards |
| F1 (4) RC1 | MET by reading and rerun; test gap m1 | Draws the same count from all the structure's cycles, taken or not; seed 20261025; share >= the gated mean, as protocol section 8 |
| F1 (5) append-only | MET | Against main: 0 removed lines in ledger.csv and gates.csv. The ledger edit is B4's one-time fill of `first_run_on` and `run_commit` |
| F1 (6) WF-G15 never retested | PARTLY | m2 |
| F6 (1) registration before any OI read | MET | 57bddc27 at branch creation (23:25:18Z), before the code (23:28:54Z) and the freeze 06646081 (23:54:29Z); discovery committed 23:55:08. Main's participant-OI row was `fresh, none` |
| F6 (2) futures STT 0.05% | MET | `FuturesRates` 0.05% sell STT, Rs 183/crore, stamp 0.002%, GST 18%, as the school probe cites (NSE/FATAX/73524, NSE/FA/73061). The protocol's Rs 966 example recomputes exactly. My F6 rerun matches except `head` |
| F6 (3) trial 118's G1 row honest | NOT MET | S2 |
| F6 (4) 115-120 under edge2-f6 | MET | Experiment `edge2-f6-participant-oi-futures-2026-10-25` |

## Findings
**S1 (should fix) B4's guard now refuses every trial 109-120.**
- `Ledger(root).require_registered("109")`, and likewise "114", "115", "118" and "120", raise `NotRegistered: ...
  changed after it was frozen`. The trials' `protocol_path` is the idea card, and the G1 inputs were appended to the
  cards after `protocol_commit` (b9b23f9d, ed28d6b7).
- EDGE1 avoided this: its cards' `protocol_commit` e7a2029d holds the G1 inputs (71 and 95 pass).
- Effect: the factory's verdict step, the trial guard and any reader of the freeze proof see these trials as altered
  after their freeze.
- Fix without rewriting frozen bytes, either:
  - point `protocol_path` at `F1_PROTOCOL.md` or `F6_PROTOCOL.md`, as GR1 does; or
  - keep the result-derived G1 inputs out of the frozen card, or change B4 (lane 1).
- Add a test that runs `require_registered` on the real rows 109-120.

**S2 (should fix) Trial 118's G1 `passed` is live and was built on inputs the protocol itself rejects.**
- The H5 cards give G1 `n` = 1,451 overlapping trades with the plain SD. The frozen protocol's own error is Newey-West,
  lag 4.
- `fno factory report` prints "EDGE2-F6-FL-H5 v1: trial 118 of 120; last gate G1 passed". Only F6_RESULTS.md's prose
  corrects it.
- My recomputation of -Rs 316 is right: 739 - 1.2816 x 824. But "about sqrt(5) too tight" is wrong: the measured
  ratio is NW 824 / iid 527 = 1.56. For FD-H5 it is 0.95 and for CD-H5 1.06.
- Fix: close 118 in the machine record by the factory's own next gate (`factory spend` logs `exploratory`, as EDGE1's
  94 went). Say so in its card and its LEDGER.md row, and correct the sqrt(5) line.

**m1 (minor, tests only; tests sit outside the code hash).** My plants that survived:
- RC1 drawing from taken trades only (R9), and RC1's >= boundary (R8);
- the gate's traded-volume filter (R15);
- `code_hash` dropping study.py (R18);
- EWMA lambda 0.97 (R19);
- F6 keeping exits after the seal day (F2);
- F6's NW lag 0 for H5 (F4).
Add a test for each, R9, F2 and F4 first.

**m2 (minor)** "Never retest WF-G15 on this data" is only in F1_RESULTS.md's prose. Add it to card 111 and the
109-114 LEDGER.md row.

**m3 (minor)** F1 protocol section 7 promised `research/edge2/LOT_CHECK.md` before any held-out read. It does not
exist, and `held_out_lots.py` says the circulars were not read. Harmless while held-out stays unread; state it in
section 11 or in the Limits.

**m4 (minor)** Dates and rows:
- `registered_on` and the gates' `on` are 24 Oct (UTC), while `first_run_on` is 25 Oct (IST).
- DATA_SPEND keeps the old "Participant open interest | history | fresh | none" row beside its new split rows.

## Plants (mine): 27 of 34 caught
- F1 caught 17 of 22: the seal (3); point in time; the settlement close; week clusters; 30 clusters; Holm; the gate
  boundary; three nomination conditions; the pad; the condor offset; the UDiFF lot; the moved expiry; at most 2.
- F6 caught 10 of 12: the seal day; STT 0.02%; entry on the signal day; the level window; the client fade; pads; two
  nomination conditions; GST; the roll.
- Survivors: m1. Run with PYTHONDONTWRITEBYTECODE=1, in their own worktree.

## Notes
- FNO_SLACK_BOT_TOKEN was set for the suites (1792884295-1792885435 and 1792887370-1792888021):
  - the second window: nothing in any channel;
  - the first: only "DRY RUN ... replay" REH1 posts. Neither study holds Slack code.
- My F6 rerun once died on a Drive "connection reset" (ChunkedEncodingError, no retry) and passed on the second try.
  That is the storage layer, not this story.
