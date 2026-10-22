# Response 318: cut-list review of process and scope (main steward, 22 Oct 2026)

Asked by the owner (DESK_DECISIONS 22 Oct, "New work during the go-live review", item 2) through the orchestrator:
for each item, what it costs and what it protects, then keep / cut / merge / simplify, with an evidence label. Text
only; the owner decides. Labels: **[strong]** measured by me in this session on `main` (commands below), **[some]**
from a credible source I did not fully re-check, **[reasoning]** judgement.

I built O12 (number claims) and O12b-d myself; they are judged here like everything else.

## 1. The facts behind every verdict

Measured on `main` 22 Oct 2026, first commit 11 Oct. **[strong]**

| What | Size |
|---|---|
| `fno/` code | 77,008 lines (it was 69,013 in the OSS review on 21 Oct: +8,000 lines in one day) |
| `tests/` | 74,785 lines; full suite 9,809 tests, 6-7 minutes |
| Judge reports | 357 files, 42,384 lines; 563 addenda (re-judge rounds) |
| Builder responses | 292 files, 30,626 lines; 31 are review requests to ChatGPT |
| ChatGPT reviews | 71 files; the last ChatGPT commit is 16 Oct, nothing since |
| Docs (outside stories) | 79 files, 28,051 lines; stories 49 files, 18,624 lines |
| Conversation logs | 21 files, 7,219 lines |
| Commits | 5,705 in 11 days; about 1,280 merge commits |
| GitHub Actions | 23 workflows, 20 on a schedule, about 100 scheduled runs a day |
| Claude routines | 4 a day (08:36, 08:38, 14:05, 19:53 IST), plus the A16 marks, AI books and A8 watch |

**Where the work goes.** Of the last 3,000 non-merge commits, only 481 (16%) touched code or tests. 652 were judge
files, 558 docs, 268 response files, 197 conversation logs and 197 number claims (62% process in all); 578 (19%) were
data from scheduled jobs. **[strong]**

**What the judges find.** Of 325 reports with a clear first verdict, 178 (55%) opened with FAIL. 72 reports needed 3
or more re-judge rounds, the most 19. The rule "after two rounds the orchestrator takes it to the owner" (JUDGE.md) is
not followed. **[strong]**

**What the paper desk has done.** It runs every trading day (pack, Book 1, decisions, snapshot, fills, exits, marks,
reviews). On 21 Oct: "Book 1 has no registered version"; fills `{}`. `journal/book1_rules/daily_totals.csv` shows 0
trades since it started; `journal/versions.csv` holds only its header. **[strong]**

## 2. Hard lines: kept, whatever else is cut

No real orders; Groww read-only. Secrets never in files, and the record scan on every commit. Privacy: the repository
is public, so nothing restricted is committed. Data write-once in Drive with SHA-256 receipts. Frozen protocol files
change only at the next protocol version. A judge PASS before anything that touches money, risk limits, fills, exits
or forecast and score records. None of the cuts below touches these. **[reasoning]**

## 3. Process

