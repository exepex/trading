# Core engine plan: the owner's goal, what delivers it, what is missing, what to drop (16 Oct 2026)

Written for the orchestrator (session_01VG1RqxLFUVdvvPuMRYZtDH) and the plan judge, on the owner's request of
16 Oct: "all the core engine functionality, data generation, evidences, they must align to my end goal and my
expectations." It reads together with `docs/CORE_ENGINE_GAP_AUDIT.md` (the data and story audit of the same day) and
does not repeat its tables. State checked on `origin/main` 9dbf1b3f and the story branches on 16 Oct.

Evidence labels: **[strong]** read from files, branches or the judge index; **[some]** partial evidence;
**[reasoning]** judgement only. States: **merged** (on `main`), **branch** (code on a story branch, not merged; the
judge verdict named), **text** (story text only), **missing** (no story text anywhere).

## (a) The end goal and the expectations, each with its source

**End goal.** "End goal is net profitability, but I want to run it as an experiment first." (conversations/
2026-10-12.md:12) The tool is "a research tool for myself" (12 Oct:961), "not for general public" (12 Oct:967),
whose "sole responsibility ... is high quality predictions and ... avoid bad trades ... warn me at the right time when
to invest and when not to invest" (15 Oct:579). Shared goal row (DESK_DECISIONS, 12 Oct): "net profitable F&O trades
(after charges, slippage and tax), found from data and proven on paper".

| # | Expectation | Owner's words (source) |
|---|---|---|
| E1 | Net profit after every charge and the 31.2% tax is the only success measure | "Everything must be measured as net profit after STT, state and central tax, transaction charges and brokerage" (12 Oct:194, condensed in log); tax row, DESK_DECISIONS 12 Oct |
| E2 | Three books proved side by side: rules, hybrid, AI team | "One is only role based, no AI ... second ... rule based but ai back ... third is fully ai based" (12 Oct:1580); "we have to prove with both of them" (12 Oct:1567) |
| E3 | Two fair scoreboards over the same data and timeline | "all 3 strategies on both scoreboards ... A, same opportunities ... B, whole system" (12 Oct:1612); "all family strategies follow the same timeline otherwise ... the comparison will not be fair" (15 Oct:506) |
| E4 | Scored forecasts, movement size first, prices too | "Agree to make predicting movement size the main focus" (14 Oct:1130); core engine covers "forecasting, evidences, prices, price forecasting, valuation, comparison" (DESK_DECISIONS 16 Oct, row 244) |
| E5 | A daily answer: trade, or no trade with the reason, warned in time | "warn me at the right time when to invest and when not to invest" (15 Oct:579); design v2 one-page: one Slack card about 15:05 (OWNER_SUMMARY) |
| E6 | Paper first on live data; realistic fills at the owner's reaction time | "first, paper trading on live data" (12 Oct:204, condensed); "earliest - within 5 minutes, average - 30 minutes and worst 1 hour" (15 Oct:30) |
| E7 | Hard risk limits: Rs 10,000 a trade, defined risk only, Rs 20 lakh paper account and its buckets | "C, go with ₹10,000 max loss per trade" (12 Oct:1209); "Paper account size Rs 20 lakh ... => YES" (14 Oct:1130); risk buckets row (15 Oct) |
| E8 | No real money without a stricter, pre-written proof | "if paper trading cannot show evidence of winning ... no real money used" (12 Oct:733, condensed); "a stricter bar for real money => I accept" (15 Oct:50) |
| E9 | External data captured every day, up to date, never lost | "the data that we capture from other sources, it must be up to date. That is non-negotiable" (DESK_DECISIONS row 246); "news, NSF uh, data, filings ... future and options, trades" (row 245) |
| E10 | Every failure alerts and is recorded | "we must notify that something failed. Error case needs to be captured properly so that we could fix them" (row 246) |
| E11 | Accuracy and evidence over luck; every claim validated | "our goal is more accuracy rather than luck" (handover 15 Oct:154); "I don't want any surprises. Every claim must be validated" (row 246) |
| E12 | AI does the heavy analysis, but the core must stand without it | "AI should do the heavy lifting ... read everything, link dots" (12 Oct:401, condensed); "if our core ... is not good enough ... AI will [not] help much" (12 Oct:930) |
| E13 | Learn from every day: post-mortems, why it was wrong | "Paper trade every day, record, analyse ... find what went wrong and why" (12 Oct:404, condensed) |
| E14 | Costs low: AI budget capped, polite free sources | "can we do it without costing any extra or unnecessary AI tokens" (13 Oct:451); monthly AI budget row (15 Oct) |
| E15 | Simple design, no broken code, nothing half-built | "we do not over-engineer and over-complicate the design. Simplicity is also our priority, but not the product quality"; "No broken code"; "there must not be anything that is not implemented" (row 246 and the 16 Oct brief) |
| E16 | Core engine first; no UI or UI-facing API now | "We don't do any UI work, any API work for now" (row 244) |

