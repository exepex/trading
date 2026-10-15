# R2 results: stock options around results (feasibility)

**Answer: NO** (stopped at stage 3 (cost wall)). trial 53 of 53. Run commit `f296e25484860650b253a5143e7ad85530bd1617`. Window 2024-10-01 to 2026-10-14.

e = 5% is the **assumed hurdle** (reasoning only, not a conservative bound); e* is the break-even edge. Clusters a year: registered rule 130 (decides); 80%-power need 297 (shown only).

## Stage 0

- Results-date coverage: 1617 of 1626 stock-quarters (99.4%); lot unknown: 0.0% of decision-window events.
- Legacy lot derivation: 3034 of 23333 exact (13.0%); valid: False.
- Events: {"events_2019_on": 5593, "decision_window_events": 1677, "decision_window_analysed": 1664, "decision_window_with_filed_at": 0.987478, "left_out_before_events": {"duplicate meeting": 32858, "filing before entry": 1, "no entry session in the archive": 13, "no reaction session in the archive yet": 2, "not F&O on the entry session": 53588, "reaction session before 1 Jan 2019": 0}, "left_out_all_years": {"corporate action": 8, "lot unknown": 3371, "no expiry at least 5 sessions after R": 14}, "left_out_decision_window": {"corporate action": 4, "no expiry at least 5 sessions after R": 9}, "notes": {}}

## Decision window (1 Oct 2024 on)

| Structure | Events | Fit cap, no pads | Fit + liquid | Fit + liquid, pads | Median EN (Rs) | Mean EN (Rs) | Median e* | Gross/cost | Clusters/yr | By 12-month part | Kish (passing) | First failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 bought call | 1664 | 0.9% | 0.9% | 0.3% | -698 | -683 | 13.9% | 0.36 thin margin | 0.0 | n/a | 0.0 | cap |
| S2 bought put | 1664 | 1.0% | 0.8% | 0.2% | -662 | -636 | 13.9% | 0.36 thin margin | 0.0 | n/a | 0.0 | cap |
| S3 long straddle | 1664 | 0.0% | 0.0% | 0.0% | n/a | n/a | n/a | n/a | 0.0 | n/a | 0.0 | cap |
| S4 long strangle | 1664 | 0.2% | 0.1% | 0.0% | n/a | n/a | n/a | n/a | 0.0 | n/a | 0.0 | cap |
| S5 bull call spread | 1664 | 89.3% | 63.4% | 50.8% | -3,177 | -3,289 | 101.2% | 0.05 thin margin | 0.0 | n/a | 0.0 | cost wall |
| S6 bear put spread | 1664 | 86.4% | 55.2% | 44.3% | -3,077 | -3,174 | 96.4% | 0.05 thin margin | 0.0 | n/a | 0.0 | cost wall |
| S7 short iron condor | 1664 | 79.3% | 49.7% | 48.3% | -2,725 | -2,999 | 49.3% | 0.10 thin margin | 0.0 | n/a | 0.0 | cost wall |

## 2019 - Sep 2024 (descriptive, never decides)

| Structure | Events | Fit cap, no pads | Fit + liquid | Fit + liquid, pads | Median EN (Rs) | Mean EN (Rs) | Median e* | Gross/cost | Clusters/yr | By 12-month part | Kish (passing) | First failed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S1 bought call | 536 | 0.4% | 0.2% | 0.0% | n/a | n/a | n/a | n/a | 0.0 | n/a | 0.0 | none |
| S2 bought put | 536 | 0.2% | 0.0% | 0.0% | n/a | n/a | n/a | n/a | 0.0 | n/a | 0.0 | none |
| S3 long straddle | 536 | 0.0% | 0.0% | 0.0% | n/a | n/a | n/a | n/a | 0.0 | n/a | 0.0 | none |
| S4 long strangle | 536 | 0.2% | 0.0% | 0.0% | n/a | n/a | n/a | n/a | 0.0 | n/a | 0.0 | none |
| S5 bull call spread | 536 | 79.5% | 40.5% | 24.8% | -4,040 | -4,056 | 131.0% | 0.04 thin margin | 0.0 | n/a | 0.0 | none |
| S6 bear put spread | 536 | 71.1% | 28.5% | 17.9% | -3,614 | -3,686 | 116.9% | 0.04 thin margin | 0.0 | n/a | 0.0 | none |
| S7 short iron condor | 536 | 63.6% | 27.2% | 24.6% | -3,790 | -4,031 | 57.9% | 0.09 thin margin | 0.0 | n/a | 0.0 | none |

