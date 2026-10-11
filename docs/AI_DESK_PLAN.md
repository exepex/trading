# AI desk plan

Status: proposal, agreed direction pending three owner decisions (see the end).

## Goal

A personal, AI-first F&O research desk for one retail investor. The AI does the heavy lifting: it reads all the
information, links the dots a human would miss, explains the market in plain language, learns from every day's
paper trades, and keeps its history so later decisions improve. Accuracy and net profit after all charges are
measured, never assumed.

## Principle

The AI decides as much as possible about **what** and **why**; code keeps the money-safety rules. The AI may make a
trade more cautious (skip, wait, tighter stop, early exit). It may never enlarge a trade, override a stop, or break
the position rules, daily loss limit, profit lock or concentration limits.

## Roles and daily cycle (IST)

| When | Role | Output |
|---|---|---|
| 08:30-09:10 | Pre-market strategist | Market map: likely direction, favoured/avoided sectors, 10-15 catalyst stocks, key levels, risk events; feeds the scanner as an `ai_premarket` signal and watchlist |
| Live, per candidate | Trade analyst | take / skip / wait, confidence, reasons, what would prove it wrong, optional tighter stop |
| Live, on material news | Position guardian | thesis intact or broken; early exit when broken |
| 15:45-16:30 | Post-market reviewer | grades trades, signal accuracy and missed opportunities (biggest option moves not caught, and why); short validated lessons |
| Daily | Plain-English reporter | simple report: what happened, why, what we learned, tomorrow's plan (Slack + GitHub) |
| Weekends | Weekly researcher | which setups make net money in which conditions; proposed rule and weight changes for approval |

## Reliability

- Facts come from code, reasoning from the AI: a context pack of verified numbers goes in; structured JSON comes
  out; every number the AI quotes is checked against the pack before use.
- The AI's calls are graded like a signal (view outcomes at 30/90 minutes and trade net P&L), so its value is
  measured against the rules alone.
- No look-ahead: only information available at decision time.
- Memory: reports, lessons and decisions stored in GitHub; relevant past lessons (same stock, setup, conditions)
  are given to the AI before each decision.

## Open decisions

1. Runtime: Claude Code on the Mumbai server with the owner's subscription (recommended start) or the Claude API.
2. AI authority in the paper month: may skip/delay entries and trigger early exits automatically; never enlarge
   trades or override limits.
3. Rule-change approval: weekly Slack summary + GitHub PR approved by the owner, or small automatic weight changes
   within fixed bounds.
