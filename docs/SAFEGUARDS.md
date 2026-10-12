# How the desk protects your money

Every rule below is enforced in code; the AI can make a trade more cautious but cannot switch any of these off.
The numbers come from the research in `reports/Retail FnO losses and safeguards.md` and are sized for a
**Rs 2 lakh** experiment with **Rs 50,000-70,000** in trades at any time. Settings live in `config.yaml`.

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
| No new entries after 14:45; first 15 minutes are watch-only | | The open and the close are where big players move prices |

## While a trade is open

| Rule | Setting |
|---|---|
| Stop loss | exit at -30% of the premium |
| Target | exit at +60% |
| Trailing stop | after +30%, never give back more than half the best gain |
| Overnight | at most Rs 20,000 held overnight; larger positions are closed at 15:15 |
| Holding period | at most 2 trading days, and always out the day before expiry |

## For the whole day, week and experiment

| Rule | Setting |
|---|---|
| Daily loss limit | stop for the day after -Rs 6,000 (3%) or 2 losses in a row |
| Profit lock | stop for the day after +Rs 6,000 |
| Weekly loss limit | stop for the week after -Rs 12,000 (6%) |
| Automatic kill switch | everything closes and stops for review if the last 20 trades lose money in total, or the drawdown reaches Rs 20,000 (10%) |
| Manual kill switch | `python deploy/desk.py live kill "reason"` |
| Every profit figure | after brokerage, STT (0.15% since 1 Apr 2026), exchange charges, SEBI fee, stamp duty and GST |

## Before any real money

`python deploy/desk.py live readiness` must show all of these:

- at least 100 closed paper trades over at least 13 weeks;
- net profit after every charge, with statistical confidence (t-stat 2 or more);
- profit factor 1.3 or more, and a drawdown no worse than Rs 20,000.