## (b) Traceability: expectation → stories → state → owner session

Owner sessions shortened to their first 8 characters (full ids in `docs/WORK_REGISTER.md`).

| # | Stories that deliver it | State [strong unless marked] | Owner |
|---|---|---|---|
| E1 net profit | C1 ledgers, E1/E1b accounts, E2c/E2d fills and marks, E7 settlement, S6 do-nothing gate | merged | various |
| E2 three books | Book 1: D1-D3, D6, E5, E5b | merged, **not running** (O1 not merged) | 0134MoC6 |
| | Book 2: D4 envelope | branch, judge 260 add. 2 PASS, not merged | 01SFDjjZ |
| | Book 3: D5 constitution | branch, judge 263 add. 2 PASS, after D4 | 01SFDjjZ |
| | D3 override refusal (decided 16 Oct row 229) | **missing** | none |
| | F1 trading runner, F5 Book 2 decider, F6 Book 3 decider, F2 analyst cards, F7 matched shadows | text (first-plan text, predates D4/D5); rewrites named in row 246 | **none** |
| E3 scoreboards | S2 board B, S3 board A, S6 measures, E6 scorecards, F9a role value | merged | 0185gR5D, 0134MoC6, 01SFDjjZ |
| | E6b missed executions | text; code waits for E8 | 0134MoC6 |
| | S1 protocol freeze (counting starts only after it) | text collecting, 15 items | 0185gR5D |
| E4 forecasts | G1-G5 (v2/v3, live since 14 Oct) | merged, live | — |
| | G6 v4 freeze | branch, waits for the G6 session | 01MgTu3L |
| | G7 phase 1, G7b part a, G8, G9, G10 part 1 | merged (v4 back-fill only until the freeze) | 0185gR5D, 01VK88Lx |
| | G7b parts b-c, G10 part 2 (14:30 pack), G11 AI books on v4 | branch or text | 0185gR5D, 01VK88Lx, 01XFXpbk |
| | M1 weather as a forecaster | merged, not live (`daily.live_from.weather` null) | 013xqaNT |
| | G13 price distribution and valuation record (row 246) | **missing** | none |
| E5 daily card | T1 card, T2 rule checks | merged | 0145TfSw |
| | T3 objections (TRADE/WATCH only) | text, after O1 | 0145TfSw |
| | M2 weather DANGER alert | text, waits for a judge | 0145TfSw |
| E6 paper, timing | E3 timetable, E4/E4c/E4d fills | merged | 0134MoC6 |
| | **O1 daily routine** (runs everything above) | branch, judge 178 add. 18 PASS, not merged | 014zYLf1 |
| | E8 owner-timing fills | branch, parts 1a-1b PASS, not merged | 01H1CmuW |
| | LM1 position monitor | branch, rounds 1-2a | 012eM7Ti |
| E7 risk | C2-C5, C2c, C2d, A14c part 1 | merged | 01Vm1WnH, 012eM7Ti |
| | per-family k (row 242), A14c part 2 (Groww margin check), STR1b-2 | text or not started | 01Vm1WnH, 01BYjW9a |
| E8 real money | RM1 gate | merged | 01CHxE3y |
| | RM2 test record | text | 01CHxE3y |
| E9 external data | A1-A17, A4b, A4c, A16, O6, A12 | merged; health in the gap audit Part A | various |
| | A19 news, A20 circulars, F&O masters, economic calendar; A17/A16b/VIX OHLC schedules | **missing** (named in row 246) | none |
| | O9 data to Drive | steps 1-2a merged, 2b next | 01WHmxEY |
| E10 alert and record | AlertSender, O8 health check, O8b/O8c, A16 heartbeat | merged | 012eM7Ti |
| | O10 capture failure alert plus committed error record (row 246) | **missing** | none |
| | O2 failure handling suite | text, after O1 | 014zYLf1 |
| E11 evidence | judge lanes, S1, G8 looks, O11 acceptance replay (this plan's story) | O11: text on story/o11-e2e-acceptance | this session |
| E12 AI analysis | F2 analysts, F6 portfolio manager | **none built**; only the two forecasters and the advocate exist | none |
| E13 learning | LR1 weekly post-mortem, devil's advocate | merged (owner's routine pending) | 0145TfSw |
| | LR3 drift CUSUM | text | 01SFDjjZ |
| | LR2 why-wrong reviews | REPLAN paragraph only | none |
| E14 costs | F8/BG1 budget meter and stop rule | merged; **book routines' usage not captured** (gap audit B2 item 8) | 0134MoC6 |
| E15 simplicity, no broken code | code-size test, gates, judge; O11 | merged; O11 makes "not implemented" a test list | this session |
| E16 no UI now | P2a-h, W3, F&O screens | in flight work finishing, then stopping (row 238) | 013xqaNT, 0134MoC6, 01XFXpbk |

