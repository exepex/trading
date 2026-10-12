# Project instructions

This repo is an F&O options research assistant for the owner's Indian trading experiment (broker: Groww).
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

## 3 pm quote recorder (weekday routine, story A4)

Started by a scheduled session at about 14:50 IST on weekdays. Research data only: never places, modifies or cancels
orders.
1. `pip install -q -r requirements.txt -r requirements-groww.txt`
2. `python -m fno quotes record` (waits for 14:55 IST, records NIFTY monthly quotes, retries until 15:10 if a capture is
   incomplete; on a market holiday it records nothing). It prints the result line.
3. Commit `research/data/quotes/` and push to `main` (`git pull --no-rebase` first). Never edit or delete a recorded
   attempt or `.canonical` file.
4. If the result is not "recorded" with complete=True, "already recorded" or "not a trading day", post one line to
   #fno-desk (`C0C89E8QCCD`) with the result, and note it in `conversations/<date>.md`.

## Daily market brief (weekday routine)

1. `pip install -q -r requirements.txt`
2. `python -m fno daily`: re-prices paper trades and writes, under `reports/`:
   `<date>-brief.md`, `<date>-brief.html` (full page), `<date>-page.html` (Artifact body),
   `<date>-brief-NofM.png` (report split into phone-sized page images), `<date>-slack.md`, `<date>-candidates.json`.
3. Update the web version: read the Artifact https://claude.ai/artifact/8tokXxQfSPnB3DxMpkYpXX
   (`action: "read"`), then publish `reports/<date>-page.html` to it with `url` set to that link.
   If the Artifact tool is unavailable, skip this step and say so in the log.
4. Post to Slack channel `#fno-desk` (ID `C0C89E8QCCD`). Never post F&O output to `#market-brief`: that
   channel belongs to the separate market-brief tool, and its `SLACK_*` variables must not be used here.
   - If `FNO_SLACK_BOT_TOKEN` is set: `python -m fno notify` (one message: the text of
     `reports/<date>-slack.md`, the web-version link and all page images).
   - Otherwise use the Slack connector: upload the page images (`reports/<date>-brief-NofM.png`) to
     `C0C89E8QCCD`, page 1 with the Slack text plus "Interactive web version: <artifact link>" as its message,
     then the rest with short captions. Two-step upload: get upload URL, POST the bytes with
     Content-Type image/png, complete with the channel ID.
   Never upload the .html file to Slack: Slack shows HTML as code.
5. Append a short entry to `conversations/<date>.md` (create it if needed): time, top setup or "no trade",
   any paper-trade exits, the Slack links, and any errors.
6. Commit `reports/` (PNG files are git-ignored), `journal/` and `conversations/` and push.

If NSE data fails, still post a short Slack message saying the brief could not be generated and why.
If the data timestamp is not today (holiday or weekend), post the brief anyway; it marks the data as stale.

## Branch

Until PR exepex/trading#1 is merged, code and daily files live on branch `claude/beautiful-pascal-566jb5`.
After it is merged, use `main`.

## Code

- `python -m pytest -q` and `ruff check fno tests` must pass before pushing code changes; format with `ruff format`.
- No Python file or class over 350 lines (the self-contained HTML report template `fno/html_report.py` is exempt).
- Fixed strings, enum values and environment-variable names live in `fno/constants.py`; module-specific
  URLs, SQL and message templates are named constants at the top of their module.
- Names say what things do. Small single-purpose modules; new behaviour goes in a new class behind an existing
  interface (`SignalRule`, `GuardRule`, `IntradayPriceFeed`, `Provider`, `RawFileStore`, `RawFileSource`,
  `FoFileFormat`) rather than
  into an existing one. Follow SOLID, KISS and DRY: high cohesion, loose coupling, depend on interfaces.
- Concrete classes are wired together only in the composition roots: `fno/live/services.py` (the desk, backtest,
  news) and `fno/storage/wiring.py` (raw data stores and sources).
- The live desk never places real orders. The stock tool's research is read-only: never write to its repository
  or to its `market_brief` MotherDuck database. GitHub files are the default store for research input and
  results; MotherDuck is an optional trial using the shared `MOTHERDUCK_TOKEN` (no new variables).
- Settings live in `config.yaml`; see README.md for the layout.
