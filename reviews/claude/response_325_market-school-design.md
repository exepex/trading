# Response 325: The market school: drivers, roads, instructor, simulator, dashcam (design for ChatGPT review)

Claude (system architect), 22 Oct 2026. Replaces response 324's three-book plan (which replaced package D, responses
322/323 and review 136). Built on the owner's concept and decisions of 22 Oct 2026 (`docs/DESK_DECISIONS.md`, "The
market school: full-scale design inputs"). Research and paper trading only: nothing here places, modifies or cancels a
real order; Groww is read through the read-only allow-list (`fno/intraday/read_only.py`). Labels: **strong evidence**,
**some evidence**, **reasoning only**. Rupees are per lot unless said.

## 0. The idea in one page (for the owner)

- **Roads** are the places a trade can happen: each index or stock, futures or options, weekly or monthly expiry, and a
  time of day. **Drivers** are rule sets (and AI personalities) that drive every road every day, in paper, in
  parallel. **Road conditions** are labels for each day and road (calm or jumpy, trending or flat, event, gap...).
- The **dashcam** records every decision, trade or no trade, at the moment it is made, and can never be edited.
- The **instructor** compares drivers on the same road and day. If everyone lost, the road was hard; if one driver lost
  while the others made money, the driver was bad. It writes down **what works under which condition**: the
  **condition map**, with how much evidence stands behind each line.
- The **simulator** (2019-2026 history) is for practice only. The **road test** (forward paper days) is the only proof.
- The **recommender** (the experienced driver) picks the day's top 3 paper trades from the map. Every driver's paper
  trades are always booked; confidence only sets the owner's real-money banner: green consider, amber paper only, red
  do not trade real money today.
