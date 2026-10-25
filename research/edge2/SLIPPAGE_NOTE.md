# What crossing half the spread costs at 15:00: a descriptive note (EDGE2)

Descriptive only: no trial, no strategy claim, no record (orchestrator, 25 Oct 2026). It feeds a later review of C1's
pad, a lane-1 cost-model change that needs the owner's word. Made by `python research/edge2/slippage.py` (output
`research/edge2/slippage/summary.json`), which reads through existing code unchanged: MS-P1b's verified
`CaptureReader` (Groww captures, hash against the sidecar), MS-SIM-b's `relative_half_spread` and `bucket_of`
(read-only reuse; MS-SIM's owner session was out of reach, the orchestrator agreed), and A20a's archived lot file.
NSE's public-chain captures (story O6) are parsed from their committed CSVs after each SHA-256 matched its sidecar.
The data read is the `exposed` row "Bid-ask spreads of the 15:00 captures" of `research/DATA_SPEND.md`, as a cost
input only.

## Answer

**For the contracts the desk and the EDGE studies actually trade (NIFTY and BANKNIFTY, near month and NIFTY's weekly,
out of the money or at the money), half the 15:00 spread is about Rs 0.03-0.65 a unit: C1's decided pad of Rs 1 a
unit a leg a side is conservative, by about 2 to 30 times.** Next-month contracts are wider, and FINNIFTY's and
MIDCPNIFTY's next-month options are often not quoted two-sided at all. [some evidence: 3,966 Groww quotes on 4-7
sessions, 13-23 Oct 2026, one 15:00 snapshot a day; one calm fortnight]

## Out-of-the-money and at-the-money strikes (the legs the EDGE structures use)

Median half-spread in rupees a unit (95th percentile in brackets), by days to expiry; under 1% means the strike is
within 1% of spot.

| Road | Moneyness | 0-7 days | 8-21 days | 22-45 days (next month) |
|---|---|---|---|---|
| NIFTY monthly | under 1% | 0.12 (0.17) | 0.22 (0.32) | 0.65 (1.33) |
| NIFTY monthly | 1-2% | 0.06 (0.10) | 0.12 (0.20) | 0.55 (0.97) |
| NIFTY monthly | 2-4% | 0.03 (0.05) | 0.07 (0.12) | 0.44 (0.83) |
| NIFTY weekly | under 1% | - | 0.41 (0.88) | - |
| NIFTY weekly | 1-2% | - | 0.32 (0.75) | - |
| BANKNIFTY monthly | under 1% | 0.50 (0.83) | 0.60 (0.72) | 3.05 (4.50) |
| BANKNIFTY monthly | 1-2% | 0.28 (0.47) | 0.36 (0.45) | 2.58 (4.65) |
| BANKNIFTY monthly | 2-4% | 0.10 (0.23) | 0.12 (0.27) | 2.07 (3.47) |
| FINNIFTY monthly | under 1% | 0.77 (1.20) | 0.77 (1.18) | 10.95 (12.12), 70% not two-sided |
| MIDCPNIFTY monthly | under 1% | 0.35 (0.45) | 0.42 (0.52) | 10.90 (26.05) |

- **Per lot:** NIFTY's near-month ATM half-spread is about Rs 8-15 a lot a leg (lot 65), against Rs 65 for the Rs 1
  pad; BANKNIFTY's about Rs 15-18 (lot 30) against Rs 30. Every bucket is in `summary.json`, in rupees a unit and a
  lot, with the share of quotes above the Rs 1 and Rs 2 pads and the size at the touch.
- **In-the-money strikes** are much wider in rupees (a large premium, fewer traders): medians of Rs 1-80 a unit. A
  structure that holds an in-the-money leg to an exit pays far more than its out-of-the-money twin.
- **Size at the touch:** the median best bid and ask hold about 1 lot (NIFTY's near strikes 1-12 lots). The
  half-spread holds for one lot; a larger order walks the book.
- **Two sources agree:** on 894 NIFTY monthly strikes quoted by both on the same sessions, NSE's half-spread minus
  Groww's has a median of Rs 0 (95th percentile Rs 0.57), which suggests Groww relays the exchange's best bid and ask
  [reasoning only].

## What it means [reasoning only; nothing here changes a result]

- **The EDGE studies' pads were conservative.** F1's always-on weekly fly paid Rs 173 of pads a trade at Rs 1 a unit;
  at these half-spreads it would be about Rs 20-40. F1's WF-G0 would then be near break-even after charges, not
  -Rs 105. F9's FLY-E0 would still lose (about -Rs 200 to -250 instead of -Rs 467). **No EDGE result may be re-read with these
  pads on the same data** (that would be fitting the cost to the result); a pad change goes through C1 as a lane-1
  change with the owner's word, and only forward or fresh-data tests would use it.
- **Closes are not quotes.** The studies filled at NSE's closing prices (the last half-hour's weighted price), not at
  the 15:00 mid; the gap between a close and a tradeable price at the close is not measured here.
- **Fills against mid** come from the school's own paper fills from Monday 26 Oct, when they exist; this note gets a
  section then.

## Limits

- 7 sessions for NIFTY's monthly (13-23 Oct), 4 for the other monthlies (from 19 Oct, A4c), 2 for NIFTY's weekly
  (from 22 Oct, A4f); one 15:00 snapshot a day; a calm fortnight. Spreads widen on volatile and event days, which
  this sample does not contain.
- The captures hold the strikes each recorder requests (the near expiries, strikes around the money), not the whole
  chain.
- Lots: A20a's archived file from 21 Oct; for 13-20 Oct the lot of the same expiry from the 21 Oct copy (a
  contract's lot does not change during its life).
- Skipped captures (missing, never repaired): listed in `summary.json` (`skipped_captures`).
