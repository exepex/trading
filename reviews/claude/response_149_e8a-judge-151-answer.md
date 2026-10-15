# Response 149: answer to judge 151 (E8a story text, FAIL 3/9/5)

Builder: Claude (project thread), 15 Oct 2026 IST. Branch `story/e8a-fill-timing`. Each finding checked; story text
revision 2 in `docs/stories/E-paper-desk.md` (E8a).

| Finding | Check | Decision |
|---|---|---|
| B1 mean of C is drift, mostly theta | True: STR1 makes BF the exact mirror of SF (and CDS/CCS, PDS/PCS), so mean C(seller) = -mean C(buyer) | Accept. The headline is now the size of the move (`|C|` and its bad-side tail) and the flip share. The theta part is shown beside the mean; 1-night and 3+-night gaps are split. Signal decay is "not measured" on the report |
| B2 "win at both" missing | True: owner row `DESK_DECISIONS.md:179` names it | Accept. Flip share, held to expiry at E7's settlement, exploratory (spent data) |
| B3 no gap list | True | Accept. The Out list gives a reason for each item. All of E8's R = 5, 30, 60 and E4's 15:15 baseline are now in scope |
| Ledger kind "measurement" invalid | True (`ledger.py:26`) | Accept: prospective, hypothesis no (as R2) |
| Data spend understated | True: C is the P&L of selling at the decision and buying back at the fill | Accept: the windows become spent, and the rows are written with the ledger row |
| No paired 14:00 vs 15:00 difference | True | Accept: paired per session and family, with an interval |
| 14:00 path broke E8's rule | True: a 14:08 card + 60 minutes reaches the 15:15 snapshot | Accept: R = 60 maps to 15:15. The lost last hour is stated as not measured |
| No stale or missing cap; the Sep 2025 symbol failed | True | Accept: a coverage-only probe (no price) runs before the freeze, and a cell with more than 10% stale or missing prints "insufficient data" |
| Spread caveat assumed | True: A4 has only a few 15:00 sessions | Accept: the spread at fill times is "not measured"; A4 gives an order of size only |
| Live rule too weak | Partly: 20 sessions is what the owner chose to wait for | Accept the paired mid-quote comparison with a stated "not confirmed" rule; keep 20 sessions |
| Expiry, units, criteria | True | Accept: sessions-to-expiry split; points and share of width (never of a small credit); new criteria for E8 mapping, exclusions, bootstrap and a 14:00 hand day |
| Minor: block checks, gap and VIX timing, call count | True | Accept: blocks 10 and 20, gap from the same window, VIX at the decision day's open, estimate 2,000-3,000 calls |
| Minor: duplicated line at E-paper-desk.md:709 | True (E7's status line) | Fixed |
| Minor: owner row appears twice | Not found: `git show origin/main:docs/DESK_DECISIONS.md` has one "Fill-timing study: history" row | Push back; no change |
| Judge's disagreements (consecutive windows do not overlap; the 14:00 path is E8's own remedy) | Agree | Kept |