## (c) Expected but covered by no story, with the smallest story for each

| Gap | Why it matters (expectation) | Smallest story proposed |
|---|---|---|
| **G1x. Books 2 and 3 have no daily step** | E2: O1's steps run Book 1 only [strong]. Without this, D4/D5 never decide anything | **F1T** (F1's trading part plus one O1 step per book): fire the AI decision session with the private pack, collect the answer, validate it against D4/D5, run C2/C4, hand to E4/E8. Fake AI answer in tests. One story, not three |
| **D3 owner_override refusal** | E8, decided row 229, precondition in D4's table | **D3c**: D3 refuses any non-empty `owner_override` for every book; one test per book. S |
| **Book 2 decider (F5) on D4's narrow envelope** | E2 | **F5 rewrite**: prompt plus output schema for the five actions only (follow_rule, choose_strategy, no_trade, choose_width, reduce_lots); the rule default comes in the private pack. S-M |
| **Book 3 decider (F6) on D5's registry** | E2, E12 | **F6 rewrite**: proposer and decider on D5's registry, propose day d, trade from d+1, pilot label. M. F7 (matched shadows) folds into F5/F6 as one field each, not its own story [reasoning] |
| **AI analyst roles** | E12 | **F2 v1 = one analyst first** (volatility analyst, the main focus), not four. Add others only when F9 can measure the first one's value [reasoning] |
| **Price distribution and valuation record** | E4 (row 244: "price forecasting, valuation") | **G13**: a daily NIFTY range record (quantiles from the 3 pm chain's implied distribution, a fair-value line per traded contract), recorded and scored, not traded. S-M. Regenerable from captured quotes, so after the books |
| **Capture failure records** | E9, E10 | **O10**: every capture job writes one row (job, day, ok or failed, reason) to one shared file and alerts on failure or staleness through AlertSender. Extend O8's health check to read it; no second health system |
| **News, circulars, F&O masters, macro calendar** | E9 | **A19** news (source, terms, first-seen, Drive), **A20** circulars plus `fo_mktlots`/ban list plus macro dates. These lose history daily, so they run in parallel with the engine work |
| **Scheduling built sources** | E9 | **A17s**: one workflow each for A17 global cues, A16b daily catch-up and the VIX OHLC append. S |
| **AI usage of the book routines** | E14 | **F8c**: each G5 routine records its own start and end minutes now (G11's timing record pulled forward). S |
| **End-to-end proof** | E11, E15 | **O11** (this session): the acceptance replay below |

## (d) Built or planned but serving no expectation now (be blunt)

| Item | Why it is a candidate to drop or defer | Recommendation |
|---|---|---|
| P2a-h read-model pages, W3 screens, contract 2.x pins | E16: no UI now; mockups not approved (row 243) | Finish only what is judged; **start nothing more** (already the rule). Defer P2c onward |
| BR1 breadth track | Its claims failed their own null check; now "descriptive only" (row 231) | **Defer** further BR1 code after the freezer generalisation; it produces no claim |
| G7b parts b-d (V2-V5) | V2 alone needs 8-22 years of outcomes (row 214) | **Defer** past the books; keep part a |
| Two forecast protocols live side by side (v2 and v4) | Double scoring and double capture until v4 freezes | Keep until the G6 freeze, then retire v2's AI run (row 227 already does) |
| LR3 CUSUM drift, F9 role value, M2 price of calm, RM2 | Need trades or roles that do not exist yet (no approved strategy; registry holds B0 only) | **Keep the texts, build no code** until the first real paper trades exist |
| LM1 position monitor round 2b | No open paper position | Defer 2b until the first position (already its plan) |
| Four F2 analyst roles at once | Cost (E14) and no way to value them yet | **One** analyst first (section c) |
| F3 red team, F4 AI judge | T3 reuses the advocate; overrides dropped | **Drop** F3 and F4 as separate stories |
| A12 full-history filings for Nifty 500 | Serves the equity-research analyst, which does not exist yet; F&O core does not read it | Keep the job (cheap, Actions), build no consumer now |
| `quote-recorder-nse.yml` | Superseded by the routine step; fails daily (gap audit) | **Retire** |
| Judge paperwork per tiny change | 257 judge files (with addenda) in 5 days; the owner asked "are we ... making it over-engineered, over-complicated?" (15 Oct:336) | Lane 2/3 as written; no new review layers |

## (e) Order to finish, with the critical path

Critical path to "all three books run end to end on paper" (each arrow is a hard dependency) [strong for the
dependencies, reasoning for the order]:

**O1 merge → D4 merge → D5 merge → D3c → F1T (Book 2/3 steps) → F5 → F6 → E8 merge → O11 green**

| Step | Work | Owner | Parallel with |
|---|---|---|---|
| 1 | Merge O1 (PASS), owner creates the daily routine; set `live_from` dates | 014zYLf1, owner | 2, 3 |
| 2 | Merge D4, then D5 (both PASS) | 01SFDjjZ | 1 |
| 3 | O10 capture failure records; A17s schedules; retire the NSE recorder; A19, A20 texts then code | new builder(s) | everything (external data first: lost daily) |
| 4 | Merge E8 part 1 (PASS), then E6b code, R3 part B | 01H1CmuW, 0134MoC6, 0145TfSw | 5 |
| 5 | D3c, then F1T, F5, F6 (one builder, in this order) | **needs an owner** | 4 |
| 6 | G6 v4 freeze → G10 part 2 pack → G11, M1 live, G7b b-c | 01MgTu3L, 01VK88Lx, 01XFXpbk, 0185gR5D | 4, 5 |
| 7 | S1 freeze (needs E8, S3/S6 code, item 12 cash rate, item 14 E8 switch) | 0185gR5D | after 4 |
| 8 | F8c usage capture now; F2 one analyst; G13 | new builder | after 5 |
| 9 | O2 failure suite over O1; O11 turns its expected-missing rows green one by one | 014zYLf1, this session | from 1 |

What the owner should hear plainly [reasoning]: Books 2 and 3 can be built and switched on end to end in paper mode,
but they will record "no approved strategy" every day until R3/R1 qualify one (row 239: built now, switched off until
a strategy qualifies). The engine being complete is not the same as it trading.
