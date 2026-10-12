# How the desk protects your money

Every rule below is enforced in code; the AI can make a trade more cautious but cannot switch any of these off.
The numbers come from the research in `reports/Retail FnO losses and safeguards.md` and are sized for a
**Rs 2 lakh** experiment with **Rs 50,000-70,000** in trades at any time. Settings live in `config.yaml`.

## Paper phase vs real money

The numbers below are the **live** profile: the limits for real money. While the framework is being built and
tested, `config.yaml` runs the **paper** profile, which changes the money limits (and allows a few more trades a day and week, to collect more evidence) so that BANKNIFTY and
FINNIFTY lots fit and more trades get graded:

| Setting | Paper (now) | Live (real money) |
|---|---|---|
| Capital | Rs 5 lakh | Rs 2 lakh |
| Most one trade may lose at its stop (2%) | Rs 10,000 | Rs 4,000 |
| Most in trades at once | Rs 1,00,000 | Rs 70,000 |
| One exceptional lot (strong evidence) | up to Rs 30,000 | up to Rs 25,000 |
| New trades per day / week | 3 / 12 | 2 / 8 |
| Daily loss limit and profit lock | Rs 15,000 | Rs 6,000 |
| Weekly loss limit | Rs 30,000 | Rs 12,000 |
| Held overnight | Rs 50,000 | Rs 20,000 |
| Automatic stop on drawdown | Rs 50,000 | Rs 20,000 |

Stops, targets, time exits, contract filters and guards are identical in both. Before going live the settings
switch to `profile: live`. The go-live drawdown test is a percentage of capital (10%), so it scales with the profile.

**Shadow book.** Besides the real paper book, the desk quietly records one lot of *every* idea that passes the
signals and guards (`journal/shadow_trades.json`), even ones the limits turned away, and closes it on the same
exit rules. It has no limits and sends no Slack messages. It exists only to measure which signals work, faster.

## Before a trade

| Rule | Setting | Why (in plain words) |
|---|---|---|
| Never more than 2% of capital lost on one trade | Rs 4,000 at the stop; the desk picks a cheaper strike or fewer lots to fit | A string of losses can never sink the account |
| At most 2 new trades a day, 8 a week | | SEBI: traders active on 100+ days a year caused 87% of all losses |
| Pause 45 minutes after any losing trade | | Stops "revenge trading" after a loss |
| No trade on expiry day; at least 4 days to expiry | | 59% of option trading happens on expiry day, where time decay is fastest |
| Skip options losing more than 12% of their value per day to time decay | | Time decay quietly eats option buyers |
| Only near-the-money options (delta 0.30 or more), premium at least Rs 25 | | Cheap far-away options are lottery tickets that usually expire worthless |
| Bid-ask gap at most 2% (index) / 5% (stock) | | Wide gaps cost money on entry and exit |
| No buying when options are priced far above the stock's real moves (1.3x) | | Expensive options lose value even when the direction is right |
| No trade within 3 days of a company's results, or around big scheduled events | | Option prices collapse after the news (India VIX fell ~30% on election results days) |
| No trade on stocks in the F&O ban list, in a stressed market, or on high-impact geopolitical news | | |
| At most 3 trades betting the same way, at most 2 index trades | | Several index calls are really one bet |
| At most 2 open trades per industry family (BANKNIFTY and FINNIFTY count with bank and finance stocks) | `max_per_family` | Three bank stocks and BANKNIFTY are one bet on banks |
| Never buy without a real bid/ask to check the spread (Groww: the contract's live quote) | `require_bid_ask` | Paper results must be priced as a real order would be |
| No buying when options are dear against their own history (IV rank above 80, once 60 days are stored) | `iv_rank` guard | Dear options lose value when volatility falls back |
| Only when the last hour trended (5-minute path efficiency 0.30 or more; nothing in the first 30 minutes) | `sideways_day` guard | Sideways markets let time decay eat the premium |
| The +60% target may need at most 1.5x the move the market expects over the 2-day hold | `max_needed_to_likely_move` | Unrealistic targets mean the option decays while waiting |
| No entry for 15 minutes after credible big news whose direction is unclear | `news_shock` guard | Let the market digest it first |
| No new entries after 14:45; first 15 minutes are watch-only | | The open and the close are where big players move prices |

## While a trade is open

| Rule | Setting |
|---|---|
| Stop loss | exit at -30% of the premium |
| Target | exit at +60% |
| Trailing stop | after +30%, never give back more than half the best gain |
| Overnight | at most Rs 20,000 held overnight; larger positions are closed at 15:15 |
| Bad news | credible news scoring -0.5 or worse against the trade closes it early (`adverse_news`) |
| Pricing | exits at the real bid; if the live quote fails, at last price minus slippage, so a stop is never skipped |
| Holding period | at most 2 trading days, and always out the day before expiry |

## For the whole day, week and experiment

| Rule | Setting |
|---|---|
| Daily loss limit | stop for the day after -Rs 6,000 (3%) or 2 losses in a row |
| Profit lock | stop for the day after +Rs 6,000 |
| Weekly loss limit | stop for the week after -Rs 12,000 (6%) |
| Automatic kill switch | everything closes and stops for review if the last 20 trades lose money in total, or net results are currently Rs 20,000 (10%) below their best point; after a person resumes it (`live resume`) only later trades count. A trade that cannot be priced is retried every review until it closes |
| Manual kill switch | `python deploy/desk.py live kill "reason"` |
| Every profit figure | after brokerage, STT (0.15% since 1 Apr 2026), exchange charges, SEBI fee, stamp duty and GST |

## Before any real money

`python deploy/desk.py live readiness` must show all of these:

- at least 100 closed paper trades over at least 13 weeks;
- net profit after every charge, with statistical confidence (t-stat 2 or more);
- profit factor 1.3 or more, and a worst-ever drawdown no worse than 10% of capital (Rs 20,000 live, Rs 50,000 paper).
