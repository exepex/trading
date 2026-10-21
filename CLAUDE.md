# Project instructions

This repo is **Omenix F&O** (part of Omenix; the dashboard is `exepex/omenix-dashboard`), an F&O options research assistant for the owner's Indian trading experiment (broker: Groww).
It is research and paper trading only: never place orders, never ask for or store broker credentials in files.

## How to work with the owner (always)

This is the owner's personal research tool for learning F&O trading and deciding their own trades. Wrong results
cost real money later, so:

- **Never hold back.** Share every relevant fact, risk, idea and doubt, including what the owner may not want to hear.
- **Be brutally honest.** Disagree openly and say why. Never agree just to please. Never present a guess as a fact:
  mark each recommendation as strong evidence, some evidence, or reasoning only.
- **Keep it simple, precise and concise.** Plain words, real numbers, short answers; explain any jargon you must use.
- **Get past blockers.** When something stops the work (missing data, a failing source, an unclear rule, a tool
  limit), find another legitimate way: another source, a test, a workaround, or a clear question to the owner. If it
  truly cannot be done, say so plainly and why. Never skip it silently or hide it.
- **No patches.** Find the root cause, validate it with data and tests, then fix the design.
- **No blind acceptance or rejection of reviews.** Check every review comment and piece of feedback (from the owner,
  Claude, ChatGPT or a judge) with your own reasoning and, where possible, data: re-run the numbers, read the code,
  test the claim. Accept it only when the check shows it is correct; push back when it is not. Every acceptance and
  every rejection states its reason and evidence. Partial agreement is fine: say which part and why.
- **Everything for the other AI goes in the repository.** Questions, proposals, solutions, suggestions and feedback
  meant for ChatGPT (or from it) are written as Markdown files in the repository, never only in chat, so each side
  reads them directly: ChatGPT writes to `reviews/chatgpt/review_<n>_<name>.md`, Claude to
  `reviews/claude/response_<n>_<name>.md` (questions and proposals included), each folder with a README index.
  Take `<n>` from the central registry, never "highest plus one": `python tools/claim_number.py <category> <name>
  --session <id>` (or by hand, as `numbers/README.md` says: the row alone, pushed to `main` before the file from a
  separate copy of `main`, never your own checkout; if the push is refused, never merge: refresh that copy and take the
  next number). Story O12.
- **Own limits too.** This applies to Claude's own limits and boundaries, not only tools: always give the fullest, most
  direct answer possible. If a limit ever shapes an answer, say so openly (what was limited and why), give everything
  that can be given, and point to where the rest can be found. Never quietly water an answer down. The same applies to
  questions and clarifications: ask them plainly and directly.
- The hard lines stay: no real orders, nothing illegal (no market manipulation), secrets never in files or chat.
- **One builder per function (owner, 15 Oct 2026).** Before starting any story, fix or design change, read
  `docs/WORK_REGISTER.md` on the latest `main`; if a row already covers the same function, files or rule, agree with
  its owner session first, and add or update your own row in your first commit. Never build a second version.
- **The main job is the desk meeting** (see `AGENTS.md`): find profitable trades from data, every role reasoning from its
  own angle; code and data bugs are fixed directly and mentioned in one line, never the main topic.
- **Answer from every financial role** listed in `AGENTS.md` (mathematician, statistician, F&O trader, options
  strategist, risk manager, portfolio manager, analyst and the rest); ChatGPT follows the same file.

## Keep a conversation log (every session)

Before ending any working session with the user, write or append to `conversations/YYYY-MM-DD.md`
(IST date): quote the user's messages as written, condense your replies to their substance, and update the
"Decisions so far" and "Open questions" sections. Commit and push it. Never include email addresses,
API keys or tokens.

## Daily desk routine (story O1; the 3 pm quote parts: stories A4, A4c and A7)

