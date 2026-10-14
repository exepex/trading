# Response 88: story S2, scoreboard B: design proposal before building

Builder: Claude, 14 Oct 2026, for the orchestrator and the judge. This is not the claims file; S2's claims follow as
addenda here once it is built. I wrote it first because several of S2's sources do not exist yet, and the way around
each one is a design choice the judge should see before it is code.

## 1. What S2 reads, and what exists today

| Source the story names | State on main today | What S2 does |
|---|---|---|
| E1 accounts (`cash_ledger.csv`) | built | the money: every fill, every charge |
| E1 `equity_history.csv` | **never written after the opening row**: no code calls `record_equity` | not used. Each day's value is rebuilt from the stored snapshots instead (2 below). The equity history may be checked against that later. |
| E4 desk records (`desk_fills.csv`, `desk_events.csv`) | built | which trade is which version (`strategy`), its decision ID, and how each attempt ended |
| C1 three ledgers | built (`Ledgers`) | trade lines (gross, pads, charges, net), by month, tax scenario; S2 criterion 2 reconciles to them |
| C1 operating costs per book | **no file exists for any book** | read `journal/<book>/operating_costs.csv` in C1's own columns (`month,item,category,amount_rs,source`) through a port. A missing file means none recorded, and the report says "no operating costs recorded", not zero spend. |
| F8 allocated AI cost | **not built** | a port, `AllocatedAiCost`. Until F8, the report shows "not available: F8 not built" and never a number. Book 1 has no AI, so its figure is a true Rs 0. |
| D6 versions and segments | built (`segments`, `journal/versions.csv`) | each trade belongs to the segment of the decision that opened it |
| D3 decision records | built | the maximum loss at entry, the stressed margin and the stress loss of each opened trade (its chosen record's `risk` and `validity`), and `owner_override` |
| F4 overridden trades | **not built**; D3's header already has `owner_override` (always empty today) | a trade whose opening record has a non-empty `owner_override` is "overridden", scored apart. This is ready for F4 and is a no-op until then. |
| S1 protocol | passed (judge 85 add. 1), **not merged; a draft, not frozen** | S2 applies its rules (common start, pilot, ratio of means, block bootstrap). Every output says which protocol version and whether it is frozen. Until the freeze, every figure is labelled "protocol not frozen: provisional". |
| E3 run log (`journal/runs/<day>.json`) | built | the day's execution snapshot ID, to mark open trades on that day |

## 2. The daily series (the heart of S2)

Net per unit of risk (protocol `primary_metric`) is the period's mean daily net change divided by its mean daily risk
at stake. Both means run over the same days, so this equals **total net change / risk-days**. The bootstrap
(`uncertainty_criterion`) needs the daily pairs themselves.

Each trade is valued on each session day it is open. The value is its cash flow so far plus its legs at the mid of
that day's execution snapshot, the same marks E6 uses. That gives:
- **Daily net change** of a book or a segment: the sum of its trades' value changes that day, minus operating costs
  dated that day. C1 dates operating costs by month only, so they are booked on the month's last session (rule 3).
- **Daily risk at stake:** the sum of the maximum loss at entry (from D3) of every trade open that day.
- **A leg with no valid mid:** the last valid mark is used and flagged stale, as E1 does. A trade with no valid mark
  ever is shown as unvalued, and those days are listed. No price is invented.

All of this is rebuilt from committed records, so a rebuild gives the same bytes (criterion 4).

## 3. Rules I propose (reasoning only; the judge or owner may change them)

1. **The segment of a trade** is the D6 segment of the D3 decision that opened it. Its later value changes stay in
   that segment even after a new version is registered. A version is credited with its own trades to their end.
2. **Common start:** the S1 rule, read from the records: the first session on which every book has an on-time
   committed decision under a registered version. Books 2 and 3 are not built, so today **everything is pilot**. The
   output says "common start: not reached" and puts all of Book 1's figures in the pilot section.
3. **Operating costs** are booked on the last session of their month, so the daily series and C1's month table
   agree.
4. **Margin-days:** the stressed margin at entry (from D3's `margin_room` numbers) times the session days held. It
   is not re-margined daily: the daily stressed margin is not recorded anywhere. Labelled "at entry margin".
5. **Stress usage:** the stress loss at entry (D3's `stress_loss` numbers) as a share of the owner's stress limit.
   Reported, never the verdict.
6. **Uncertainty** is computed only where the protocol allows a claim. Its figures (block 20, 10,000 resamples,
   seed 20261014, nearest-rank 5th percentile) are named constants in the scoring module. A test checks that each
   one appears in the protocol's `uncertainty_criterion` text. The S1 freeze then hashes the module.
7. **Output:** `research/scoreboards/B/<date>.json`, canonical JSON (sorted keys, fixed rounding to the paisa),
   with:
   - per book: overall, head-to-head, pilot, unscored and overridden sections, each with the full detail list of
     design 12.5;
   - per segment;
   - the inputs it read, with their SHA-256 (so the judge can rebuild it).

## 4. Questions for the orchestrator (I proceed on the proposals above unless told otherwise)

1. Is reading D3's `owner_override` as the F4 hook acceptable, rather than waiting for F4's format?
2. Rule 2: should Book 1 also get a "since its own first decision" view, clearly labelled pilot, so the owner sees
   something before books 2 and 3 exist? I propose yes, since the pilot section is exactly that.
3. Should S2 also start writing `equity_history.csv` daily (an E3 change), or leave that file to a separate story?
   I propose a separate story: S2 should read records, not change the desk.
