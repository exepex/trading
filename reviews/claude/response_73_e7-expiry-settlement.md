# Response 73: story E7, expiry settlement: builder's claims

Builder session, 14 Oct 2026. Story: `docs/stories/E-paper-desk.md` E7 (written in this branch, from the
orchestrator's scope after judge 68). Branch `story/e7-expiry-settlement`, built on `story/e4-entry-limit` (it needs
E4's blocking code); judge first, nothing on `main`.

**Verdict in one line:** a position still open at expiry now closes at NSE's cash settlement (intrinsic value against
the index's final settlement price from the expiry day's file only), with exercise STT, so no book carries a dead
contract at a stale mark. A missing file blocks the book's new risk with an alert. 51 desk tests; 31 of 31 planted
defects caught (8 for E7, 2 for judge 68's entry-limit condition).

## 1. A data finding that shapes the design (strong evidence: NSE's own file)

I fetched NSE's UDiFF F&O file for the NIFTY monthly expiry of **25 Jan 2024** from its public archive. On the expiry
day, **every expiring NIFTY row (the future and each option) carries the index's final settlement price, 21,352.60, in
`SttlmPric`**. An option row's `SttlmPric` is not the option's value. Its `ClsPric` is not its settlement value
either: the 21300 CE closed at 19.70 while it settled at 52.60 in the money (the 21000 PE closed at 0.10 and settled at
0). Settling at the close would have been badly wrong. A cut of the file (NIFTY rows only, 12 rows) is committed as
`tests/fixtures/nse_settlement/` and the test `test_the_real_file_shows_why_the_close_is_never_used` pins these numbers.

## 2. What was built

| Part | What |
|---|---|
| `fno/desk/settlement.py` | `SettlementPrices` interface; `NseFinalSettlement` reads only `NseDailyFoSource.path_for(expiry)` through A2's library; requires every expiring row's `TradDt` = the expiry and one agreed, positive `SttlmPric`; else `SettlementError`. Unpublished file: `None`. `settlement_record` closes a leg at `Leg.intrinsic(final price)`, dated the expiry at 15:30 IST, with the file's SHA-256 in the row. |
| `fno/desk/exits.py` | An expired leg is settled in the exit review. A missing or unclear price gives `settlement_needed` (alert once a day, blocks the book through E4's `BLOCKING_OUTCOMES`). When every leg is flat: `closed` with the price and file named. Legs of a later expiry stay open. |
| `fno/costs.py` (C1) | `settlement_charges_breakdown`: exercise STT `stt_exercise_pct` on an in-the-money long's intrinsic value; brokerage + GST on each in-the-money leg (conservative); nothing else; nothing on a worthless leg. |
| `fno/accounting/ledgers.py` (C1) | `Order.settlement` and `Order.charges(table)`: **one** dispatch used by E1's `Fill.priced` and C1's `trade_line`, so the three ledgers and the account agree. |
| `fno/books/fills.py`, `account.py` (E1) | Ledger row kind `settlement` (read back as a settlement order); `PaperAccount.fills()` reads both kinds. |
| `config.yaml` | `charges.stt_exercise_pct: 0.15`. |
| `fno/desk/wiring.py` | `build_exit_desk` wires `NseFinalSettlement(build_nse_fo_library())`. |

## 3. Acceptance criteria, claims and evidence (`tests/desk/test_settlement.py`, 10 tests)

| # | Criterion | Claim | Evidence |
|---|---|---|---|
| 1 | ITM short closes at intrinsic, never the stale mid or the close | Met. Settlement 25,100: short 25000 CE bought back at 100.00 (its pre-expiry mid was 150.50), charges Rs 23.60 (brokerage + GST, no STT); net = opening cash flow - 6,500 - 23.60, hand computed. | `test_an_itm_short_settles_at_intrinsic_value_not_its_stale_mid`; real-file test above |
| 2 | OTM leg settles at 0 with no charges | Met. Settlement 25,000 (pinned): all four legs at 0, charges 0; net = the credit kept. | `test_out_of_the_money_legs_settle_at_zero_with_no_charges` |
| 3 | ITM long pays exercise STT; a short does not | Met. Settlement 25,300: long 25200 CE sold at 100: STT 0.15% x 6,500 = Rs 9.75 plus Rs 23.60; short 25000 CE at 300: Rs 23.60 only. | `test_an_itm_long_pays_exercise_stt_on_its_intrinsic_value` |
| 4 | Only the expiry day's file; disagreeing rows refused | Met. The store is asked for exactly one path, the expiry day's; a copy with one changed `SttlmPric` is refused ("disagree"); a file without contracts expiring that day is refused. | `test_the_final_settlement_price_comes_from_the_expiry_day_s_file_only`, `test_a_file_without_one_clear_price_is_refused_never_guessed` |
| 5 | Missing file: `settlement_needed`, alert, no new risk until settled | Met. One alert; Book 1's next entry refused "(settlement_needed) blocks new risk"; once the file exists the next review settles and closes. | `test_a_missing_settlement_file_blocks_new_risk_until_published` |
| 6 | C2 no longer sees it; C1 equals the account | Met. Before: `account.state({})` raises `MissingMark` (dead contracts still need marks). After: `load_risk_book` has no open trades; `trade_line(trade).net` equals the account's net to 1e-9; 4 ledger rows of kind `settlement`. | `test_settlement_releases_c2_s_view_and_c1_s_ledger_agrees_with_the_account` |

**Mutations (each must fail a test), 8 for E7, all caught:** settle at the index price instead of intrinsic; no
exercise STT; exercise STT charged to the short; settlement charged as a trade; settlement kind lost in the ledger;
disagreeing rows accepted; the previous day's file read; expired legs never settled. The 21 E4 mutations are still
caught (29 of 29).

## 3a. Judge 68's condition, fixed at the root on this branch: the entry limit comes only from C2

**Problem (judge 68 addendum 1, checked in the code):** `EntryOrder.approved_entry_rs` was a free field and
`RiskDecision` carried no entry cash, so any caller could pass a looser number and widen the limit.

**Fix:**
- C2's `RiskManager` now computes the proposal's entry cash with the same `TradeCosts` its maximum-loss rule uses
  (wired in `fno/risk/wiring.py`). It records that cash in `RiskDecision.entry_cash_rs` (and in `record()`), together
  with the `proposal` it judged. An unpriceable proposal gets `None`, and its decision is refused anyway.
- E4's `EntryOrder` no longer has a limit field. The limit is `order.risk.entry_cash_rs`, and E4 refuses any decision
  whose proposal is not exactly the order's (the same lots, legs and terms) or that carries no entry cash.

**Evidence:**
- `test_entry_limit.py::test_the_limit_comes_only_from_c2_s_decision_on_this_exact_proposal`: the field is gone; a
  1-lot decision used for a 2-lot order is refused; a decision without entry cash is refused.
- `test_c2_records_the_approved_entry_cash_with_the_same_cost_model`: a real C2 decision carries exactly
  `entry_cash_flow`, also in its record.
- Mutations "decision on another proposal accepted" and "C2 records no entry cash" are both caught (31 of 31 overall).

What stays possible: code that builds a `RiskDecision` by hand. Only C2 should create one; E3's C4 re-check is the
independent second gate (reasoning only).

## 4. Honest limits (confidence labelled)

1. **Exercise STT rate 0.15% (strong evidence for the rate; enactment from secondary sources).**
   - **Primary text read:** the Finance Bill, 2026 (Gazette text), notes on clauses, clause 143, which amends section
     98 of the Finance (No. 2) Act, 2004. It says the STT on sale of "an option in securities when such option is
     exercised is 0.125 per cent. of the intrinsic price" and proposes "an option in securities, where option is
     exercised to 0.15 per cent. of the intrinsic price". It also raises STT on option premium from 0.1 to 0.15 per
     cent. I read it with `pdftotext` from a third-party copy of the Gazette extract
     ([PDF](https://d23z1tp9il9etb.cloudfront.net/download/pdf26/Relevant%20Extract%20of%20The%20Finance%20Bill,%202026.pdf)),
     not from a government host.
   - **Enactment and effective date (secondary):** the Finance Act, 2026 received assent on 30 Mar 2026, and the
     rates apply to trades from 1 Apr 2026 ([Business Standard](https://www.business-standard.com/amp/economy/news/new-i-t-law-higher-securities-transaction-tax-on-f-o-trade-to-kick-in-from-april-1-126033100344_1.html);
     broker notices of the NSE circular: [Fyers](https://fyers.in/notice-board/revision-in-securities-transaction-tax-stt-effective-april-01-2026/),
     [Arihant](https://www.arihantplus.com/market-insights/bulletin/revision-in-securities-transaction-tax-stt-rates-effective-april-1-2026)).
     The purchaser (the long holder) pays it on the intrinsic value.
   - **Not read myself:** NSE's STT page
     ([nseindia.com](https://www.nseindia.com/static/products-services/equity-derivatives-securities-transaction-tax))
     and the Income Tax Department's section 98 page
     ([incometaxindia.gov.in](https://www.incometaxindia.gov.in/w/section-98-55)) both refuse automated reads (HTTP
     403). I did not find the NSE circular itself or a CBDT notification. The owner can open those two pages in a
     browser to confirm the enacted table.
2. **Brokerage on settlement (reasoning only).** Charged on every in-the-money leg, long or short, as if an order.
   Groww's exact charge for an expiry exercise or assignment is not verified; this is the conservative side. No
   exchange, SEBI, IPFT or stamp charge is applied because no premium is traded (reasoning only).
3. **Timing.** Settlement happens at the first exit review after the expiry day whose file is published (the review
   runs at the 15:15 snapshot). The settlement row is dated the expiry day at 15:30, so the trade's closed day is
   correct, but marked equity between the expiry evening and that review still shows the stale mark (flagged). The
   book is blocked meanwhile.
4. **NIFTY only.** The underlying is `NIFTY_SYMBOL`; another index needs its symbol passed (one line), stock options
   are physically settled and out of scope.
5. **One file, A2's library.** If NSE's file is in neither Drive nor the archive yet, the library asks NSE's archive
   (A2's normal path); nothing else is ever used.

## 5. Checks on the merged tree

Full suite, `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py`: results in the commit message
and the message to the orchestrator.
