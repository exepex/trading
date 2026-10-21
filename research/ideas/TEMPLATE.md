# Idea card: <id> <short name>

Copy this file to `research/ideas/<id>.md`, fill every field (write "none" or "unknown" rather than leaving one
blank), fill its `factory` block below, and register it with `python -m fno factory register <id>` (story R1): that
writes its ledger row (`research/ledger.csv`) and its `idea` row in the gate log (`research/factory/gates.csv`, where
an idea's status is its last row); commit the three files together before G1 runs. Rules: `research/FACTORY_RULES.md`. Label every claim **strong evidence**, **some evidence** or **reasoning only**.

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

## Machine block (story R1)

Read by `python -m fno factory`; a card without exactly one valid block is refused with the field named. The G0 fields
are checked at `register`; each later input only when its gate runs (`screen` G1, `spend` G2, `plan` G3), and a
missing one is refused by name, never defaulted. Commit the card's inputs before its gate runs: each gate runs once,
and changing an input after seeing its numbers makes a new idea. `trial` is the next ledger trial number;
`experiment` and `question` are lower-case words joined by hyphens; `hypothesis` is yes when the idea tests an edge;
`measurement` is yes for a measurement (never screened, never promoted).

- `gross.kind`: `measured` (with `mean`, `sd`, `n`: the screen uses the lower one-sided 90% t bound of the mean),
  `published` or `arithmetic` (with `least_favourable`), `none` ("no stated edge") or `assumed_hurdle` (a cost-hurdle
  study, never a G1 pass); always a `source`.
- `tail`: the maximum loss's `probability` and `loss` (rupees a trade), `in_gross` (yes when the gross figure already
  contains it, as a measured history does), and `family_probability` with `family_source` where a measured rate of
  the structure's family exists (the worse rate is used). Not needed when no edge is stated.
- `cost`: either `measured` with its `source` (a measured round trip), or `legs`, each with `instrument`
  (`index_option` or `stock_option`; a stock option cannot use `settlement`, since C1 has no physical-settlement
  charge yet, so its card states a measured cost), `side` (buy or sell),
  `units`, `entry` premium, `exit` premium or `settlement` (intrinsic value a unit, cash-settled), and its measured
  half-spread `pad` with `pad_source`; C1's charges come from `config.yaml`.
- `data_sets`: rows of `research/DATA_SPEND.md` as "data set | price type | period"; `measures`: the quantity tested.
- `sd_per_trade`, `frequency_per_year` and `pass_level` (one-sided, for example 0.01) for the sample plan.
- For a shadow's freeze (`freeze`, G4): `playbook_name` and `playbook_version` (its research playbook version; the
  shadow account is `shadow:<name>-v<n>`) and `minimum_useful_net` (rupees a trade, the stop rule's Test B). The
  card's `question` must be registered with `python -m fno factory question`, and its `pass_level` must equal that
  question's alpha: the verdict (`verdict`, G6) is Holm across every shadow ever registered on the question.

```factory
id: <id>
version: 1
trial: <next trial number>
experiment: <experiment-slug>
description: "<one line for the ledger>"
question: <research-question-slug>
hypothesis: yes
measurement: no
gross: {kind: measured, mean: <rupees>, sd: <rupees>, n: <trades>, source: "<where>"}
tail: {probability: <0-1>, loss: <rupees>, in_gross: yes}
cost: {measured: <rupees>, source: "<where>"}
data_sets: ["<data set> | <price type> | <period>"]
measures: "<the quantity the test measures>"
sd_per_trade: <rupees>
frequency_per_year: <trades a year>
pass_level: 0.01
```

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