## Within-week correlation (2019-2021 events only)

- 1870 events in 849 clusters; ICC of m: 0.030 (90% [-0.076673, 0.152056]); ICC of |m|: 0.082 (90% [-0.07697, 0.259338]); Kish effective count 1569.6. Left out: {"derived lot changed from entry to R": 6, "no same-expiry future close or no NIFTY close": 3}.
- Decision-window events analysed: {"clusters": 602, "kish": 1289.696754}

## Descriptive

```json
{
 "lot_value_rs_by_year": {
  "2024": {
   "n": 176,
   "p25": 596567.5,
   "median": 744562.78,
   "p75": 877225.3125
  },
  "2025": {
   "n": 863,
   "p25": 523215.0,
   "median": 618135.75,
   "p75": 736812.5
  },
  "2026": {
   "n": 628,
   "p25": 554413.75,
   "median": 655214.625,
   "p75": 791058.75
  }
 },
 "strike_step_pct_by_year": {
  "2024": {
   "n": 176,
   "p25": 1.040962,
   "median": 1.274154,
   "p75": 1.590002
  },
  "2025": {
   "n": 863,
   "p25": 1.032034,
   "median": 1.339585,
   "p75": 1.677177
  },
  "2026": {
   "n": 628,
   "p25": 0.85677,
   "median": 1.096223,
   "p75": 1.406643
  }
 },
 "pushed_share_by_year": {
  "2024": 0.318182,
  "2025": 0.214368,
  "2026": 0.264331
 },
 "unknown_sector_events": 13,
 "unknown_sector_label": "unknown",
 "all_years": {
  "lot_value_rs_by_year": {
   "2024": {
    "n": 716,
    "p25": 644215.625,
    "median": 768225.0,
    "p75": 929304.375
   },
   "2025": {
    "n": 863,
    "p25": 523215.0,
    "median": 618135.75,
    "p75": 736812.5
   },
   "2026": {
    "n": 628,
    "p25": 554413.75,
    "median": 655214.625,
    "p75": 791058.75
   }
  },
  "strike_step_pct_by_year": {
   "2024": {
    "n": 716,
    "p25": 0.829005,
    "median": 1.099584,
    "p75": 1.407957
   },
   "2025": {
    "n": 863,
    "p25": 1.032034,
    "median": 1.339585,
    "p75": 1.677177
   },
   "2026": {
    "n": 628,
    "p25": 0.85677,
    "median": 1.096223,
    "p75": 1.406643
   }
  },
  "pushed_share_by_year": {
   "2024": 0.251397,
   "2025": 0.214368,
   "2026": 0.264331
  },
  "unknown_sector_events": 32,
  "unknown_sector_label": "unknown"
 },
 "eligible_stocks_by_year": {
  "2019": {
   "median_daily": 162,
   "distinct": 200
  },
  "2020": {
   "median_daily": 140.0,
   "distinct": 150
  },
  "2021": {
   "median_daily": 160,
   "distinct": 197
  },
  "2022": {
   "median_daily": 196.0,
   "distinct": 199
  },
  "2023": {
   "median_daily": 186.0,
   "distinct": 191
  },
  "2024": {
   "median_daily": 182,
   "distinct": 228
  },
  "2025": {
   "median_daily": 216,
   "distinct": 256
  },
  "2026": {
   "median_daily": 209.0,
   "distinct": 224
  }
 }
}
```

