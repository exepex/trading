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
- **Own limits too.** This applies to Claude's own limits and boundaries, not only tools: always give the fullest, most
  direct answer possible. If a limit ever shapes an answer, say so openly (what was limited and why), give everything
  that can be given, and point to where the rest can be found. Never quietly water an answer down. The same applies to
  questions and clarifications: ask them plainly and directly.
- The hard lines stay: no real orders, nothing illegal (no market manipulation), secrets never in files or chat.
- **The main job is the desk meeting** (see `AGENTS.md`): find profitable trades from data, every role reasoning from its
  own angle; code and data bugs are fixed directly and mentioned in one line, never the main topic.
- **Answer from every financial role** listed in `AGENTS.md` (mathematician, statistician, F&O trader, options
  strategist, risk manager, portfolio manager, analyst and the rest); ChatGPT follows the same file.

## Keep a conversation log (every session)

Before ending any working session with the user, write or append to `conversations/YYYY-MM-DD.md`
(IST date): quote the user's messages as written, condense your replies to their substance, and update the
"Decisions so far" and "Open questions" sections. Commit and push it. Never include email addresses,
API keys or tokens.

## 3 pm quote recorder (daily routine, stories A4 and A7)

Started by a scheduled session at about 14:50 IST every day; the NSE session calendar (A7) decides whether it is a
trading day, so special weekend sessions are recorded and closed days print "not a trading day". Research data
only: never places, modifies or cancels orders.
1. `pip install -q -r requirements.txt -r requirements-groww.txt` and `git config core.hooksPath .githooks` (turns on
   the public-record scan, story O5, for every commit).
2. `python -m fno quotes record` (waits for 14:55 IST, records NIFTY monthly quotes, retries until 15:10 if a capture is
   incomplete). NSE's session calendar (`research/data/calendar/nse_sessions.csv`, story A7) decides the day: a
   holiday, weekend or muhurat-only day records nothing ("not a trading day"); a special weekend session is recorded.
   It prints the result line.
3. Commit `research/data/quotes/` and push to `main` (`git pull --no-rebase` first). Never edit or delete a recorded
   attempt or `.canonical` file. If the record scan refuses the commit, do not commit and never bypass it
   (`--no-verify`). The hook posts its lines (file, line and kind of value; never the value) to #fno-desk itself when
   `FNO_SLACK_BOT_TOKEN` is set; if it prints "alert NOT sent", post those lines with the Slack connector. Note them in
   `conversations/<date>.md`.
4. If the result is not "recorded" with complete=True, "already recorded" or "not a trading day": the command itself
   posts its two alerts to #fno-desk (`FNO_SLACK_BOT_TOKEN`): "calendar says session, no same-day trades" and
   "stopped, nothing recorded" (the calendar cannot answer for today, e.g. a new year missing: add NSE's holiday
   circular rows for that year). Post one line with the result to #fno-desk (`C0C89E8QCCD`) yourself only for any
   other result, or if it printed "alert NOT sent". Note every such result in `conversations/<date>.md`.

## Branch

**Temporary owner rule (14 Oct 2026, `docs/DESK_DECISIONS.md`), in force until the owner lifts it: no code reaches `main`
without a judge PASS.** Push code to a branch `story/<id>-<short>`, tell the orchestrator, and merge into `main` only after
the judge passes that branch (pull, full suite on the merged tree, then push). Not affected: judge files, conversation logs,
decision and status rows, and data commits by scheduled jobs. A checkout on a detached HEAD pushes with
`git push origin HEAD:<branch>`.

Work on `main` (`git pull --no-rebase origin main` before every push: ChatGPT also pushes to `main`).
Every session commits with the public-record scan on (story O5): `.claude/settings.json` runs
`git config core.hooksPath .githooks` at session start; run it yourself if `git config core.hooksPath` is empty. Never
commit with `--no-verify`.

## Code

- `python -m pytest -q`, `ruff check fno tests tools` and `python tools/check_imports.py` must pass before pushing code
  changes; format with `ruff format`.
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
  `fno/storage/wiring.py` (raw data stores and sources), `fno/risk/wiring.py` (the risk manager, story C2),
  `fno/forecast/wiring.py` (the forecasts, epic G), `fno/forecast/baseline_wiring.py` (forecast baselines, back-fill
  and protocol v2's live capture, G2-G3; apart because the G1 freeze pins `wiring.py`), `fno/filings/wiring.py` (the
  company filings archive, story A12), `fno/pipeline/wiring.py` (fetch-and-trigger jobs, story O6),
  `fno/pipeline/panel_wiring.py` (the daily NIFTY panel job, story A13; apart so G1 v3 can freeze it without O6),
  `fno/market_read_models/wiring.py` (the market read models and their publisher, stories P6-P9),
  `fno/forecast_scoring/wiring.py` (forecast scoring and reports, story G4; outside the frozen `fno/forecast/`),
  `fno/ai/wiring.py` (the AI books' forecasts: fire and collect, F1 and G5), `fno/ai/book_wiring.py` (the AI books'
  routine side, standard library only), `fno/playbook/wiring.py` (the playbook loader and status changes, story D1),
  `fno/desk/wiring.py` (the paper desk's fills and exits, story E4), `fno/desk/pack_wiring.py` (the daily common and
  private packs, story E2), `fno/scorecard/wiring.py` (strategy scorecards and pause rules, story E6),
  `fno/checks/wiring.py` (the data checks before every decision and the hard-validity checks, stories C3 and C4),
  `fno/desk/daily_wiring.py` (the paper desk's daily timetable run, story E3), `fno/books/book1_wiring.py` (Book 1,
  pure rules: its decider, orders and exit rules, story E5) and `fno/evaluation/wiring.py` (the evaluation protocol's
  freeze and checks, story S1).
- Nothing in this repository places real orders. The stock tool's research is read-only: never write to its
  repository or to its `market_brief` MotherDuck database. GitHub files are the default store for research input
  and results.
- F&O output goes only to Slack #fno-desk (`C0C89E8QCCD`) with `FNO_SLACK_BOT_TOKEN`; never the market-brief tool's
  `SLACK_*` variables or #market-brief.
- Settings live in `config.yaml` (allowed keys only, see `fno/config.py`); see README.md for the layout.
