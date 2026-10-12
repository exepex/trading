# Re-evaluation of the old AI desk plan against the approved desk design and stories

Status: **draft for owner and ChatGPT review** (12 Oct 2026). Owner's request: re-read the old AI layer plan
(`docs/AI_DESK_PLAN.md`, written before the team-of-experts design) and decide what the approved stories already
cover, what conflicts, and what is new, so no story or feature is built that contradicts another.

Sources compared: `docs/AI_DESK_PLAN.md` (old plan), `docs/WAVES.md` (waves 0-3, built for the old intraday desk),
`docs/DESK_DESIGN.md` v2.1 (approved), `docs/DESK_DECISIONS.md`, `docs/stories/` (28 approved stories).

## 1. The root difference

| | Old AI desk plan | Approved design v2.1 |
|---|---|---|
| Trading style | Intraday to 2-day **option buying** on ~200 underlyings, scans every 5 minutes | **Protected** NIFTY monthly trades (sell, buy or none), held 2-3 weeks |
| Decision time | All day: pre-market plan, live per-candidate calls, live news guard | **Once a day at about 3 pm** (owner decision); all-day watching only if proven useful later |
| Who decides | AI decides what and why; code keeps money rules; AI may skip, delay, or **exit early automatically** | Tested playbook rules decide; AI roles write evidence-backed finding cards; code applies rules; judge verifies |
| How rules change | Claude may merge rule changes itself within bounds (weights +/-50% a week, disable noisy rules, thresholds in ranges) | Any change to a decision parameter is a **new playbook version** through the research loop, judge and owner approval |
| How strategies are made | Idea -> spec -> backtest -> shadow paper -> promote if better | Research loop: ledger, frozen protocol, historical challenge, red team, judge, owner approval, paper gate |
| Evidence so far | 30-day backtest of the old rules: 219 trades, -Rs 1.95 lakh; rule hit rates 49-54% (no edge) | Lead hypotheses from data (volatility premium, conditions), under test in experiment 1 |

Most conflicts below follow from this: the old plan was built for a strategy the evidence rejected.

## 2. Item by item

Verdicts: **covered** (an approved story does it), **superseded** (replaced by the new design; do not build the old
version), **conflict** (old and new rules contradict; needs a decision), **gap** (useful, not in any story yet),
**keep** (already built, still useful, no story change needed).

### Roles and daily cycle

| Old item | Verdict | Where in the new plan / what to do |
|---|---|---|
| Pre-market strategist 08:30-09:10 (market map, catalyst stocks, watchlist feeding the scanner) | superseded | No pre-market decision exists; macro, market-research and positioning views become F1 finding cards at the 3 pm decision |
| Live trade analyst per candidate (take/skip/wait, tighter stop) | conflict | New: rules decide; a role's skip is a recorded discretionary veto scored separately (design 5, F4); never a live per-candidate call. Decision D1 below |
| Position guardian on material news (automatic early exit) | conflict | New: exits are playbook rules (time, profit, loss, **event** exit) reviewed once a day (E1); intraday watching only if proven. Decision D2 below |
| Post-market reviewer (grades trades, missed moves, lessons) | covered in part | Grading: E3 paper scorecard and F4 role scorecards. "Missed opportunities" and "lessons": gap G1 |
| Plain-English reporter | covered in part | E2 daily report (code, numbers from records). An AI-written plain-English narrative: gap G2 (optional F story) |
| Weekly researcher (setups by conditions; proposes rule changes) | covered in part | Research loop, B6 candidate scan, desk meetings. Its proposals go through the research loop, never straight into rules. Automating the weekly meeting: gap G3 |

### Data by phase

| Old item | Verdict | Where / what to do |
|---|---|---|
| Overnight and pre-market data (US close, Asia, futures, crude, USD/INR, yields, VIX, calendar) | covered in part | India VIX (A1/A3), events calendar (A6); global cues are inputs to the macro role's finding card (F1); no new story needed until F1 |
| Groww prices and option chains every scan; fast news watcher in minutes | keep (old desk) / superseded (new desk) | New desk uses the 3 pm snapshot (A4) and daily files; the fast news watcher stays with the old desk only; see decision D3 |
| Stock tool's verified news (slow layer, read from GitHub) | keep | Read-only input for the market-research role (F1); never write to the stock tool |

### "Before the AI layer" items (built as waves 1-3 for the old desk)

| Old item | Built as | Verdict for the new desk |
|---|---|---|
| 1. Realistic fills (bid/ask) and IV history | W1.1, W1.2 | Fills: superseded by A4 quotes + E1 fill model. IV history: the code exists but collects only while the old live desk runs; **no IV history is in the repository** (checked 12 Oct). The new desk computes implied volatility from NSE's daily files instead (A3, B1) |
| 2. Trend vs range day filter | W2.1 | superseded (intraday option-buyer filter; not used by monthly protected trades) |
| 3. Move needed vs move likely | W2.2 | superseded for the old desk's purpose; the idea (implied vs expected move) lives on as F1 (implied vs realised) |
| 4. One bet, not three (family limit) | W1.3 | covered by C2 (portfolio stress across all open trades, 3-slot limit) |
| 5. FII/DII positioning signal | W2.3 | keep as data; becomes a candidate feature for the positioning analyst (edge family E6), tested through B6, not a live signal |
| 6. Price-shock detector (Groww every 20 s) | W3.1 | old desk only; not used by the 3 pm desk unless intraday watching is approved later |
| 7. Backtest harness (Yahoo 5-minute, modelled options) | W3.2 | superseded by the research engine (B1-B3) on real NSE option prices |
| 8. Time-of-day and expiry-week statistics | W1.4 | old desk only (intraday entries) |

