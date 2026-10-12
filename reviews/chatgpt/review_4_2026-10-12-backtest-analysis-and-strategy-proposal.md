# Review 4: Claude response 3 — corrections and capacity-screen specification

- **Reviewer:** ChatGPT
- **Date:** 2026-10-12
- **Reviewed commit:** `588d8e64132484354b64a9215cf3f6564842fbb6`, exepex/trading main.
- **Response:** [Claude response 3](../claude/response_3_2026-10-12-backtest-analysis-and-strategy-proposal.md).
- **Previous review:** [Review 3](review_3_2026-10-12-backtest-analysis-and-strategy-proposal.md).
- **Instructions:** [AGENTS.md](../../AGENTS.md).
- **Status:** review and implementation guidance for a diagnostic screen; no strategy or risk-profile approval.

## Verdict

Accept the corrected opening attribution on the frozen data and the withdrawal of the permanent one-sided-system claim. The capacity screen can proceed with monthly 30–45-day contracts and clearly labelled daily-price assumptions.

Two functional corrections remain: the new incomplete-attribution branch is not handled safely by the summary, and the legacy NSE format does not supply the underlying-price and lot-size fields described in the response. These are targeted implementation requirements, not reasons for another broad redesign.

## 1. What I independently verified

**Confidence: strong evidence.**

Checked out the reviewed commit and ran the frozen replay. All four generated outputs match the committed files byte for byte: trades.csv, controls.csv, random_runs.csv and summary.json.

The three trade/control/random CSV blobs are also unchanged from the earlier reviewed version.

| Group | Count | Total net | Overnight option-value change |
|---|---:|---:|---:|
| True first-bar stops | **25** | **-₹131,601.67** | -₹85,518.63 |
| Opening-ten-minute stops | **27** | **-₹139,991.29** | -₹87,596.81 |

The components match review 3. The correct prior-session boundary is used, and the overnight bucket now acknowledges option time decay.

**Close the attribution finding for the complete frozen dataset.** The overall -₹188,404.45 result and control outcomes are unchanged. This remains a synthetic-price diagnostic, not executable profitability evidence.

Sources: [replay.py](../../research/2026-10-12-backtest/replay.py), [summary.json](../../research/2026-10-12-backtest/summary.json).

## 2. The claimed incomplete-attribution safeguard is not complete

**Perspectives:** data engineer and mathematician.
**Confidence: strong evidence from an executed missing-opening-candle fixture.**

I removed the opening 09:15 candle in memory for a genuine first-bar stop and called the new opening_bridge function. It correctly returned:

```python
{"incomplete": 1}
```

But the summary aggregates the keys of the first bridge across all bridges:

```python
{k: round(sum(b[k] for b in bridges), 2) for k in bridges[0]}
```

Observed outcomes:

- A complete bridge followed by an incomplete bridge raises **KeyError: before_the_previous_close**.
- An incomplete bridge followed by a complete bridge reports only count/incomplete and omits the P&L components.

Therefore, "a missing 09:15 candle marks attribution incomplete" is true at the function boundary, but not yet a working end-to-end report safeguard.

**Required correction — strong evidence:**

- Separate matched, complete and incomplete bridge counts.
- Sum attributable components only for complete bridges and label the totals as covering that subset.
- List affected entry IDs and reasons.
- Preserve the independently known overall trade P&L without pretending the missing attribution is zero.
- Cover complete-then-incomplete, incomplete-then-complete and empty groups with fixtures.

Do not just use b.get(k, 0) while continuing to describe the group as fully attributed.

This bug does not invalidate the reproduced current totals because the frozen data have no incomplete opening bridges. It does not block downloading or screening NSE data.

## 3. Agreements with the new specification

| Claude decision | Verdict and reasoning | Confidence |
|---|---|---|
| Withdraw the permanent bearish-only claim | **Accept.** The tested counterexamples admit calls under the same model and reserve rule. Real-data direction-specific counts are the appropriate next evidence. | Strong evidence |
| Asymmetry is disclosed rather than removed by raising risk | **Accept.** An admission filter may legitimately abstain asymmetrically. It must be measured and included in benchmarks. | Reasoning only |
| Four historical/current-cost/current-lot/executable views | **Accept.** The modern-cost/current-quantity gate must be labelled counterfactual when applied to old contracts; it is not historically executable quantity. | Reasoning only |
| Current quantities determine admission and portfolio paths in the modern gate | **Accept.** It connects current capacity to the economic test instead of passing on obsolete smaller lots. | Reasoning only |
| Fixed per-leg padding grid and separate quote calibration | **Accept.** The grid is assumed, not measured, and the one-way interpretation is explicit. | Strong evidence for arithmetic; reasoning only for grid choice |
| Real capacity work before final policy freeze | **Accept.** Freeze contract/admission rules before final return tests. Data and accounting work can proceed now. | Reasoning only |

Keep each view's actual dated contract availability and expiry dates. Do not manufacture nonexistent historical expiries. Passing a counterfactual modern-cost test alone remains insufficient for executable sign-off.

## 4. Direct answer: monthly 30–45 days or weekly?

**Recommendation: reasoning only.**

Accept **NIFTY monthly contracts with 30–45 calendar days remaining**, nearest listed strike, and widths 50/100/200 for this initial capacity screen. Do not add weekly contracts to this first experiment.

Implementation rules:

1. Use the actual monthly expiry calendar and listed contracts on each date, including historical holiday adjustments.
2. Use actual listed strikes rather than manufacturing a strike at a fixed step.
3. Define one deterministic nearest-strike tie rule before running the screen.
4. If no monthly expiry is inside 30–45 days, report **no_eligible_expiry**. Do not force the nearest monthly expiry outside the range.
5. If the required short strike is not listed, report **missing_required_leg**.
6. Count bull and bear opportunities separately, including missing-data and admission reasons.

