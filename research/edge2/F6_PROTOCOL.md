# Protocol: EDGE2 F6, participant open interest and the next NIFTY futures move

Story: EDGE2 edge search (`docs/WORK_REGISTER.md`; owner, 25 Oct 2026: "no proven edge: let's try to find them using
dry runs"). Builder: session_01VhppcYHXq3yTJBV2UnsWSs. Written and committed **before any participant-OI file is
read** by this study. **Research only:** futures trading and capture are on hold (owner, 25 Oct 2026), so F6 starts no
capture and any finding is reported as "research; cannot be traded until the owner lifts the futures hold". Everything
is EXPLORATORY: it can nominate, never prove.

## 1. The question

Does the change or level of foreign investors' (FII) or retail clients' net index-futures position, as published in
NSE's end-of-day participant-wise open interest file, predict the next 1 or 5 sessions of the NIFTY future well enough
to pay real costs?

Why it could work [some evidence: FII index-futures positioning is widely read in India as informed or hedging flow;
studies of FII flows and Nifty returns find contemporaneous links, a predictive one is not established; reasoning only
that it survives costs]. Who pays: the other side of a better-informed flow; for the client fade, retail traders, who
lose in aggregate (SEBI's 2023 and 2024 studies: 89-93% of individual F&O traders lost money) [some evidence]. Why
futures: one leg, about Rs 1,100 a lot round trip with the pad (section 5) against a typical daily NIFTY move of about
Rs 13,000 a lot, so a small edge is not eaten by costs as F1's four legs were.

## 2. Status, periods and data spend

- **Predictor:** participant OI (A8), 1,929 files 2019-2026, `fresh` in `research/DATA_SPEND.md` (the parser's
  identity checks read the files' sums, never as a predictor).
- **Outcome:** the NIFTY near-month future's open and close from NSE's daily F&O files. NIFTY's index closes are
  `exposed` (many studies read its moves), so even the held-out years are weaker evidence: the move series has been
  seen, though never against participant OI. Every result is exploratory.
- **Discovery:** trades whose exit session is on or before 31 Dec 2024 (signals from 2019).
- **Held-out:** trades whose signal day is on or after 1 Jan 2025, to the last archived session; read **once**, only
  for nominated variants, only after a lane-1 judge has passed the frozen rules (orchestrator, 25 Oct 2026). The code
  refuses any OI file or futures row dated after 31 Dec 2024 until the discovery results file is committed and
  unchanged and names a nominee.

## 3. Signals (point in time)

- From day t's file: for participant P and the index-futures group, net_t = long - short (contracts; all index
  futures, NIFTY's and the others', as NSE reports them).
- The file is published after the close. **A signal from day t's file trades only from day t+1's open.**
- Three signals, each with a pre-registered direction:
  - **FD** (FII change, follow): d_t = net_t - net_(t-1) of FII; long if d_t > 0, short if d_t < 0, no trade if 0.
  - **FL** (FII level, follow): l_t = net_t - mean(net_(t-19) .. net_t) of FII; long if > 0, short if < 0.
  - **CD** (client change, fade): d_t of Client; short if d_t > 0, long if d_t < 0.
- Missing file on t or t-1 (or fewer than 20 files for FL): no signal that day (`no_signal`, counted).

## 4. Trades

- **Horizons:** H1, from the open of session t+1 to its close; H5, from the open of t+1 to the close of t+5.
- **Variants (6 trials):** {FD, FL, CD} x {H1, H5}. Every session with a signal gives a trade, so H5 trades overlap.
- **Contract:** the NIFTY future with the nearest expiry on or after the exit session (no roll inside a trade); its
  open (`OpnPric`) at entry and close (`ClsPric`) at exit. A missing or zero price: `no_price`, counted.
- **Lot:** the contract's market lot on the entry session (UDiFF `NewBrdLotQty`; before 2024, EDGE1's NIFTY schedule).
- One lot a trade; P&L = side x (exit close - entry open) x lot - charges - pads.

## 5. Costs (stated per lot, the repo's futures rates)

The rates are the market school's checked futures model (`research/school/probes/2026-10-22-p0-5-futures-calendar-model.md`,
section 4; NSE circulars FATAX/73524 and FA/73061), applied to both orders of every trade, decided at today's rates for
every date (conservative): STT 0.05% of the sell side; NSE transaction charge and IPFT Rs 183 a crore each side; SEBI
fee Rs 10 a crore each side; stamp duty 0.002% of the buy side; brokerage Rs 20 an order; GST 18% on brokerage, NSE
charge and SEBI fee. **Pad:** 1 index point a unit a side (decided); 2 points (reported, nomination condition 2).
`config.yaml`'s `charges` table is for options and is not used for futures (it has no futures STT).

**Per-lot round trip, stated before the run** [arithmetic on the rates above]: NIFTY at 25,000, lot 65, notional Rs
16.25 lakh: STT 812.50, NSE 59.48, SEBI 3.25, stamp 32.50, brokerage 40.00, GST 18.49: **Rs 966 of charges, plus Rs
130 of pads, Rs 1,096 a round trip** (Rs 1,226 at the 2-point pad), about 17 index points or 0.067% of notional. A historical-STT run is
reported beside it (futures STT 0.01% to 31 Mar 2023, 0.0125% to 30 Sep 2024, 0.02% to 31 Mar 2026, then 0.05%)
[some evidence: Finance Acts 2023 and 2024, NSE/FATAX/73524], never decided on.

## 6. Statistics and nomination (discovery)

- Per variant: mean net per trade; standard error by Newey-West with lag 0 for H1 and lag 4 for H5 (the overlap); one
  -sided p of mean > 0 = 1 - Phi(mean / SE). Holm across the 6 at 0.05.
- **Controls** (reported beside each variant): N0 (no trade), AL (always long, same horizon and days), RS: 2,000
  random sign series that keep the variant's days and its share of long trades (seed 20261025); p_sign = share of
  random means >= the variant's mean.
- **Nomination to the held-out read** (all four; at most 2, lowest p first): (1) Holm-significant; (2) mean net > 0 at
  the 2-point pad; (3) p_sign <= 0.10; (4) mean net > 0 in each half of discovery (exits 2019-2021 and 2022-2024).
- Reported: trades and skips by reason, mean gross, charges, pads, net (pad 1, pad 2, historical STT), win share,
  worst trade, max drawdown (H5: on the non-overlapping trades starting at the first, as a figure only), by year, long
  and short apart, and G3's sample plan for a forward test at 250 trades a year.

## 7. Held-out read (once)

Only the nominated variants, same code, trades with signals from 1 Jan 2025. Pass: Holm across the nominated at 0.05
one-sided and mean net > 0 at the 2-point pad. A pass is a **proposal** to the owner for a forward test, under the
futures hold's terms; a fail is final for that version.

## 8. Registration and counting

Ledger trials 115-120 (reserved by the orchestrator, 25 Oct 2026), one per variant, with idea cards
`research/ideas/EDGE2-F6-*.md` and DATA_SPEND rows in one commit before any OI file is read. Question
`edge2-f6-participant-oi-futures`, alpha 0.05. The EDGE2 program reports a cumulative Holm across families.

## 9. Deviations

None yet.
