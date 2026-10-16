# G13. Daily NIFTY valuation record and price-distribution forecasts

**Repository:** trading · **Lane:** 1 (new story; forecast and evaluation records; Drive) · **Judge:** E · **Response:** 262 · **Builder:**
session_01UkTaDeTRF9ksDgQB9cTU5C · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH · **Branch:**
`story/g13-price-distribution` · **Status:** story text for the judge (no code yet)

**Description.** As the volatility trader and the quantitative modeller, I want one record per session of what the
3 pm option chain says (IV surface, skew, term structure, the option-implied price distribution, a smile value against
mid for every quoted contract) and daily NIFTY price-range forecasts as quantiles, scored against the closes, so the
desk can see whether options are rich or cheap against what NIFTY then did, and so every later price forecaster (the
AI books included) has a record and a yardstick.

**Context and why.**
- Owner, 16 Oct 2026 (`docs/DESK_DECISIONS.md`): the core engine covers "forecasting, evidences, prices, price
  forecasting, valuation, comparison", "including all the data that we need for price forecasting. Capture it. We
  have to capture or generate it." Also "do not over-engineer ... Simplicity is also our priority, but not the product
  quality" and "no surprises, every claim validated".
- `docs/CORE_ENGINE_GAP_AUDIT.md` Part B2 #14 and Part E: no question forecasts a NIFTY price range or distribution
  (v2 Q1 is direction only; v4 is movement size), and nothing records fair value or the IV surface. Both are internal
  data, rebuilt from captured quotes [strong: code search, `fno/` has no density, skew, surface or fair-value code].
- Design v2 2.1 ("the 15:00 chain summary" among the small derived daily tables) and 2.2 (forecasters, baselines,
  one score class per scoring rule, failure modes).

**Does this change a trade or stop decision?** No. Every number here is descriptive. Nothing reads it to size, enter,
exit or block a trade, and it is in no frozen protocol. Registering it in one is an owner question (Q2).

## What the data allows today (checked on main 9dbf1b3f)

| Input | State | Evidence |
|---|---|---|
| 3 pm NIFTY chain, two nearest monthlies, strikes within 5% of spot, bid/ask | Groww from 14 Oct (raw rows in Drive only), NSE from 16 Oct (in the repository); 188 contracts a day | `fno/quotes/recorder.py:36-38`; `research/data/quotes/*/.../nifty_2026101*.canonical` |
| Same-expiry futures (last, volume), spot, VIX | in each sidecar, not the CSV | `nifty_20261016_145500.meta.json` |
| Parsed chain for a day | `RecordedSnapshots.snapshot(day) -> CutoffSnapshot` (`LiveQuote.mid` only for a valid two-sided quote) | `fno/research_data/quote_snapshots.py:41-104` (v2 freeze: imported, never edited) |
| BANKNIFTY, FINNIFTY, MIDCPNIFTY 3 pm chains (A4c) | first run 19 Oct | `fno/quotes/indices.py` |
| Weekly expiries | only inside A16's raw Groww payload, no parser | `fno/intraday/groww_source.py` (G7b part d needs the same parser) |
| NIFTY daily closes | regular sessions 2 Jan 2017 to 15 Oct 2026, appended each evening | `research/data/nifty-panel/warmup_closes.csv`; `fno/forecast_v4_rules/series.py` |
| End-of-day option panel (traded closes, volume, OI; no bid/ask) | 2019-2026 | `fno/research_data/panel_reader.py` |
| Black-76 price and IV solver | yes | `fno/research_engine/implied_vol.py` (`Black76.price`, bisection 1%-200%) |
| 30-day ATM IV interpolation | yes | `fno/forecast/iv30.py:38 interpolate_30d` (frozen; imported only) |
| Rate | a constant, `config.yaml` `risk_free_rate: 0.065` | `fno/config.py`; no T-bill source in the code |
| Quantile scoring (pinball, CRPS) | none | code search |

