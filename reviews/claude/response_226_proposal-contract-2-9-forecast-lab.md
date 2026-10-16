# Response 226: proposal for contract 2.9, two Forecast-lab fields (for the owner; text only, nothing built)

Screens lead, 16 Oct 2026. The orchestrator asked for this after judge 217 (mockup 37 had to drop three of the owner's
13 Oct requests because contract 2.8.0 has no field for them). **Nothing is built until the owner answers.**

## What the owner asked for on 13 Oct and cannot see today

1. **A period you choose** (last week, 2 weeks, month, 2 or 3 months, since the start, or picked dates), with a table
   and a **race chart** of how each forecaster's miss score moves over time. Also one line graph of all families by
   day.
2. **"What made the difference"**: who wins and loses and why, with the costliest mistakes written as sentences ("On 2
   Nov it said 99% sure NIFTY would be higher by 2 Dec; it ended lower.").

2.8.0's `FnoForecastLab` has only today's forecasts and one score per forecaster since the start. Drawing either view
from it would mean inventing numbers, so the rebuilt mockup 37 left them out and said so.

## The two fields

**A. `questions[].scores.history[]`: the running score by session.** One row per session for each forecaster:
`{session, forecaster, n, mean_loss}`, meaning "after this session, its average miss over its n scored days".
- **It enables:** the race chart, the line graph, and the period table. The period table needs the screen to work
  out the average over the chosen dates from two rows. That is one subtraction (`(n2·m2 − n1·m1) / (n2 − n1)`);
  alternatively the field could carry `sum_loss`, so the screen only subtracts.
- **Source:** G4's daily score reports (`research/forecasts/scores/<day>.json`, already one file per day, holding
  `mean_brier` per forecaster), and later G8's v4 reports.
- **Size:** about 250 sessions × 7 forecasters × 7 questions is about 12,000 rows a year. That is too big to resend
  every day. Better: its own page (`forecast_history`, one row per session added) or only the last 250 sessions.
- **Public:** yes (strong evidence). The same numbers are already in the public repository's score files. It shows
  results, never how a forecaster decides.

**B. `questions[].settled[]`: recent forecasts with their answers.** The last N settled forecasts per question:
`{made_on, answered_on, forecaster, said, happened, loss}`.
- `said` is the probability, or the variance for v4. `happened` is yes or no, or the realised value.
- **It enables:** "costliest mistakes" sentences, and "what made the difference" cards built from them, e.g. the 3
  biggest misses and the 3 best calls per forecaster in the period.
- **Source:** the forecast records (`research/forecasts/live_v2/<year>/<day>_forecasts.csv`, already public) and
  G4's outcome resolver (`fno/forecast_scoring/resolution.py`).
- **Public:** yes for the probabilities and outcomes (strong evidence: the records are public).

## What the owner should know before choosing (brutally honest)

- **"Why" stays shallow (reasoning only).** The rule "strategy internals stay private" means these cards can say
  *what* a forecaster said and *what happened*, never *why it said it*. A card can say "Hybrid was most wrong on big
  moves in November"; it cannot say "because its volatility filter lagged". If "why" meant reasons, this can't
  deliver it.
- **Early data is noise (strong evidence).** Protocol v2 has 2 live days; G4 counted 1 of 2 days for Rule-based and
  0 for the AI books. A race chart over the first weeks will mostly show luck. The screen would need a "too few
  days" state, just like the verdicts' "not enough days yet".
- **Costliest mistakes can mislead.** One 99%-wrong call looks dramatic but may be a fair bet that lost. Each card
  should sit beside the forecaster's overall score, never on its own.
- **Cost:** about one P2 page builder plus one W3 view each. Field A is the larger, because of the size choice.

## Recommendation

**Some evidence:** build **A** first, as its own page. It answers the owner's main request (choose a period, see the
race) with numbers that already exist. **Reasoning only:** build **B** after about 60 scored days, when the misses
mean something. Until then, the empty state says why.

Owner's choice: (1) both, (2) A only, (3) neither for now.
