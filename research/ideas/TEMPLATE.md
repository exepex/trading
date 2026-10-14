# Idea card: <id> <short name>

Copy this file to `research/ideas/<id>.md`, fill every field (write "none" or "unknown" rather than leaving one
blank), and commit it **together with its ledger row** (`research/ledger.csv`; status `idea` in `research/LEDGER.md`
until R1's code adds a status field) before G1 runs. Rules: `research/FACTORY_RULES.md`. Label every claim **strong evidence**, **some evidence** or **reasoning only**.

## G0: the idea

| Field | Value |
|---|---|
| Id and version | <id> v1 (a variant is a new id) |
| Ledger trial | <trial_id> |
| Registered research question | <the question this idea belongs to; its cumulative Holm family> |
| Proposed by (role or AI) and date | |
| Who pays and why | <the counterparty and the economic reason they lose to this trade> |
| Forecast it rests on | <v4 question and forecaster, or "none"> |
| Instrument and structure | <underlying, expiry rule, legs (bought +, sold -), strikes rule; never a naked short leg> |
| Entry rule | <decision time, inputs known by then, entry price rule> |
| Exit rule | <time, target, stop, expiry handling; physical settlement if a stock option> |
| Size | <lots> |
| Worst loss in Rs | <maximum loss per trade incl. costs; must be at most Rs 10,000> |
| Expected gross per trade, with source | <figure or distribution, and where it comes from> |
| Needs a reaction faster than 60 minutes? | <yes: flagged "needs fast reaction", judged at R = 60> |
| Frequency | <trades a year; effective independent ones if trades cluster> |

## G1: feasibility screen inputs

| Field | Value |
|---|---|
| Gross payoff: distribution or conservative bound | |
| Its source | |
| Tail assumption: maximum-loss probability and size | <card's figure; the measured family rate, if any; the worse is used> |
| Round-trip cost per trade, Rs | <C1 charges per leg, entry and exit> |
| Pads per leg and their measurement | <half-spread source: A4, A16, Groww snapshot; date> |
| Volatility ideas: IV-point edge per vega per lot to clear costs | |
| **Expected net on the conservative bound, Rs** | <must be above zero to pass> |
| Gross / cost ratio | <shown; below 2 adds the warning `thin margin`; never a pass mark> |
| Result | pass / `screened_out` |

## G2: data spend

| Field | Value |
|---|---|
| Data sets the test reads | <rows of `research/DATA_SPEND.md`> |
| Status of each for the quantity measured | fresh / exposed / spent / forward |
| Result | fresh / exploratory (cannot pass G6) |

## G3: sample plan

| Field | Value |
|---|---|
| SD per trade and its source | |
| Expected net per trade used | |
| z (one-sided) | |
| n needed = (z x SD / expected net)^2 | |
| Time to reach n at the idea's frequency | <above 3 years: `exploratory_shadow` only, promoted only via rung 1> |

## G4-G6: registration, test, verdict

| Field | Value |
|---|---|
| Protocol file and frozen commit | |
| Code hash | |
| Test type | historical (fresh data only) / forward shadow / `exploratory_shadow` |
| Frozen sample (decision horizon) | |
| Pass mark | |
| Alpha-spending rule, if any (registered before collection) | <none: one judgement at the frozen sample> |
| Result and verdict | <filled once; never edited> |