**Probe on real data (16 Oct NSE chain, the method below in a scratch script, not committed).** Near monthly (27 Oct,
11 days): put-call-parity forward 23,122.0, equal to the future's last trade; 47 strikes 21,950-24,250; the measured
CDF runs from 2.2% to 98.9%, so all seven quantiles are inside the quoted strikes: 5% at -3.79%, 50% at +0.11%, 95% at
+2.98% from the forward, as log returns `ln(q/F)` (index levels 22,263, 23,147, 23,822; as simple returns `q/F - 1`:
-3.72%, +0.11%, +3.03%, the judge's figures in judge 304: the same quantiles in the other unit). The left tail is
longer: skew. Three raw CDF points went backwards (quote noise), fixed by
the monotone step. Next monthly (23 Nov, 38 days): the quoted strikes cover the CDF only from 10.3% to 87.4%, so its
5%, 10%, 90% and 95% quantiles come from the tail rule, and 10 raw points went backwards [strong: one day; the 5%
band is A4's frozen recording rule].

## Design

New package `fno/price_distribution/` (each file well under 350 lines), composition root
`fno/price_distribution/wiring.py` (added to CLAUDE.md's list). Nothing in `fno/forecast/`,
`fno/forecast_scoring/` or `fno/forecast_v4*` is edited.

### 1. Chain inputs (interface `ChainSource`)

- `SnapshotChains` (live and 3 pm back-fill): `RecordedSnapshots` over the quote store, Groww first, NSE if Groww's
  day is `none` (as `fno/forecast/capture.py:44 load_snapshot`); the source used is recorded.
- `PanelEodChains` (exploratory back-fill, 2019 on): the panel's traded closes as prices, the same-expiry future close
  as the future. Used only for back-fill labelled `backfill_eod`, never mixed with the 3 pm rows.
- Per expiry: only the monthly expiries the source carries (two), and only an expiry at least 1 calendar day after
  the day (an expiry on the day itself has 30 minutes left).
- **Quote filter (reasoning only, printed with each record):** a 3 pm quote is used when `LiveQuote.mid` exists and
  `ask - bid <= max(0.10 x mid, Rs 0.50)`. An EOD price is used when its volume is above zero and its close at least
  Rs 0.50.
- **Forward (Black-76's underlying):** from put-call parity at the three strikes where `|call mid - put mid|` is
  smallest, `F = K + e^{rT}(C - P)`, averaged. The one-strike formula is a small standalone pure function
  (`parity_forward(strike, call_mid, put_mid, rate, days)`), the averaging a separate one, so G7b part d can import
  the former for protocol 1.4's forward (its builder's request). The future's last trade and the gap to it are recorded. Reason: Groww
  gives no quote time, so the future's last trade can be older than the option quotes; the parity forward is
  consistent with the very prices it is used with. On 16 Oct they agreed to 0.0 points (above).
- **Rate:** `config.yaml` `risk_free_rate` (6.5% today), recorded in every file. On a futures-based Black-76 the
  rate only discounts: at 38 days a 1-point rate change moves prices by about 0.1% and the CDF by the same factor
  [strong: arithmetic, `e^{0.01 x 38/365} = 1.0010`]. Q3 asks whether to read RBI's 91-day T-bill instead (the S6
  cash-rate decision of 16 Oct uses it for the S1 freeze).
- **Implied volatility:** every IV and Black-76 price comes from `fno/research_engine/implied_vol.Black76`
  (`price`, `implied_vol` on an `OptionPricing`), the project's one inverter; G13 adds none.
- **Time:** calendar days / 365 for pricing (as B1 and G1); regular sessions from the session calendar (A7) for the
  forecast horizons.

### 2. Valuation record (one per underlying per session)

Per expiry:
- **ATM IV:** the strike nearest the forward (lower on a tie), mean of the call and put Black-76 IVs at their mids
  (G1/B1's rule, with the parity forward).
- **Compact surface:** each OTM quote's IV (puts below the forward, calls at or above it) and Black-76 delta; IV at
  delta points 10P, 25P, 50 (ATM), 25C, 10C by linear interpolation in delta between the two nearest quoted points;
  missing when the delta point is outside the quoted deltas (never extrapolated).
- **Skew:** 25-delta risk reversal `IV25C - IV25P` and butterfly `(IV25C + IV25P)/2 - IV_ATM`, in IV points.
- **Term structure:** ATM IV of each expiry, and the 30-day ATM IV from the frozen `interpolate_30d` (flag carried).
- **Option-implied price distribution** (the method below): the CDF at each strike midpoint, the quantiles at 1%,
  5%, 10%, 25%, 50%, 75%, 90%, 95%, 99%, each marked `body` or `tail`, and two checks.
- **Smile fit and smile value (the brief's "model fair value"):** a quadratic in log-moneyness `k = ln(K/F)` fitted
  by least squares to the OTM IVs (needs at least 5 points; its RMSE in IV points is recorded). Each quoted contract
  gets: bid, ask, mid, its own IV, delta, smile IV, **`smile_value` = Black-76 at the smile IV**, `smile_value - mid`
  in rupees and IV points, and whether `smile_value` lies inside the bid-ask. **Said plainly, and written in every
  record (`smile_value_note`):** this is a smoothness residual, how far one quote sits from a curve fitted to the same
  day's quotes, not a valuation that says a contract is cheap or rich, and **no trade signal**: a contract off the
  curve is usually a stale or wide quote (judge 304 minor 1, accepted: the owner must not read it as an edge).
- **Implied minus realised:** ATM IV minus the `rv20` baseline's volatility (the volatility risk premium every
  option-selling idea rests on, forward-looking rather than on spent history).

Records in the same file: source (groww, nse or panel), snapshot id and its CSV SHA-256, `observed_at` (the
snapshot's `finished_at`), rate, quote-filter counts (quoted, used, dropped by reason), the method version and the
SHA-256 of the method files. BANKNIFTY, FINNIFTY and MIDCPNIFTY get the same record from their A4c chains (no
forecasts: no closes series yet).

**Why this distribution method (Breeden-Litzenberger body, anchored lognormal tails).** The second strike derivative
of option prices is the risk-neutral density (Breeden and Litzenberger 1978); its first derivative of put prices is
the CDF: `CDF(K) = e^{rT} dP/dK`.
1. **Body, model-free:** OTM calls become puts by parity (`P = C - e^{-rT}(F - K)`), giving one put curve; between
   adjacent used strikes `K_i < K_j` (gap at most 200 points), `CDF((K_i + K_j)/2) = e^{rT}(P_j - P_i)/(K_j - K_i)`.
   Quote noise can make it fall; one isotonic (pool-adjacent-violators) pass makes it non-decreasing, clipped to
   [0, 1]; the number of raw decreases is recorded. Pinned (judge 304 should-fix 1):
   - a pair of adjacent used strikes more than 200 points apart forms **no** midpoint, so it is left out **before**
     the pass (never pooled);
   - the pass weighs every midpoint **equally** (not by strike gap);
   - a quantile inside the measured CDF is **linear in strike** between the two CDF points around it: the first
     segment `c_i < p <= c_j` with `c_j > c_i` (flat pooled segments are skipped), `K = K_i + (p - c_i)(K_j - K_i) /
     (c_j - c_i)`;
   - quantiles are stored as index levels and as log returns `ln(K / F)` (distribution) or `ln(K / S_ref)`
     (forecasts); a percentage in any text says which.
   On the 16 Oct chain the four combinations (equal or gap weights, strike or log-strike interpolation) all give the
   same quantiles to 0.01 points (one CDF segment changes and none of the seven quantiles falls in it; strike gaps are
   all 50 points), so judge 304's difference is the unit: it reported `q/F - 1`, the probe `ln(q/F)` [strong:
   recomputed both, -3.72% = 22,263/23,122 - 1 and -3.79% = ln(22,263/23,122)].
2. **Tails, one fixed rule:** below the lowest midpoint `K_L` (CDF `c_L`), `CDF(K) = c_L x N(-d2(K, s_L)) / N(-d2(K_L,
   s_L))` with `s_L` the IV of the lowest used put; above the highest `K_H`, `1 - CDF(K) = (1 - c_H) x N(d2(K, s_H)) /
   N(d2(K_H, s_H))`. The tail is lognormal-shaped at the edge option's own volatility and keeps the measured mass
   exactly, so the CDF is continuous and monotone with no fitted parameter.
3. **Checks:** the distribution's mean against the forward (`|mean / F - 1|`, flagged above 0.5%), and at least 8
   CDF points. The mean is exact for the stated distribution, no grid (judge 304 minor 3): the body's CDF is linear
   between points, so each segment contributes `(c_j - c_i)(K_i + K_j) / 2`; the lower tail contributes
   `c_L x F N(-d1(K_L, s_L)) / N(-d2(K_L, s_L))` and the upper `(1 - c_H) x F N(d1(K_H, s_H)) / N(d2(K_H, s_H))` (the
   lognormal partial expectations `E[X; X < K] = F N(-d1)`, `E[X; X > K] = F N(d1)`, scaled as the tails are); a failed check makes that expiry's distribution `missing` with the reason (counted, never filled).

Alternatives weighed (reasoning only): a fitted smile (quadratic or SVI) differentiated twice gives a smooth density
but its wings are the fit's guess, and a quadratic can produce negative density; a two-lognormal mixture is always
valid but needs a nonlinear fit (no scipy here) and imposes a shape; a plain lognormal at ATM IV ignores the skew the
probe shows. The chosen rule is model-free where quotes exist and states plainly where it is not (`tail` marks).
The quadratic smile is used only for the smile value, where a smooth reference is the point.

**Said plainly:** this is the **risk-neutral** distribution, not a forecast of where NIFTY will be. Implied volatility
usually sits above realised volatility and the left tail is priced heavier [strong: widely documented volatility risk
premium], so its quantiles are expected to be too wide on average. Measuring by how much, per horizon and tail, is
the point of scoring it.

### 3. Price-distribution forecasts (interface `QuantileForecaster`)

- **Target:** the NIFTY 50 close at a target session, as `y = ln(close / S_ref)`, where `S_ref` is the spot in the
  chain (live and 3 pm back-fill) or the day's close (EOD back-fill).
- **Horizons:** `h1` (next regular session), `h5` (5 regular sessions), `e1` and `e2` (the near and next monthly
  expiry sessions). An expiry horizon is skipped when that expiry is not used (above). Weekly expiries: out of scope
  (see the gap list).
- **Levels:** 5%, 10%, 25%, 50%, 75%, 90%, 95%, stored as log returns from `S_ref` and as index levels.
- **Forecasters (ids in `fno/price_distribution/constants.py`; `fno/constants.py` is at 349 lines):**
  - `implied`: the expiry's implied quantiles of `ln(F_T / F)` plus `ln(F / S_ref)`. For `h1` and `h5`, the
    shortest used expiry with `n >= h` sessions to it, split around its median `m = ln(F_T median / F)`: `ln(q_h /
    S_ref) = (h/n) x ln(F / S_ref) + (h/n) x m + sqrt(h/n) x (ln(q_T / F) - m)`. The centring (carry and the median's
    offset, about `-s^2 T / 2` for a lognormal) scales linearly in time, the spread around the median by the square
    root, exactly as a lognormal would (judge 304 minor 2, accepted). Reasoning only: the shape is kept and variance
    assumed spread evenly over sessions; event days break it.
  - `rv20`: lognormal with zero log drift at the B1 realised volatility of the last 20 regular closes before the day
    (root mean square of daily log returns, not demeaned, times sqrt(252)), over `h` sessions.
  - `hist750`: the empirical quantiles (numpy's default linear rule) of all `h`-session log returns among the last
    750 regular sessions whose end is before the day; at least 500 such returns, else `not_eligible`. Zero fitted
    parameters; it carries NIFTY's fat tails and drift.
  - `book2_hybrid` and `book3_ai` (`fno/constants.py` `BOOK2_HYBRID`, `BOOK3_AI`, imported, never retyped): slots
    only. The record schema and the scorer accept their rows; until a story has them answer they have no rows and no
    start date, so no miss is ever counted for them (G11's owner, 16 Oct). The story that adds them sets their
    start and whether earlier days count as misses (G11 counts misses from each slot's `effective_start`). Who fires
    them is G11's or a later story's decision, through the orchestrator.
- **One row per (day, forecaster, horizon):** `day, forecaster, horizon, target_day, s_ref, q05 ... q95, status,
  reason, label, tail_levels, method_version, method_sha256, inputs_sha256, made_at`. Status `ok`, `missing` (input
  failure, reason given) or `not_eligible`; quantiles must be strictly increasing when `ok`.

### 4. Labels, live_from, regeneration

- `live`: written by O1's daily run on day `d` (made_at recorded, before the first target close), only from the
  step's `config.yaml` `daily.live_from.price_distribution` date (null until the owner sets it, as the other O1
  steps). The first live day is that date; a hand run never writes `live`.
- `backfill_3pm`: rebuilt later from the captured 3 pm chains (14 Oct on); `backfill_eod`: from the panel, 2019 on.
  Back-fill stops before the first live day (none set: it may cover every captured day). All three are scored and reported apart, never pooled.
- Every output is a pure function of captured inputs and the method files: re-running a day reproduces it byte for
  byte. A changed method file changes `method_sha256`; earlier files are never edited (Drive is write-once), so a
  regenerated back-fill goes to a new path named by the method hash, and live rows keep the method they were made
  with.

### 5. Storage (O9's rule)

Files go write-once to Drive's `data` area through `fno/storage/data_wiring.build_data_store`, each with its SHA-256
receipt under `receipts/`; readers use the verified Drive cache. Layout:
`data/price_distribution/v1/live/<YYYY>/<MM>/<underlying>_<day>.json` (valuation and that day's forecasts, one file),
`data/price_distribution/v1/backfill/<label>_<method_sha8>/<underlying>_<YYYY>.json.gz`, and scores under
`.../scores/<day>.json`. No Groww-derived value is committed to the repository (contract rows come from Groww quotes).

### 6. Scoring (once outcomes exist)

- **Outcome:** the target session's close from the committed closes file; a row is scored only once that close is in
  the file (never before; a missing close is "unresolved", never filled).
- **Loss (one class per rule, `ForecastScore` style):** the quantile score `QS = (2/7) x sum over the seven levels of
  pinball_tau(y - q_tau)`, `pinball_tau(u) = max(tau x u, (tau - 1) x u)`, in log-return units. Averaged over a grid
  of levels, twice the pinball loss approximates the CRPS (Gneiting and Raftery 2007); seven levels is a coarse grid,
  said in every report.
- **Calibration:** per level, the share of outcomes below the quantile against the level; the 50% and 90% central
  interval coverage; per horizon and label.
- **Comparison (descriptive only):** for each horizon, `implied` against `rv20` and `hist750`, the mean daily QS
  difference on paired days with the existing moving-block bootstrap (`fno/forecast_scoring/block_bootstrap.py`,
  imported unchanged: block 20, fixed seed, fewer than 40 paired days not tested). No claim, no family, no Holm: no
  protocol registers these questions (Q2).
- Output: one report per run (Drive, receipt) and its printed summary; the weekly post-mortem may read it later (LR1's
  owner decides).

### 7. Daily command and failures

- `python -m fno pricedist record [--day D]` (default today IST): builds the day's valuation and forecasts for NIFTY
  and each A4c index with a chain, writes them, prints one result line per underlying. Not a trading day: prints
  "not a trading day", writes nothing.
- `python -m fno pricedist backfill --from D1 --to D2 --source {3pm,eod}` and `python -m fno pricedist score`.
- `python -m fno pricedist value --day D --source {groww,nse} --dry-run`: prints one day's valuation record and
  forecasts and writes nothing (no Drive, no receipt); the judge's and the claims file's way to see real output.
- **Rerun and a failed receipt commit (judge 304 minor 4):** the live file holds `made_at`, so a rebuilt day would not
  be byte-identical. So `record` never rebuilds a live day whose Drive file exists: it reads that file back, checks its
  SHA-256, restores the receipt if the checkout lacks it, and prints `already recorded` (exit 0). A Drive file whose
  receipt commit failed is therefore picked up by the next run of the day (O1 reruns a failed step) or a hand rerun,
  never written twice; Drive's write-once conflict (`RawFileConflict`) is the backstop. Back-fill files carry no
  `made_at` and are byte-identical on a rerun, so `DataStore.put`'s same-bytes no-op covers them.
- **Data failures (owner, 16 Oct: "we must notify that something failed"):** no canonical chain (`none` or absent),
  the raw file unreadable or failing its hash, an expiry failing its checks, the closes file missing a session
  needed: the command writes the day's file with `status: missing` and the reason for each part affected, prints
  one line per problem, and ends on a non-zero exit whose last line names them all (`written with problems: ...`).
  When nothing could be written at all (no chain for any underlying), it prints `nothing written: <reason>` and exits
  0. The command never sends an alert itself: O1's `Alerted` wrapper sends exactly one alert for a failed or refused
  step (O1's rule: one sender, `tests/daily/test_steps.py` walks the graph), and O1's `CommandStep` still commits the
  receipts of what was written. Back-fill and scoring print counts per reason and never alert.
- **Daily run (orchestrator's answer to Q1; O1's joining rules, its owner, 16 Oct):** a step `price_distribution`
  in O1's `DAILY_RUN_STEPS` (`fno/constants_operations.py`, which O8's health check reads), after `card`: it reads
  the day's canonical 3 pm chains (NIFTY and A4c's), committed once `quotes_done` ends, and nothing reads it (not the
  pack, not the card), so the card never waits on it (O1's owner). One entry in the steps dict of
  `fno/daily/wiring.py`: `Alerted(name, LiveFrom(CommandStep(processes, lambda day: (..., "pricedist", "record",
  "--day", day), receipt_pathspecs(), git.changed), live[name]), alerts)`, with the name in `daily.live_from`
  (`config.yaml`, null), `LIVE_STEPS` and `fno/config.py`'s allowed keys. G13's code branch makes these lines; O1's
  owner reviews that diff (whoever merges second merges `main` in). The pathspecs come from G13's own module
  (`fno.price_distribution.folders.receipt_pathspecs()`, G13's receipts only, as M1's `record_folders()`), never a
  shared folder. **No cutoff of its own** (unlike v4's 14:30): its inputs are the 3 pm captures, already timestamped,
  and a row is `live` when made before its first target close, which the 15:30-ish end of the run always meets. It
  takes seconds, well under O1's 600 s limit. No git outside the run's thread. It changes no schedule: the run already
  exists. O1's owner checks the plug-in part of this text before code.

## Acceptance criteria (each with a test: positive, negative, boundary, empty)

1. **Forward and filter:** the parity forward on a fixture chain matches a hand value; quotes failing the spread rule
   (just over and at the limit), invalid or one-sided quotes are dropped and counted by reason; an expiry on the day
   is skipped; an empty chain gives `missing: no quotes`.
2. **ATM IV and surface:** ATM IV equals the hand Black-76 call/put mean on a fixture; delta points interpolate as
   hand-computed; a delta point outside the quoted range is missing; risk reversal and butterfly match hand values.
3. **Term structure:** the 30-day IV equals the frozen `interpolate_30d` on the record's ATM IVs (bracketed and the
   flagged single-expiry case).
4. **Distribution:** on a chain generated from a known lognormal (flat IV), the body CDF and the quantiles match
   Black-76's `N(-d2)` within 0.002 in probability; with planted quote noise the monotone step removes every decrease
   and the count is recorded; the tail rule is continuous at the edge and matches the formula; a chain with fewer
   than 8 CDF points or a mean more than 0.5% off the forward is `missing` with its reason; each pinned choice of
   design 2 has a test that fails under the other choice (a gap over 200 points, unequal-gap pooling, a quantile in a
   non-uniform segment); the mean check equals a hand value on a fixture. **Committed fixture:**
   `tests/price_distribution/fixtures/nse_20261016_expected.json`, made by the committed code from the committed
   16 Oct NSE CSV and checked by a test: 27 Oct forward 23,122.0, 47 strikes, CDF range 0.0217-0.9895, 3 raw
   decreases, q05/q50/q95 at 22,263 / 23,147 / 23,822 (+-1 point; log -3.79% / +0.11% / +2.98%); 23 Nov CDF range
   0.1034-0.8742, 10 decreases, q05, q10, q90, q95 marked `tail`. Any judge reruns it with
   `python -m fno pricedist value --day 2026-10-16 --source nse --dry-run`.
5. **Smile value:** with a flat-IV chain, `smile_value` equals mid within Rs 0.01 for every contract; with one planted
   off-curve contract, only it is outside the bid-ask; fewer than 5 OTM IVs gives no smile and no smile values
   (reason given); every record carries `smile_value_note` (no trade signal).
6. **Forecasters:** `implied`, `rv20` and `hist750` match hand values on fixtures for each horizon (the sqrt scaling
   for `h1`/`h5`; the 20-close RV; the 750-window empirical quantiles); fewer than 20 closes or 500 returns gives
   `not_eligible`; a holiday inside the horizon moves the target session (A7 calendar); non-increasing quantiles are
   refused by the record check; an AI slot row is accepted with `not_started` and left out of comparisons.
7. **Point in time:** no input dated on or after the day (or, live, after `observed_at`) is read: a test plants a
   future close and a later snapshot and shows the outputs unchanged.
8. **Labels and regeneration:** live, `backfill_3pm` and `backfill_eod` are written to their paths and never pooled
   in scores; back-fill stops before the first live day; rebuilding a day reproduces identical bytes; a changed
   method hash writes a new back-fill path and never touches the old one; a live row is never overwritten (Drive
   conflict surfaces).
9. **Daily step:** with `live_from` null the step records `not_live` and nothing is called; from its date it runs the
   command once, and a rerun the same day skips it (O1's rule); a written-with-problems day is a failed step with
   exactly one alert and its receipts committed; a day with no chain is refused (`nothing written:`) with one alert;
   the step's pathspecs name only G13's receipts; the built graph has no second sender (O1's graph test, fake
   processes).
10. **Storage:** every file goes through `DataStore.put` and gets a receipt; a failed Drive write leaves no receipt and
   the command reports it; readers read through the Drive cache only; a rerun of a recorded live day writes nothing,
   restores a missing receipt with the same SHA-256 and prints `already recorded`; `value --dry-run` writes nothing.
11. **Scoring:** the pinball loss and QS match hand values (outcome below, inside and above the quantiles; at a
    quantile exactly); a row is not scored before its target close exists; calibration shares match a hand count;
    the bootstrap comparison equals `block_bootstrap` called directly on the same differences; under 40 paired days
    it is "not tested".
12. **Failures:** each failure case of section 7 writes its `missing` reason, prints its line and gives the exit and
    last line of section 7; the command itself sends no alert; back-fill never fails a run for a missing day (counted);
    "not a trading day" writes nothing.
13. **Indices:** a fixture BANKNIFTY chain gives a valuation record and no forecasts.
14. **No frozen file changes:** the existing freeze tests pass unedited; no file added to `fno/forecast/`.
15. **Real output sample** (quality rule 6): the claims file shows the 16 Oct NSE valuation record and forecasts made
    by the committed code in a dry run (index levels, no strategy internals), and the EOD back-fill's first scores.

**Test plan:** unit tests per module (`tests/price_distribution/`), the flat-IV round trip, the planted-noise and
planted-mispricing chains, the real 16 Oct NSE chain, a fake Drive store and fake processes, determinism tests. Builder
self-review agents and broken-code proofs per criterion (judge quality rules 3-4).

**Judge verifies:** recomputes one expiry's forward, ATM IV, two CDF points and one tail quantile by hand from the
16 Oct NSE CSV; recomputes one `rv20` and one `hist750` quantile from the closes file; recomputes one QS.

## Gap list

| Requirement (source) | Covered by |
|---|---|
| ATM IV per listed expiry (brief 1) | design 2, criterion 2 |
| IV by delta/strike, compact surface (brief 1) | design 2, criterion 2 (per-contract IVs in the record) |
| Skew, term structure (brief 1) | criteria 2, 3 |
| Implied distribution per expiry, method justified (brief 1) | design 2, criterion 4 |
| Fair value vs mid per contract, Black-76 on the future, rate source named (brief 1) | design 1-2 (`smile_value`, said to be no signal), criterion 5, Q3 |
| A4c indices when live (brief 1) | criterion 13 |
| Quantile forecasts at fixed horizons from implied, realised-vol baseline, AI slot (brief 2) | design 3, criterion 6 |
| Proper scoring rule (pinball/CRPS) once outcomes arrive (brief 2) | design 6, criterion 11 |
| Plug into G4/G8's pattern without editing frozen files; registration as an owner question (brief 2) | design 4-6 (G7/G8's labels, first-live rule, block bootstrap reused), criterion 14, Q2 |
| Regenerable from captured inputs; backfill and live labels after live_from (brief) | design 4, criteria 8-9 |
| Data failures alert and are recorded (brief; owner 16 Oct) | design 7, criterion 12 |
| Runs daily in O1's run with a `live_from` date (orchestrator, Q1) | design 7, criterion 9 |
| Every data file write-once in Drive with a receipt (owner 16 Oct, O9) | design 5, criterion 10 |
| Point in time, `first_seen_at` before the cutoff (design 2.1 failure modes) | criterion 7 |
| A method changed quietly (design 2.2 failure modes) | `method_sha256` in every row, criterion 8 |
| **Out:** weekly-expiry horizon | needs an A16 weekly quote parser (G7b part d needs the same); `h5` stands in until then |
| **Out:** realised-vol baseline on A16 intraday RV | A16 has one session (16 Oct, void by construction); add as `rv20_intraday` once 20 valid sessions exist, a new forecaster id |
| **Out:** AI books answering | G11 or a later story; G13 gives the slot |
| **Out:** any use in a trade decision, protocol registration | Q2 |
| **Out:** V5's option-implied probability (G7b part c) | G7b's; G13's density module is offered for it via the orchestrator, never imposed |

## Decisions (orchestrator, 16 Oct 2026, answers to Q1-Q4)

- **Q1:** G13 runs as a step of O1's daily run, after the 3 pm quote parts, not as a separate routine (design 7).
- **Q2:** no protocol registration now; the orchestrator takes registration to the owner once there are scores.
- **Q3:** `config.yaml` `risk_free_rate` (6.5%), labelled in every file. A daily 91-day T-bill and repo capture is
  being assigned to another builder; G13 switches to it when it lands (a new `method_version`, so old rows keep
  their rate).
  - **Measured gap (orchestrator, from A21's builder reading RBI on 16 Oct):** repo 5.50%, 91-day T-bill cut-off yield
    5.7281% (14 Oct), so config's 6.5% is about 0.8 points high. **Kept at 6.5% until A21 lands, and why:**
    `config.yaml` is hashed by the v1 and v2 freezes and read by the frozen forecasts, so changing it is not G13's
    to do, and a second G13-only rate constant would be a stale copy by A21's first run. **The effect, bounded:**
    with the parity forward the rate enters only through `e^{-rT}`; at 0.8 points and 38 days that is
    `0.008 x 38/365 = 0.08%` of every option price and every CDF value (at most 0.0008 in probability), and less
    for the near month (11 days: 0.024%) [strong: arithmetic]. Every file records the rate used, so a later switch
    is visible.
- **Q4:** boundaries agreed directly with each owner; each owner's answer is quoted in the claims file:

| Neighbour | Owner session | Boundary (proposed by G13) |
|---|---|---|
| O1 daily run | 014zYLf18PgCzR7YoHs1X5Dp | **Agreed** (O1's owner, 16 Oct: "the plug-in part ... fits O1's code"; partial write = non-zero exit "written with problems", recorded `failed`, one alert, receipts committed; after `card`). O1's joining rules applied in design 7: one `DAILY_RUN_STEPS` entry, one steps-dict entry in `fno/daily/wiring.py`, `LIVE_STEPS` and the `daily.live_from` key; nothing else in `fno/daily/`; O1's owner checks this text's plug-in part |
| G7b (part c, V5's implied probability) | 0185gR5DmoDh2zBAvgRU4CEB | **Agreed** (G7b's builder, 16 Oct): G13 edits nothing in `fno/forecast_v4*/` or `research/forecasts/v4/` and writes nothing G8 reads. No overlap: G7b reads G10's v4 pack (14:30-14:40), never the A4 chains, and V5 stays protocol 3.1's lognormal (G7b will not import G13's density). Asked of G13: Black-76 only from `implied_vol.Black76`; `parity_forward` kept a standalone pure function for V4 (part d) |
| G10 (v4 pack) | 01VK88LxJvV1Gi7Wbr3D4fzp | **Agreed** (G10's builder, 16 Oct): G13 reads the 3 pm A4 chains, never the v4 pack (`fno/v4_pack/`, Drive `v4/packs/`); edits nothing in `fno/forecast_scoring/v4/`, `fno/forecast_v4*/`, `fno/v4_pack/` or `fno/intraday/`; writes nothing G8 or G10 reads. No weekly parser is planned there (read G7b part d's if built). **Open risk:** A4's NIFTY capture may move to 14:30 for v4 (G10's lean: add a 14:30 capture, not move). G13 reads whatever `RecordedSnapshots` gives as the day's canonical and records `observed_at`, so a move changes the label of the inputs, not the code; the orchestrator's decision is noted in the claims file |
| G11 (AI books) | 013xqaNTCbSBytKgqpfaYFqZ | **Agreed** (G11's owner, 16 Oct): G13 edits nothing in `fno/ai/` or `agents/`; AI price quantiles are a later story with its own budget check under BG1's cap; ids imported from `fno/constants.py` |

## Original questions (kept for the record; answered above)


- **Q1. Where the daily run lives.** Recommended: a step in the 3 pm routine right after NIFTY's push (and after A4c
  for the indices), since the routine already reads the day's chain and has the Drive settings; O1 owns that prompt.
  Alternative: an evening GitHub workflow (late starts do not matter: rows stay `live` if made before the next close),
  only if the Drive data store's settings are in GitHub. Until decided, the command is run by hand and those rows are
  `backfill_3pm` [reasoning only].
- **Q2. Protocol registration.** Recommended: none now. The scores are descriptive; after about 250 live sessions the
  desk decides whether a price-distribution question joins a new protocol version (frozen before its first scored
  row). G13 writes nothing into any protocol [reasoning only].
- **Q3. Rate.** Recommended: `config.yaml` `risk_free_rate` now (recorded per file; effect about 0.1% per rate point
  at 38 days), and the 91-day T-bill when a story captures RBI's auction results [strong: arithmetic above].
- **Q4. Boundaries (orchestrator).** G7b part c (V5 implied probability), G10's pack and G11 touch nearby things; G13
  edits none of their files. Please confirm with their owners that G13 owns the valuation record and the quantile
  forecasts.
