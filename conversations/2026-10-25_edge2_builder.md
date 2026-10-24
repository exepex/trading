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
