# R2: stock options around company results, feasibility study (registered protocol, 15 Oct 2026)

Story R2 (`docs/design_v2/REPLAN_new_stories.md`; REPLAN slice A item 5). Research only: no `fno/` code, no orders,
nothing in the playbook. Ledger trial 53 (`research/ledger.csv`). Factory rules: `research/FACTORY_RULES.md`.

**This file is written before any outcome of this study has been computed or looked at.** Nothing listed in section 3
has been read for this study: no volume, open interest, lot value, strike step, price or spread of any stock option.
It is frozen by the commit that adds it; the ledger row and `FREEZE.md` name that commit. Any change afterwards is a
new, separately registered trial, never an edit of this one (the one allowed exception is in section 9, stage 0).

Labels: **strong evidence**, **some evidence**, **reasoning only**.

## 1. The question

Can any defined-risk stock-option structure, 1 lot, fit the Rs 10,000 maximum-loss cap with a **positive expected net
on a conservative bound**, and how many **effective independent clusters** (sector x results week) of such trades are
there a year? Answer: **YES or NO, with numbers** (or "cannot answer", only for the data gaps of section 9).

A YES means only "a P&L study of stock options around results is worth registering" (it would be a new idea, a new
row and a new protocol, story A18 first). A YES says nothing about profit. A NO stops the branch (A18 is not built).

## 2. What this study does not do

- No P&L on outcomes: no exit prices are compared with entry prices, no implied-vs-realised move comparison, no hit
  rate. Exit-session data is read only for liquidity (contracts traded).
- The only outcome-like quantity read is the market-adjusted event move of **2019-2021 events**, for its within-week
  correlation (section 7). 2022-2026 event moves are not read.
- No tuning: every threshold below is fixed here. Results are reported once.

## 3. Data

| Input | Source | Use |
|---|---|---|
| Stock option and stock future daily rows | NSE F&O bhavcopy in Drive (`fno-research/raw`; manifests `research/data/manifests/fo-bhavcopy-legacy.csv` 2019 - Jul 2024, `fo-bhavcopy.csv` from 2024) | Point-in-time F&O list, strikes, closes at entry, contracts traded, open interest, lot sizes |
| Results dates | A12 archive in Drive: NSE board meetings (purpose: financial results) and results filings with `filed_at` | Event dates and filing times |
| Sector | NSE Nifty 500 list (`ind_nifty500list.csv`, snapshot of 12 Oct 2026), column `Industry` | Clusters |
| Corporate actions | A12 / NSE corporate-actions files | Exclude events with a split, bonus or other lot or strike adjustment between entry and exit |
| Bid/ask | **One Groww snapshot** (section 6.2), read-only | Half-spread pads |
| Charges | C1: `fno.costs.order_charges` with `config.yaml` charges of the run date | Costs |

- **Period:** events whose reaction session (section 4) is from 1 Jan 2019 to the last session in the archive when
  the study runs. **Decision window:** reaction sessions from **1 Oct 2024** to that last session (today's lot sizes,
  contract sizes and charges apply only to recent events); 2019 - Sep 2024 is reported descriptively and never decides.
- **Universe (point-in-time):** a stock is eligible for an event if, on the entry session, the bhavcopy lists both
  stock futures (FUTSTK) and stock options (OPTSTK) on it. No today's F&O list is used (no survivorship).
- **Underlying price:** the near-month stock future's close (one rule for all years; the legacy format has no
  underlying column). Basis to spot is ignored (reasoning only: under 1% for a near-month future).
- **Lot size:** the current format's lot-size column (`NewBrdLotQty`). Legacy rows: derived as
  round(VAL_INLAKH x 100,000 / (CONTRACTS x SETTLE_PR)) on the near-month future, accepted only if the same value comes
  out on at least 3 of the 5 sessions ending at the entry session; otherwise the event is "lot unknown". The derivation
  is validated on the overlap of the two formats (Jan - Jul 2024): it must match the column exactly on at least 98% of
  stock-sessions, otherwise every legacy-only event is "lot unknown".
- **Open interest** in contracts: legacy OPEN_INT (in shares) divided by the lot size.

## 4. Events and timing

- **Event:** one results board meeting of an eligible stock. Results date D = the board-meeting date.
- **Reaction session R:** the session containing the filing time if the results were filed between 09:15 and 15:30
  IST; the next session if filed after 15:30 or before 09:15 (then the first session after the filing). With no
  `filed_at`, R = the first session after D (conservative: assumes an after-hours filing).
- **Entry session:** the last session before D (the board-meeting date is announced in advance under SEBI's listing
  rules, so the decision is knowable). Events filed before the entry session's close are excluded and counted.
