# EDGE2 F6 results: participant open interest and the next NIFTY futures sessions

Protocol `research/edge2/F6_PROTOCOL.md`, frozen in `F6_FREEZE.md` (commit `02665284`, code SHA-256 `48250512`). One
discovery run at `06646081` (`f6/discovery.json`). Trials 115-120, one Holm family at 0.05. **Exploratory and
research only: futures are on hold (owner, 25 Oct 2026); nothing here can be traded until the owner lifts the hold.**
Rupees per trade for 1 lot of the time, after the futures charges at today's 0.05% STT and a 1-point pad a side.

## Answer

**No variant passes, nothing is nominated, and the held-out years 2025-26 stay unread.** [strong evidence for these 6
rules on 1,478 sessions, 2019-2024; the NIFTY move series was already exposed, so "strong" means "these rules fail",
not more]

| Variant (trial) | Trades | Mean gross | Costs | Mean net | SE (Newey-West) | p | Holm | 2-point pad | Historical STT | Always long, same days | p_sign | Halves 2019-21 / 2022-24 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| FD-H1 (115) FII change, 1 session | 1,475 | 379 | 657 | -278 | 197 | 0.92 | no | -393 | +64 | -585 | 0.024 | -25 / -531 |
| FD-H5 (116) FII change, 5 sessions | 1,469 | 964 | 658 | 306 | 497 | 0.27 | no | 191 | 648 | 846 | 0.027 | 357 / 255 |
| FL-H1 (117) FII level, 1 session | 1,457 | 356 | 657 | -301 | 199 | 0.94 | no | -416 | +41 | -564 | 0.035 | -404 / -202 |
| FL-H5 (118) FII level, 5 sessions | 1,451 | 1,397 | 658 | 739 | 824 | 0.19 | no | 625 | 1,082 | 891 | 0.005 | 667 / 810 |
| CD-H1 (119) client fade, 1 session | 1,475 | 194 | 657 | -463 | 197 | 0.99 | no | -578 | -121 | -585 | 0.17 | -668 / -257 |
| CD-H5 (120) client fade, 5 sessions | 1,469 | 401 | 658 | -257 | 553 | 0.68 | no | -372 | 85 | 846 | 0.19 | -817 / 301 |

- **The 5-session "winners" are the market's rise, not the signal.** On the same days, always long earned +Rs 846 to
  +891 a 5-session trade, more than FD-H5 (+306) and FL-H5 (+739). Their longs earned +Rs 1,825 and +2,289, their
  shorts lost Rs 1,194 and 808. NIFTY roughly doubled over 2019-2024; any rule that is long half the time shares it.
- **The FII signals do carry some next-session direction, too little to pay.** FD-H1's gross is +Rs 379 a trade
  against about +Rs 72 for always long on the same days, and only 2.4% of random sign series with its long share do
  as well (p_sign 0.024; FL-H1 0.035). That is about 5 index points a lot, while today's costs are Rs 657 (about 12
  points at the period's mean lot of about 55). At the old 0.01-0.02% futures STT the 1-session FII rules would have
  netted about Rs 40-64 a trade. [some evidence, post-hoc reading of p_sign, which no Holm family covers]
- **The client fade has no edge.** Gross Rs 194 (1 session), worse than random in both horizons (p_sign 0.17, 0.19).
- **Tails.** Worst single trades: -Rs 72,418 (1 session) and -Rs 1,23,779 (5 sessions) a lot. A future has no cap; the
  house's Rs 10,000 cap per trade would need a stop or an option hedge that this study did not test.

**G1's "passed" for FL-H5 (trial 118) in `research/factory/gates.csv` is not a pass of this study.** The factory's
screen takes the lower 90% bound from the plain SD over n = 1,451, but H5 trades overlap (five open at once), so the
bound is too tight: measured on the run (judge 642), the Newey-West lag-4 error is 1.56 times the plain one for FL-H5
(824 against 527), 0.95 for FD-H5 and 1.06 for CD-H5 (this file first said "about sqrt(5)", which was wrong). With the protocol's Newey-West error the bound is 739 - 1.28 x 824 = -Rs 316, below
zero; Holm fails (p 0.19) and the always-long control beats it. The first gate row stays as logged (append-only);
a correcting G1 row (`screened_out`, net -Rs 316.2 on the Newey-West bound, `supersedes=passed_2026-10-24`) is appended
after it, so the machine record's last gate for 118 is `screened_out` (judge J's S2). [strong evidence: arithmetic on the frozen run's figures]

## What each role takes from it

- **Statistician:** six correlated tests, none near Holm. The only small p-values are for "better than a coin with the
  same long share" (p_sign), which is not the pre-registered test; they point at a direction signal of a few points.
  The factory's G1 bound needs an overlap correction for multi-day holds (a proposal, below).
- **Derivatives flow analyst:** FII index-futures changes lean the right way for the next session, as the desk
  folklore says, but a one-lot daily trade cannot harvest 5 points.
- **Tax and cost accountant:** the 0.05% futures STT from 1 Apr 2026 (2.5 to 5 times the old rate) is decisive: the
  same 1-session FII rules were about break-even under the old STT and are clearly negative now.
- **Risk manager:** naked futures risk Rs 70,000 to 1.2 lakh a lot in one trade; nothing here fits the house's
  per-trade cap without a hedge.
- **Portfolio manager:** nothing goes forward. The finding worth keeping is a direction lean of about 5 points a day
  from FII futures changes; it could only matter as a tilt inside a trade taken for another reason (for example the
  side of a defined-risk option spread), never as a stand-alone futures trade.
- **Red team:** 2019-2024 includes the 2020 crash and rebound and a strong bull market; the halves agree in sign for
  FL-H5 only because of the drift. The held-out years were not needed and stay fresh.

## Proposals (lane 2, the orchestrator's call)

1. The factory's G1 screen should take an overlap or dependence-corrected bound for multi-day holds (a card field such
   as `independent_n`, or the study's own standard error), so an overlapping study cannot "pass" by counting each day
   as independent. Owner of R1's factory code decides; I build nothing there.
2. A later pre-registered family could test the FII-change lean as a **side filter** for a defined-risk NIFTY option
   spread, where the cost per trade is already paid by the structure (reasoning only).

## Limits

- Daily opens and closes from NSE's F&O files; slippage as a fixed 1 point a side (2 reported).
- All index futures together in NSE's participant file (NIFTY's and the other indices'), as published.
- Always long is a control on the same days with the same costs, not a strategy: it is the market's drift.

## Deviations

- The G1 inputs were first appended to the six idea cards after the freeze (commit ed28d6b7), which made B4's
  `require_registered` refuse them (judge J's S1). The cards are restored to their frozen text; the inputs stay in
  history at ed28d6b7 and the gate rows are unchanged. No number changed.
