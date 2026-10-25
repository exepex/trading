# EDGE2 F8 discovery: the 2-leg NIFTY weekly credit spreads alone (2019-2024)

Protocol `research/edge2/F8_PROTOCOL.md`, frozen in `F8_FREEZE.md` (commit `1f69681c`, code SHA-256 `f4fd512c`). One
discovery run at `d38baa12` (`f8/discovery.json`). **No participant-OI file was read**: this step measures the
spreads alone, both sides on every cycle, as the protocol requires. Exploratory (NIFTY weekly option prices spent).
Rupees per trade for 1 lot of the time, C1's charges at today's STT, Rs 1 entry pad a leg, held to settlement.

## Answer

**Unfiltered, every spread loses after costs on both sides.** By the pre-registered futility rule (side-average net
below -Rs 300), P0W10 is dropped; P0W5 and P5W5 go to the held-out read of the side filter (2025-26), which waits for
a lane-1 judge. [strong evidence for the unfiltered spreads on 305 cycles; says nothing yet about the filter]

| Variant | Side | Taken | Mean gross | Charges | Pads | Mean net | SE | Win share | Worst trade |
|---|---|---|---|---|---|---|---|---|---|
| P0W5 (121) | put | 282 | -18 | 89 | 113 | -220 | 130 | 56% | -5,376 |
| P0W5 (121) | call | 282 | -136 | 95 | 113 | -344 | 137 | 49% | -4,695 |
| P5W5 (122) | put | 284 | 123 | 78 | 112 | -67 | 125 | 67% | -4,550 |
| P5W5 (122) | call | 294 | -172 | 85 | 114 | -370 | 126 | 56% | -4,958 |
| P0W10 (123) | put | 297 | 36 | 84 | 114 | -162 | 229 | 60% | -8,467 |
| P0W10 (123) | call | 302 | -409 | 91 | 114 | -613 | 238 | 52% | -8,287 |

Side averages (the random-side baseline): P0W5 -Rs 282 (Rs 2 pad -395; entered at closes -269), P5W5 -Rs 219 (-332;
-274), P0W10 -Rs 388 (-505; -368, **futile**). Skips: 7-22 entries a variant at impossible opening prices (opening
trades of two legs at different moments), 1 at the cap.

## What it means for the held-out read [reasoning only]

- The puts did better than the calls in every variant (2019-2024 was a rising market): the drift, not a skill.
- To pass, the filtered spread's mean gross must clear Rs 260. The kept variants' side-average gross is about -Rs 77
  (P0W5) and -Rs 25 (P5W5), so the FII side filter would have to add about Rs 285-340 of gross a trade. F6's lean, carried
  through a spread's delta, was estimated at about Rs 100. **My prior that the held-out read passes is low.**
- The held-out read spends participant OI 2025-26, the last fresh predictor history; the orchestrator decides
  whether that is worth it or the held-out stays unread (protocol: the read happens only after a judge).

## Limits

- Opening prices are each contract's first trade; two legs' first trades are seconds to minutes apart (the
  impossible-price rule caught 7-22 a variant).
- Daily data: no intraday stop; held to settlement.
