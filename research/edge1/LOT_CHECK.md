# EDGE1 lot cross-check (protocol section 8, revision 5)

Run on 22 Oct 2026 with `python research/edge1/lot_changes.py` on the F&O row cache (1,920 sessions, 2 Jan 2019 to
19 Oct 2026; legacy files to 29 Dec 2023, UDiFF from 1 Jan 2024).

## What the check found

- **The derived lot is not a lot.** On legacy files, turnover / (contracts x settlement price) wanders around the true
  lot: NIFTY 72-77 around 75 (2019-21), 49-51 around 50; BANKNIFTY 19-21 around 20, 24-26 around 25. Turnover is
  traded at the day's average price, not the settlement price, so the ratio is off on volatile days (March 2020 the
  most). Using it, as build part 1 did, would have moved some trades' P&L by up to 4% and their cap width. Root cause
  fixed: legacy days now take the circular schedule (`edge1study/lots.py`), and the derived lot only checks it.
- **Against the schedule:** NIFTY 0 legacy lots more than 5% off; BANKNIFTY 30, every one a 19 or 21 against 20 (one
  unit, 5.0%, in Sep 2019 and Mar-Jun 2020). No derived value points to a different regime, so the schedule's
  change dates hold on every legacy day [strong evidence for the regimes; the one-unit noise is the cause above].

## The schedule (legacy files)

| Index | Lot | From the monthly expiry | Source |
|---|---|---|---|
| NIFTY | 75 | before 2019 (data: 75 from 1 Jan 2019) | data |
| NIFTY | 50 | July 2021 | NSE/FAOP/47854, 31 Mar 2021 [some evidence: broker notices citing it]; data: first 50 on 30 Apr 2021 for the 29 Jul 2021 expiry |
| BANKNIFTY | 20 | before 2019 (data: 20 from 1 Jan 2019) | data |
| BANKNIFTY | 25 | July 2020 | NSE's June 2020 revision (Zerodha bulletin, 26 Jun 2020; circular number not found) [some evidence]; data: first 25 on 4 May 2020 for the 30 Jul 2020 expiry |
| BANKNIFTY | 15 | July 2023 | NSE/FAOP/56233, 31 Mar 2023 [some evidence]; data: first 15 on 28 Apr 2023 for the 27 Jul 2023 expiry |

## NSE's board lot (UDiFF files, from 2024): agrees with every circular found

- NIFTY 50 to 25 on 26 Apr 2024 for every open contract from the May 2024 expiries; the April 2024 monthly kept 50
  (NSE circular of 2 Apr 2024, per broker notices).
- NIFTY 25 to 75 for new contracts from 20 Nov 2024 (first monthly at 75: Feb 2025; the Jan 2025 monthly stayed 25
  to expiry; long-dated contracts moved on 27 Dec 2024).
- NIFTY 75 to 65 from the Jan 2026 contracts, long-dated moved on 31 Dec 2025 (NSE/FAOP/70616).
- BANKNIFTY 15 to 30 (first monthly Feb 2025, long-dated moved 26 Dec 2024), 30 to 35 from 25 Apr 2025, 35 to 30
  from the Jan 2026 contracts (long-dated moved 31 Dec 2025).

A lot changed during a contract's life does not change a position's units, so each trade keeps its entry day's lot
to exit, as the code does.
