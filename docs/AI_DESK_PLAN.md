# AI desk plan

Status: agreed design (12 Oct 2026); not built yet.

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

## Data by phase (owner's model, 12 Oct 2026)

| Phase (IST) | What decides | News and data used |
|---|---|---|
| Overnight to 08:30 | the world moves | stock tool: news runs every 4 h (world, India, filings) and its 07:40 pre-open analysis, read from GitHub; fast news watcher keeps collecting overnight headlines |
| 08:30-09:15 pre-market | strategist: day plan for NIFTY, BANKNIFTY, FINNIFTY and catalyst stocks | stock tool's pre-open results and news; US close; Asia live (Nikkei, Kospi, Hang Seng); US futures, crude, gold, dollar, USD/INR, US yields; India VIX; results/events calendar |
| 09:15-09:30 opening | no entries; opening range forms; open checked against the plan | Groww prices and option chains; fast news |
| 09:30-15:15 session | scanner, trade analyst, position guardian | Groww every scan; fast news watcher (minutes) for open trades, shortlist, indices and world-risk themes |
| 15:45-16:30 evening | reviewer: what went right/wrong and why, missed moves | the day's trades, views, news timeline; stock tool's post-close run |
| Weekend | weekly researcher | the week's graded signals, AI calls and news-source speed table |

The stock tool and the F&O desk share the slow, verified layer (the stock tool's GitHub data); only the F&O desk
needs the fast layer (Groww and minute-level news), because options magnify moves and decay with time.

## Before the AI layer: what an option buyer still needs (recommended 12 Oct 2026)

In priority order. Each new rule is graded like every other signal and kept only if it earns its place.

1. **Realistic fills and IV history**: price paper entries/exits at Groww's bid/ask (quote call) and start storing
   one end-of-day ATM implied-volatility snapshot per underlying now, so IV rank is possible in ~3 months.
2. **Day-type filter (trend vs range)**: option buyers lose most on sideways days (time decay plus spreads). Classify
   each underlying after the opening range: directional efficiency of the first hour, opening-range width vs
   average range, VIX. Buy options only on trending conditions.
3. **Move needed vs move likely**: before entry, the underlying move the option needs to reach its target within the
   holding time (delta, gamma, theta) against the move the market expects (ATM straddle, recent intraday range).
   Skip trades that need most of the expected move.
4. **One bet, not three**: count correlated trades as one (bank stocks + BANKNIFTY; IT stocks together): at most two
   open trades per sector or index family.
5. **FII/DII derivatives positioning**: NSE's free daily participant-wise open interest (FII index futures long/short,
   index options) as a pre-market bias for NIFTY/BANKNIFTY/FINNIFTY.
6. **Price-shock detector**: Groww live feed (up to 1,000 instruments, push); a sudden move protects open trades within
   seconds and pulls the news for that name.
7. **Backtest harness**: replay the rules on Groww historical candles to give weights an evidence-based start instead
   of waiting 13 weeks of paper trading.
8. **Time-of-day and expiry-week statistics**: record when trades are opened and how they do (opening hour, midday,
   last hour; days to expiry) so the desk learns its good and bad hours.

## Reliability

- Facts come from code, reasoning from the AI: a context pack of verified numbers goes in; structured JSON comes
  out; every number the AI quotes is checked against the pack before use.
- The AI's calls are graded like a signal (view outcomes at 30/90 minutes and trade net P&L), so its value is
  measured against the rules alone.
- No look-ahead: only information available at decision time.
- Memory: reports, lessons and decisions stored in GitHub; relevant past lessons (same stock, setup, conditions)
  are given to the AI before each decision.

## Owner decisions (12 Oct 2026)

1. Runtime: the owner's always-on PC with Claude Code (subscription). Cloud VM or API only after a proven record.
2. AI authority: may skip or delay entries and trigger early exits automatically; never enlarge trades or override
   limits.
3. Rule changes: Claude may open and merge pull requests itself within fixed bounds:
   - allowed: signal weight change up to +/-50% per week within 0-2; disable a rule the accuracy report shows is
     noise; entry thresholds within fixed ranges;
   - owner approval: anything touching money rules (sizes, rupee limits, stops, daily limits), any loosening of
     safety rules, and promoting a new strategy to live.

## How strategies are created

Idea (AI reviews or owner) -> exact specification (entry, contract choice, exits; one versioned file) ->
backtest on history (Groww historical candles) -> shadow paper trading beside the live strategies -> promoted only
if it beats them on net profit after charges over enough trades; retired the same way.

## Before real money

Groww accepts API orders only from a whitelisted static IP: real trading needs a static IP (ISP add-on, Groww
Cloud, or the Mumbai VM). Paper trading and research do not.