- **Exit session:** R (close). Only its contracts traded are read.
- **Expiry:** the nearest monthly stock-option expiry that is at least 5 sessions after R, so that no position is held
  into the expiry week (physical settlement of stock options; NSE raises margins on in-the-money stock options before
  expiry). Events where this pushes to the second month are counted and reported.
- **Excluded and counted, never silently dropped:** lot unknown; corporate action between entry and R; no results
  date; filing before entry; no listed ATM strike.

## 5. Structures (1 lot; defined risk; never a naked short leg)

K0 = the listed strike nearest the entry close (ties to the higher); step = the gap from K0 to the next listed strike
above it (and below it for put legs). "Listed" = present in the entry session's bhavcopy for the chosen expiry.

| Id | Structure | Legs (bought +, sold -) | Price P | Maximum loss |
|---|---|---|---|---|
| S1 | Bought call | +C(K0) | debit | P x lot + costs |
| S2 | Bought put | +P(K0) | debit | P x lot + costs |
| S3 | Long straddle | +C(K0), +P(K0) | debit | P x lot + costs |
| S4 | Long strangle | +C(K0 + 1 step), +P(K0 - 1 step) | debit | P x lot + costs |
| S5 | Bull call spread | +C(K0), -C(K0 + 1 step) | debit | P x lot + costs |
| S6 | Bear put spread | +P(K0), -P(K0 - 1 step) | debit | P x lot + costs |
| S7 | Short iron condor | -C(K0 + 1 step), +C(K0 + 2 steps), -P(K0 - 1 step), +P(K0 - 2 steps) | credit | (wider wing width - credit) x lot + costs |

Entry prices: each leg's bhavcopy close on the entry session; a leg with close 0 or no contracts traded is untradable.
A structure whose debit is at least its width (S5, S6) is untradable (owner rule of 13 Oct 2026).

**Fits the cap:** maximum loss, with C1 charges on both sides and the pads of section 6, at most **Rs 10,000**.
**Liquid:** every leg has at least **50 contracts traded** on the entry session and on the exit session, and at least
**100 contracts of open interest** on the entry session (reasoning only: one lot must be a small share of a day's
trade).

## 6. Costs and expected net on the conservative bound

### 6.1 The rule (factory G1, `research/FACTORY_RULES.md` section 2)

For each event and structure:

    EN = e x P x lot - C - T

- **e = 5% of the structure's entry price**: the conservative bound of the gross edge. Reasoning only: no Indian
  evidence exists on stock-option event premia; published US studies disagree on its sign and size, so the screen
  asks "if a 5% mispricing of the structure existed, would it survive costs?". The report also shows the break-even
  edge e\* = (C + T) / (P x lot) per structure, so the answer at any other e can be read off.
- **C, round-trip cost:** C1 charges for every leg on entry and exit (exit charged on the entry price, since exit
  prices are not read), plus a pad per leg per side = the bucket's **75th-percentile half-spread** (6.2) x the leg's
  entry price x lot.
- **T, tail term:** 0 for debit structures (S1-S6: the debit is the maximum loss and the edge is on it). For S7,
  T = 2% of its maximum loss (reasoning only: an allowance for gap risk beyond what the credit prices).
- Per structure on the decision window: the median and mean EN, and the gross/cost ratio with the `thin margin`
  warning below 2 (a warning only, never a pass mark).

### 6.2 The Groww snapshot

- **When:** one regular session between this registration and 30 Nov 2026 (the Oct-Nov results season), at 14:00-15:00
  IST. Only after the owner has confirmed Groww's terms on storing quotes (REPLAN slice A item 3); raw quotes go to
  Drive only, the repository gets only the bucket statistics.
- **What:** read-only quotes (no order code) for every F&O stock with a results board meeting in the next 10 sessions:
  the expiry rule of section 4, strikes K0 - 3 steps to K0 + 3 steps, calls and puts: bid, ask, best quantities, time.
- **Half-spread** h = (ask - bid) / 2 / mid, per leg with both bid and ask.
- **Buckets:** moneyness (K0; 1 step; 2-3 steps) x liquidity tercile of the previous session's contracts traded. A
  bucket with fewer than 30 quoted legs is merged with its neighbour in the liquidity direction. A bucket where more
  than 20% of legs have no bid or no ask is **untradable**: historical legs in it are treated as not liquid.
- **Applied to history** by the same buckets. Some evidence at best: one session, in 2026; spreads in earlier years
  were probably wider, which is one more reason only the decision window decides.