## Spread buckets (one Groww snapshot; depth descriptive only)

```json
{
 "tercile_bounds": [
  0.0,
  10.666666666666629
 ],
 "buckets": [
  {
   "moneyness": "K0",
   "terciles": [
    0
   ],
   "legs": 64,
   "two_sided": 62,
   "half_spread_p75": 0.193307,
   "untradable": false,
   "depth": {
    "bid_lots_median": 1.0,
    "bid_lots_p25": 1.0,
    "ask_lots_median": 1.0,
    "ask_lots_p25": 1.0,
    "share_one_lot_both_sides": 0.96875
   }
  },
  {
   "moneyness": "K0",
   "terciles": [
    1,
    2
   ],
   "legs": 80,
   "two_sided": 80,
   "half_spread_p75": 0.065104,
   "untradable": false,
   "depth": {
    "bid_lots_median": 1.5,
    "bid_lots_p25": 1.0,
    "ask_lots_median": 1.0,
    "ask_lots_p25": 1.0,
    "share_one_lot_both_sides": 1.0
   }
  },
  {
   "moneyness": "1 step",
   "terciles": [
    0
   ],
   "legs": 139,
   "two_sided": 131,
   "half_spread_p75": 0.191776,
   "untradable": false,
   "depth": {
    "bid_lots_median": 1.0,
    "bid_lots_p25": 1.0,
    "ask_lots_median": 1.0,
    "ask_lots_p25": 1.0,
    "share_one_lot_both_sides": 0.942446
   }
  },
  {
   "moneyness": "1 step",
   "terciles": [
    1
   ],
   "legs": 34,
   "two_sided": 34,
   "half_spread_p75": 0.169421,
   "untradable": false,
   "depth": {
    "bid_lots_median": 1.0,
    "bid_lots_p25": 1.0,
    "ask_lots_median": 2.0,
    "ask_lots_p25": 1.0,
    "share_one_lot_both_sides": 1.0
   }
  },
  {
   "moneyness": "1 step",
   "terciles": [
    2
   ],
   "legs": 113,
   "two_sided": 113,
   "half_spread_p75": 0.022735,
   "untradable": false,
   "depth": {
    "bid_lots_median": 1.0,
    "bid_lots_p25": 1.0,
    "ask_lots_median": 2.0,
    "ask_lots_p25": 1.0,
    "share_one_lot_both_sides": 1.0
   }
  },
  {
   "moneyness": "2-3 steps",
   "terciles": [
    0
   ],
   "legs": 319,
   "two_sided": 303,
   "half_spread_p75": 0.202929,
   "untradable": false,
   "depth": {
    "bid_lots_median": 1.0,
    "bid_lots_p25": 1.0,
    "ask_lots_median": 1.0,
    "ask_lots_p25": 1.0,
    "share_one_lot_both_sides": 0.949843
   }
  },
  {
   "moneyness": "2-3 steps",
   "terciles": [
    1
   ],
   "legs": 82,
   "two_sided": 82,
   "half_spread_p75": 0.16122,
   "untradable": false,
   "depth": {
    "bid_lots_median": 1.0,
    "bid_lots_p25": 1.0,
    "ask_lots_median": 1.0,
    "ask_lots_p25": 1.0,
    "share_one_lot_both_sides": 1.0
   }
  },
  {
   "moneyness": "2-3 steps",
   "terciles": [
    2
   ],
   "legs": 170,
   "two_sided": 170,
   "half_spread_p75": 0.023972,
   "untradable": false,
   "depth": {
    "bid_lots_median": 2.0,
    "bid_lots_p25": 1.0,
    "ask_lots_median": 2.0,
    "ask_lots_p25": 1.0,
    "share_one_lot_both_sides": 1.0
   }
  }
 ]
}
```
