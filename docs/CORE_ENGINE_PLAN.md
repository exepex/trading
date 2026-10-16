# Core engine plan: the owner's goal, what delivers it, what is missing, what to drop (16 Oct 2026)

Written for the orchestrator (session_01VG1RqxLFUVdvvPuMRYZtDH) and the plan judge, on the owner's request of
16 Oct: "all the core engine functionality, data generation, evidences, they must align to my end goal and my
expectations." It reads together with `docs/CORE_ENGINE_GAP_AUDIT.md` (the data and story audit of the same day) and
does not repeat its tables. State checked on `origin/main` 986b5993 and the story branches on 16 Oct (revision 4: owners from the
orchestrator, 16 Oct; D3, D4, D5, O1, R1b, R1c and G8 merged; judge 305 add. 1 answered; the go-live gate, DESK_DECISIONS row 247). Response 267.

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
| E17 | Once live, no issues anywhere | "once the system is up and running and live then I don't want any issues whether it's related to core engine or fetching data from external sources"; "10-day trial (Recommended)" (row 247) |


## Definition of done: the go-live gate (owner, DESK_DECISIONS row 247)

The core engine is **done** only when both hold:
1. **O11 green and judged** with **zero expected-missing rows**: every strict xfail in
   `tests/e2e_acceptance/test_expected_missing.py` has become a real, passing check.
2. **10 trading days in a row of full live capture and daily runs with zero silent failures.** A silent failure is
   missing data or a skipped step with no alert and no record, and it restarts the count at day 0. An alerted,
   recorded and root-caused failure does not restart it, and re-fetching corrupted or missed external data is
   allowed. "Live" also needs the owner's routine, every `daily.live_from` date set, and the v4 freeze.
   Books recording "no trade" because nothing is approved is correct behaviour, not a failure.

Until then, every "done" in this plan means "merged and judged", never "live".

## (b) Traceability: expectation → stories → state → owner → how the 10-day trial evidences it

Owner sessions shortened to their first 8 characters (full ids in `docs/WORK_REGISTER.md`). States on 16 Oct
[strong]. "Trial evidence" is what the 10 days must show, read from committed records, every day of the 10.

