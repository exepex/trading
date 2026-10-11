# Project instructions

This repo is an F&O options research assistant for the owner's Indian trading experiment (broker: Groww).
It is research and paper trading only: never place orders, never ask for or store broker credentials in files.

## Keep a conversation log (every session)

Before ending any working session with the user, write or append to `conversations/YYYY-MM-DD.md`
(IST date): quote the user's messages as written, condense your replies to their substance, and update the
"Decisions so far" and "Open questions" sections. Commit and push it. Never include email addresses,
API keys or tokens.

## Daily market brief (weekday routine)

1. `pip install -q -r requirements.txt`
2. `python -m fno daily`: re-prices paper trades, writes `reports/<date>-brief.{md,html}`,
   `reports/<date>-candidates.json` and `reports/<date>-slack.md`.
3. Post to Slack channel `#market-brief` (ID `C0C6REB7QS2`): upload `reports/<date>-brief.html` with the
   contents of `reports/<date>-slack.md` as the message.
4. Append a short entry to `conversations/<date>.md` (create it if needed): time, top setup or "no trade",
   any paper-trade exits, the Slack link, and any errors.
5. Commit `reports/`, `journal/` and `conversations/` and push.

If NSE data fails, still post a short Slack message saying the brief could not be generated and why.
If the data timestamp is not today (holiday or weekend), post the brief anyway; it marks the data as stale.

## Branch

Until PR exepex/trading#1 is merged, code and daily files live on branch `claude/beautiful-pascal-566jb5`.
After it is merged, use `main`.

## Code

- `python -m pytest -q` must pass before pushing code changes.
- Settings live in `config.yaml`; see README.md for the layout.
