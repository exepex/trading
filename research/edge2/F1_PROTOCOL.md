# Protocol: EDGE2 F1, a volatility-premium gate on weekly index option premium

Story: EDGE2 edge search (`docs/WORK_REGISTER.md`; owner, 25 Oct 2026: "no proven edge: let's try to find them using
dry runs"). Builder: session_01VhppcYHXq3yTJBV2UnsWSs. Research only, paper only: nothing here changes the daily run,
the card, the captures, Book 1 or the school. **Everything below is EXPLORATORY: it can nominate a candidate for the
school's forward test; it never proves an edge.** Written and committed before any F1 number exists.

## 1. The question

Does selling a defined-risk weekly index option position, held to expiry, make money after every real cost, and does
trading it only when implied volatility is rich against a point-in-time forecast of realised volatility do better than
trading it every week (and than a random gate of the same frequency)?

Why it could work [strong evidence that a variance risk premium exists in index options: Carr and Wu 2009; Bollerslev,
Tauchen and Zhou 2009; India VIX above later realised in most months; that it survives costs on Indian weeklies with
defined risk is NOT shown, and EDGE1 found 0 of 24 monthly defined-risk variants positive after costs]. Who pays:
hedgers and retail buyers of short-dated options (SEBI's 2023 and 2024 studies: 89-93% of individual F&O traders lost
money) [some evidence]. Why weeklies: about 50 trades a year an index instead of EDGE1's 5-10, so a real edge could be
seen in a sample and later confirmed forward in a useful time.

## 2. Status and data spend

- **Discovery** (NIFTY and BANKNIFTY weeklies) is on `spent` data (NIFTY weeklies by trials 43-52; BANKNIFTY option
  closes `exposed` by EDGE1 and G13b, its weeklies' P&L never computed). Every discovery figure is exploratory.
- **Held-out** (FINNIFTY and MIDCPNIFTY weeklies): no trial has read their prices (`research/DATA_SPEND.md` has no row
  for them; checked 25 Oct 2026 by a search of `research/`). The code refuses to load their rows until the discovery
  results file is committed (section 9). They are read **once**. Limit stated in every report: they trade on the
  same days as NIFTY and BANKNIFTY and are strongly correlated with them, so the held-out read guards against
  instrument noise and overfitting, not against a change of regime.
- **The regime break.** SEBI's rules of 1 Oct 2024 (effective 20 Nov 2024) left one weekly per exchange: BANKNIFTY,
  FINNIFTY and MIDCPNIFTY weeklies ended in November 2024; only NIFTY's weekly is tradeable now (on NSE). A finding on
  the other three transfers to NIFTY's weekly by assumption only [reasoning only]. NIFTY's cycles after 20 Nov 2024
  are reported as their own column, never decided on.

## 3. Data and sources

- NSE's daily F&O files in Drive (UDiFF and legacy libraries, `fno/storage/wiring.py`, read through the stores only:
  never NSE, never a Drive write), read by `fno.fo_bhavcopy.read_fo_file`; EDGE1's day-row reader
  (`research/edge1/edge1study/day_files.py`) generalised to every expiry (not only monthly) in a new module here.
- Index closes: NSE's daily index-close files (NIFTY 50, NIFTY BANK, NIFTY FINANCIAL SERVICES, NIFTY MIDCAP SELECT),
  stores only.
- Settlement: NSE settles index options at the index's closing value on the expiry day; the expiry day's index close
  is used, and cross-checked against the same-day future settlement where a future of that expiry exists.
- Calendar: A7's session calendar; muhurat and special sessions are never entry days.
- Expiries: as each file lists them (weekday moves and holiday moves followed from the files; EDGE1's relabelling of
  moved expiries, `edge1study/expiries.py`, applied the same way).

| Set | Index | Expiries |
|---|---|---|
| Discovery | NIFTY | every expiry from 1 Jan 2019 to 9 Oct 2026 (the end of its `spent` row; later sessions stay fresh) |
| Discovery | BANKNIFTY | every expiry from 1 Jan 2019 to its last weekly (13 Nov 2024) |
| Held-out | FINNIFTY | every expiry from its first listed weekly to its last weekly (Nov 2024) |
| Held-out | MIDCPNIFTY | every expiry from its first listed weekly to its last weekly (Nov 2024) |

## 4. Cycles

For each index and each listed expiry X (weekly or monthly: the nearest expiry each week):
- **Entry:** the close of the first regular session after the previous expiry of the same index. n = regular
  sessions after the entry session up to and including X. A cycle with n < 2 is skipped (`short_cycle`, counted).
- **Exit:** held to X and cash-settled at the expiry day's index close, with C1's settlement charges. No stop, no
  target (fewer variants; EDGE1's TP50 and SL2 added nothing out of sample).

## 5. The gate (point in time)

- Forward F = K0 + C(K0) - P(K0) at the strike K0 nearest the entry day's index close with both legs traded; ATM
  strike K = the listed strike nearest F (ties down).
- Implied volatility of the cycle: sigma_IV = (C(K) + P(K)) / (0.7979 x F x sqrt(n / 252)) (the ATM straddle
  approximation).
- Forecast realised volatility: sigma_RV = sqrt(252 x v), v the EWMA (lambda 0.94) of squared daily log returns of
  the index close, through the session **before** the entry session, seeded with the variance of its first 20
  returns from 1 Jan 2018.
- A cycle without these inputs (no traded call and put pair, the ATM straddle untraded, or too few closes) is
  skipped by every variant (`no_gate_input`, counted), so all six variants share one cycle set.
- Ratio r = sigma_IV / sigma_RV. Gates: G0 none (always trade), G12 r >= 1.2, G15 r >= 1.5. Fixed now, before any
  ratio is seen: 1.2 is about the typical India VIX to realised ratio, 1.5 "rich" [reasoning only].
- Limit stated: the gate uses entry-day option closes (NSE's last-half-hour weighted price), which a decision at 15:15
  sees only approximately; the same prices are the fill.

## 6. Structures (defined risk only)

| Code | Shorts | Wings |
|---|---|---|
| WF | call and put at K | one width W either side |
| WC | call nearest F x (1 + m) (ties up), put nearest F x (1 - m) (ties down), m = sigma_IV x sqrt(n / 252) | one width W beyond each short |

- **Width W:** the largest in the index's list with (W - credit) x lot <= Rs 10,000, credit per unit after pads.
  Lists, fixed now: NIFTY and FINNIFTY 300, 250, 200, 150, 100; BANKNIFTY 900, 750, 600, 450, 300 (EDGE1's);
  MIDCPNIFTY 150, 125, 100, 75, 50 (index about half NIFTY's, strikes 25 apart) [reasoning only]. A wing not listed
  tries the next width; none fits: `no_trade_cap`, counted.
- **Variants (6 trials):** {WF, WC} x {G0, G12, G15}.

## 7. Fills, pads, lots and costs

- **Entry:** every leg traded (volume > 0) on the entry day, priced at its close; else `untraded_leg_at_entry`.
  EDGE1's impossible-price rule (`edge1study/verticals.py`: each vertical in [0, width], the position in its bounds)
  at entry (`impossible_prices_at_entry`, next width tried). Exit at settlement: no exit price, no exit pad.
- **Pads:** Rs 1 a unit a leg at entry (decided); Rs 2 (reported, condition 2 of section 8).
- **Lots:** the contract's market lot on the entry day: UDiFF `NewBrdLotQty` from 2024; before, EDGE1's schedule for
  NIFTY and BANKNIFTY (`edge1study/lots.py`), and for FINNIFTY and MIDCPNIFTY a schedule from NSE's circulars written
  in the build (`research/edge2/LOT_CHECK.md`), checked against R2's derived lot, committed before the held-out read.
  Today's lot is a reported column, never decided on.
- **Charges:** C1's `fno.costs` at `config.yaml`'s rates for every order and the settlement (today's 0.15% STT on
  every date: conservative, decided); a historical-STT run (EDGE1's dated rates) reported beside it.
- No margin figure (return on margin is not a condition here; EDGE1's calculator is reused only if it runs unchanged).

## 8. Discovery: statistics and nomination

Per variant, on the discovery trades of both indices pooled (one trade per index per cycle, one lot):
- **Mean net per trade** (Rs, after charges and the Rs 1 pad). Standard error clustered by expiry week (both indices'
  trades of a week form one cluster); one-sided p of mean > 0 = 1 - Phi(mean / SE), the normal approximation of the clustered t (the
  clusters number in the hundreds; with fewer than 30 clusters the variant is reported only, p = 1).
- **Holm** across the 6 variants at 0.05 (one family, F1's question). Also each variant's G1 bound (mean - 1.2816 x SE,
  the lower one-sided 90% bound of mean net).
- **Gate value** for G12 and G15: the gated mean against 2,000 random gates (RC1) that keep the same number of
  the same structure's always-trade cycles (seed 20261025); p_gate = share of random means >= the gated mean.
- **Nomination to the held-out read** (all four needed; at most 2 variants, lowest Holm-adjusted p first):
  1. Holm-significant at 0.05;
  2. mean net > 0 at the Rs 2 pad;
  3. mean net > 0 on each index alone;
  4. for a gated variant, p_gate <= 0.10 (otherwise its G0 twin stands for it).
- Controls reported beside every variant: N0 (no trade, 0), G0 (always trade), RC1 (above).
- Reported per variant: cycles, taken and each skip reason, mean gross, charges, net (pad 1, pad 2, historical STT),
  win share, worst trade, max drawdown, worst 4 consecutive weeks, by year and by index, share of cycles gated, the r
  distribution, NIFTY after 20 Nov 2024 alone, and G3's sample plan for a forward test on NIFTY's weekly at 50
  trades a year, n = (1.645 x sd / mean)^2.

## 9. Held-out read (once)

- Only after `research/edge2/f1/discovery.json` and its report are committed on the branch; the code checks that the
  file is committed and unchanged (git) before it loads any FINNIFTY or MIDCPNIFTY row.
- Only the nominated variants (none nominated: the held-out set is not read, and F1 ends "nothing nominated").
- Same code, same rules, FINNIFTY and MIDCPNIFTY pooled, clustered by expiry week. **Pass:** Holm across the
  nominated variants at 0.05 one-sided, and mean net > 0 at the Rs 2 pad.
- A pass is a **proposal** to the owner: a forward test of the variant on NIFTY's weekly in the school (a
  registered driver card, a later story), never a book change. A fail is final for that version.

## 10. Registration and counting

- Ledger trials 101-106 (`research/ledger.csv`), one per variant, registered with their idea cards
  (`research/ideas/EDGE2-F1-*.md`) and the DATA_SPEND rows (`registered`) in one commit before the code runs; the
  protocol commit is filled in when this text is frozen. Question `edge2-f1-weekly-vrp-gate`, alpha 0.05.
- The EDGE2 program reports a cumulative Holm across every family it runs (F1-F7), beside each family's own.
- Any change after a number is seen is a new variant with its own trial, or a stated deviation (section 11).

## 11. Deviations

None yet.