| # | Item | Costs | Protects | Verdict |
|---|---|---|---|---|
| P1 | **Judge lane 1 for everything not listed as lane 2/3** | 652 judge commits, 42k lines; most stories wait 1-3 rounds | Real defects: 55% of first verdicts are FAILs, e.g. judge 354 (my manual claim would have wiped uncommitted work), judge 128 (V6 cannot be proven in useful time), judge 410 (two tests read growing data) | **Simplify.** Keep lane 1 for money, risk, fills, exits, forecast and score records, frozen files, secrets and outside writes. Move tools, CI and test-only fixes with no record impact to lane 2 (orchestrator check, daily audit). **[strong** that judges find real defects; **reasoning** on where the line goes] |
| P2 | **Unlimited re-judge rounds** | 72 reports with 3+ rounds, one with 19 | Nothing more than round 2 does | **Cut** to the existing rule: two rounds, then the owner decides from both sides' evidence. **[strong** on the count; **reasoning** on the fix] |
| P3 | **Seven judge pools (A-G plus older ones)** | Routing work for the orchestrator, uneven standards, messages | Parallel throughput | **Merge** into two: one code judge, one daily lane-2 auditor. With fewer stories (section 4), one judge keeps up. **[reasoning]** |
| P4 | **Judge report format** (criteria table, claims-vs-reality for every claim, project-rule check) | About 120 lines per report | Traceable evidence | **Simplify** to a fixed template of 40-60 lines: verdict, findings with evidence, plants caught. Quote only the claims that failed. **[reasoning]** |
| P5 | **Builder response (claims) files** | 292 files, 30.6k lines, 268 commits | The judge's input | **Merge** into the story file: a "Claims" section updated per round. Keep separate response files only for the other AI. **[reasoning]** |
| P6 | **ChatGPT loop**: review requests, quality rule 9 (a second reviewer for money stories), AGENTS.md duties | 31 request files, waits on reviews that never come | A second opinion on money stories | **Pause** while ChatGPT is inactive (no commit since 16 Oct): drop rule 9's wait; keep AGENTS.md for when it returns. **[strong** that it is inactive; **reasoning** on the pause] |
| P7 | **Number claims (O12, mine)** | 197 commits in 6 days, 588 lines plus the alert and CI step | Clashes (at least 4 on 16 Oct; since O12, the 307.307 heading and judge 464's unclaimed number) | **Keep for now; delete later.** Numbers are needed only because each round creates a new numbered file. With P4 and P5 (one judge file and one story file per story, named by story id, e.g. `reviews/judge/O12.md`), numbering is not needed at all. Then delete `fno/numbering/`, `numbers/`, the claim tool and both checks. Also **cut now** O12b's hourly reminder (up to 24 posts a day while red): the push-time alert is enough. **[reasoning]** |
| P8 | **Conversation logs** | 21 files, 7.2k lines, 197 commits | The owner's words, verbatim | **Simplify**: keep the owner's quotes and the decisions; drop the condensed replies (DESK_DECISIONS already holds the decisions). **[reasoning]** |
| P9 | **WORK_REGISTER** | About 50 commits, a long table | Duplicate builders: it caught the second fix of the g7 test on 21 Oct | **Keep**, but enforce its own rule: delete done rows after a day. **[some]** |
| P10 | **Merge procedure**: one full suite per merge, fast checks for lane-3 drift | 6-7 minutes per merge | Main stays green | **Keep** (owner rule, 21 Oct). **[strong]**: main was red only from data-dependent tests, not from merges |
| P11 | **Orchestrator overhead** | 374 commits (2nd-most active session); every handoff passes through it | Assignment, owner questions, decision rows | **Simplify.** It assigns, asks the owner, and writes decisions; status lives in WORK_REGISTER, not in messages. From my own inbox on 21-22 Oct: four "merge now / what is your state" messages crossed my reports. Number 275 was promised to A20, then to T1c. One message said Judge D "has seen nothing" while it had my request. **[some]** (one session's view) |
| P12 | **Rule documents** | CLAUDE.md 275 lines, about 45 of them a list of every composition root; JUDGE.md 160; AGENTS.md 122 | Shared rules | **Simplify**: drop the composition-root list (the code shows it) and the routine texts that duplicate each command's own help. **[reasoning]** |

## 4. Paused stories and dormant code

| # | Item | Costs | Protects | Verdict |
|---|---|---|---|---|
| S1 | **Paper desk stack**: desk 5.7k, books 2.1k, playbook 2.9k, scoreboard 2.3k, scorecard 0.8k, risk 2.0k, checks 2.5k, evaluation 0.8k, role_value 0.9k, budget 1.4k, cards 1.4k, learning 0.7k (23,459 lines, 16,636 of tests) | Runs every trading day in the 14:05 routine; every change to shared code must keep its tests green | Nothing yet: 0 trades, no registered version | **Freeze**: stop the desk steps in `daily run` until the owner registers a version; no new desk stories until the edge study (decision 293 item 1) shows an edge after costs. Keep risk and checks unchanged: they are the hard line the day a trade exists. **[strong** on 0 trades; **reasoning** on the freeze] |
| S2 | **Books 2 and 3** (`fno/ai` 2.1k, `fno/book3`, F4, F5, F6 branches) | AI runs, judge rounds on parked branches | Two more decision makers that cannot trade before a strategy is approved | **Close for good** unless the edge study finds an edge; keep the branches as history. **[reasoning]** |
| S3 | **Innovation Lab** (design only) | A new pipeline above the existing playbook, R1, S1, S2 and RM1 | Candidate promotion | **Cut**: it is more process above process. R1's factory already runs the edge study. **[reasoning]** |
| S4 | **A14c part 2 and families** (margin check, `margin_check` not live) | Unjudged code, 4 margin runs a day | Margins only matter once trades exist | **Freeze with S1**; cut the margin cron from 4 runs a day to 1. **[reasoning]** |
| S5 | **O2b** (trade-row failure handling) | A story | Trade rows that do not exist yet | **Freeze with S1.** **[reasoning]** |
| S6 | **G10 b2** (v4 pack builder) and further v4 machinery | Judge rounds | Judge 128: with the measured noise no v4 member is provable in useful time (V6b at best 14-22 years); the owner made v4 "an honest daily yardstick" (21 Oct) | **Cut** new v4 machinery; keep running what is live. **[strong** (judge 128's numbers, owner row 280)] |
| S7 | **LR3** (drift CUSUM) | A story, code waits | Drift detection | **Cut**: the signed-off report already has the 20-day reliability trend with a 90% target and an 80% warning (decision 288). **[some]** |
| S8 | **O9 remaining steps** (every data file to Drive, step by step) | Coordination with about 10 owners per step | Write-once provenance | **Simplify**: new datasets are born write-once; migrate old ones only when a live reader needs them. Do not migrate everything. **[reasoning]** |
| S9 | **UI** (`fno/market_read_models` 4.3k, P2 pages, dashboard repo) | Code and tests that every model change must keep green | Nothing while the UI is paused | **Freeze**; no work until the owner unpauses. **[strong** that it is paused; **reasoning** on the freeze] |
| S10 | **E8** (owner-timing fills) | Code and tests | Fills, of which there are none | **Freeze with S1.** **[reasoning]** |

## 5. Duplicate code

| # | Item | Verdict |
|---|---|---|
| D1 | **Option pricing in four places**: `fno/analytics.py` (spot BS, Greeks, IV), `fno/checks/validity_pricing.py` (Black-76 and IV, a third `norm_cdf`), `fno/price_distribution/pricing.py` (Black-76 wrappers), `fno/research_engine/implied_vol.py` (models behind an interface) | **Merge** into one module outside the frozen files, as decided on 22 Oct (decision 291/293 item 3). **[strong** that the copies exist] |
| D2 | **Brier in three places**: `fno/forecast_scoring/scores.py`, `fno/forecast_v4/loss.py` (both frozen) and a private `_brier` in `fno/price_ranges/scores.py` | **Merge** the unfrozen one now; the frozen two only at protocol v5. **[strong]** |
| D3 | **`fno/global_cues`** (2.7k lines): scrapes CBOE, Nasdaq, the Treasury, EIA and RBI/FBIL | **Simplify** at its next change: FRED has the 10-year (DGS10), Brent (DCOILBRENTEU), USD/INR (DEXINUS) and the S&P 500/Nasdaq (SP500, NASDAQCOM), and the owner has a FRED key. One FRED adapter could replace most of the scrapers. Check first: FRED's publication lag for the 03:41 IST pre-open read. **[some** on the series; **reasoning** on the lag] |

## 6. Docs nobody reads

Counted by files that refer to each doc outside reviews and logs (a proxy, not a read count). **[strong** on the counts]

| Doc | Lines | Referenced by | Verdict |
|---|---|---|---|
| `docs/HANDOVER_2026-10-16.md` | 5,057 | 0 files | **Move** to `docs/archive/` (one-off, now stale) |
| `docs/design_v2/` (13 files) | 1,586 | 1-11 each | **Move** to `docs/archive/`; DESK_DECISIONS and the stories supersede them |
| `CLEAN_SLATE_DESIGN.md`, `MIGRATION_PLAN.md`, `BUILD_MAP.md`, `CORE_ENGINE_GAP_AUDIT.md`, `IMPLEMENTATION_PLAN.md` | 965 | 2-25 | **Move** to `docs/archive/`; their status cells are stale (O1 and O12 merged, still marked open on 21 Oct) |
| `DATA_USE_MAP.md`, `DATA_SOURCES.md` | 134 | 3-4 | **Merge** into one data page |

Reading list for a new session, after the move: CLAUDE.md, AGENTS.md, JUDGE.md, DESK_DECISIONS.md, WORK_REGISTER.md and
the story it works on. **[reasoning]**

## 7. Scheduled routines

| # | Routine | Runs | Verdict |
|---|---|---|---|
| R1 | The 14:05 desk routine | 1 a day, about 90 minutes | **Keep** quotes, weather, v4 and the price forecasts; **skip** the desk steps while S1 is frozen. **[reasoning]** |
| R2 | 08:36 pre-open, 08:38 morning, 19:53 evening | 3 a day | **Keep**: they feed the owner's chosen report. **[reasoning]** |
| R3 | AI books (fire and collect) | Daily | **Stop** with S2. **[reasoning]** |
| R4 | `participant-oi-watch.yml` | 28 runs a day | **Simplify** to 2-3 runs once the release time is measured (A8 has the times). **[reasoning]** |
| R5 | `number-alert.yml` hourly (mine) | 24 a day | **Cut** the hourly cron and keep the push alert (P7). **[reasoning]** |
| R6 | `nse-margins.yml` | 4 a day | **Cut** to 1 while the margin check is off (S4). **[reasoning]** |
| R7 | `circulars.yml` | 15 a day | **Keep** only if a live reader uses circulars; none does today. Then 2 a day. **[reasoning]** |

## 8. What the owner would gain

If P1-P8, S1-S10, R1-R7 and the doc moves are accepted:
- about 40-50% fewer commits per day, since process commits are 62% now;
- about 23.5k lines of desk code no longer run daily or need extending;
- about 8k lines of docs out of the reading path;
- 30-40 fewer scheduled runs a day.

The time saved goes to the one open question the OSS review and this list both point at: does any NIFTY or BANKNIFTY
trade have an edge after costs and 31.2% tax? None has been shown yet. **[reasoning** on the size; **strong** on the
counts it rests on]

## How these numbers were made

On `main` 22 Oct 2026:
- `find fno -name '*.py' | xargs cat | wc -l` (and the same per package and for tests and docs);
- `git log --since=2026-10-11` grouped by the files each commit touched;
- the first verdict line of each `reviews/judge/judge_*.md`;
- `numbers/judge-addendum.csv` for rounds per report;
- `journal/runs/2026-10-21.json` and `journal/book1_rules/daily_totals.csv` for the desk;
- the `cron:` lines of `.github/workflows/*.yml`;
- `grep -rl` for references to each doc.