## 7. Effective independent clusters

- **Cluster:** sector (Nifty 500 `Industry`) x ISO week of R. A stock not in that Nifty 500 list goes to one `unknown`
  sector per week (fewer clusters: conservative). The sector snapshot is today's, not point-in-time (a limit).
- **Count used by the decision:** the number of clusters a year containing at least one event that passes for the
  structure (each cluster counted once, as if events in it were perfectly correlated: the conservative bound).
- **Within-week correlation (reported, not deciding):** on **2019-2021 events only**, the market-adjusted event move
  m = ln(F_R / F_entry) - ln(NIFTY_R / NIFTY_entry) (F: near-month future close). The intra-cluster correlation (one-way
  ANOVA estimator) of m and of |m|, with a cluster bootstrap 90% interval (2,000 resamples of clusters, seed 20261015).
  Kish's effective count, the sum over clusters of n_c / (1 + (n_c - 1) max(rho_abs, 0)) with n_c the cluster's
  number of events, is reported beside the cluster count.

## 8. Decision rule

**YES** if at least one structure S1-S7 meets all three on the decision window:
1. **Fit:** at least **25%** of eligible events have the structure fitting the cap with all legs liquid.
2. **Cost:** among those events, **median EN > 0 and mean EN > 0**.
3. **Count:** at least **130 clusters a year** (count of section 7) with an event meeting 1 and 2.

Why 130 (reasoning only): a later P&L study's sample plan (G3) at e = 5% and an assumed SD of 60% of the structure's
price needs n = (1.645 x 0.60 / 0.05)^2 = 390 independent units, which must be reachable within 3 years.

**NO** if no structure meets all three. The report names, per structure, the first criterion it fails and its numbers.
There is no "almost": a structure at 24% fit or 129 clusters is NO.

## 9. Stages and early failure (run in order; stop at the first failing stage)

- **Stage 0, data (no fit, liquidity or cost numbers):** counts of eligible stocks, events, exclusions by reason,
  results-date coverage and the lot-size validation. **Cannot answer** (not NO) if, in the decision window, results
  dates are found for fewer than 80% of eligible stock-quarters, or lot size is unknown for more than 10% of events;
  the report says what data would fix it. If the Groww snapshot cannot be taken by 30 Nov 2026, stages 1-2 still run
  and report, the answer is "cannot answer yet: no spread evidence", and the snapshot is taken in the next results
  season (Jan-Feb 2027) under this same protocol; this date is the only thing that may change without a new trial.
- **Stage 1, cap (fails early):** maximum loss with C1 charges but no pads and no liquidity filter. If for **every**
  structure fewer than 25% of events fit the cap: **NO, stopped at stage 1** (the Rs 10,000 cap makes the structures
  unfit).
- **Stage 2, liquidity:** fit and liquid, no pads. If for every structure fewer than 25%: **NO, stopped at stage 2**.
- **Stage 3, cost wall:** pads from the snapshot, EN. If no structure passes criteria 1-2: **NO, stopped at stage 3**.
- **Stage 4, clusters:** criterion 3. If none: **NO, stopped at stage 4**. Otherwise YES.

Every stage also reports, descriptively: lot values (lot x underlying) by year, strike steps as % of price, the share of
events pushed to the second monthly expiry, and the stage numbers for 2019 - Sep 2024.

## 10. Known limits (said before running)

- F&O ban days (market-wide position limit) are not in the archive: new positions were not allowed on them, so the
  study slightly overstates feasibility.
- One spread snapshot stands for all years (section 6.2).
- Sector is today's classification (section 7).
- Bhavcopy closes are last trades, possibly stale for thin strikes; the liquidity filter limits this but cannot remove
  it.
- **Prior, registered before any number (reasoning only):** NO is more likely than YES. Bought ATM options and straddles
  on a stock with a Rs 5-15 lakh lot probably cost more than Rs 10,000 a lot; one-step spreads probably fit, but two
  legs crossed twice at stock-option spreads may cost well above 5% of their debit. This prior does not change any rule.

## 11. Running and freezing

- The analysis script (`study.py`, research folder only) is written after this commit, tested only on synthetic data
  and a `--check` mode that prints file counts and schemas (no stage numbers). Its SHA-256 is added to `FREEZE.md` in a
  commit before the first full run. It implements this file exactly; where they differ, this file governs and the
  difference is reported.
- It runs once. Output: `results.md` and `results.json` in this folder, with the stage reached, the answer and every
  number named above, plus "trial 53 of K".
- After the run, `research/DATA_SPEND.md` rows for these data sets change to what was actually read (section 2).