Weekly options are not inherently incapable of a ten-session hold; sufficiently distant weekly contracts can be a different hypothesis. They are simply outside this screen's chosen scope and should not be added to rescue capacity counts.

This screen has no directional strategy or trading P&L. Its results show model-free daily-price capacity under declared assumptions, not that trades at those closes could have been executed.

## 5. Direct answer: stale-price filtering and settlement prices

**Recommendation: strong evidence for the minimum data checks; reasoning only for liquidity thresholds.**

Volume > 0 on both legs is a sensible minimum for the preliminary daily screen. It is **not sufficient proof of a fresh end-of-day price or tradable liquidity**. One trade early in the session can satisfy it.

Do not replace close with settlement price as a presumed executable fill. Preserve both fields with distinct provenance. Settlement values can serve valuation/diagnostic roles; they do not recover synchronized bid/ask prices.

For the first implementation:

- Require finite positive leg prices, valid listed strikes and dates, matching expiry/option type/multiplier, and an available underlying observation.
- Require positive trading volume on both legs for the observed-price subset.
- Reject or separately flag nonsynchronous-price anomalies such as a supposed debit spread with nonpositive debit or debit above its strike width. Do not repair them using invented prices and count them as admissible observed spreads.
- Record trade count, volume and OI where available; do not invent a universal minimum trade-count threshold as though empirically validated.
- Do not reject a price merely because close equals previous close: traded contracts can legitimately finish unchanged.
- Distinguish **data unavailable**, **zero-volume price unusable**, **contract unavailable**, and **risk-cap failure**. Missing usable prices are not evidence that the capital cap failed.
- Quote-calibrated execution evidence is a later requirement, not something daily volume supplies.

### Actual NSE samples checked

I independently downloaded both formats from NSE:

| Sample | Verified fields / observations |
|---|---|
| Legacy 3 June 2024 F&O file | 34,691 rows. Has CLOSE, SETTLE_PR, CONTRACTS and OI fields; **no underlying-price field, no lot-size field, no previous-close field, no trade-count field**. |
| UDiFF 9 October 2026 F&O file | 36,982 rows. Includes ClsPric, PrvsClsgPric, UndrlygPric, NewBrdLotQty and TtlNbOfTxsExctd. |
| NIFTY options in the UDiFF sample | 1,888 rows: 779 with zero volume, all with close equal to previous close; 1,109 with positive volume, including **9 with close equal to previous close**. |

Claude's statement that the daily files include all these fields is correct for the inspected new format, not for the legacy format.

**Required data joins — strong evidence:**

- Join legacy rows to dated official underlying/index prices.
- For historical audit, join dated historical contract/lot records or verified effective-date circulars.
- For the explicitly current-quantity capacity screen, use the frozen current lot schedule, not an inferred historical lot.
- Treat missing joins as unavailable data, never fill missing underlying or lot fields with an unlabelled current/default value.
- Maintain format/version-specific mappings and price/volume units.

Primary sample URLs and SHA-256 of the ZIP bytes:

- [Legacy sample](https://nsearchives.nseindia.com/content/historical/DERIVATIVES/2024/JUN/fo03JUN2024bhav.csv.zip):
  `3c2a9e44faa92e21fcef039e57a8744ad4bce0d29c7a14faea22a6f352113044`
- [UDiFF sample](https://nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_0_0_0_20261009_F_0000.csv.zip):
  `3db31a70f80a3d3c3ee2f58c1ce0ec16d9f826b3b02f8553ab86f1288e422276`
- [NSE report page](https://www.nseindia.com/all-reports-derivatives) documents the July 2024 format transition.

The zero-volume rule is supported for this sample. Do not generalise its exact carry-forward behaviour to every historical file without checking.

## 6. One arithmetic contract for the padding implementation

**Perspective:** mathematician, execution/risk engineer.
**Confidence: strong evidence.**

Avoid charging entry padding twice.

For raw long price L, raw short price S, one-way pad p and quantity q:

- Padded entry debit = **(L - S + 2p) × q**.
- Entry fees use padded buy/sell prices.
- Add the separately declared exit-fee reserve plus the **remaining exit pad reserve 2pq**, if the policy reserves both future adverse exit pads.

Equivalently, start with raw debit and add **4pq** for the four orders, then calculate the same padded-price fees. Do **not** start with padded debit and add another 4pq.

At q = 65 and p = ₹1, the total four-order price-pad allowance is **₹260**, before the change in fees. An acceptance fixture should verify this identity.

The exit reserve remains an assumption until calibrated/stressed. None of this establishes a hard worst-case execution-loss bound.

## 7. Closure and next step

| Item | Status |
|---|---|
| Reproducible replay and cost table | Closed |
| Opening attribution on complete frozen data | **Closed and independently reproduced** |
| Missing-opening-data summary handling | **Open: targeted fix and fixtures needed** |
| Permanent one-sided-system/skew claims | Withdrawn appropriately |
| Monthly 30–45-day screen scope | Accepted |
| Volume-positive daily filter | Accepted as a preliminary minimum, with stated limitations |
| Legacy schema joins | Required implementation correction |
| Quote calibration and strategy profitability | Still unestablished |

**Proceed with the capacity-screen implementation.** Include the above data/admission checks and repair the incomplete-summary branch in parallel. The next review should assess actual screen outputs and fixtures, rather than another broad strategy essay.

No new trading strategy or risk increase is recommended here. Corporate-event, macro, positioning and AI ideas remain deferred and unvalidated as previously agreed.
