# Review 108 — E1b paper-account capital top-up

**Date:** 15 Oct 2026. **Reviewer:** ChatGPT, independent second reviewer under quality rule 9. **Reviewed:** response 136 Part 1, `story/e1-topup` at `ddcefcc8f969f42cb82e7ef706173d68234183c3`, E1b story, response 110 addendum 2, `fno/books/account.py`, and judge 110's reported PASS. **Overall verdict: PARTIAL: accounting principle accepted; a point-in-time inconsistency remains before counted paper replay.** Evidence labels follow AGENTS.md. I did not independently run the 5,142-test suite or 19 mutation probes.

## 1. Restore capital, not equity — ACCEPT (strong evidence)

`AccountWriter.top_up` computes `amount = target - account.capital()`, and `PaperAccount.capital(at)` sums only opening/top-up entries. Realised losses remain in cash and P&L; they are not replenished as if the owner had earned them.

**Worked example:** initial capital ₹500,000; realised loss ₹10,000; cash ₹490,000. Top-up ₹1,500,000 yields **capital ₹2,000,000, cash ₹1,990,000 and P&L −₹10,000**. Restoring *equity* instead would add ₹1,510,000 and erase the loss economically. The design correctly avoids that. The brake should be computed on cumulative trading P&L, not deposits; response 110's tests and C2/C4 story explicitly enforce that.

**Qualification (reasoning only):** account return is flow-sensitive. Never use `ending equity / opening ₹500k − 1` across a top-up. Report a time-weighted return or segmented capital-normalized P&L, with capital-at-risk by interval; S2's future benchmark change must account for the cash-flow date. A top-up is neither a profitable trade nor an increase in strategy skill.

## 2. Past decisions, double counting, oversized books — PARTIAL (strong evidence)

**Positive:** `capital(at)` correctly gates the top-up by its timestamp; C2 and C4 use the 15:00 cutoff. Top-up is excluded from `FILL_KINDS`, trade positions and C1 ledgers. `AccountWriter.top_up` refuses an unstarted, above-target or non-flat book and requires the book's lock. The judge's real-ledger example gives ₹500k at 15:00 and ₹2m at 17:00 on the same day.

**Remaining issue:** `PaperAccount.state(marks, at)` calls `account_state(self.capital(at), self.fills(), ...)`. Thus **capital is time-filtered but fills are not**. Response 110 explicitly lists this as a known unchanged limit: “C2 reads every fill in the ledger, not only those by the cutoff.” On a historical replay, a decision at 15:00 may see a fill or cash change from 16:00, while the top-up at 17:00 is correctly excluded. That can change margin room, closed P&L, drawdown and a risk refusal. The story's statement that past decisions are replay-safe is therefore true for capital alone, not the full risk state.

**Exact fix before historical/counted replay:** provide a point-in-time account view where `fills_at(cutoff)` includes only fills/settlements with timestamps <= cutoff, and derive cash, positions, realised P&L and C2/C4 state from that same view. Alternatively bind every decision to its immutable originally recorded account snapshot and disallow recomputation from the latest ledger. Add a regression fixture: decision 15:00, later fill 16:00, top-up 17:00; replay must see neither later event. This is a root-cause cutoff contract, not a special-case top-up patch.

**Additional small risk (reasoning only):** `top_up` uses a day-derived entry ID. Multiple authorised increases on one day could reuse that ID; currently owner policy permits only the initial increase, so treat any further same-day target change as a new owner decision and fail closed until a unique immutable capital-event ID is defined.

## 3. Scoring, reporting, three-book comparison — PARTIAL (strong evidence on current behavior; reasoning only on future comparisons)

**Positive:** P10's `pnl = marked_equity − capital(day)` and S2's cash reconciliation avoid classifying a ₹1.5m deposit as a ₹1.5m loss or gain. The writer rebuilds the current view and records a daily equity row. Judge's tests cover the zero-P&L example.

**Remaining requirement:** the capital flow changes the denominator and exposure window. Three books topped up at different instants are not strictly comparable on raw returns or rupee-day capital unless the report aligns their effective capital histories. For a fair contest, publish each book's capital flow timestamp, capital-weighted/rupee-day exposure and whole-account P&L; align the common comparison start and avoid using deposits as strategy returns. If books have prior gains/losses, a flat book can have cash below/above ₹2m while capital is exactly ₹2m; do not claim it is “fully funded” merely because the capital setting passes. Cash/margin sufficiency must remain a separate hard check.

**Worked example:** Book A receives ₹1.5m at 10:00 and Book B at 17:00. Both show ₹2m end-of-day capital, but only A was eligible for a 15:00 trade. The opportunity/denominator difference is operational, not forecasting skill. The comparison must disclose it.

## Financial-role cross-check

- **Mathematician / statistician / quant modeller:** separate external cash flows from returns; align opportunity windows.
- **F&O trader / options strategist / volatility trader / execution:** a larger notional account does not improve quote liquidity or guarantee fills; enforce original per-trade caps.
- **Risk manager / portfolio manager / head of desk:** cash/margin availability and brake must be independent of deposits; refuse oversized or unknown states.
- **Market research / macro / derivatives flow / equity research / investment banking:** the top-up does not change market evidence, only allocation capacity; compare identical market dates.
- **Regulation:** this is a paper deposit, not an NSE margin credit or real brokerage transaction.
- **Behavioural finance:** do not hide losing performance behind a fresh capital injection.
- **Tax/cost accountant:** deposit is not taxable F&O income and cannot enter trade charges.
- **Data engineer / red team:** attack replay after late fills, duplicate capital IDs and ledger/view crashes.

## Final decision

**PARTIAL.** E1b's capital-versus-equity treatment and dated append-only top-up are correct. The outstanding risk is not the top-up amount but **the inconsistent as-of boundary between capital and fills during historical replay**. Fix or explicitly constrain counted decisions to immutable recorded account snapshots before claiming complete point-in-time reproducibility. The future S2 capital-flow benchmark must also be defined before comparing the books. No real orders are authorized.
