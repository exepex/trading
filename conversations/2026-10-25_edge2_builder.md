# 25 Oct 2026 (IST): EDGE2 edge-search builder (session_01VhppcYHXq3yTJBV2UnsWSs)

Owner, 25 Oct 2026 (relayed in this session's task): "no proven edge: let's try to find them using dry runs".

## Decisions so far

- Plan sent to the orchestrator: families F1-F7 (VRP gate on weeklies, expiry eve, events, term structure, skew,
  participant OI on futures, overnight drift); stock options around results and plain monthly condors dropped (R2,
  EDGE1). Orchestrator: discovery runs as exploratory without a judge; a judge before any held-out read or
  nomination; FINNIFTY + MIDCPNIFTY weeklies as F1's held-out.
- F1 registered as ledger trials 109-114 (101-108 are protocol v4's; renumbered after the orchestrator found the
  collision; the first branch story/edge2-f1-vrp-weekly is dead). Branch story/edge2-f1-weekly.
- F1 run once (freeze 270959dd): no edge after costs, nothing nominated, held-out not read (stays fresh).
  `research/edge2/F1_RESULTS.md`.

## Open questions

- The orchestrator routes a lane-1 judge on story/edge2-f1-weekly (hand edits under research/), merged after the v4
  freeze.
- Next family: F6 (participant OI on NIFTY futures) proposed first because futures costs are small; waiting on the
  orchestrator.
- A ledger-trial claim registry is being built by the v4 freeze builder.

## Later the same day

- F1 branch merged with main (v4 freeze on main): story/edge2-f1-weekly at da2b113a, full suite green.
- F6 (participant OI on NIFTY futures, research only while futures are on hold; trials 115-120 reserved by the
  orchestrator) registered before any OI file was read, frozen at 06646081 and run once: no edge, nothing nominated,
  held-out 2025-26 unread (`research/edge2/F6_RESULTS.md`). FII change leans right for the next session (+Rs 379
  gross vs +72 always long) but far below today's Rs 657 costs. G1's "pass" of trial 118 is an overlap artefact,
  flagged to the orchestrator for R1's owner.

## Open questions (updated)

- Judge J on F1 (da2b113a) and F6 (a5cc130f), lane 1.
- Next family: F7 as planned, or a family using the FII-change lean as the side filter of a defined-risk NIFTY weekly
  spread (orchestrator's call).
- R1 factory: a dependence-corrected G1 bound for multi-day holds (proposal to its owner).

## F8 (later)

- Orchestrator chose a side-filter family (F8, block edge2-f8, trials 121-123; F7 parked). Registered before any
  option price was read; discovery (spreads alone, no OI read) at d38baa12: every 2-leg NIFTY weekly credit spread
  loses on both sides (side averages -Rs 219 to -388); P0W10 futile; P0W5 and P5W5 kept
  (`research/edge2/F8_DISCOVERY.md`).
- Open: whether to spend participant OI 2025-26 on F8's held-out read (my recommendation: keep it unread; low prior,
  low power); judge J on the branch.

## Judge J round 1 and F8's closure

- Judge J's early findings on F1+F6: S1 (cards edited after their freeze: restored to their frozen bytes, guard test
  added) and S2 (trial 118's live G1 pass: a correcting appended row). Both accepted by the orchestrator.
- Orchestrator chose option 2 for F8: participant OI 2025-26 stays unread; F8 closed as "spread fails unfiltered;
  filter untested"; 124-126 unused.
- One head for judge J round 2: story/edge2-f8-fii-side-spread at 56031075 (the F6 fixes re-applied on F8's line:
  the gate log's append-only check reads history linearly, so a merge of parallel appends fails it).
- Next-search candidates (event IV crush, weekly calendar) sent to the orchestrator; no discovery until J passes.

## Judge 642 and round 2

- Judge 642 (J): FAIL on F1+F6 with 2 should-fixes and 4 minors; the "no edge" results reproduced exactly.
- Fixes on a new line, story/edge2-round2 (d9979131): result-derived G1 inputs in a sidecar beside each frozen card
  (the factory's card reader extended), 118 closed by `factory spend` (G2 exploratory), tests for J's 7 surviving
  plants, the minor notes. Full suite 16,900 passed.
- Orchestrator: F9 (event IV crush, block edge2-f9, trials 127-132) next, registered only after J passes; calendars wait
  for a verified payoff and margin model; the wide-wing condor declined.

## F9 (later)

- EDGE2 F1+F6+F8 merged to main (judge J pass, 56031075 + 90becf94); plant tests on a lane-2 branch.
- F9 event IV crush registered as trials 124-127 (orchestrator: the factory needs consecutive trials; 128-132
  released), 58 scheduled A6 events fixed, entry at the prior close exposed to the gap; frozen at effae511; run once:
  no edge (net -Rs 388 to -467 a trade, gross Rs 175-216 against the Rs 820 bar), event days about Rs 150 better than
  ordinary days; nothing nominated, held-out unread (`research/edge2/F9_RESULTS.md`).
- Open: a judge on e3ec093a; the next step after four no-edge families (orchestrator, then the owner).

## Slippage note (later)

- Orchestrator: a descriptive slippage study, no trials. Reused MS-SIM-b's reader and spread functions read-only
  (its owner out of reach). Finding: for NIFTY and BANKNIFTY near-month and NIFTY weekly OTM strikes, half the 15:00
  spread is about Rs 0.03-0.65 a unit, under C1's Rs 1 pad; next-month and FINNIFTY/MIDCPNIFTY next-month quotes are
  much wider or missing (`research/edge2/SLIPPAGE_NOTE.md`). No EDGE result is re-read with new pads.
- Open: an owner question on a measured, per-bucket pad in C1 (lane 1); the fills-against-mid section from Monday.

## Close of the day's work

- F9 passed judge 668 (round 2 plus a text minor) and is merged (2391b8bd). Four families, 19 trials, no edge; every
  held-out set unread.

## Decisions so far

- Owner, 25 Oct 2026: "no proven edge: let's try to find them using dry runs". Searched F1 (weekly VRP gate), F6
  (participant OI on futures, research only), F8 (FII-side credit spreads; held-out waived by the orchestrator) and F9
  (event IV crush): no edge after costs in any; nothing nominated.
- F7 parked; calendars wait for a verified payoff and margin model; the wide-wing condor declined (orchestrator).
- A descriptive slippage note: C1's Rs 1 pad looks conservative for NIFTY/BANKNIFTY near-month OTM legs.

## Open questions

- Q13 to the owner: keep searching option rules at one lot, or pause (no new family until answered).
- Owner: should C1's pad become a measured, per-bucket figure (lane 1)?
- R1's owner: the inputs sidecar for result-derived G1 inputs and a dependence-corrected G1 bound.

## Owner decisions relayed (25 Oct, DESK_DECISIONS "DOC1 approved; four third rounds; A14c merge; one-lot searches paused; measured cost pads")

- Q13: "New option-strategy searches at one lot are paused" (item 4): EDGE2 starts no new family.
- Q14: "Future studies use measured per-bucket half-spread pads instead of C1's flat Rs 1, as a new registered study;
  past results are never re-read" (item 5): story CP1 written, text first (`docs/stories/CP1-measured-cost-pads.md`,
  story/cp1-measured-pads 5348d501), lane 1 with two judges; the flat pad is B2's (frozen file), so CP1 adds a pad
  source beside it and reuses MS-SIM-b's spread functions.
- New document rules (owner, 25 Oct): documents judged like code, one owning document per functionality, 500 lines.

## Open questions (updated)

- CP1's three owner questions (30 or 20 sessions; median decided with p75 reported; the 15:00 bucket for
  close-to-close studies) and its two judges.

## CP1 text round 2 (after judges 679 J and 681 B, both FAIL, nothing blocking)

No owner message this round; the orchestrator relayed both judges' findings.
- Decision (some evidence, data check on 3,768 quotes from 13-23 Oct): the pad's unit is relative × the leg's own price.
  Leave-one-session-out median error: out-of-the-money Rs 0.113 vs Rs 0.137 for a rupee median; in-the-money Rs 2.46
  vs Rs 2.92. The otm/itm split is kept: in-the-money paid more in 26 of 33 buckets beyond 1%; the mean error is 8% lower.
- MeasuredPad is built per trial in the composition root and refuses at construction (three named errors). Q1 now
  gives dates per band (most non-NIFTY buckets stay provisional into 2027). New Q4: trades before the table's first
  session pay max(Rs 1, measured). A16 is out of scope.
- CP1 is at 1fd94daf. slippage.py's duplicate tick floor is removed on story/edge2-slippage-floor a77e9f78 (lane 2;
  full suite 17570 passed).

## Decisions so far
- No new EDGE2 search family (Q13 pause). CP1: no code until both judges PASS and the owner answers Q1-Q4.

## Open questions
- CP1 Q1-Q4 for the owner (in the story file).
