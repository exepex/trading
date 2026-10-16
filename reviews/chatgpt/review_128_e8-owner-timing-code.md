# Review 128 — E8 owner-timing fills, code part 1

**Target:** `story/e8-code-part1` at **cfd6a95b**; Response 207, E8 rules, Judge 203 addenda, owner-timing implementation and reported tests. **Second reviewer:** ChatGPT under quality rule 9. **Verdict: PARTIAL — the central fill/risk model is acceptable, with one consequential operational boundary to test before activation.** Evidence labels follow AGENTS.md. This is source inspection, not an independent rerun of the reported 7,061 tests. Paper only.

## 1. Fixed T+60 minutes — ACCEPT (strong evidence for clock implementation; reasoning only for realism)

`OwnerTimingClock.due` takes a server-observed order time and the fixed reaction, selects the first 15-minute mark at or after it, and rolls a mark after 15:25 to the next eligible session. At 15:15 card receipt plus 60 minutes, the due mark is next session **10:15**. This is deliberately conservative relative to the owner's variable availability; it does not claim the owner always reacts in exactly one hour. It may **penalise** fast-decaying strategies through overnight gaps, but can also **favour** them when overnight moves improve prices. Neither direction is assured. R=5 and R=30 should be diagnostics, not independent trials or replacements for the frozen R=60 verdict. Show per-view fill rates, opportunity nets and overnight-gap cohorts.

## 2. Price cap only — PARTIAL (strong evidence on `DueFill.price`; some evidence from E8a)

`due_fill.py` checks every leg at one snapshot, then `entry_range.admits` against the approved limit. A price-cap filter can be adversely selective: a bought call becomes cheaper after a bearish gap, fills, and may continue losing; a call that rises on a bullish gap can miss even though it would have profited. This is not a bug in the owner's approved limit policy. **Required reporting in part 2:** all original eligible opportunities by sign and magnitude of overnight NIFTY move, `opened` versus `missed_price_moved`, net per filled trade and net per original opportunity, plus the direction/structure of the proposed position. Compare the diagnostic R=5/30 and E4=15:15 views on the **same original decision cohort**, not only their filled subsets. Report missed-card/no-quote/away separately; never infer missed P&L as realised profit. No extra ±0.5% filter without evidence.

## 3. Fill-day risk and separate books — ACCEPT (strong evidence)

`FillDayRisk.miss` rebuilds C2's market from the due-mark copy, reads the current **book's** open positions and tests the proposal again. `margin_room` maps to `MISSED_FUNDS`; other failed C2 rules or fill-time maximum loss map to `MISSED_RISK_CAP`. This split is useful and is not a new risk calculation. `OwnerTimingStep._pending` sorts by server T, and `sync.write` persists each fill before the next book check. Within one book, earlier morning entries consume funds before later entries. Different books are independent hypothetical accounts and must **not** share cash or touch capacity. If two T values tie, use the already deterministic order and disclose it; no optimizer.

## 4. Misses in scorecards — PARTIAL (strong evidence on outcome classes; reasoning only for attribution)

An entry reaching execution but not filling should contribute **zero realised P&L** and remain in the execution-opportunity denominator. This includes price moved, no quote, thin size, expired, funds and risk-cap misses. However, `MISSED_NO_CARD` is a delivery/operations failure, and `MISSED_OWNER_AWAY` an availability constraint, not a market execution-quality failure. Keep them in the **owner-achievable opportunity** denominator but report them as distinct reasons; do not describe their frequency as a strategy's liquidity failure. Gate refusals before execution remain outside the fill-rate denominator, separately reported. An unfilled pending entry belongs in neither denominator until resolved; a partial unwind contributes its actual negative cash flow. This matches E6b's shared counter without changing the frozen score.

## 5. Exits waiting — ACCEPT with a normal-path test (strong evidence on code)

`OwnerTimingExits.apply` traverses later valid marks, closes available legs, and retains the rest through `open_positions`; `ExitDesk.pending` records a pending exit. C2's book view must continue seeing the remaining leg risk at the next morning's evaluation. **Integration test:** after a short leg has closed but its protective leg is still pending, build the next morning's real `RiskBook` and assert remaining open exposure is counted and new entries are refused when it consumes the relevant cap. Repeat for an entirely unfilled exit. Do not mark a pending exit as closed merely because an alert was delivered. The known risk of an unavailable quote delaying exit is genuine but inherent in the agreed E8 policy.

## 6. Cross-day, go-live, seals and copies — PARTIAL (strong evidence on inspected code; reasoning only on residual operations)

**Cross-day decision:** `OwnerTimingEntries.apply` checks `order.decided_at >= card_time`, which rejects a decision committed after the delivered card. A decision from a previous day can still be eligible for its own card and due mark; do not substitute today's card time for yesterday's pending order. Test a prior-day order recovered two sessions later: it must use the **original** delivery time and due mark, or record its original miss, never take a newly favourable mark.

**Midweek activation:** the default-off switch preserves E4 before the owner date. Test one entry decided before the live date and due afterward: it must not be filled twice by old E4 and new E8. The contract must say whether such pre-live pending entries are excluded; the safest interpretation is **only decisions created under the live owner-timing mode** enter E8's queue.

**Seals:** `SealedDriveAvailability` verifies the prefix hash from the seal committed before T; a later edit to a sealed line refuses rather than silently rewriting owner history. This is appropriate. A newly appended away row after T cannot excuse a missed entry. The missing-seal case defaults to available; that is the documented rule, not proof the owner was present.

**Two copies:** `MarkSnapshots.at` must deterministically choose the canonical A16 copy over a valid A4 stand-in or reject conflicting values; never select whichever is more favourable to a trade. Verify the actual selection and add one planted disagreeing-copy fixture if not already present. The 2-minute on-time window and snapshot hash must bind the chosen source.

**A16 near-month future:** `FillDayRisk._missing_reason` distinguishes missing futures from missing quotes; a further-month structure may legitimately miss because its expiry future is unavailable. Report it, never synthesize a forward.

**No-snapshot day:** if no exit review fires, there is no delivered exit alert and therefore no T. This can delay a risk-reducing exit until the next 15:15 review. The book must remain exposed and operationally flagged; no invented backdated exit. This is a known limit, not a new scheduler request.

**Most consequential pre-activation check:** the live-mode handover at the boundary must not double-fill or drop pre-live decisions. This affects actual paper trades. Add one boundary fixture if absent; do not add a new service.

## Financial-role challenge

**Mathematician/statistician/quant modeller:** conditional fills versus original opportunities; diagnostic views are correlated. **F&O/options/volatility trader:** overnight price caps select by gaps; one-hour fills are a model, not execution proof. **Risk/portfolio/head of desk:** pending exits retain risk, and each book funds its own trades. **Execution/microstructure:** same-mark bid/ask, displayed size and quote provenance; no guaranteed market order fill. **Market/macro/flows/equity research/investment banking:** overnight events can reverse the apparent value of a signal. **Regulation:** paper-only. **Behavioural:** do not retrospectively shorten R or loosen a limit to rescue missed winners. **Tax/cost accounting:** no-fill pays no trading charges; partial unwind does. **Data engineer/red team:** test activation boundary, original card T, conflicting A16/A4 copies and sealed availability.

**Final verdict: PARTIAL — code can proceed toward activation, contingent on the one live-boundary regression and the specified reporting/exit-risk integration checks.** No new price filter, scheduler, lock or scoring system is justified by observed evidence. No real orders are enabled.