| # | Stories (state, owner) | Trial evidence (every day of the 10) |
|---|---|---|
| E1 net profit | C1, E1/E1b, E2c/E2d, E7, S6 (merged) | Scoreboard B per book: net after charges, pads and 31.2% tax arithmetic, with a marks row per open trade; O11 checks the chain once, the trial daily |
| E2 three books | Book 1: D1-D3, D6, E5 (merged); D4, D5 (merged); Book 2/3 orders and exits (F5, F6); model reporting (F1t); D3 no override (merged as e5906769, judge 300; F4's "no paper override" text merged after it); **F1t** (01PLbKH1); **F5** (01SFDjjZ); **F6/F7** (01KTAQCD) | A decision record per book per session: Book 1 from D2, Books 2 and 3 from F1t's sealed AI answers with the model served recorded ("no approved strategy" counts); zero books missing from the run log |
| E3 scoreboards | S2, S3, S6, E6, F9a (merged); E6b (text, 0134MoC6); S1 freeze (0185gR5D) | Boards A and B built every day from the same common pack's SHA-256 for all three books |
| E4 forecasts | G1-G5 (live); G7, G7b part a, G8, G9, G10 part 1, M1 (merged, not live); **G6 freeze** (01MgTu3L); G10 part 2, G7b b-c (01VK88Lx, 0185gR5D); G11 (round 1 PASS, 01XFXpbk); **G13** (01UkTaDe) | Weather and every v4 row written live before 14:30 (needs the 14:05 start and `live_from`); the AI books' v4 rows; a G13 valuation record from the 3 pm chain |
| E5 daily card | T1, T2 (merged); T3 (0145TfSw); M2 (text); **T1c: card reads M1's weather** (no owner: the card still prints "M1 pending") | One card per session in #fno-desk by about 15:08 (delivery log), TRADE or NO TRADE with its reason and M1's colour |
| E6 paper, timing | E3, E4/E4c/E4d, O1 (merged); **E8** (branch, parts 1a-1b PASS, 01H1CmuW); LM1 (012eM7Ti) | Each card's fills at R = 5, 30 and 60 minutes (or "missed") recorded the same or next session |
| E7 risk | C2-C5, C2c, C2d, A14c part 1 (merged); A14c part 2 and per-family k (01Vm1WnH); STR1b-2 (01BYjW9a) | A C2 and C4 verdict in every chosen record; no trade above Rs 10,000 or a bucket cap; the over-cap card hold never fires |
| E8 real money | RM1 (merged); RM2 (text, 01CHxE3y) | Nothing to show in 10 days: the gate stays shut. The trial proves the engine, never an edge |
| E9 external data | A1-A17, A4b, A4c, A16, O6, A12 (merged); **O10** (013YJ5gj, part 1 with the judge); **A19 news** (01Qj3wtY); **A20 circulars, masters, macro dates** (013u1Ac2); **A17 schedules** (01MBnbVU); O9 (01WHmxEY) | Every capture job leaves one daily row (ok, or failed with its alert) in O10's file; zero days without a row for any source |
| E10 alert and record | AlertSender, O1's `Alerted`, O8/O8b/O8c, A16 heartbeat (merged); O2 (text PASS, code after O1, 014zYLf1); O10 | Each failure in the 10 days has its alert and its committed row and is root-caused in the conversation log; one silent failure restarts the count |
| E11 evidence | Judge lanes, S1, G8 looks; **O11** (this session, with the judge); O8 health check (first run due 16 Oct 17:51 IST) | O11 green with zero xfails at the trial's start; O8's daily health message every evening, its own absence caught by O10's staleness alert (O11 xfail "O10") |
| E12 AI analysis | **F2** volatility analyst first (01WSMMv5); F6 (01KTAQCD) | One analyst finding card per session, used by Book 2/3's sealed decision |
| E13 learning | LR1 weekly post-mortem (merged; owner's routine pending); LR3 (text, 01SFDjjZ); LR2 (paragraph, no owner) | Two Saturday post-mortems inside the 10 trading days |
| E14 costs | F8/BG1 (merged); **F8c** usage per routine (0134MoC6, with G11) | Each AI routine's minutes recorded per session; the budget meter under the cap |
| E15 simplicity, no broken code | code-size test, gates, judge; O11; **O12** number claims (01KS9xBc) | Gates green on every merge in the 10 days; zero xfails |
| E16 no UI now | P/W work finishing, then stopping (row 238) | No new screen work in the trial's commits |
| E17 no issues once live | the go-live gate itself | The 10 days |

## (c) Gaps: what was ownerless is now owned (orchestrator, 16 Oct), and what is still open

| Gap | Owner now | Still open? |
|---|---|---|
| Books 2 and 3 in the daily run (F1t: `ai_fire`, `ai_collect`, sealed decisions) | 01PLbKH1 | text |
| D3 refuses any `owner_override` | 01SFDjjZ | merged as e5906769 (judge 300); O11 checks it on the recorded day |
| **Book 2's orders and exits** in the daily run (E3 takes each book's `OrderBuilder` and `ExitRules`; only Book 1's exist) | F5, 01SFDjjZ (orchestrator, 16 Oct) | text |
| **Book 3's orders and exits** | F6, 01KTAQCD | text |
| **Model reporting** (`model_served`, `session_id` in each AI decision record) | F1t, 01PLbKH1 | text |
| **Capture health before the trial** (judge 305 add. 1): (1) `health-check.yml` has no run yet; (2) `nse-margins.yml`'s 03:30 cron has never started (1 scheduled run ever, 16 Oct 07:12 UTC, about 5 h late); (3) `participant-oi-release.yml`'s second slot is cancelled each evening | (1) O8, 012eM7Ti; (2) A14, 01Vm1WnH; (3) O10, 013YJ5gj, until the orchestrator names A8's owner; every one also O10's staleness alert | open: see step 2b. On (1): O8 reached `main` at 2026-10-15 18:46 UTC, after that day's 12:21 UTC slot, so its first scheduled run is due 16 Oct 12:21 UTC (17:51 IST). "0 runs" is not yet a failure; no run by 18:21 UTC is |
| F5 Book 2 decider on D4's narrow envelope | 01SFDjjZ | text |
| F6/F7 Book 3 decider and matched shadows on D5 | 01KTAQCD | text |
| F2 analysts, volatility first | 01WSMMv5 | text |
| O10 capture failure rows plus alerts | 013YJ5gj | part 1 with the judge |
| A19 news; A20 circulars, F&O masters, macro dates | 01Qj3wtY; 013u1Ac2 | text |
| G13 valuation and price distribution | 01UkTaDe | text |
| F8c AI usage per routine | 0134MoC6 (folded with G11) | text |
| A17/A15 schedules | 01MBnbVU | with judge F |
| **T1c: the card reads M1's weather record** (found by O11: `fno/cards/weather.py` still prints "M1 pending" and blocks trades; M1's text left T1 out) | T1/T2 builder 0145TfSw (orchestrator, 16 Oct) | text: one `WeatherSource` adapter over `WeatherRecords.for_day` plus one wiring line |
| **O1 start at 14:05** (known: the 14:33 start misses the 14:30 forecast cutoff, proven in O11's failure test) | owner decided (DESK_DECISIONS, 16 Oct): the owner moves the routine once G10's pack code (b) merges, about 19-21 Oct; O1's follow-up (captures as child processes at the run's start) with judge D | open until moved |
| **`daily.live_from` dates** for margin check, weather, v4 forecasts, card | owner, set as the **first step of the 10-day trial** (orchestrator, 16 Oct) | null until the trial starts |

## (d) Built or planned but serving no expectation now

| Item | Recommendation |
|---|---|
| P2a-h read-model pages, W3 screens, contract pins | Finish only what is judged; start nothing more (row 238) |
| BR1 breadth code beyond the freezer | Defer: claims failed their own null check; descriptive only (row 231) |
| G7b parts b-d (V2-V5) | Defer past the books: V2 alone needs 8-22 years of outcomes (row 214) |
| LR3, F9 shadow firing, M2 price of calm, RM2 code, LM1 round 2b | Keep texts, build no code until the first real paper trades |
| Four F2 analysts at once; F3 red team as its own story | One analyst first (now the F2 owner's plan); fold F3 into T3. F4 stays: its text was amended to "no paper override" and it is being built (owner decision; builder 01AN94h4); I withdraw "drop F4" |
| A12 full-history filings | Keep the cheap job; build no consumer now |
| `quote-recorder-nse.yml` | **Kept** (orchestrator: the owner's NSE fallback; I withdraw "retire"). But a fallback that fails every day is no fallback: its failures must reach O10's rows and alerts, and O11's finding 2 (NSE contract IDs refused by C5's buckets) must be fixed before it can ever feed the desk |
| Judge paperwork per tiny change | 257 judge files in 5 days; the owner asked "are we ... making it over-engineered, over-complicated?" (15 Oct:336). Keep lane 2 and 3 as written; add no review layer |

## (e) Order to finish, with the critical path

Critical path (each arrow a hard dependency) [strong for the dependencies, reasoning for the order]:

**F1t → F5 (Book 2's decider, orders, exits) → F6/F7 (Book 3's) → E8 merge → capture health (2b) → owner switches (routine at 14:05, `live_from` dates, G6 v4
freeze) → O11 zero xfails, judged → 10-day trial with zero silent failures = done**

| Step | Work | Owner | Parallel with |
|---|---|---|---|
| 1 | F5; F1t; F6/F7 | 01SFDjjZ; 01PLbKH1; 01KTAQCD | 2, 3 |
| 2 | External data first, because history is lost daily: O10, A17 schedules, A19, A20 | 013YJ5gj, 01MBnbVU, 01Qj3wtY, 013u1Ac2 | everything |
| 2b | Capture health before the trial, each with a **first run verified** row under O8/O10 (orchestrator, 16 Oct): health-check's first slot 16 Oct 12:21 UTC (no run by 18:21 UTC is the failure); nse-margins' early cron first runs the night of 16 Oct (A14's catch-up crons with judge D); participant-OI's cancels fixed in O10. Then: O8's first runs seen (or fixed); nse-margins' early cron starts or moves to a time GitHub honours; participant-OI's second slot root-caused; O10's staleness alert proven on a job that never started (its O11 xfail turns real) | 012eM7Ti, 01Vm1WnH, 013YJ5gj | 1 |
| 3 | E8 merge, then E6b code, R3 part B | 01H1CmuW, 0134MoC6, 0145TfSw | 1 |
| 4 | O1's 14:05 start; T1c card weather | 014zYLf1; needs an owner | 1 |
| 5 | G6 v4 freeze → G10 part 2 pack → G11 merge, M1 live, G7b b-c | 01MgTu3L, 01VK88Lx, 01XFXpbk, 0185gR5D | 1 |
| 6 | F2 volatility analyst; G13; F8c | 01WSMMv5, 01UkTaDe, 0134MoC6 | 1 |
| 7 | S1 freeze (needs E8, S3/S6 code, cash rate, E8 switch) | 0185gR5D | after 3 |
| 8 | Owner: routine time, `live_from` dates, A16 and LR1 routines, secrets | owner | after 4, 5 |
| 9 | O11 turns each xfail real as its story lands, then is judged with zero xfails; O2 over O1 | this session; 014zYLf1 | from 1 |
| 10 | **10-day trial**: day 0 is the owner setting every `daily.live_from` date; any silent failure restarts the count | everyone | last |

Plainly [reasoning]: Books 2 and 3 will record "no approved strategy" every day until R1/R3 qualify one (row 239).
A finished engine is not the same as an engine that trades, and the 10-day trial proves reliability, not profit.

## Found by the O11 replay (16 Oct, [strong]: reproduced in `tests/e2e_acceptance/`)

- **Book 1 works end to end on real data, under O1's run.** On NSE's real 16 Oct chain, a test version passed real
  C2/C5 risk and every C4 check, filled 4 legs, was marked, and reached E6's reviews, the scorecard and both
  scoreboards. This proves the parts fit. It proves nothing about profit.
- **At the routine's stored 14:33 start, no live forecast can ever be made.** The weather and v4 steps are refused
  (after 14:30) and alerted every day. This is the known O1 follow-up (the 14:05 start).
- **The card's weather is not wired to M1** (gap T1c above).
- **The NSE fallback cannot feed the desk.** NSE's contract IDs parse as underlying `OPTIDXNIFTY` in C5's bucket map,
  so every trade would be refused.
- **A restart after 15:00 logs a false pack failure.** The private pack holds the book's decisions folder, so a
  rebuild after the decision differs and is logged "built: False". No trade is affected. For O2's kill-and-rerun.
