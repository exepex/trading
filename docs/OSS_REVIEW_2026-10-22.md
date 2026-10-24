# Open-source projects that do what Omenix F&O does: clone, borrow or ignore?

Research date: 21 Oct 2026. Every project listed below was checked in this session in one or more of these ways:
- a shallow `git clone` to read the last commit date, the licence file and the file tree;
- shields.io for star and open-issue counts (GitHub's own API is blocked in this container);
- PyPI's JSON API for the latest release and its date;
- for the NSE libraries and the maths libraries, installing them in a throw-away virtualenv and calling them.

Repository facts come from `/home/user/trading` at `main` (last commit 21 Oct 2026). Evidence labels: **[strong]** means I verified it myself; **[some]** means a credible source I did not fully re-check; **[reasoning]** means my judgement only.

---

## 1. The answer in 10 lines

1. **No ready-made equivalent exists.** I found no open-source project that captures NSE chains with provenance, forecasts NIFTY/BANKNIFTY price ranges, scores them under frozen protocols and runs a paper desk for Indian index options. **[strong for the projects checked; reasoning that none exists anywhere]**
2. **Partly, at the level of pieces.** NSE data fetchers (nsepython, nselib, jugaad-data), option maths (vollib), scoring rules (scoringrules), bootstrap and GARCH (arch), a SPAN calculator (marginism) and a broker gateway with a paper sandbox (OpenAlgo) all exist. Each covers a slice. **[strong]**
3. **Cloning a "platform" would not have saved much.** Our real-time cost is not the maths, which is about 700 lines and gives the same numbers as the libraries to 1e-9 (tested below). The cost is provenance, governance and process, and no project offers that for our rules. **[strong for the line counts and the maths check; reasoning for the conclusion]**
4. **The honest uncomfortable part: we over-built the process, not the maths.** In 10 days (first commit 11 Oct 2026) the repository grew to 5,169 commits, about 69,000 lines of `fno/` code, about 68,000 lines of tests and about 107,000 lines of docs, reviews and conversation logs. It has 329 judge files. It has no proven profitable trade yet. **[strong for the counts; reasoning for "over-built"]**
5. **Do not adopt a framework** (OpenAlgo, Lean, Nautilus, vectorbt, backtrader, optopsy). None of them fits pre-registered daily range forecasting on NSE end-of-day data, and two of them (OpenAlgo, optopsy) are AGPL. **[strong for the licences and features; reasoning for the fit]**
6. **Borrow pieces:**
   - vollib for Black-76 and implied volatility;
   - scoringrules for pinball, interval and CRPS scores, but only in new, unfrozen code;
   - arch for a GARCH baseline as new research;
   - nselib or nsepython as a fallback fetcher;
   - pandas_market_calendars as a cross-check of our NSE calendar.

   **[strong that they work; reasoning on the priority]**
7. **Delete our own duplication first.** The repository has three separate Black-Scholes/IV implementations and two separate Brier functions. That is a DRY problem to fix whatever we decide about libraries. **[strong]**
8. **Frozen files block swapping now.** `fno/forecast/`, `fno/forecast_v4/`, `fno/forecast_v4_rules/`, `fno/forecast_scoring/v4/` and `fno/forecast_scoring/scores.py` are byte-checked by the freezes. Swap only at the next protocol version, or in new code. **[strong]**
9. **The biggest saving is to stop growing the process, not to change the code.** Freeze the scope and spend the next weeks on whether any trade has an edge after costs. No open-source project has published one for NIFTY options. **[some]**
10. **One project is worth reading before going further:** `sahilempire/nifty-options-research-lab`. It reports 40+ NIFTY option strategies losing after costs on 6.1 million rows. It has 1 star, its results are unverified, and its own research notes are AI-generated, but it is the closest honest prior work to our goal. **[some]**

---

## 2. Candidates checked

Part numbers: 1 data capture, 2 forecasting and scoring, 3 paper desk and risk, 4 reporting, 5 governance and pipeline. "Stars" were read from shields.io on 21 Oct 2026. "Last commit" is the newest commit on the default branch, read from a clone.

### Indian data and platforms

| Name | Covers of ours | Stars / issues | Last commit / release | Licence | Verdict and why |
|---|---|---|---|---|---|
| [OpenAlgo](https://github.com/marketcalls/openalgo) | 1 (live chain, Greeks, history via brokers incl. Groww), 3 (sandbox: virtual capital, order simulation) | 2.9k / 162 | 2026-10-18; PyPI 2.0.5, 2026-09-11 | AGPL-3.0 | **Borrow ideas only.** A Flask server built around placing orders on 36 brokers, which clashes with our "never place orders" hard line. Its sandbox is order-centric with no forecasting or scoring. AGPL is fine for personal use, but copying its code into our public repository would make that code AGPL. [strong] |
| [nsepython](https://github.com/aeron7/nsepython) | 1: option chain, FII/DII, participant OI, lot sizes, circulars, holidays, pre-open, VIX | 371 / 3 | 2026-10-08; PyPI 2.101, 2026-10-07 | GPL-3.0 | **Borrow as a fallback fetcher.** Tested working today: option chain (via NSE's newer `GetQuoteApi`), FII/DII, participant OI for 19 Oct, lot sizes (NIFTY 65). It is one 1-file module of global functions, with no raw-file archive and no tests in the repository. [strong] |
| [nselib](https://github.com/RuchiTanmay/nselib) | 1: F&O bhavcopy, participant OI, ban list, VIX, FII stats, lot lists | 181 / 6 | 2026-07-18; PyPI 2.5.1, 2026-05-01 | Apache-2.0 | **Borrow as a fallback fetcher.** Tested: bhavcopy for 19 Oct (38,485 rows), participant OI, ban list (AMBUJACEM, KAYNES, SAIL), VIX. **Live option chain broken** (`KeyError 'records'`, since NSE moved to `option-chain-v3`, which we already use). FII stats needs `xlrd`. [strong] |
| [jugaad-data](https://github.com/jugaad-py/jugaad-data) | 1: F&O bhavcopy (UDiFF), index history, F&O history | 587 / 27 | 2026-10-22 (UTC); PyPI 0.36.0 | "YOLO licence v2" (permissive joke licence) | **Borrow for back-fill only.** Tested: the 19 Oct F&O bhavcopy came back in UDiFF columns, and the NIFTY index history works. Its licence is unusual, so check it before vendoring any code. [strong] |
| [NSEpy](https://github.com/swapniljariwala/nsepy) | 1 (historical) | 807 / 155 | 2023-12-24; PyPI 0.8, 2020 | LGPL-3.0 | **Ignore: dead.** Built on the old NSE site. [strong] |
| [nsetools](https://github.com/vsjha18/nsetools) | 1 (equity quotes) | 908 / 2 | 2025-03-18 | MIT | **Ignore.** Equity-focused and stale. [strong] |
| [marginism](https://github.com/marketcalls/marginism) | 3: NSE SPAN from `.spn` files | 9 / – | 2026-06-01; PyPI 0.1.1 | MIT | **Use as a cross-check only.** Same idea as our `fno/nse_margins/`, but very young: 2 releases, 9 stars. [strong] |
| [pandas_market_calendars](https://github.com/rsheftel/pandas_market_calendars) (NSE) | 1 / 5: session calendar | – | PyPI 5.5.0, 2026-10-05 | MIT | **Use as a cross-check.** Its NSE calendar matched ours for 15 Oct to 12 Nov 2026 (20 Oct and 10 Nov holidays). It has no muhurat sessions and no circular references, which our CSV has. [strong] |
| [OpenBB](https://github.com/OpenBB-finance/OpenBB) | 1 (global cues only: its cboe, nasdaq, government_us, fred and eia providers are the same sources our `fno/global_cues/` scrapes) | 75k / 50 | 2026-10-18; 5.0.0 | Apache-2.0 | **Borrow the idea, not the dependency.** It has no NSE or India provider (verified in the provider folder list). Pulling in the whole platform for 5 global series is heavy. [strong] |

### Backtesting and trading frameworks

| Name | Covers of ours | Stars / issues | Last commit / release | Licence | Verdict and why |
|---|---|---|---|---|---|
| [QuantConnect LEAN](https://github.com/QuantConnect/Lean) | 3 (engine, options) | 22k / 250 | 2026-10-21 | Apache-2.0 | **Ignore.** No NSE options data; QC staff say NSE does not allow redistribution. A Zerodha brokerage exists, but equities only. C# core. [strong for repo facts; some for the forum statement] |
| [NautilusTrader](https://github.com/nautechsystems/nautilus_trader) | 3 (event engine, options, local Greeks) | 31k / 125 | 2026-10-21; 1.231.0 | LGPL-3.0 | **Ignore for now.** Strong engine with no Indian adapter except a community Fyers one. It is built for tick-level event simulation; our desk decides once a day. [strong for repo facts; reasoning for the fit] |
| [vectorbt](https://github.com/polakowo/vectorbt) | 3 (vectorised signal backtests, parameter sweeps) | 9.5k / 112 | 2026-10-19; 1.2.0 | Apache-2.0 + Commons Clause | **Ignore for the desk; maybe for research sweeps.** Built for single-price signal series, and awkward for multi-leg option structures. [strong for repo facts; reasoning for the fit] |
| [backtrader](https://github.com/mementum/backtrader) | 3 | 24k | 2023-04-19 | GPL-3.0 | **Ignore: unmaintained.** [strong] |
| [zipline-reloaded](https://github.com/stefan-jansen/zipline-reloaded) | 3 (equities) | 2k | 2026-10-17; 3.2.0 | Apache-2.0 | **Ignore.** Equity-centric, with no options. [strong for repo facts; reasoning for the fit] |
| [bt](https://github.com/pmorissette/bt) | 3 (portfolio allocation) | 3k / 13 | 2026-10-20; 1.4.1 | MIT | **Ignore.** Allocation, not options. [strong] |
| [optopsy](https://github.com/goldspanlabs/optopsy) | 3 (option strategy backtests on chain data) | 1.5k | 2026-04-02; 2.3.0 | AGPL-3.0 | **Ignore.** Needs bid/ask chain history. We have bhavcopy close/settle back to 2019, but bid/ask only from 14 Oct 2026. AGPL. [strong for repo facts; reasoning for the fit] |
| [hftbacktest](https://github.com/nkaz001/hftbacktest) | none (tick/HFT) | 4.9k / 8 | 2025-12-23 | MIT | **Ignore: wrong problem.** [strong] |
| [StockSharp](https://github.com/StockSharp/StockSharp) | 3 (C# platform) | 11k | 2026-10-20 | custom licence | **Ignore.** C#, custom licence. [strong] |
| [Lumibot](https://github.com/Lumiwealth/lumibot) | 3 (US brokers, paper trading) | – | 2026-10-21; 4.6.23 | GPL-3.0 | **Ignore.** No Indian broker found. [strong for repo facts; some for the broker list] |
| [opstrat](https://github.com/hashABCD/opstrat) | 4 (payoff diagrams) | 169 / 10 | 2021-07-25 | MIT | **Ignore: dead.** [strong] |

### Maths and scoring libraries

| Name | Covers of ours | Stars / issues | Last commit / release | Licence | Verdict and why |
|---|---|---|---|---|---|
| [vollib / py_vollib](https://github.com/vollib/py_vollib) | 2, 3: Black-Scholes, Black-76, implied vol, Greeks | 441 / 1 | 2026-04-30; vollib 1.0.11 | MIT | **Adopt in new code.** Gives our Black-76 IV and BS prices exactly (below). `py_vollib` now warns "deprecated, import from vollib". [strong] |
| [MibianLib](https://github.com/yassinemaaroufi/MibianLib) | 2 (BS Greeks) | 290 / 11 | 2021-06-15; 0.1.3, 2016 | no licence file | **Ignore: dead, no licence file.** [strong] |
| [QuantLib](https://github.com/lballabio/QuantLib) | 2, 3 (everything in pricing) | 7.7k / 34 | 2026-10-21; 1.44 | BSD-3 | **Ignore.** Far more than we need. European index options need 40 lines. [strong for repo facts; reasoning for the fit] |
| [scoringrules](https://github.com/frazane/scoringrules) | 2: quantile/pinball, interval score, weighted interval score, CRPS (normal, t, ensemble, quantile), Brier, log score | 107 / 15 | 2026-06-20; 0.11.0 | Apache-2.0 | **Adopt in new, unfrozen scoring code.** Matches our pinball to the last digit (below). Small project, active. [strong] |
| [properscoring](https://github.com/properscoring/properscoring) | 2 (CRPS) | 188 / 9 | 2022-10-12; 0.1 (2015) | Apache-2.0 | **Ignore.** Stale; scoringrules supersedes it. [strong] |
| [arch](https://github.com/bashtage/arch) | 2: GARCH/EGARCH family, moving-block and stationary bootstrap | 1.6k / 28 | 2026-10-21; 8.0.0 | NCSA (permissive) | **Adopt for new research.** A GARCH baseline is something we have not built. Do not replace the frozen bootstrap. [strong] |
| [sktime](https://www.sktime.net) / [darts](https://github.com/unit8co/darts) | 2 (interval forecasts, generic) | – | sktime 1.2.0, 2026-09-22; darts 0.48.1, 2026-10-16 | BSD-3 / Apache-2.0 | **Ignore.** General ML forecasting stacks; a heavy dependency for a 3-baseline problem. [strong for releases; reasoning for the fit] |
| [quantstats](https://github.com/ranaroussi/quantstats) | 3, 4 (performance tear-sheets) | 7.7k / 5 | 2026-09-27 | Apache-2.0 | **Maybe later.** Useful once paper equity curves exist. [strong for repo facts; reasoning for timing] |
| Datapane | 4 | – | discontinued (maintainers' notice) | Apache-2.0 | **Ignore: discontinued.** [some] |

### Indian personal projects (closest in spirit)

| Name | Covers of ours | Stars / issues | Last commit / release | Licence | Verdict and why |
|---|---|---|---|---|---|
| [Shivaansh29/nifty_backtest](https://github.com/Shivaansh29/nifty_backtest) | 1, 3: NSE F&O bhavcopy download and normalisation, lots, expiries, holidays, cost model, short-straddle backtest | 0 | 2026-10-21 | MIT | **Read for comparison.** Same data traps we handle (moving expiry weekdays, lot changes, special sessions). Built from scratch in the last weeks too. [strong] |
| [sahilempire/nifty-options-research-lab](https://github.com/sahilempire/nifty-options-research-lab) | 3 (backtests, walk-forward), negative results | 1 | 2026-09-07 | MIT | **Read before building more strategies.** Self-reports that 40+ strategies lose after costs. Unverified. [some] |
| [shivam61/nifty-options-backtester](https://github.com/shivam61/nifty-options-backtester) | 3 (ML regime plus option selling, Fyers) | 0 | 2026-10-21 | no licence file | **Ignore.** Its own README admits its BS-priced figures are "not validated" and that real prices give −177 rupees per lot. [strong] |
| [omsingh090/options-research-platform](https://github.com/omsingh090/options-research-platform) | 2, 3 (BS, Greeks, paper accounting) | 0 | 2026-08-20 | no licence file | **Ignore.** A demo project, unlicensed. [strong] |
| [aaryansinha16/AI-trader](https://github.com/aaryansinha16/AI-trader) | 3 (intraday ML, TrueData ticks, TimescaleDB) | 77 / 4 | 2026-07-09 | has a LICENSE file | **Ignore.** Paid tick feed, intraday focus. [strong for repo facts] |
| [buzzsubash/algo_trading_strategies_india](https://github.com/buzzsubash/algo_trading_strategies_india) | 3 (Zerodha option-selling scripts) | 82 / 1 | 2026-10-06 | no licence file | **Ignore.** Live-order scripts. [strong] |

Commercial tools (AlgoTest, Sensibull, Opstra, StockMock) are closed-source and do backtests and payoffs, not pre-registered forecast scoring. Most comparisons online come from AlgoTest's own blog, so they are biased. **[some]**

---

## 3. Per part: best reuse option and the honest trade-off

**Part 1, data capture.**
- **Best reuse:** nselib or nsepython as a second fetcher behind our existing `Provider`/`RawFileSource` interfaces, and jugaad-data for bhavcopy back-fill.
- **What they do not give:** write-once Drive storage, SHA-256 receipts, the 15:10 deadline evidence, retries inside the 3 pm window, or Groww. Those are about 80% of our data code, so a library would replace only the thin HTTP call (for example `fno/providers/public.py`, 147 lines).
- **Risk:** these libraries break when NSE changes endpoints. nselib's live chain is broken today. Ours already uses `option-chain-v3`.
- **Container note:** `www.nseindia.com` returns 403 from this cloud container (Akamai). The archives host returns 200.
- **Trade-off:** small saving, and a new dependency to watch. **[strong]**

**Part 2, forecasting and scoring.**
- **Best reuse:** vollib for Black-76/IV, scoringrules for pinball, interval and CRPS, arch for GARCH and bootstraps, `scipy.stats.t.ppf` instead of our closed-form t(4) quantile.
- **Gain:** fewer lines to own, and more scores for free (weighted interval score, CRPS for a t law).
- **Cost:** frozen files cannot change mid-trial. The maths already matches the libraries exactly, so the gain is maintenance, not correctness.
- **What no library gives:** the implied-density method (Breeden-Litzenberger plus monotone pass plus lognormal tails, `fno/price_distribution/density.py`, 158 lines) and the pre-registration and freeze machinery. **[strong]**

**Part 3, paper desk and risk.**
- **Best reuse:** none as a whole.
  - OpenAlgo's sandbox needs a running server and is built around orders.
  - Lean and Nautilus have no NSE options data.
  - optopsy needs bid/ask history we do not have.
- **Parts worth borrowing:** marginism to cross-check our SPAN arithmetic; quantstats for equity-curve stats later.
- **Trade-off:** our once-a-day, multi-leg, point-in-time desk is simple enough that a framework adds more than it removes. **[reasoning]**

**Part 4, reporting.**
- **Best reuse:** matplotlib or Plotly to render chart images, and Jinja2 for the HTML, if the FL1 v7 report is built. As far as I found, it is only a design so far (the commits touch `docs/previews/...`, which is not on `main` now).
- **Trade-off:** one dependency instead of hand-built SVG.
- Avoid Datapane (discontinued). Evidence and Quarto are overkill for a Slack post. **[reasoning]**

**Part 5, governance and pipeline.**
- **Best reuse:** none needed. Dagster or Prefect would replace `fno/daily/` (1,026 lines) plus GitHub Actions, but would add a server or cloud to run, for one job a day. Not worth it. **[reasoning]**
- **The real issue is volume.** Judges, story files, number claims (`fno/numbering/`, 578 lines), record scans, work registers and 329 judge files are our own invention. No library would shrink them; only a decision to do less would. **[strong for the counts; reasoning for the judgement]**

---

## 4. Where our code reinvents a library

The maths check was run in this session:
- Our Black-76 at F=25,000, K=25,200, 30 days, r=6.5%, σ=13% gives 280.1727523290068. Its implied vol recovers 0.13 within 1e-10. vollib's `black` gives the same price.
- Our spot BS gives 340.2387125795358, identical to `vollib.black_scholes`.
- Our pinball (0.0007, 0.003) and the 5-level quantile score (0.0032) equal `scoringrules.quantile_score` exactly.

Our code is correct; the case for swapping is maintenance only. **[strong]**

| Our code (path, lines) | What it does | Library | Swap recommendation | Risk of swapping |
|---|---|---|---|---|
| `fno/analytics.py` (106; about 65 for `norm_cdf`, `bs_price`, `bs_greeks`, `implied_vol`) | Spot BS, Greeks, IV | vollib (MIT) | Keep for now. First merge the three copies below into one module. | `norm_cdf` is imported by `research_engine/implied_vol.py` (recorded in the v4 freeze) and `price_distribution/density.py`. A change shifts the last float digits of frozen outputs. |
| `fno/research_engine/implied_vol.py` (91) | Black-76 and spot-BS IV models behind an interface | vollib | Keep the interface; swap the inside only at the next protocol version. | Listed in v4's `RECORDED_NOT_CHECKED` (`fno/forecast_scoring/v4/freeze_check.py`); v4's tests lock its behaviour. |
| `fno/checks/validity_pricing.py` (83) | **A third copy** of `norm_cdf`, Black-76 and IV | vollib, or our own one module | **Fix now: delete the duplicate** and import from one place. | Low. C4 checks are not under v4's freeze list. Run its tests. |
| `fno/price_distribution/pricing.py` (42) | Black-76 wrappers in days | vollib | Fine as thin wrappers. | G13 sealed records; keep the outputs identical. |
| `fno/price_distribution/scoring.py` (32), `fno/price_ranges/scores.py` (140) | Pinball, quantile score, coverage, Brier | scoringrules (`quantile_score`, `interval_score`, `weighted_interval_score`, `brier_score`) | Use scoringrules for **new** scores (for example a CRPS for the t law). Keep the existing ones. | G13/G13b scoring is live; its numbers must not move. |
| `fno/forecast_scoring/scores.py` (74) and `fno/forecast_v4/loss.py` (43) | Brier, clipped log score, calibration bins; **Brier defined twice** | scoringrules | **Do not touch:** both are byte-checked by v4's freeze. Note the duplicate for v5. | Breaks the v4 freeze check. |
| `fno/forecast_scoring/block_bootstrap.py` (65) | Moving-block bootstrap with a pinned seed scheme | `arch.bootstrap.MovingBlockBootstrap` | Keep. The protocol pins the exact random draw scheme, and arch's draws differ. | Changes p-values; breaks the protocol. |
| `fno/price_ranges/t4.py` (16) | Student t(4) quantile in closed form ("no scipy") | `scipy.stats.t.ppf` | Keep: 16 lines and exact. Adding scipy only for this is not worth it. | None if kept. |
| `fno/forecast_v4_rules/baselines.py` `Ewma` (about 15) | RiskMetrics EWMA λ=0.94 | arch (EWMA/GARCH) | Keep (frozen, trivial). **New research:** a GARCH(1,1)-t baseline from arch. | Frozen file. |
| `fno/providers/public.py` (147), `fno/vix_history/` (1,000), `fno/circulars/` (527), `fno/fo_masters/` (150) | NSE fetchers for chains, VIX, circulars, ban list and lots | nselib, nsepython, jugaad-data | Add one as a **fallback source** behind `RawFileSource`. Do not replace: most of these lines are archive, receipt and check code that the libraries lack. | GPL (nsepython) is fine for private use; vendoring its code into our public repository would make that code GPL. Endpoint breakage hits libraries too. |
| `fno/nse_margins/calculator.py` (89) + `span_file.py` (188) | NSE SPAN from risk-parameter files | marginism (MIT, 9 stars) | Use as an independent cross-check in a test, not a swap. | The library is very young. |
| `fno/research_data/calendar.py` (111) + `nse_sessions.csv` | NSE trading calendar with circular references and muhurat | pandas_market_calendars `NSE` | Keep ours; add a test comparing it to the library each year. | None. |
| `fno/global_cues/` (1,728 lines, 20 files) | US indices (CBOE, Nasdaq), Treasury, Brent (EIA), RBI/FBIL USD/INR | OpenBB providers for the same sources; FRED series (`DEXINUS`, `DCOILBRENTEU`, `DGS10`) | Too late to undo. It was the clearest "could have borrowed" case (1,728 lines for 5 daily series, all of them collected but unused by any forecaster, per `docs/DATA_USE_MAP.md`). | A swap now gains little. |

**In total, about 700 lines of maths and scoring could come from libraries.** That is roughly 1% of `fno/` (69,013 lines). About 450 of those lines sit in frozen or sealed files. **[strong]**

---

## 5. Recommendation (each claim labelled)

1. **Do not clone a platform.** Nothing on GitHub combines NSE index-option data provenance, pre-registered range forecasts with calibration scoring, and a once-a-day paper desk. The general engines have no NSE options data (Lean, Nautilus), need bid/ask history we lack (optopsy), are dead (backtrader, NSEpy, opstrat, MibianLib), or are order gateways (OpenAlgo, AGPL). **[strong]**
2. **The owner's instinct is still partly right: we reinvented, but not where it hurts most.** We hand-built maths that libraries do (about 700 lines, correct), and three copies of Black-Scholes. The far larger cost is self-made process: 5,169 commits, 329 judge files and 107k lines of docs in 10 days. That governance is what makes us slow, and no open-source project would have replaced it. **[strong for the counts; reasoning for the judgement]**
3. **Act now, all cheap and safe:**
   - (a) Merge the three Black-Scholes/IV copies (`fno/analytics.py`, `fno/research_engine/implied_vol.py`, `fno/checks/validity_pricing.py`) into one module, outside frozen files first. **[strong that the duplicates exist]**
   - (b) Use vollib, scoringrules and arch in every **new** forecasting or scoring module instead of hand-writing. **[reasoning]**
   - (c) Add nselib as a fallback NSE fetcher behind the existing interface, plus a yearly test against pandas_market_calendars. **[reasoning]**
   - (d) Add a test that checks our SPAN margin against marginism on one archived file. **[reasoning]**
4. **At the next protocol version (v5), not before:** replace the frozen hand-written scores (Brier twice, log score, pinball) with scoringrules calls, and delete the duplicate Brier. Swapping mid-trial would break the v4 byte-check (`fno/forecast_scoring/v4/freeze_check.py`) and invalidate the pre-registration. **[strong]**
5. **Read before building more strategies:** `sahilempire/nifty-options-research-lab` reports that costs, not strategy, decided every result, and that 40+ NIFTY option strategies lost out of sample. That matches SEBI's "9 in 10 lose" in our own README. If true, the forecasting lab is valuable, but a profitable Book 1 is the unproven part. **[some: self-reported, 1 star, not re-run]**
6. **Stop growing scope until a trade shows an edge.** The bottleneck is evidence of profit after costs and 31.2% tax, not missing code. Libraries cannot supply that, and more process does not either. **[reasoning]**

### Limits of this research (stated openly)
- GitHub's REST API is blocked in this container. Stars and issues come from shields.io; last-commit dates come from shallow clones, which are reliable.
- `www.nseindia.com` returns 403 from this container. The NSE library tests ran through their own routes, and nsepython's chain call succeeded anyway, probably via a different endpoint path.
- Reddit, TradingQnA and Hacker News searches returned almost no direct threads. Most "comparison" pages are vendor blogs (AlgoTest), so I gave them little weight.
- I did not verify every claim in `sahilempire`'s AI-written research notes (for example its Groww API price). I only used its headline as "some evidence".