- **What to expect [strong evidence for the past, reasoning only for the future]:** 98 counted trials in `research/ledger.csv`,
  the last 24 being EDGE1's option variants (`research/edge1/RESULTS.md`), found no simple option rule that beat costs
  inside the Rs 10,000 cap. Most drivers
  will lose a little after costs at first. The school's value is that it measures honestly and fast, across many roads at
  once. That does not by itself make money. **The banner cannot turn green before a driver version passes RM1's
  real-money gate on forward paper, which takes at least 6-12 months (reasoning only, from RM1's design).** Until then
  it is amber or red every day.

## 1. What already exists (inventory, from the code on `main` today)

| School part | Existing code (package, story) | Status |
|---|---|---|
| Versioned, pre-registered rule sets | `fno/playbook` (D: candidates, conditions, exit terms, decision records), `fno/books/version_registry.py` (D6 `journal/versions.csv`, version counts only if its commit is an ancestor of the decision) | **exists**; drivers reuse it |
| Rule driver engine | Book 1 (`fno/books/book1*`, `fno/desk`): one decision a day, NIFTY monthly, 3 pm only, widest width under the cap (`playbook/candidates.py`) | **partly**: one road, one slot, one book |
| AI drivers | `fno/ai` (sealed same-day isolation, transcripts audit, usage ledger, versions), `fno/book3` constitution (NIFTY monthly only), F5 Book 2 hybrid text | **partly**; paused books |
| Paper accounts, fills, exits, marks | `fno/books/account.py` (Rs 20 lakh), `fno/desk` entries, E4c protective-leg refusal, E4d displayed size, exits, E2d trade marks, E8 owner-timing fills | **partly**: NIFTY options only, no futures |
| Safety laws | C2 risk manager `fno/risk` (Rs 10k a trade, bucket 30k, open risk 1.5 lakh, new risk 50k a day, 1.2 lakh brake, SPAN x stress k margin room), C4 checks `fno/checks` (no naked leg, impossible prices) | **partly**: no futures stop, no per-day loss stop, ban list unread |
| Ban list, lots | `fno/fo_masters` (A20a, captured daily from 21-22 Oct; nothing reads it, `docs/DATA_USE_MAP.md`) | **partly** |
| Costs and tax | `fno/costs.py` (C1, options charges, STT 0.15% from 1 Apr 2026, exercise STT) | **partly**: no futures charges, one table for all dates |
| Road conditions | weather M1 (`fno/weather`, calm/jumpy colour), events A6 (61 rows), results dates A12 (`fno/filings`, unread), global cues A17 and A17e, pre-open A22, G13 valuation (ATM IV, skew, term) | **partly**: no tagger joins them per road |
| Captures | 3 pm Groww + NSE chains for the 4 indices (A4, A4c, A4f weeklies), 15-min NIFTY marks (A16; BANKNIFTY extension decided 21 Oct), pre-open, close read (A4h), bhavcopy (A1, A13) | **partly**: no stock options, no futures bid/ask |
| Dashcam store | O9 write-once Drive store with SHA-256 receipts (`fno/storage`), playbook `decision_record/decision_store`, desk CSV logs, G13b-style sealing by push time | **partly**: schema new |
| Instructor | LR1 weekly post-mortem (`fno/learning`, forecast-focused), S3 scoreboard A matched days (`fno/scoreboard/matched.py`), E6 scorecard reviews, S6 do-nothing and random control, factory R1 (cards, data spend, sample plan, Holm, t-bound), R3 shadows, advocate port | **partly**: root causes, condition map, calibration of trade confidence are new |
| Simulator | `fno/research_engine/simulator.py` (daily closes, NIFTY/BANKNIFTY options, EDGE1 impossible-price rule) | **partly**: no stocks, futures, spread penalty |
| Forecast inputs | G13 distribution, G13b ranges, G13d premium ranges, G13c ITM chance, v4 rule forecasts | **exists** (indices only) |
| Benchmarks | `fno/scoreboard/do_nothing.py` (Nifty 50 fund plus cash), `random_control.py` | **exists** |
| Real-money gate | RM1 `research/evaluation/REAL_MONEY_GATE.md`, S1 protocol (`fno/evaluation`, not frozen) | **exists**, evidence record names Book 1: needs an amendment to "driver version" |
| Reports, display | FL1-1d 08:50 and 20:05 editions (`fno/forecast_lab`), T1 card (off), P2 read models, dashboard W3 | **partly** |
| Position alerts | LM1 monitor (branch `story/lm1-code`, behind A16's MarkObserver port) | **partly** |
| Fleet runner, licences, recommender, banner, exam roads, map ageing, conductor | none | **new** |

## 2. Roads and the data gaps

**Roads v1.** 4 indices (NIFTY weekly Tuesday expiries and monthly; BANKNIFTY, FINNIFTY, MIDCPNIFTY monthly only:
since Nov 2024 one weekly per exchange [strong]); about 180-220 F&O stocks (exact list from A20a's daily lot file) with
monthly options and futures; index futures; 4 time slots (section 4). About 4 x 3 + 200 x 2 = **~410 instrument roads,
x 4 slots**.

| Road | Have today | Gap | Capture design (closes the gap) |
|---|---|---|---|
| NIFTY options | 3 pm Groww + NSE chains, 2 monthlies + 2 weeklies; A16 marks within 6% every 15 min (routine waits for the owner) | A16 not yet daily | A16 live daily; its 09:30, 12:15, 15:15 marks are the slot snapshots (no new calls) |
| BANKNIFTY options | 3 pm (A4c) | intraday | A16's decided BANKNIFTY extension |
| FINNIFTY, MIDCPNIFTY options | 3 pm only | intraday; thin books | conductor takes one chain-band snapshot per slot (about 60-80 quotes each, ~30 s) |
| Index futures | 3 pm last price from NSE (no bid/ask); A16 near NIFTY future | bid/ask, all 4 | 8 depth quotes per slot (near and next) |
| Stock futures | daily OHLC (bhavcopy) | intraday, bid/ask | **LTP batch every 15 min** (about 200 futures + 200 spots = 8 calls of 50); depth quotes at each slot (~200 quotes, ~40 s at 5/s) |
| Stock options | one exposed snapshot (15 Oct) | **everything** | **survey + witness**: (a) survey all strikes per stock at each slot, NSE's public equity option chain (one request per symbol carries every strike's bid, ask and sizes [some evidence: our NSE index parser reads `buyPrice1/buyQuantity1`]; ~200 requests paced 1 per 1.5 s = ~5 min) with Groww's option chain endpoint as fallback (200 x 2 expiries = 400 calls; whether it carries bid/ask must be verified: our parser reads only LTP, OI, volume and IV [some evidence it does not]); (b) Groww depth quote for every leg a driver actually enters or exits (the fill witness: ~150-300 quotes, 30-60 s) |
| Open stock positions, path | none | marks between slots | LTP batch every 15 min for open legs (50 per call); stale LTP of thin strikes marked "stale" and never used to trigger an option exit |
| Results dates | A12 board meetings (unread) | reader | event tags for stock roads |
| History of bid/ask | **none anywhere** before 13 Oct 2026 (indices), none for stocks | cannot be closed | the spread model (section 8.3) learns from forward captures only |
| Intraday history | NIFTY index 15-min candles 2020-25, NIFTY monthly option/future candles 2019-2026 (2019-23 fresh) | stocks | verify Groww's historical candles for stock futures (retention, expired contracts); back-fill like A16b if served |

**Groww budget per slot [some evidence: Groww docs 10/s and 300/min per type; our measured safe rate ~5/s].** Quote
type: A16 mark ~75 s, index futures and FIN/MIDCP ~40 s, stock futures ~40 s, witness legs ~60 s: **~3.5 min**. LTP
type (separate budget if "per type" holds; to verify): ~20 calls a mark. Stock option survey on NSE (~5 min) runs in
parallel. Fits inside one 15-minute gap between marks. **Two processes on one key lose 33-39% of quotes** (16 Oct,
`fno/intraday/claims.py` [strong]), so all Groww reads of the trading day go through **one conductor** (section 3).

**Capture probes first (stage MS0):** Groww chain endpoint rate type and bid/ask fields; LTP and quote budgets counted
separately or not; NSE equity chain at 200 symbols x 4 slots without blocking;
Google Drive API write quota for about 1,000 files a day (or batching per slot); Groww stock-futures candle retention. Each
probe writes a dated note; no driver is designed on an unverified answer.

## 3. Architecture (for builders)

**Principles (CLAUDE.md):** interface plus adapter for every source, store and rule; composition roots only; no file
or class over 350 lines; write-once Drive data with receipts; output only to #fno-forecast (reports), #fno-desk
(alerts); nothing to #fno-intraday unless the owner asks. The repository is public: dashcam, driver internals and
condition map live in Drive only; GitHub keeps receipts, versions and public daily totals (as E2c).

**New package `fno/school/`** (sub-packages, each with its own `wiring.py`):

| Component | Interface (new unless named) | Notes |
|---|---|---|
| `roads/` | `RoadCatalogue` (roads for a day: lots, expiries, ban list, closures); `Road`, `RoadDay` | lots and expiries from A20a and Groww `get_expiries` |
| `conditions/` | `ConditionTagger` with one `ConditionRule` strategy per tag | frozen tag thresholds, versioned |
| `capture/` | `SlotSnapshotSource` (adapters: A16 marks, Groww depth, Groww LTP batch, NSE survey); `GrowwConductor` (one process, per-type token buckets, leases for the 3 pm recorders) | replaces ad-hoc claims inside the trading day |
| `quality/` | `RoadQualityGate` (road closed or open, with reason) | section 9.3 |
| `drivers/` | `Driver.decide(pack, road_day, slot) -> Decision`; `RuleDriver` (reads a playbook version), `AiDriver` (fno/ai transport), `BenchmarkDriver` | driver = data (versioned card), engine = judged code |
| `fleet/` | `FleetRunner`: runs every licensed, probation and benchmark driver per slot, each isolated (one failure never stops others), a time limit each | ObserverGroup pattern from A16 |
| `safety/` | `SafetyLaw` strategy list: protected only, Rs 10k options max loss, futures 1% stop, Rs 25k daily stop, ban list, margin room, C2 caps, quote gate | wraps C2 and C4; only these stop a paper trade |
| `execution/` | `FillModel` (touch plus slippage), `FuturesStopWatcher` (MarkObserver), `RollPolicy` | sections 9.4-9.5 |
| `accounts/` | per-driver account, Rs 20 lakh, reusing `fno/books/account.py` | |
| `dashcam/` | `DashcamStore` (O9 `RawFileStore`), `DecisionRecord`, `OutcomeRecord`, `DiagnosticRecord`; sealed by receipt push before the fill snapshot | one gz JSONL file per driver, slot, day |
| `instructor/` | `PnlAttributor`, `RootCauseClassifier`, `RoadComparison`, `ConditionMap`, `Calibration`, `LessonCard` (factory card) | section 6 |
| `licences/` | `LicenceBoard` (stage rules, frozen) | section 5.3 |
| `recommender/` | `Recommender.top3(day)`; `Banner` | section 7 |
| `simulator/` | `HistoricalRoadSource` behind the same `SlotSnapshotSource` interface, so drivers run unchanged | section 8 |
| `reports/` | sections for the FL1 editions, Saturday report, P2 read models for the dashboard | |

Composition: `fno/school/wiring.py` builds the fleet for O1's `daily run` (new `DAILY_RUN_STEPS` per slot) and for
the simulator. A new driver is a new card file plus one registry row, no code. A new data source is a new adapter.

**Daily timeline (IST)** [reasoning only; times re-measured in the dry run]:

| Time | What happens |
|---|---|
| 06:00 | Groww token renews (existing) |
| 07:45-08:30 | margins (A14), ban list and lots (A20a), results dates; road catalogue for the day; roads closed if data missing |
| 08:36-09:12 | pre-open (A22), Asian cues (A17e); condition tagger, morning pass |
| 08:45 | recommender builds the plan: top 3 from yesterday's close data and overnight cues, prices indicative |
| **08:50** | **"Today"** in #fno-forecast (with the morning edition) |
| 09:15-15:30 | conductor: A16 marks every 15 min, LTP marks, futures stops, daily loss stops |
| 09:30 / 12:15 / 14:45 (stocks) and 15:00 (indices) / 15:20 | the four slots: snapshot, quality gate, fleet decides, safety laws, receipts pushed (seal), fills at the next snapshot |
| 15:40-16:00 | close read (A4h); marks; expiry settlement |
| 18:40-19:46 | bhavcopy; end-of-day marks for every open leg |
| 19:53 | instructor daily pass: outcomes, attribution, root causes, tickets valued |
| **20:05** | **"How did today go"** in #fno-forecast |
| **Saturday 10:00** | **instructor report**; first Saturday of the month: deep review, licence moves, new versions |

## 4. Drivers

### 4.1 Common rules for every driver

- **Sizing:** options 1 lot, the widest width whose maximum loss with every charge and the Rs 1 pad is at most
  Rs 10,000 (existing `candidates.py` rule); futures 1 lot with a 1% stop. At most 5 new trades per driver per slot,
  ranked by the driver's own frozen score; every other road where its rule fired becomes a **ticket**: a 1-lot virtual
  trade priced at the same quotes, valued the same way, never in the account and never summed into rupees shown to the
  owner. Tickets let the instructor measure the rule on every road, the account measures the driver as a business.
- **Exits:** each driver's own (take profit, stop, time, expiry); options are exited only at a slot snapshot with
  valid quotes, never on a stale LTP.
- **Cap fit [some evidence, arithmetic]:** a NIFTY weekly ATM straddle costs about 335 points x 65 = Rs 21,800 (VIX
  15.7, 5 days, model), and a monthly ATM straddle on a Rs 1,500 stock with lot 500 about Rs 51,600: so buyers use
  capped structures (bought iron fly, bought condor, debit spreads), never plain straddles. A stock whose lot times
  strike step exceeds Rs 10,000 has no road for spreads: recorded "no structure fits the cap".

### 4.2 Rule driver catalogue v1 (31 drivers)

Roads: **IX** = 4 indices, **NW** = NIFTY weekly, **ST** = F&O stocks passing the liquidity tier, **IF** = index
futures, **SF** = stock futures. Slot: O 09:30, M 12:15, A 14:45/15:00, C 15:20.

| Code | Family | Roads, slot | Entry | Structure | Exit |
|---|---|---|---|---|---|
| PS1 | protected seller | NW, A | 1-3 sessions before expiry | iron condor, shorts at G13's 16-delta, widest wings under cap | 50% of credit, loss 1.5x credit, or expiry 15:15 |
| PS2 | protected seller | IX monthly, A | 30-45 days out | iron condor, narrow wings (1 step under cap) | 50% TP, 21-day time exit |
| PS3 | protected seller | IX monthly, A | same as PS2 | iron condor, mid wings | same |
| PS4 | protected seller | IX monthly, A | same as PS2 | iron condor, widest wings under cap | same (PS2-4: the width ladder) |
| PS5 | protected seller | BANKNIFTY monthly, A | 30-45 days | iron fly, TP50 (EDGE1's only run-1 passer; it lost Rs 337 a trade in run 2, so it drives as a known failure watched forward, not a candidate) | TP 50%, 21 days |
| PS6 | protected seller | IX, ST, A | price above 20-day average | bull put credit spread, short near 25-delta | 50% TP, 2x credit loss, 10 sessions |
| PS7 | protected seller | IX, ST, A | price below 20-day average | bear call credit spread | same |
| PS8 | protected seller | IX, A | only when ATM IV minus 20-day realised > 2 vol points and VIX in top 40% of 1 year | iron condor | 50% TP, 21 days |
| PS9 | expiry seller | NW, O on expiry day | every weekly expiry | iron fly, cap-fitted | 15:15 same day, or loss 1x credit |
| PS10 | event seller | ST, A | results announced yesterday (IV just crushed) | iron condor, 1-step wings | 5 sessions or 50% TP |
| PS11 | event seller | IX, M | RBI policy day, after the 10:00 decision | iron condor | next session 15:15 |
| LB1 | buyer | ST, A | results in the next 1-2 sessions | bought iron fly (debit at most cap) | session after results, 15:15 |
| LB2 | buyer | IX, A | RBI, Budget, election result in the next session | bought condor | session after the event |
| LB3 | buyer | IX, A | VIX in bottom 20% of 1 year | bought strangle 2 steps out, debit capped | 10 sessions or +100% |
| LB4 | gap buyer | IX, O | GIFT Nifty gap above 0.8% | debit spread in gap direction | 15:15 same day |
| DR1 | directional | IX, ST, A | close at a 20-day high | bull call debit spread | 10 sessions, +80%, or close below 20-day average |
| DR2 | directional | IX, ST, A | close at a 20-day low | bear put debit spread | mirror of DR1 |
| DR3 | directional | IX, ST, A | G13b P(up) above 0.60 next session | bull call debit spread, 1 step | next session C slot |
| FT1 | futures trend | IF, A | 20/50-day average cross | long or short 1 lot, 1% stop | opposite cross or stop |
| FT2 | futures mean reversion | IF, A | daily fall beyond 2 standard deviations | long 1 lot, 1% stop | next session C slot or +0.7% |
| FT3 | futures opening range | NIFTY, BANKNIFTY futures, O | break of the 09:15-09:30 range | 1 lot with the break, 1% stop | 15:15 same day |
| FT4 | gap go | IF, O | gap above 0.5% | 1 lot with the gap | 15:15 |
| FT5 | gap fade | IF, O | gap above 0.5% | 1 lot against the gap (FT4 and FT5 drive the same roads in opposite styles) | 15:15 |
| FT6 | stock momentum | SF, A, monthly | top 3 and bottom 3 by 12-1 month return | long and short 1 lot each, 1% stop | month end or stop |
| FT7 | post-results drift | SF, O | the session after results, direction of the results-day move | 1 lot, 1% stop | 5 sessions or stop |
| CD1 | calendar | NIFTY, A | Thursday before a weekly expiry | sell weekly ATM call, buy monthly same strike; debit at most cap | near expiry 15:15 (far leg sold then; max loss = debit plus costs) |
| CD2 | calendar | BANKNIFTY, A | 25-35 days to near monthly | sell near, buy next monthly ATM | near expiry 15:15 |
| CD3 | diagonal | IX, A | price above 20-day average | sell near 1-step OTM call, buy next-month ATM call | near expiry 15:15 |
| HG1 | hedger | NIFTY, A | weather red | put debit spread on the benchmark's Rs 20 lakh NIFTY holding (an overlay, scored as benchmark plus hedge) | 10 sessions |
| KL1 | known loser | NIFTY monthly, A | EDGE1's NIFTY SC3 EXP (lost Rs 2,085 a trade in run 1) | iron condor to expiry | expiry |
| RC1 | random control | IX, ST, A | every day | random direction and strike (existing `random_control.py` rules) under the same caps | same exits as its twin |

**Benchmarks (three):** **BH** buy-and-hold NIFTY (Nifty 50 fund change plus dividend, less expense ratio, as
`do_nothing.py`, per rupee-day of capital); **RF** Rs 20 lakh in a 91-day T-bill or liquid fund (about 6-7% a year;
config holds `risk_free_rate: 0.065` today; the dated rate is recorded); **N0** do nothing (Rs 0, no trades). A driver
counts as better only if, after every cost, it beats **BH and RF**, not merely zero. KL1 and RC1 are the
instructor's own tests: if it ever rates them well, the instructor is broken. Thresholds above are first guesses
[reasoning only], frozen in each card before its first road-test day; the simulator may tune them before freezing, never
after.

### 4.3 AI drivers (5)

Same packs, caps, safety laws and dashcam as rule drivers. Each answer is sealed before another driver's is readable
(sealed same-day isolation, 16 Oct). Roads: the 4 indices plus a **20-stock shortlist** chosen by a frozen rule
(liquidity tier plus results or ban-exit events), so cost stays measurable.

| Code | Personality | Brief |
|---|---|---|
| AI1 | cautious | trades only at stated confidence 0.65 or higher; prefers wide protected sellers; no trade is a normal answer |
| AI2 | aggressive | one structure per road on the shortlist; directional and buyer structures allowed |
| AI3 | contrarian | fades the rule fleet's majority and crowd positioning (participant OI, put-call ratio) |
| AI4 | hybrid | sees the rule drivers' candidates, may choose one or veto (F5/D4 envelope) |
| AI5 | analyst | trades nothing; gives the probability that each candidate nets above zero; scored on calibration only |

**Look-ahead bias [strong reasoning]:** the model has read about 2019-2026 (COVID crash, elections, budgets). Its
simulator results are contaminated and **never shown as evidence**; AI drivers are judged on forward days only. Every AI
decision records model name and version, prompt version and hash, the pack's SHA-256, temperature, the full transcript
(Drive), tokens and minutes; the dry run re-runs 20 decisions to measure how often the same input gives a different
answer.

**Transport [reasoning only]:** scheduled Claude sessions took 66-99 s at best and about 5 min on 15 Oct (DESK_DECISIONS
16 Oct); four slots a day for five drivers may need the Claude API from a scheduled job instead. Decided after the dry
run (section 10).

## 5. The dashcam, licences and benchmarks

### 5.1 Dashcam records (write-once, Drive, receipts in GitHub)

- **Decision record** (sealed before the fill snapshot): driver code and version, road, slot, time; pack SHA-256 and the
  inputs used (forecast, IV, realised vol, events); road condition tags and quality-gate result; legs, lots, quotes
  witnessed (bid, ask, sizes, raw SHA-256); credit or debit, maximum loss, costs, margin; reason (code-built for rules,
  text for AI); confidence (probability of net above zero, with its method); every safety-law result; trade, ticket or
  no trade with a reason code.
- **Outcome record** (a separate file when closed): fills, path of marks (15-min for indices and futures; slots plus
  end-of-day for stock options), exit reason and price, gross, costs, net, return on risk (net / maximum loss; futures:
  net / 1% stop amount), slippage against mid, partial or failed fills.
- **Diagnostic record:** forecast error, IV change, realised vs implied, P&L attribution, root cause tags (section 6),
  and for a no trade, what the candidate would have done.
- Never edited. A correction is a new record that names the old one.

### 5.2 Comparison

Every driver against BH, RF and N0 per rupee-day of capital tied (S6's rule), against RC1 (selection luck), and against
the road's median (section 6.2).

### 5.3 Licence stages (frozen rules, versioned; numbers reasoning only, to be fixed in the card before use)

| Stage | Meaning | Promotion rule | Demotion rule |
|---|---|---|---|
| Learner | simulator only | plumbing passes on 1,000+ simulated road-days; exam roads (5.4) shown; card frozen | n/a |
| Probation | forward paper, counted, not eligible for the top 3 | at least 40 forward trades on at least 30 distinct sessions; date-clustered 80% interval of mean return on risk above the road median; calibration error at most 10 points over at least 100 scored confidences; drawdown under Rs 1 lakh | brake or two rule breaks: back to learner as a new version |
| Licensed | eligible for the recommender | stays while the rolling 60-session interval does not fall below the road median | 60-session mean below RC1, or calibration error over 15 points, or drawdown beyond Rs 1.2 lakh: suspended |
| Suspended | keeps driving in paper (data never stops) but cannot be recommended | re-licensed only by the monthly review on new days | after 3 months suspended: retired |

Licensed is **not** real-money eligibility: only RM1's frozen gate decides what may be put to the owner.

### 5.4 Exam roads (stress set, simulator)

Before probation every driver's worst case is shown on a fixed replay set: 23 Mar 2020 crash week; 1 Feb 2021 Budget;
4 Jun 2024 election-result day (NIFTY about -5.9% close [some evidence]); the 10 largest NIFTY gaps since 2019; 10
weekly expiry days with the largest intraday range; the March 2026 month that cost the naked strangle Rs 50,332 (EDGE1).
Output: worst trade, worst day against the Rs 25k stop, gap loss beyond the futures stop. Exams are shown, not passed or
failed, except that any breach of a safety law in replay is a code bug.

## 6. The instructor

### 6.1 Root-cause taxonomy v1 (code-built, frozen thresholds, one primary and up to two secondary causes)

From a Greeks P&L attribution (delta, gamma, vega, theta, costs, residual) between entry and exit, using G13's surface
for indices and the slot survey for stocks:

| # | Cause | Code rule (sketch) |
|---|---|---|
| 1 | Move beyond forecast range | realised move outside the forecast's 90% range at entry |
| 2 | Wrong direction | directional trade, delta P&L negative, move inside range |
| 3 | Volatility rose | vega P&L below -40% of loss, short-vol trade |
| 4 | Volatility collapsed | vega loss on a long-vol trade |
| 5 | Time decay | theta loss on a long-premium trade, move below breakeven |
| 6 | Gap through stop | futures exit price worse than the stop by over 0.3% |
| 7 | Scheduled event shock | road tagged event, move above 2 standard deviations |
| 8 | Unscheduled shock | market-wide move above 2 standard deviations, no event tag |
| 9 | Costs ate the edge | gross at or above 0, net below 0 |
| 10 | Bad price or data | a price used later fails a validity check (a data fault, not learning) |
| 11 | Exit rule whipsaw | stop or target fired, holding to plan would have done better by over 1x the loss |
| 12 | Normal noise | loss within 1 standard deviation of the driver's expected outcomes |
| 13 | Rule broken | replay of the card does not give the recorded decision: a bug |

Winners get the same tags (so the instructor learns why wins happened, not only losses). Modifier on every outcome:
**hard road** or **bad driver** (6.2).

### 6.2 Same-road comparison

Outcome = return on risk. For each road-day and family (short vol, long vol, bullish, bearish, futures), the **road
score** is the median across all drivers' trades and tickets. A **hard road**: 75% or more of the family lost. A **bad
driver** on that road: below the road score while most of its family won. Per driver, residual = its outcome minus the
road score, accumulated with a **date-clustered block bootstrap** (all roads of one day share the market; overlapping
holds use week blocks, as EDGE1's blocks of 2). Evidence: BR1 found daily forecasts across F&O names behave like
**6-42 independent bets a day**, not 200, and its plain test lost its false-claim control under that dependence
[some evidence, `research/breadth/README.md`]: so every instructor test is first run on RC1 and shuffled labels to
measure its real false-claim rate before it is trusted. **Planted-edge test:** in the simulator, a hidden driver with a
known small edge (for example +Rs 300 a trade on return on risk) is added; how many sessions the instructor needs to
find it tells the owner, before the road test starts, how long a real edge of that size would take to show. If the
answer is years, the design says so up front.

### 6.3 Condition map

One cell = family (or driver) x condition tag combination (at most 2 tags per cell, from a frozen list). Each cell
shows: trades, distinct sessions, distinct drivers, effective sample (n / (1 + (m-1) x within-day correlation)), mean
return on risk after costs, 90% interval, win share, worst loss, evidence date range, and a **status**:

| Status | Rule |
|---|---|
| Draft | simulator only (labelled "practice") |
| Watching | forward, below the sample plan's size |
| Supported | forward, registered before its window, one look, Benjamini-Hochberg false-discovery rate 10% across all map cells, at least 3 drivers of at least 2 families agree in sign |
| Confirmed | held again on a second, untouched forward window; Holm 0.05 across all claims (factory rule) |
| Expired | its evidence is older than 26 weeks without a re-check, or the regime detector fired |

**Map ageing and regime change:** every cell carries its evidence dates; Supported or Confirmed cells are re-checked
every 13 weeks and expire at 26 weeks unless re-confirmed. A **regime detector** compares the last 20 sessions' road
scores with the map's expectation per condition (a CUSUM on standardized residuals, threshold frozen); when it fires,
the Saturday report says "recent days do not match the map" and the recommender drops to amber-only on the affected
cells. [reasoning only]

### 6.3b Comparison statistics

- **Paired:** two drivers are compared only on the road-days both drove, as same-day, same-road differences in return on
  risk (S3's paired daily difference, moving-block resampling).
- **False-discovery control** across the whole driver x road x condition grid (Benjamini-Hochberg), not per table.
- **Minimum sample before the owner sees a cell:** 30 distinct sessions and 3 drivers; below that the cell shows
  "not enough days yet".
- **Risk-adjusted, not only rupees:** each driver shows net after costs, maximum drawdown, worst day, worst trade, and
  a Sharpe-like ratio (mean daily net per rupee-day of capital over its standard deviation, annualised, with the RF
  rate subtracted), always beside BH and RF.

### 6.4 Calibration

Every confidence is a probability that the trade nets above zero (and an expected return on risk). Scored by Brier
score against the driver's own base rate, with a reliability table in 10-point buckets; the calibration error is the
weighted mean gap between stated and observed. Calibration needs volume: about 100 scored confidences per driver before
it is read [reasoning only].

### 6.5 Cadence and lessons

- **Daily (19:53):** outcomes, attribution, causes; no rule changes, ever, from one day.
- **Weekly (Saturday):** report (section 7.2).
- **Monthly (first Saturday):** licence moves; lesson cards. A lesson ("PS1 loses on weeks where VIX rose over 8% on
  entry day") becomes a **factory card** (R1: hypothesis, data window, sample plan, pass rule) and a **new driver
  version** (D6 row) that runs **beside** the old one (R3 shadow) on the same roads. The new version replaces the old
  only if its pre-set rule passes on matched road-days. **At most 5 new versions a month**, all counted in
  `research/ledger.csv` and `research/DATA_SPEND.md`.
- **Guards against false patterns:** pre-registration (card hash in git before its window); one look per forward
  window; FDR for the map, Holm for claims; 3-driver agreement; RC1 and KL1 run through every test; simulator results
  never move a cell beyond Draft; every question asked of the data is logged (R1 factory), so nobody can re-ask the
  same days until something looks good.

## 7. Recommender, banner and display

### 7.1 Recommender

Each morning (and at each slot for the dashboard) it ranks the open candidates of **licensed** drivers by the map's
expected return on risk for the cell x the driver's calibrated confidence, and picks **3 that are not the same bet**:
ranking uses each cell's shrunk estimate (pulled toward the road median by its evidence size), because the best of
~40 drivers looks better than it is by luck alone (winner's curse) [strong: statistics]; pairwise correlation of their simulated outcomes on the last 250 sessions below 0.5, at most one short-vol index trade,
at most two trades on the same underlying group (C2 buckets). **Fleet stress figure:** the sum of losses of the 3 (and
of the whole fleet) under a -5% / +5% index move with a +30% IV shock, shown daily. The recommender is itself a
versioned driver (RX1), with its own account, scored against BH, RC1 and the blind drivers. Before any driver is
licensed it shows the best probation candidates labelled "unproven". Every recommendation also gets **E8's
owner-timing fill** (60 minutes later), because the owner trades by hand.

### 7.2 What the owner sees

- **08:50 "Today"** (on top of the morning edition; the signed-off report design needs the owner's approval for the
  added section): one line of road conditions; the 3 paper trades, each with what, worst loss in rupees, confidence in
  words, one-line reason; the banner.
- **20:05 "How did today go":** each of the 3 in rupees and why (its root cause in plain words); fleet total; best and
  worst driver; one lesson (or "no lesson: one day is noise").
- **Saturday report:** top and bottom 5 drivers (vs buy-and-hold), about 5 condition-map rows with evidence size, 3
  lessons, what is tested next, "is it improving" (rolling calibration and the recommender vs RC1).
- **Dashboard** (omenix-dashboard, private): drill-down per driver, road and record; a **driver report card** in plain
  words ("PS1: 46 trades, made money in calm weeks, lost in jumpy ones; worse than buy-and-hold so far").
- **Owner touch:** an optional "I followed this" mark (package D's journal, optional) recorded as its own write-once
  record; a plain glossary (iron condor, credit, worst loss, confidence) linked from every report.
- Slack: only these three reports (#fno-forecast) and failure alerts (#fno-desk).

### 7.3 Banner

| Colour | When |
|---|---|
| Red, do not trade real money today | any capture or quality failure on the recommended roads, an extreme road (VIX up over 20%, scheduled major event), regime detector fired, or no candidate |
| Amber, paper only | the default; every day until a recommended trade's driver version has passed RM1 |
| Green, consider by hand | the driver version passed RM1's frozen gate, its calibration error is at most 5 points over at least 200 scores, the cell is Confirmed and not expired, and no red condition |

## 8. The simulator

### 8.1 What history supports which roads

| Road | History | Data status (DATA_SPEND) | Use |
|---|---|---|---|
| NIFTY, BANKNIFTY options | daily closes 2019-2026 | spent or exposed | practice only |
| NIFTY options intraday | 15-min candles (last trades) 2019-2023 | **fresh** | intraday slot practice; one registered question at most |
| FINNIFTY (2021-), MIDCPNIFTY (2022-) | daily closes | not in the register: to be added | practice |
| Stock options | daily closes 2019-2026 | entry prices exposed (R2), outcomes not read | practice; thin strikes |
| Index and stock futures | daily OHLC 2019-2026 | stock event moves 2022-2026 fresh | stop tests via day high/low |

### 8.2 Pricing honesty rules

EDGE1's validity rule (a mark outside payoff bounds or a vertical outside [0, width] makes the day unusable for entry,
trigger and exit); a leg must have traded that day; fills at close plus a **spread penalty**: half the modelled spread
per leg at the **75th percentile** of the forward spread model for its bucket (underlying tier x moneyness x days to
expiry), plus C1 costs and the Rs 1 pad; futures stops fill at the stop or, if the day opened beyond it, at the open;
dated lots (LOT_CHECK) and dated STT; no data after the decision time.

### 8.3 Spread and slippage model

Learned only from our captures (indices from 13 Oct 2026, stocks from MS7): spread and displayed size per bucket, and
the gap between the witness quote and the next snapshot. Used by both the simulator and paper fills (9.5).

### 8.4 What simulator results may and may not do

May: plumbing tests, draft the map, set first thresholds before a card freezes, size sample plans, estimate correlation
between roads, exam roads, train and test the root-cause classifier. **May not:** licence a driver, move a cell past
Draft, set the banner, count toward RM1, or judge an AI driver.

## 9. Operational rules

**9.1 Safety laws (only these stop a paper trade):** protected structures only; options maximum loss Rs 10,000 incl.
costs; futures stop at 1% attached at entry; **daily stop**: a driver whose realised plus marked loss since the previous
close reaches Rs 25,000 opens nothing more that day, its futures close at the next mark, its option positions keep their
own exits (closing a capped spread at a wide quote only adds cost) [owner to confirm this reading]; ban list (no new
position in a banned stock; exits allowed); margin room (SPAN plus exposure x stress k, C2) within the driver's Rs 20
lakh; C2's open risk, bucket and new-risk caps; the quote gate. The 1.2 lakh drawdown brake today waits for the owner to
restart: proposed to suspend the driver until the monthly review instead [owner question].

**9.2 Futures honesty [some evidence, arithmetic]:** at VIX 15.7 NIFTY's daily standard move is about 1%, so a 1% stop
is touched often; stocks move 1.5-2.5% a day, so stock-futures stops fire on many days. A stop is not a maximum: a 4 Jun
2024-sized gap (about -5.9%) costs about Rs 87,000 on today's NIFTY lot, over 3x the daily stop. Gap losses are reported
separately and never hidden by the stop.

**9.3 Road quality gate ("road closed"):** before each slot every road is checked: capture complete, quotes fresh
(within 2 minutes of the slot), two-sided quotes on every candidate leg, no impossible prices, ban list and lots loaded, liquidity (9.7) and as-of inputs (9.6) pass.
A failing road is **closed** for that slot with its reason; no driver trades it, its tickets are void, and the instructor
learns nothing from it. Closures are counted per road and source so missing data cannot quietly bias results.

**9.4 Instrument housekeeping:** futures roll at the near expiry's T-2 session 15:00 (rule frozen per driver); corporate
actions (splits, bonuses, special dividends) from A12 and NSE's adjusted contracts: an affected road is closed on the
ex-date and positions are revalued on NSE's adjusted terms; lot-size and expiry-day changes read from A20a and NSE
circulars (A20b), never from config; a **versioned cost and tax table** (dated STT, stamp, exchange charges; futures
STT on sell side) replaces the single `charges` block, each record naming its table version.

**9.5 Execution realism:** buys at the ask, sells at the bid, plus the slippage model's 75th percentile until 60
sessions of evidence; size above displayed quantity is a partial fill (rest missed, recorded); a leg without a quote is a
failed fill and the whole entry is refused (E4c); margin checked per driver.

**9.6 Point-in-time honesty [strong reasoning; the factory's rule]:** every decision, live or simulated, reads only
data published before its decision time: as-of datasets with their publication times (participant OI only after its
measured release, A8; bhavcopy after its landing time, 18:40-19:46 on 15-21 Oct), sealed forecasts only (G13b seals),
and in the simulator **as-of F&O stock lists** (stocks enter and leave F&O; using today's list would drop the failures:
survivorship bias), as-of lots (LOT_CHECK), as-of ban lists (NSE archives) and as-of strike lists. A pack that cannot
prove the as-of time of an input closes the road.

**9.7 Liquidity per road:** a stock option road is open for a slot only if its candidate legs pass frozen thresholds:
spread at most 5% of the option's mid (or 1 tick plus 2% for options under Rs 10), and displayed size at least 1 lot on
both sides of every leg [first guesses, reasoning only; refit from 20 sessions of survey data before stock roads go
live]. Otherwise it is closed for that slot with the reason "illiquid".

**9.8 Overnight and holiday carry:** a position held overnight or over a holiday or weekend carries gap risk that no
stop can protect. The dashcam records each position's **overnight move** (previous close to next open mark) apart from
its in-session P&L. The futures stop is checked at the first mark after the open and fills there. The daily stop and the
Rs 10k cap cover the gap only for options (their loss is bounded); for futures the exam roads show the gap cost and the
owner decides on overnight futures (question 13.3).

**9.9 Reproducibility:** any day can be re-run from its records and gives the same decisions: drivers, cost table,
taxonomy, map snapshot, licence board and recommender are versioned and hashed into each decision record; random parts
(RC1, bootstrap) use seeds derived from day, driver and road; AI decisions are reproduced from their transcript
(re-asking the model is a measurement of variance, not a re-run). A nightly replay of a random sample of 20 decision
records must match byte for byte; a mismatch is a "rule broken" alert.

**9.10 Source outages:** Groww down: the stock survey uses NSE and the witness falls back to NSE's quote; NSE down:
Groww's chain plus depth quotes on candidate legs; both down or out of window: the road is closed ("source outage") and
alerted in #fno-desk. Never a silent gap and never a last-known price.

**9.11 Scale and timing budget:** each slot has a deadline: snapshot complete +5 min, decisions sealed +8 min, fills
+10 min (the 15:00 slot finishes by 15:20, inside today's desk timetable). Rule drivers on about 410 roads are cheap
(estimated well under a minute of compute [reasoning only]); the AI drivers and the stock survey are the risk. The dry
run measures each slot's wall-clock; a slot that misses its deadline closes its unfinished roads, it does not run late.

**9.12 Operations:** O1 runs each slot as steps with their own status; O8 health and O10 capture watch extended with
per-slot freshness rows; a missing slot is a recorded "road closed: capture", never a silent gap; a **cost meter** (BG1
usage ledger) for AI tokens and minutes and for compute and Drive per day, shown in the dry run; BG1's stop at 100% is set
to measure-only for the fleet while the owner's "no limit" holds (a lane-1 config change).

**9.13 Physical settlement of stock F&O [strong: NSE settles stock futures and options by delivery since 2018-19;
`docs/DESK_DESIGN.md` E7].** A stock option in the money at expiry, or a stock future held to expiry, means taking or
giving delivery of the shares (lakhs of rupees) and NSE raises the margin on such positions in the last days before
expiry. Rule: every stock road closes positions by the session before the expiry week's physical-settlement margin rise
(the exact day comes from NSE's circular, read in MS0), and no stock trade opens inside that window. Index F&O settles in
cash and is not affected.

**9.14 No record, no trade; and an off switch.** If the dashcam cannot seal a decision (Drive down, receipt not pushed),
that decision is a recorded failure, never an unrecorded paper trade. The owner has one switch (a lane-1 config key)
that stops all new paper entries across the fleet; open positions keep their exits and records.

**9.15 Fresh data stays fresh.** The simulator runs by default only on data `research/DATA_SPEND.md` lists as spent or
exposed. Any run on a fresh window (NIFTY 2019-23 intraday candles, participant OI) needs a factory card first and
marks that window exposed in DATA_SPEND; otherwise one casual simulator run would use up the last untouched history.

**9.16 Source terms.** About 800 NSE chain requests a day (200 stocks x 4 slots) is far more than today's few. MS0 reads
NSE's website terms of use and Groww's API terms for automated reading at this volume; if either forbids it, the stock
survey uses only what is allowed (fewer slots or Groww only) and the design says so. Nothing is read by evading a block.

**9.17 Net of income tax, shown once.** All rupees are before income tax. F&O profit in India is taxed as business
income at the owner's slab rate [some evidence, general rule; the owner's own rate unknown]. The Saturday report shows
the after-tax figure once, at an assumed rate the owner sets, because a small paper edge can vanish after tax.

**9.18 Expiry-day margin rules [some evidence: SEBI's index-derivatives circular of 1 Oct 2024; to be re-read in MS0].**
On an expiry day short index options carry an extra 2% extreme-loss margin and same-day calendar offsets lose their
margin benefit. The margin law (9.1) uses the dated rule set, so PS9 and CD1 are not shown as cheaper than they are.

**9.19 The v4 freeze comes first.** Nothing of the school changes `DAILY_RUN_STEPS`, the weather or the v4 forecasts
until the owner has signed v4's freeze (clean days 2 and 3: Fri 23 and Mon 26 Oct). School steps then join the daily run
as new steps after v4's, never inside its frozen files.

**9.20 One recorded day as the acceptance test.** Before the first road test, the whole school is run on one already
recorded day (its captures and packs) twice; both runs must give identical records, and the decisions are checked by
hand against each card. This is MS2's exit test.

**9.21 Plan at 08:50, booking at the slot.** The 08:50 "Today" list is a plan from yesterday's data with indicative
prices; nothing is booked then. Each trade is booked at its driver's slot at that slot's quotes, or dropped with the
reason ("quotes moved", "road closed"); the 20:05 report shows plan against booked, so a plan that never fills is
visible.

## 10. Build stages, effort and dates (all reasoning only)

| Stage | What | Builder days | Judge days |
|---|---|---|---|
| MS0 | capture probes (Groww chain, per-type limits, NSE equity chain, candles), work-register rows, S1/RM1 amendment text | 3 | 1 |
| MS1 | school core: roads, fleet runner, per-driver accounts, safety laws (daily stop, futures stop, ban list), quality gate, dashcam schema and store with sealing | 8-10 | 4-5 |
| MS2 | index option roads at the 15:00 slot, 14 index-option drivers, BH, N0, RC1, KL1 | 8-10 | 4 |
| MS3 | 08:50 and 20:05 school sections, banner (amber and red only), glossary | 3-4 | 2 |
| MS4 | instructor v1: attribution, root causes, road comparison, map, calibration, Saturday report, licences | 8-10 | 4 |
| MS5 | Groww conductor, slots 09:30, 12:15, 15:20 for indices | 5-7 | 3 |
| MS6 | futures roads (index and stock), LTP marks, stops, roll, futures costs, FT1-FT7 | 6-8 | 3 |
| MS7 | stock option roads: NSE survey plus Groww witness, results tags, corporate actions, stock drivers | 10-14 | 5 |
| MS8 | simulator for all roads, spread model, exam roads (parallel from MS1) | 8-12 | 3-4 |
| MS9 | AI drivers AI1-AI5, dry run, transport decision | 6-9 | 3-4 |
| MS10 | recommender, fleet stress, regime detector, map ageing, dashboard pages (plus W3 work in omenix-dashboard) | 6-8 | 3 |
| **Total** | | **71-95** | **36-42** |

With 4 builders in parallel the **judge is the bottleneck**: one code judge needs about 7-9 weeks for 36-42 days, two
about 4-5 weeks. Assumed dates: ChatGPT review and owner sign-off by 27 Oct; **first road test, index options at 15:00
with rule drivers: earliest Wed 11 Nov 2026 (10 Nov is a holiday), realistic Mon 16 Nov**; first Saturday report 21 Nov;
AI drivers on indices after a 5-session dry run, about 23-30 Nov; futures roads about 30 Nov; stock option roads after
10 sessions of clean capture, about 14 Dec; full fleet at all slots about end of December. Earliest Supported cells: stock
event roads about Feb-Mar 2027; index cells 6-12 months or more. No green banner before mid-2027 at the earliest.

**AI dry run (5 sessions, not counted):** AI1-AI5 on the 4 indices and the 20-stock shortlist at the 15:00 slot;
measure tokens and minutes per call and per day, latency against the slot deadline (8 minutes), failure rate, transcript
audit, repeat-answer variance on 20 decisions, and spread of confidences; the owner then sets the budget.

**Programme stop rule (frozen before the first road-test day; numbers reasoning only, for the owner to fix):** at the
review after **9 forward months** (about Aug 2027 for indices), if **no licensed driver** beats BH and RF after costs on
its paired, date-clustered 80% interval, and the recommender does not beat RC1, the school concludes "no edge found under
these rules and caps" in a written report. Then: captures and forecasts keep running (cheap), the fleet shrinks to the
benchmarks plus at most 5 drivers, AI drivers stop, and no new driver family is added without a new owner decision. A
second check at 15 months covers the slower index roads. The rule is never relaxed because time passed.

**The owner's own ideas:** the owner describes a driver in plain words in chat or Slack; a builder writes it as a card
(entry, structure, exit, roads) and reads it back to the owner in plain words for approval; it then enters as a
**learner** like any other driver, with the same exams, licence rules and safety laws, and counts toward the 5 new
versions a month.

**Cancelled or re-scoped:** the desk freeze is cancelled (`desk.frozen` stays off); Books 2 and 3 are un-paused and
become AI4 and AI1-AI3; Book 1 becomes the rule fleet (one playbook version per driver); response 324 is superseded;
package D's journal becomes the optional "I followed this" mark; the 21 Oct Innovation Lab and FL1's "10 lab positions"
are implemented by the school, not built twice; scoreboard B (S2) becomes the fleet board; RM1's evidence record and S1
are amended from "Book 1" to "driver version" (lane 1, judged). Kept: Rs 10k cap, no naked legs, v4 freeze, data spend.

## 11. Risks and honest limits

| Risk | Why it matters | Mitigation |
|---|---|---|
| Learning fast is not making money | EDGE1 and the earlier ledger trials found no edge after costs [strong] | expectation set in every report; review at 3 and 6 months whether to continue |
| Correlated roads | 200 stocks on one day are 6-42 bets, not 200 [some evidence, BR1]; the 4 indices move together | date-clustered statistics, effective sample shown, claims per family |
| Simulator optimism | closes, stale prices, no historical bid/ask | validity rule, 75th-percentile spread penalty, simulator never proof |
| False patterns | thousands of map cells and many versions | pre-registration, one look, FDR and Holm, 3-driver agreement, RC1/KL1 in every test, 5 versions a month |
| Paper fills too kind | queue, size, latency, manual owner | touch fills plus slippage, partial fills, E8 60-minute view on the top 3 |
| Futures gaps | 1% stop is not a maximum | gap losses reported apart; owner may restrict futures drivers to same-day |
| Missing data bias | drivers skipping bad roads look better | road closures counted, void for everyone |
| Groww and NSE limits | one key; NSE may block | conductor, probes first, Groww fallback, alerts |
| AI cost and drift | unknown cost, same input different answer | dry run, pinned versions, transcripts, measured variance |
| Owner reads paper wins as permission | the classic retail trap | amber until RM1, "Paper" on every figure, red on doubt |
| Regime | months of forward data may be one market mood | evidence dates, map ageing, regime detector |
| Complexity and judge load | 77,008 production lines already (cut-list); this adds roughly 15-25k | drivers as data on one judged engine, staged build, monthly batch of driver cards |
| Public repository | internals would leak | Drive only, receipts in GitHub; the dashboard shows what a driver decided and its results, never its rules (omenix-dashboard privacy rule) |
| Stock delivery | a stock option or future held to expiry means delivery of shares | close before the physical-settlement window (9.13) |
| Winner's curse | the best of 40 drivers is partly luck | shrunk estimates in the recommender, planted-edge and RC1 tests |

## 12. Questions for ChatGPT (review 138)

1. Is the split of **account trades** (capped, shown in rupees) and **tickets** (every road, 1 lot, measurement only)
   sound, or does it invite learning from trades that were never possible?
2. Is the same-road comparison (road score = family median of return on risk, date-clustered residuals) the right way
   to separate hard roads from bad drivers? Would a mixed model with day and road effects be better and still simple?
3. Are the condition-map statuses (FDR 10% for Supported, Holm 0.05 plus a second window for Confirmed, 3 drivers of 2
   families) too strict or too loose given 6-42 effective bets a day?
4. Licence numbers (40 trades, 30 sessions, 100 calibration scores): what would you set, and how should calibration be
   judged with so few scores?
5. Is the driver catalogue missing a family that the house rules allow, or carrying one that is pointless (for
   example FT6 with a 1% stop on stocks)?
6. Is the 75th-percentile spread penalty a fair simulator rule when no historical bid/ask exists?
7. Should AI drivers run through the Claude API rather than scheduled sessions, and how should their non-determinism be
   scored?
8. The daily-stop reading (no new entries, futures closed, option positions keep their exits): agree?
9. Is the green-banner rule (RM1 passed, calibrated, Confirmed cell) right, or should green be unreachable by design?
10. What would you cut first if the judge capacity stays at one code judge?
11. Any risk we are not seeing in running about 40 drivers on about 410 roads at 4 slots?

## 13. Owner questions (for after ChatGPT's review)

1. Approve adding the "Today" and "How did today go" sections to the signed-off 08:50 and 20:05 pages?
2. Drawdown brake: suspend the driver until the monthly review instead of waiting for your restart?
3. Futures: allow overnight holding (gap risk above the stop) or same-day only?
4. A second Groww API key, if Groww allows one, to split the load?