Started by the owner's scheduled session at 14:05 IST every day (owner, 21 Oct 2026, from 22 Oct: the weather and the
v4 forecasts must run before their 14:30 cutoff, so setup must end well before 14:30);
its stored prompt is exactly: "Run the daily desk routine in CLAUDE.md, section 'Daily desk routine'." One command runs
the whole desk day; the NSE session calendar (A7) decides whether it is a trading day (a closed day records only
`skipped` and each quote part prints "not a trading day"). Research and paper trading only: never places, modifies or
cancels orders.
1. `sh tools/routine_setup.sh --groww` (story O7: installs into every Python the routine and the commit hook can call,
   checks each imports the packages, turns on the public-record scan, story O5, and prints "routine setup ok").
   Every scheduled routine sets up this way, never with bare `pip` (it may fill another Python).
2. `python -m fno daily run` (story O1). It runs the day's steps in the order of `DAILY_RUN_STEPS`
   (`fno/constants_operations.py`): the 3 pm quote parts start first, then A14c's margin check, the weather and the v4
   forecasts (each from its `daily.live_from` date in `config.yaml`, `not_live` before it), E3's desk (pack, Book 1's
   decision, fills, exits), E6's reviews, the quote parts' end and T1's card in #fno-desk and, from 15:33 IST (after
   A16's 15:30 mark), A16b's candle catch-up (`intraday backfill`: yesterday's 15-minute candles, read-only Groww).
   It writes `journal/runs/<date>.json` and commits each step's own files itself. It ends on one line: `day done`, `day
   done with problems: <steps>`, or the desk's stop line ending "; no card today" (exit 1 for the last two). A rerun the
   same day skips the steps already done.
3. If it printed "alert NOT sent", post those lines to #fno-desk (`C0C89E8QCCD`) with the Slack connector. Note any
   result other than `day done` in `conversations/<date>.md`, then commit and push it (`git pull --no-rebase` first).

### What the run does for the 3 pm quote parts (A4c's routine steps, word for word)

The routine never runs these commands itself: `daily run` runs each part's own command as a child process and makes
each part's commit in its one thread. The `git add` lines below are also the hand fix when the run reports a part
"NOT committed". Their rules hold for every commit of the day: never edit a recorded attempt, never `--no-verify`.

2. `python -m fno quotes record` (NIFTY, Groww) and `python -m fno quotes record --source nse` (NSE's public chain,
   story O6) run in parallel from the routine's start; each waits for 14:55 IST, records NIFTY monthly quotes and
   retries until 15:10 if a capture is incomplete. NSE's session calendar (`research/data/calendar/nse_sessions.csv`,
   story A7) decides the day: a holiday, weekend or muhurat-only day records nothing ("not a trading day"); a special
   weekend session is recorded. It prints the result line. Groww's raw quote rows go to Google Drive only (story A4b;
   needs the four `FNO_GDRIVE_*` settings): the repository gets each attempt's sidecar (`.meta.json`, with the Drive
   file's SHA-256) and the day's `.canonical` marker, never a Groww quote file (`.gitignore` keeps them out).
3. Each part commits and pushes only its own files to `main`, one commit at a time (`git pull --no-rebase` first); never
   `git add research/data/quotes/` as a whole. NIFTY first, as soon as its result line is printed: `git add
   ':(glob)research/data/quotes/groww/**/nifty_*'`. NSE when it is done: `git add research/data/quotes/nse/`. Never edit
   or delete a recorded attempt or `.canonical` file. If the record scan refuses the commit, do not commit and never
   bypass it (`--no-verify`). The hook posts its lines (file, line and kind of value; never the value) to #fno-desk
   itself when `FNO_SLACK_BOT_TOKEN` is set; if it prints "alert NOT sent", post those lines with the Slack connector.
   Note them in `conversations/<date>.md`.
3b. Right after NIFTY's push, run `python -m fno quotes record-indices` (story A4c: BANKNIFTY, FINNIFTY and
   MIDCPNIFTY; 15:01-15:13 IST, paced; raw quotes to Drive only), alongside NSE if it is still running. When it is
   done: `git add ':(glob)research/data/quotes/groww/**/banknifty_*'
   ':(glob)research/data/quotes/groww/**/finnifty_*' ':(glob)research/data/quotes/groww/**/midcpnifty_*'`, commit and
   push. It alerts #fno-desk itself for any index not recorded.
4. If the result is not "recorded" with complete=True, "already recorded" or "not a trading day": the command itself
   posts its three alerts to #fno-desk (`FNO_SLACK_BOT_TOKEN`): "calendar says session, no same-day trades",
   "stopped, nothing recorded" (the calendar cannot answer for today, e.g. a new year missing: add NSE's holiday
   circular rows for that year) and "raw quote file NOT saved to Drive" (Drive down or its settings missing or
   expired; the day ends "none" if it lasts to 15:10). Post one line with the result to #fno-desk (`C0C89E8QCCD`)
   yourself only for any other result, or if it printed "alert NOT sent". Note every such result in
   `conversations/<date>.md`.

## Morning and evening forecast routines (story FL1-1d)

Started by the owner's two scheduled sessions (owner, DESK_DECISIONS lines 284 and 287; the owner creates them, no
session does). Their stored prompts are exactly: "Run the morning routine in CLAUDE.md, section 'Morning and evening
forecast routines'." at 08:38 IST, and "Run the evening routine in CLAUDE.md, section 'Morning and evening forecast
routines'." at 19:53 IST, both every day: NSE's calendar decides the day. Each edition posts only from its
`forecast_lab.live_from` date in `config.yaml` ("not live" before it). Research and paper trading only: never places,
modifies or cancels orders, and neither uses Groww.
1. `sh tools/routine_setup.sh` (prints "routine setup ok").
1b. The morning only, before `lab open`: `python -m fno data-librarian index-close --from "$(TZ=Asia/Kolkata date -d
   '-7 days' +%F)"` archives the previous sessions' official index-close files in Drive (A9's command, unchanged;
   orchestrator, 22 Oct). It commits its own manifest rows itself; a file NSE has not published yet is not a
   failure of the routine: the morning then says "not archived yet".