### Reliability

| Old item | Verdict | Where |
|---|---|---|
| Facts from code, reasoning from AI; numbers in AI output checked against a context pack | covered | Design 3.1/5 and F1 (finding cards with sources and cutoff), C4 (hard validity in code) |
| AI calls graded like a signal against rules alone | covered | F4 (paired shadow decisions, after cost) |
| No look-ahead | covered | B1 look-ahead tests, A6 announcement dates, design 6 |
| Memory: lessons stored and given to the AI before each decision | gap | G1 |

### Owner decisions in the old plan

| Old decision | Verdict | What to do |
|---|---|---|
| Runtime: owner's always-on PC with Claude Code | conflict / open | New routines already run in the cloud (3 pm recorder, 9:25 brief). Where the AI roles run (cloud routine or PC) and its cost: decision D4 |
| AI authority: may skip or delay entries and exit early automatically; never enlarge | conflict | New design: AI never changes trades; vetoes recorded and scored. Decisions D1, D2 |
| Claude may merge rule changes within bounds without owner approval | **conflict** | New design: every decision-parameter change is a new playbook version with research evidence, judge and owner approval. Proposed: the old bounded self-change rule is withdrawn for the new desk. Decision D5 |
| Real money needs a static IP for Groww orders | keep (fact) | Outside all stories; real money is not in scope |

### How strategies are created
Old: idea -> spec -> backtest -> shadow paper -> promote. **Superseded** by the research loop (design 2.1, 4, 6; stories
B4-B6, D1, E3), which keeps the same steps and adds the ledger, frozen protocols, a historical challenge, the red team,
the judge and owner approval.

## 3. Conflicts that need an owner decision (one at a time)

| # | Question | Recommendation (reasoning only) |
|---|---|---|
| D1 | May an AI role stop a trade the playbook rule wants to open? | Yes, only as a **recorded veto**, scored separately (F4); remove the role's veto right if its vetoes cost money |
| D2 | May an AI role close an open trade early on news? | Not automatically. A playbook "event exit" rule (tested) closes trades; the AI may raise an alert for the owner |
| D3 | What happens to the old intraday desk, its 9:25 brief (which still publishes option-buying candidates), fast news watcher and shock detector? | Keep the brief and news watcher as information only, clearly labelled "old strategy, not tested profitable"; stop paper-trading the old strategy when the new desk starts (E4) |
| D4 | Where do AI roles run, and at what monthly budget? | Cloud routines at the 3 pm decision (like the recorder), budget set before F1 starts; costs tracked by F5 |
| D5 | Withdraw the old rule that lets Claude merge rule changes itself? | Yes for the new desk: every decision-parameter change goes through the research loop and owner approval |

## 4. Gaps: useful items not covered by any story (proposed new stories, for review)

| # | Proposed story | Epic | Why |
|---|---|---|---|
| G1 | Lessons memory: validated lessons (from scorecards, research results, judge verdicts) stored and retrieved for each role by underlying, structure and conditions | F | The old plan's memory idea; prevents repeating known mistakes. Lessons are evidence-linked, never free-floating opinions |
| G2 | Plain-English AI summary appended to the daily report, numbers taken only from the records | F | The owner reads plain English; the code report (E2) stays the source of truth |
| G3 | Weekly research meeting automation: the roles run the research loop on a schedule and write a meeting record; proposals enter the ledger | F | The old weekly researcher, done the new way; on hold with the AI layer |
| G4 | Old desk and brief separation: implement decision D3 (labels, switch-off, lock) | E (extends E4) | Avoids two strategies being reported or paper-traded as if both were current |
| G5 | Not needed: implied volatility history comes from NSE's daily files for every day since 2019 (A3, B1); the old W1.2 snapshot adds nothing the panel lacks | - | Withdrawn after checking: no W1.2 history exists in the repository |

## 5. Order of work (owner, 12 Oct 2026)
1. Validate this re-evaluation (owner and ChatGPT); correct any wrong verdict.
2. Owner decides D1-D5, one at a time.
3. Remove or switch off the conflicting parts (old plan sections marked superseded; old behaviour per D3).
4. Only then create GitHub issues for the remaining stories (E, F) and any new stories (G1-G4), so no two issues
   describe different behaviour. Issues #3-#21 (stories A1-D3) were created before this order was set; they carry
   only approved stories that do not conflict with the old plan.

## 6. What does not change
The approved 28 stories need **no change** to their acceptance criteria from this review; the conflicts are with the
old plan, which is now marked superseded where stated. New stories G1-G4 are added only after review (G5 withdrawn).
