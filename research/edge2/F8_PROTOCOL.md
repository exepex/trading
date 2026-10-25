# Protocol: EDGE2 F8, the FII-change lean as the side of a 2-leg NIFTY weekly credit spread

Story: EDGE2 edge search (owner, 25 Oct 2026: "no proven edge: let's try to find them using dry runs"); orchestrator's
conditions of 25 Oct 2026 (block `edge2-f8`, trials 121-126 reserved; this family uses 121-123). Builder:
session_01VhppcYHXq3yTJBV2UnsWSs. Written and committed **before any option price of this study is read**.
EXPLORATORY: it can nominate for the school's forward test, never prove.

## 1. The question and where the idea came from

Does choosing the side of a defined-risk NIFTY weekly credit spread by the sign of the FII net index-futures change
(sell a put spread after a rise, a call spread after a fall) make money after every cost, and more than random sides?

**The idea is post-hoc.** F6 (`research/edge2/F6_RESULTS.md`) found, on 2019-2024, that the FII change leans the
right way for the next session (+Rs 379 a futures lot gross against +Rs 72 always long; p_sign 0.024, not its
registered test). Re-testing that lean on 2019-2024 would be circular, so **the filter is tested only on the held-out
years 2025-26**; 2019-2024 measures the spread alone (section 6). [some evidence that the lean exists; reasoning only
that a spread can carry it: a 2-leg spread pays its costs from premium, and the lean only chooses the side]

## 2. Status and data spend

- NIFTY weekly option prices are `spent` to 9 Oct 2026 (trials 43-52, EDGE2 F1). F1 read entry closes and the
  settlement; F8 reads the entry session's **opening** prices of the same contracts. Every figure is exploratory.
- Participant OI 2019-2024 is `exposed` (F6's predictor); **2025-2026 is `fresh`** and is read once, in the held-out
  step only. Discovery reads no participant-OI file.
- The held-out read's option prices (2025-26) were read by F1 without any OI condition: the pairing is new, the prices
  are not. Stated in every report. The fresh weeks after 9 Oct 2026 are left for the forward test.

## 3. Cycles and entry

- F1's weekly cycles for NIFTY (`f1study/cycles.py`): the entry session is the first regular session after the
  previous expiry; held to the next expiry and cash-settled at the expiry day's index close (C1's settlement charges).
- **Entry at the entry session's open:** each leg at its `OpnPric` (its first trade), only if the leg traded that day
  (volume > 0, open > 0); else `untraded_leg_at_entry`. The vertical must be worth between 0 and its width at the
  opening prices (EDGE1's rule); else `impossible_prices_at_entry`.
- **Forward at the open:** F = K0 + C_open(K0) - P_open(K0) at the strike K0 nearest the previous session's index close
  with both legs traded at the open.
- Sensitivity, never decided on: the same trades entered at the entry session's closes.

## 4. The side (held-out only)

- Day t = the session before the entry session (the previous expiry day). Its participant OI file is published after
  t's close, so it is known before the entry session's open.
- d_t = FII net index-futures contracts on t minus on the session before t. d_t > 0: **put spread** (bullish);
  d_t < 0: **call spread** (bearish); d_t = 0 or a missing file: no trade (`no_signal`, counted).

## 5. Structures (3 trials; fixed distance and width as fractions of F)

| Code (trial) | Short leg | Long leg |
|---|---|---|
| P0W5 (121) | the strike nearest F (ATM) | 0.5% of F further out of the money, nearest strike |
| P5W5 (122) | the strike nearest F x (1 - 0.005) for a put spread, F x (1 + 0.005) for a call spread | 0.5% of F beyond the short |
| P0W10 (123) | ATM | 1.0% of F further out |

- A put spread sells the short put and buys the long put below it; a call spread sells the short call and buys the
  long call above it. Width W = the strike distance actually used.
- **Cap:** (W - credit) x lot <= Rs 10,000 with the entry pads; else `no_trade_cap`, counted. One lot of the
  contract's market lot on the entry session (UDiFF's lot from 2024; EDGE1's schedule before).

## 6. Costs and the gross bar (stated before the run)

- C1's charges (`fno.costs`, `config.yaml` at today's 0.15% STT for every date) on both entry orders and the
  settlement; pad Rs 1 a unit a leg at entry (decided), Rs 2 reported; no exit pad (settlement).
- **2-leg cost, per lot, at today's lot of 65** [arithmetic, `fno.costs`]: entry charges about Rs 64 (sell a 120 put,
  buy a 70 put), settlement charges Rs 0 to about Rs 64 (both legs in the money by 300), pads Rs 130: **about Rs 195
  to 260 a trade. The gross bar is Rs 260 a lot a trade**: a variant whose filtered mean gross is below it cannot pay.

## 7. Discovery (2019-2024): the spread alone

For each variant, every NIFTY weekly cycle with an expiry from 1 Jan 2019 to 31 Dec 2024, **both sides** (put spread
and call spread) priced on the same cycle. Reported: taken and skips, mean gross, charges, pads, net per side and for
the side average (the random-side baseline), win share, worst trade, by year.

**Futility rule (decided now):** a variant whose side-average mean net is below **-Rs 300** a trade is dropped and
not read in the held-out step, since the filter would need more than about three times F6's lean carried through a
spread's delta (about Rs 100 a lot a trade, reasoning only) to rescue it. The other variants go to the held-out read
(at most 3); none is chosen by a filtered result.

## 8. Held-out read (once, after a lane-1 judge)

- Cycles with an expiry from 1 Jan 2025 to 6 Oct 2026 (F1's last NIFTY expiry), the side from section 4.
- **Metric:** mean net per trade after the full cost model. **Comparison:** RC1, 2,000 random side series (seed
  20261025) with the same number of call spreads on the same cycles; p_side = share of random means >= the filtered
  mean.
- **Pass (each variant):** one-sided p of mean net > 0 (normal approximation, plain SE: one trade a week, no overlap)
  and p_side both below their Holm thresholds at 0.05 across the variants read; mean net > 0 at the Rs 2 pad; filtered
  mean gross above the Rs 260 bar.
- **Power, stated now:** about 90 cycles with a per-trade SD of several thousand rupees give an SE near Rs 400
  [reasoning only], so only a large edge can pass; a fail is weak evidence of no edge. A pass is a proposal to the
  owner for a forward test in the school on NIFTY's weekly (a registered driver card, a later story).

## 9. Registration

Ledger trials 121-123 (block `edge2-f8`), idea cards `research/ideas/EDGE2-F8-*.md`, question
`edge2-f8-fii-side-weekly-spread` (alpha 0.05), DATA_SPEND rows, all in one commit before the code reads any price.
Trials 124-126 stay unused (reserved, released to the registry when F8 ends).

## 10. Deviations

None yet.
