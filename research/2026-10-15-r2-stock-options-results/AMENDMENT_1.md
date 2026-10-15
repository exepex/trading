# R2 pre-run amendment 1 (15 Oct 2026): judge 97's follow-ups and the data details the protocol leaves open

Ledger trial 53 stays one trial. `PROTOCOL.md` is unchanged (SHA-256 `89947b4c...e40a6b`) and governs; this file only
fills in what the protocol does not say, in the way judge 97 asked ("state this in the script's freeze commit").
**Written before any data of this study was read**: no stock-option or stock-future row, lot size, strike, price,
volume, open interest, spread or event move, and no results date of 2019-2026. The only things looked at are file
lists and manifests (dates, URLs, hashes, row counts) and the column names of NSE's board-meeting list (one January
2025 request, read for its column names only, no row content used), and, while testing that NSE answers from this
container, the last 300 characters of NSE's event-calendar answer (two November 2026 results meetings of companies). No rule below was chosen with any outcome in view.
`study.py` implements `PROTOCOL.md` plus this file; its hash goes into `FREEZE.md` in its own commit before the run.

Labels: **strong evidence**, **some evidence**, **reasoning only**.

## A. Criterion 3: what "130 clusters a year" means (judge 97 follow-up 2)

- **Counted:** a cluster (Nifty 500 `Industry` x ISO year and week of the reaction session R) counts for a structure
  when it holds at least one decision-window event that **fits the cap with all legs liquid and has its own EN > 0**
  (criteria 1 and 2 read per event; criterion 2's median and mean are the structure-level test of stage 3).
- **Annualised:** clusters a year = clusters counted in the decision window / (window length in days / 365.25), where
  the window runs from 1 Oct 2024 to the last session in the archive, both included. One number per structure; the
  decision compares it with 130.
- Reported beside it, never deciding: the count in each 12-month part of the window (Oct 2024 - Sep 2025, Oct 2025 -
  Sep 2026, and the part after) and the Kish effective count of section 7.
- Why this form (reasoning only): it uses every season in the window once. The window ends early in the Oct-Nov 2026
  season, so its last weeks add days but few results; that biases the rate down, the conservative direction.

## B. Depth (judge 97 follow-up 1)

Per spread bucket, descriptive only (no decision role): the number of legs, the median and 25th percentile of the best
bid quantity and of the best ask quantity **in lots** (quantity / the stock's lot size), and the share of legs with at
least one lot on both sides. The raw quantities stay in Drive with the raw quotes.

## C. Power (judge 97 follow-up 3)

The registered count rule uses n = (z x SD / net)^2 = (1.645 x 0.60 / 0.05)^2 = 390 units, 130 a year over 3 years.
That n gives about **50% power** at the assumed effect. At 80% power (one-sided 5%): n = ((1.645 + 0.842) x 0.60 /
0.05)^2 = 891 units, **297 a year** over 3 years. The report prints clusters a year against both, labelled: **130 is
the registered rule and alone decides YES or NO**; 297 is shown as the 80%-power need, so a YES between 130 and 297 is
reported as "YES under the registered rule; below the 80%-power need". Changing the rule to 297 would be a new trial.

## D. Data details (fixed before reading; none changes a threshold)

1. **Results dates (D).** The A12 archive in Drive holds NSE's board-meeting lists only for 2005-2007 (manifest
   `board-meetings.csv`), none for 2019-2026. The study reads the same NSE list (the API A12 archives,
   `corporate-board-meetings`) one calendar month per request, Jan 2019 to the run month; the raw answers go to Drive and
   their SHA-256 into the study's `inputs.csv`. A results meeting is a row whose purpose or description contains
   "financial result" (any case). One event per stock and meeting date; meetings of one stock fewer than 30 days apart
   are one event (a reschedule): the meeting with a matched filing is kept, else the later one; the rest are counted as
   "duplicate meeting".
2. **Filing time (`filed_at`).** From A12's results filings (`research/data/manifests/filings/results-xbrl.csv`): the
   earliest results filing of the stock from the entry session's date to D + 3 days. None found means "no `filed_at`"
   and the protocol's rule R = first session after D. A filing at or before the entry session's 15:30 IST close
   excludes the event ("filing before entry"). Limit (reasoning only): NSE's XBRL time can lag the results PDF by hours,
   which can move R one session later.
3. **Corporate actions.** NSE's corporate-actions file covers only about 400 days before 13 Oct 2026, so for every
   event the study also detects an F&O adjustment from the bhavcopy itself: the stock's lot size differs between the
   entry session and R, or K0 of the chosen expiry is not listed on R. Where the corporate-actions file covers the
   dates, an ex-date in (entry, R] with a split, bonus, consolidation, rights, demerger or arrangement also excludes.
   Both counted under "corporate action".
4. **Lot size and open interest.** Current format: `NewBrdLotQty` of the stock's near-month future on the entry
   session. Open interest in contracts = `OpnIntrst` / lot in both formats (both carry shares; `fno/fo_bhavcopy.py`
   maps OPEN_INT to `OpnIntrst`). Contracts traded = `TtlTradgVol` (legacy `CONTRACTS`).
5. **Sessions.** NSE sessions = days with a bhavcopy file in the manifests, checked against
   `research/data/calendar/nse_sessions.csv`. "At least 5 sessions after R": at least 5 sessions strictly after R up to
   and including the expiry day. A "push to the second month" is an event whose chosen expiry is later than the nearest
   expiry on or after R.
6. **Strikes.** K0 + 2 steps = K0 + 2 x (the upward step), K0 - 2 steps = K0 - 2 x (the downward step); a leg whose
   strike is not listed makes the structure untradable for that event ("no listed strike", counted).
7. **Stage 0's thresholds** (80% results-date coverage, 10% lot unknown) are read on the decision window. A
   stock-quarter is a stock and calendar quarter with the stock F&O-listed on the quarter's first and last session;
   it is covered when the stock has a results meeting with D in that quarter. The partial last quarter is left out.
8. **Snapshot (section 6.2).** Stocks: F&O stocks (both FUTSTK and OPTSTK in the previous session's bhavcopy) with a
   results meeting in the next 10 sessions on NSE's event calendar on the snapshot day. R is taken as the first session
   after D (the protocol's no-`filed_at` rule) for the expiry choice. K0 is the strike nearest the underlying's last
   price in Groww's option chain (basis ignored, as section 3 says). Each leg: one Groww `get_quote` (read-only). Liquidity
   terciles: boundaries are the 1/3 and 2/3 quantiles of the quoted legs' previous-session contracts traded; history
   legs use the same boundaries on their contracts of the session before entry. A bucket with fewer than 30 quoted legs
   merges toward the more liquid neighbour (the top tercile toward the middle), repeated until each bucket has 30 or no
   neighbour is left. A bucket's 75th-percentile half-spread uses legs with both bid and ask.
9. **Within-week correlation.** F is the stock future with the nearest expiry on or after R, its close on the entry
   session and on R; NIFTY is the `Nifty 50` index close of the same two sessions. Only events with R in 2019-2021 are
   read. The intra-cluster correlation uses the one-way ANOVA estimator with unequal cluster sizes, n0 = (N - sum
   n_c^2 / N) / (k - 1); the bootstrap draws clusters with replacement, 2,000 times, `numpy.random.default_rng(20261015)`,
   and reports the 5th and 95th percentiles. Kish's count is printed for all decision-window events and, per structure,
   for the events that pass criteria 1 and 2. The report also counts events in the `unknown` sector (judge 97
   follow-up 5).
10. **Cost-hurdle wording.** The report calls e = 5% the **assumed hurdle** (`FACTORY_RULES.md` section 2, judge 97
    must-fix 1) and prints e\* per structure.
