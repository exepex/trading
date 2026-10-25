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