1c. The evening only, before `lab close`, the same way (orchestrator, 22 Oct; each unchanged, committing only its own
   dataset's rows): `python -m fno data-librarian fo-bhavcopy --from <today> --to <today>`, `python -m fno
   data-librarian participant-oi --from <today> --to <today>` and `python -m fno data-snapshot
   fii-dii-cash-by-session`. A librarian line "not published by the source <day>" means "not out yet" (the edition
   says so); any other problem line ("damaged in store", "rejected from source", "stopped:", a Drive sign-in
   refusal) is noted and posted to #fno-desk. After `lab close`, `python -m fno lab release-check` (read-only, never
   fails) appends to `research/data/forecast_lab/release/`; commit those logs with the receipts in step 3.
2. The morning: `python -m fno lab open` posts today's forecast to #fno-forecast before 09:15, with the earlier
   evenings' checks confirmed against NSE's official closes; at or after 09:15 it posts nothing and alerts once. The
   evening: `python -m fno lab close` checks today's forecast against today's close and posts to #fno-forecast. Each
   prints its lines and exits 1 when its report was not posted (it alerts #fno-desk itself).
3. Commit only that edition's receipts: `git pull --no-rebase origin main`, then `git add
   receipts/data/forecast_lab/v1/<morning|evening>/` (the evening also `research/data/forecast_lab/release/`), commit and `git push origin HEAD:main` (record scan on, never
   `--no-verify`). If the push is refused, pull and push once more; if it fails again, post "receipt NOT pushed" with
   the edition and day to #fno-desk (`C0C89E8QCCD`) with the Slack connector: the Drive copy is the record.
4. If it printed "alert NOT sent", post those lines to #fno-desk with the Slack connector. Note any failure in
   `conversations/<date>.md`, then commit and push it (`git pull --no-rebase` first).

## Pre-open capture (story A22)

Started by the owner's scheduled session at 08:36 IST every day; its stored prompt is exactly: "Run the pre-open capture
in CLAUDE.md, section 'Pre-open capture (story A22)'." Research only: Groww is read through the read-only allow-list.
1. `sh tools/routine_setup.sh --groww` (prints "routine setup ok").
2. `python -m fno preopen record`. On a day that is not a trading day it prints "not a trading day" and ends. Otherwise
   it reads GIFT Nifty (08:40-08:44:59), NSE's F&O pre-open list (09:08:30-09:10:59) and NIFTY's and BANKNIFTY's 09:09
   one-minute candle from Groww (09:10:00-09:10:59), saves the raw answers and the day row write-once to Drive, and
   itself commits and pushes `research/ops/capture_errors.csv` and `receipts/` to `main` by about 09:12. It ends on
   "pre-open recorded" or "pre-open recorded with problems: ..." (exit 1; it posts that one line to #fno-desk itself).
3. If it printed "alert NOT sent" or a line with "NOT committed", post its problem line to #fno-desk (`C0C89E8QCCD`)
   with the Slack connector, then commit the named files by hand (`git pull --no-rebase` first; only `receipts/` and
   `research/ops/capture_errors.csv`, never `--no-verify`). No value is ever posted or committed.

## Branch

**Judge lanes (owner, 14 Oct 2026, `docs/DESK_DECISIONS.md`; details in `docs/JUDGE.md`).** A change's lane is set by
what it can damage, not by its size; when unsure, lane 1. Lane 1 is decided by the path list in `docs/JUDGE.md`
(judge 91 refinements), whatever a change's description.
- **Lane 1, judge PASS before `main`:** every new story, and any change of any size touching money or risk (margins,
  funds, limits), fills, exits or anything that decides a trade, scoring or forecast and evaluation records, frozen
  files, secrets or outside services (Slack, Groww, Drive, NSE), schedules and workflows, or the dashboard's privacy
  rule. Push to a branch `story/<id>-<short>`, tell the orchestrator, merge only after the PASS (pull, full suite on the
  merged tree, then push).
- **Lane 2, orchestrator check before `main`, judge audit after:** only new tests and docs outside the rule documents
  (list in `docs/JUDGE.md`). Everything not in lane 2 or 3 is lane 1. The orchestrator re-runs the checks and compares
  the builder's claim with the diff before merging; the judge audits each day's lane-2 merges once, and a FAIL is
  fixed first.
- **Lane 3, no judge:** judge files, conversation logs, decision and status rows, number claims (`numbers/`, story O12),
  and data commits by scheduled jobs.

A checkout on a detached HEAD pushes with `git push origin HEAD:<branch>`.

Work on `main` (`git pull --no-rebase origin main` before every push: ChatGPT also pushes to `main`).
Every session commits with the public-record scan on (story O5): `.claude/settings.json` runs
`git config core.hooksPath .githooks` at session start; run it yourself if `git config core.hooksPath` is empty. Never
commit with `--no-verify`.

## Code

- `python -m pytest -q -n auto` (parallel, pytest-xdist), `ruff check fno tests tools` and
  `python tools/check_imports.py` must pass before pushing code changes; format with `ruff format`. On `main` (after
  `git pull --no-rebase origin main`, never on a story branch alone: claim rows live on `main`),
  `python tools/check_numbers.py` must pass too. When the gates run: `docs/JUDGE.md`, "Merge procedure".
- **Engineering standards (owner, mandatory for every agent and every session):** SOLID, DRY, KISS and clean code
  (clear names, small single-purpose functions and classes, no duplication, no dead code, comments only for the "why").
  **No file and no class over 350 lines.** Anything that would pass 350 lines is broken down into smaller single-purpose
  units, never squeezed (no long lines or joined statements to dodge the limit). Enforced by `tests/test_code_size.py`
  and checked by the judge (`docs/JUDGE.md`).
- **Design for change (owner, 12 Oct 2026: "Today it's Google Drive, tomorrow it can be something else"; "flexible,
  modular, scalable", "production quality"):** high cohesion and loose coupling through design patterns. Every external
  service, data source, store and rule sits behind an interface, so swapping it means one new class plus one line in a
  composition root. Patterns in use: interface plus adapter (`RawFileStore`, `RawFileSource`, `Provider`), strategy
  (`FoFileFormat`, `RecordPattern`, rules), factory (`get_provider`) and composition root with dependency injection
  (below). Choose the simplest pattern that keeps the parts swappable (KISS); never add a pattern without a second use.
- Fixed strings, enum values and environment-variable names live in `fno/constants.py`; module-specific
  URLs, SQL and message templates are named constants at the top of their module.
- Names say what things do. Small single-purpose modules; new behaviour goes in a new class behind an existing
  interface (`Provider`, `RawFileStore`, `RawFileSource`, `FoFileFormat`, `ListedExpiries`, and those the stories add)
  rather than into an existing one. Follow SOLID, KISS and DRY: high cohesion, loose coupling, depend on interfaces.
- Concrete classes are wired together only in the composition roots: `fno/composition.py` (the app's services),
  `fno/storage/wiring.py` (raw data stores and sources), `fno/storage/quote_wiring.py` (the 3 pm quote store: Groww's
  raw quote files in Drive only, story A4b; apart because `wiring.py` is at the size limit), `fno/quotes/window_wiring.py`
  (a named 3 pm capture window, protocol v4's 14:30-14:40, in its own dataset, story A4e), `fno/risk/wiring.py` (the
  risk manager, story C2),
  `fno/forecast/wiring.py` (the forecasts, epic G), `fno/forecast/baseline_wiring.py` (forecast baselines, back-fill
  and protocol v2's live capture, G2-G3; apart because the G1 freeze pins `wiring.py`),
  `fno/forecast_v4_rules/wiring.py` (protocol v4's baselines and rule forecasters, story G7; apart because the v2 freeze
  pins every file of `fno/forecast/`), `fno/filings/wiring.py` (the
  company filings archive, story A12), `fno/pipeline/wiring.py` (fetch-and-trigger jobs, story O6),
  `fno/pipeline/panel_wiring.py` (the daily NIFTY panel job, story A13; apart so G1 v3 can freeze it without O6),
  `fno/market_read_models/wiring.py` (the market read models and their publisher, stories P6-P9),
  `fno/forecast_scoring/wiring.py` (forecast scoring and reports, story G4; outside the frozen `fno/forecast/`),
  `fno/forecast_scoring/v4/wiring.py` (protocol v4 scores, comparisons and the two looks, story G8),
  `fno/ai/wiring.py` (the AI books' forecasts: fire and collect, F1 and G5), `fno/ai/book_wiring.py` (the AI books'
  routine side, standard library only), `fno/playbook/wiring.py` (the playbook loader and status changes, story D1),
  `fno/desk/wiring.py` (the paper desk's fills and exits, story E4), `fno/desk/pack_wiring.py` (the daily common and
  private packs, story E2), `fno/scorecard/wiring.py` (strategy scorecards and pause rules, story E6),
  `fno/checks/wiring.py` (the data checks before every decision and the hard-validity checks, stories C3 and C4),
  `fno/vix_history/wiring.py` (the India VIX full history: NSE's month files, its table and checks, story A15),
  `fno/global_cues/wiring.py` (the global cues: US closes, US 10-year, Brent and USD/INR, their tables, story A17),
  `fno/desk/daily_wiring.py` (the paper desk's daily timetable run, story E3), `fno/books/book1_wiring.py` (Book 1,
  pure rules: its decider, orders and exit rules, story E5), `fno/evaluation/wiring.py` (the evaluation protocol's
  freeze and checks, story S1), `fno/scoreboard/wiring.py` (scoreboard B, whole systems, story S2),
  `fno/budget/wiring.py` (AI usage, the budget meter and the stop-rule tracker, stories F8 and BG1),
  `fno/cards/wiring.py` (the daily trade card, story T1), `fno/weather/wiring.py` (the market weather as a
  scored forecaster, story M1), `fno/intraday/wiring.py` (the 15-minute quote recorder:
  Groww source behind a read-only allow-list, Drive store, clock check, story A16),
  `fno/storage/data_wiring.py` (story O9: every data file write-once in Drive's `data` area, its SHA-256 receipt
  under `receipts/`, the verified Drive cache; apart because `wiring.py` is at the size limit),
  `fno/intraday/backfill_wiring.py` (the 15-minute candle back-fill: Groww candles, Drive archive, NSE check, story
  A16b), `fno/intraday/clock_wiring.py` (A16's checked clock, shared by A16 and A4e), `fno/health/wiring.py` (the daily health check: repository evidence, GitHub push receipts, calendar,
  run record, story O8), `fno/learning/wiring.py` (the weekly post-mortem: committed scores, weather, data health,
  its AI routine and the devil's advocate port, story LR1), `fno/role_value/wiring.py` (the role-value evaluation:
  paired rows, role sets, S3's standard unit, F8's allocation, S1's review dates, C4's log, story F9a),
  `fno/v4_pack/wiring.py` (protocol v4's released packs through the verified Drive cache and the 15:10
  deadline on GitHub's receipt time, story G10 part 2),
  `fno/book3/wiring.py` (Book 3's strategy registry: git history, the research ledger, the IST clock, story D5),
  `fno/daily/wiring.py` (the daily run: E3's desk with the weather, v4 forecasts, Book 1's decision, the 3 pm quote
  parts and the card around it, story O1), `fno/numbering/wiring.py` (number claims on `main`, story O12),
  `fno/fo_masters/wiring.py` (NSE's daily F&O master files: the ban list and market lots, story A20a),
  `fno/preopen/wiring.py` (the morning capture: GIFT Nifty, NSE's pre-open list, Groww's 09:09 candles, story A22),
  `fno/circulars/wiring.py` (NSE's and SEBI's circular lists, first-seen times and F&O files in Drive, story A20b) and
  `fno/price_distribution/wiring.py` (the daily valuation record and NIFTY's price-distribution forecasts and their
  scores: A4's chains, the panel, closes, O9's Drive store, story G13) and `fno/price_ranges/wiring.py` (NIFTY's and
  BANKNIFTY's 15:45 price ranges: A4/A4c chains, the archived F&O and index-close files, O8's push evidence, story G13b).
- Nothing in this repository places real orders. The stock tool's research is read-only: never write to its
  repository or to its `market_brief` MotherDuck database. Every data file (fetched or derived) lives write-once in
  Google Drive and is read through the verified Drive cache; GitHub keeps code, docs and one SHA-256 receipt per Drive
  file (owner, 16 Oct 2026; story O9, built step by step).
- F&O output goes only to three Slack channels, all with `FNO_SLACK_BOT_TOKEN` (owner, 21 Oct 2026; story FL1):
  #fno-desk (`C0C89E8QCCD`) takes every alert and the daily card; #fno-forecast (`C0CAZS76WBC`) the forecast lab's
  morning (08:50) and evening (20:05) editions (story FL1-1d); #fno-intraday (`C0CAZRX0ZQA`) the lab's fills and hourly lines. Never the market-brief
  tool's `SLACK_*` variables or #market-brief, and no other channel (the record scan allows only these three IDs).
- Settings live in `config.yaml` (allowed keys only, see `fno/config.py`); see README.md for the layout.
