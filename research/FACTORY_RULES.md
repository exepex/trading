# Strategy factory rules (story R1, documents part)

Source: design v2, `docs/design_v2/03_layers_factory_desk.md` section 3.1 (layer 4), with REPLAN slice A item 4. This
file is the rule text the factory's code (R1 code, slice B) must implement. G0-G4 and G6 run by code (stories R1b and
R1c: `python -m fno factory register | screen | spend | plan | freeze | verdict`, recorded in `research/ledger.csv`,
`research/factory/gates.csv` and `research/factory/questions.csv`); G5, the test itself, is run by its own story (B4's
experiments, R3's shadows). A change to this file is lane 1 (rule
document, `docs/JUDGE.md`). Labels: **strong evidence**, **some evidence**, **reasoning only**.

Related files: idea-card template `research/ideas/TEMPLATE.md`; data-spend register `research/DATA_SPEND.md`; trial
record `research/ledger.csv` and `research/LEDGER.md`.

## 1. The gates (one recorded step each; an idea stops at the first gate it fails)

| Gate | Check | Output |
|---|---|---|
| G0 Idea card | The card of `research/ideas/TEMPLATE.md`, filled in | `research/ideas/<id>.md` and a ledger row, status `idea` |
| G1 Feasibility screen | Section 2 below | pass, or `screened_out` with the numbers |
| G2 Data spend | Section 4 below and `research/DATA_SPEND.md` | `fresh` or `exploratory` |
| G3 Sample plan | n = (z x SD / expected net)^2 from the idea's own SD estimate, and the time it takes | registered n and date |
| G4 Registration | Protocol text, code hash, ledger row committed before any result (B4's ledger guard) | ledger row naming the frozen commit |
| G5 Test | Historical on fresh data, or forward shadow (decisions recorded, never in a book) | the result, once; no retuning |
| G6 Verdict | The registered pass mark; a fail is final for that version | verdict in the ledger |

**Every idea is a trial from G0.** The ledger row is written when the card is committed, before G1 runs, so an idea
stopped at any gate still counts in the trial total ("trial k of K" on every report). The status (`idea`,
`screened_out`, `exploratory_shadow`, ...) is kept in R1's gate log (`research/factory/gates.csv`, append-only: an
idea's status is its last row), since B4's guard fixes the columns of `research/ledger.csv`. A variant (a new threshold,
filter, structure, strike rule, exit or period) is a new idea with its own card and its own row, never an edit.

## 2. G1 feasibility screen (the cost wall)

The screen is a cheap feasibility observation, not an outcome test. It never reads the outcomes the idea will be
tested on (no P&L, no hit rate, no realised moves of the test data).

**Inputs, all written on the idea card before the screen runs:**
1. **Gross payoff per trade:** a documented distribution, or a conservative bound, with its source (a published study,
   an earlier frozen result, or arithmetic stated in full). An idea with no source for its gross edge is screened out
   with the reason "no stated edge".
2. **Tail assumption:** the probability and size of the structure's maximum loss. The screen uses the **worse** of
   the card's figure and the measured maximum-loss rate of the structure's family where one exists (for example
   response 94's W5 short condor: maximum loss in 27% of RED weeks). A measured rate from a different underlying or
   regime is used only if no closer one exists, and the card says so.
3. **Round-trip cost:** C1 charges (`fno.costs`, `config.yaml` rates of the screen's date) for every leg, entry and
   exit (or settlement), plus a pad per leg from **measured** half-spreads (A4 15:00 quotes, A16 15-minute quotes, or a
   Groww snapshot for instruments those do not cover), never from a guess when a measurement exists. Physical
   settlement costs are included where a leg could be held into it.
4. **For volatility ideas:** the implied-volatility-point edge per vega per lot needed to clear the round-trip cost.

**Rule.** Expected net per trade on the conservative bound, after costs and tail losses, must be **above zero**:

    expected net = expected gross (conservative bound) - round-trip cost - expected tail loss beyond what the
                   gross figure already contains

where "conservative bound" is the lower end the card's source supports (for a measured distribution: the lower
one-sided 90% confidence bound of its mean; for a published range: its least favourable published value; for
arithmetic: the least favourable input). Expected net at or below zero gives ledger status `screened_out`, with the
numbers, and the idea stops.

**The 2x ratio is a warning only.** The ratio "expected gross at least 2 x round-trip cost" is shown beside every
result as a labelled warning, `thin margin` when it fails. It is never a pass mark and never a reason to screen out:
an idea with gross twice its cost can still lose on average once rare maximum losses are counted, and an idea with a
ratio below 2 can pass if its expected net is positive on the conservative bound.

**Cost-hurdle feasibility study (a separate case, judge 97).** When the gross edge is unknown (no source, or
published studies disagree on its sign), the least favourable edge is at most zero, so the idea itself cannot pass G1.
A registered study may still ask "would an assumed edge survive costs?" under these rules:
- the assumed edge is called an **assumed hurdle**, labelled reasoning only, never a "conservative bound" (where a
  frozen protocol written before this rule uses that phrase for such an edge, it means the assumed hurdle);
- the results report prints the break-even edge e\* = cost / price per structure beside the hurdle, and uses the name
  "assumed hurdle" for the assumed edge;
- a YES only says that a later study is worth registering. It **never counts as a G1 pass for any later idea**: a later
  idea passes G1 only on its own stated source of gross edge, under the rule above.

**What happens to a screened-out idea.**
- It **stays in the ledger and in the trial count**, with status `screened_out` and its numbers; it is never deleted
  or renumbered.
- It may still be tested by a **pre-registered counterexample study** (a new idea and a new row, registered through
  G2-G4 like any other), if someone believes the screen's inputs are wrong; the study states which input it disputes.
- Changing the card's inputs after seeing the screen's numbers makes a new idea and a new row; the old row keeps
  `screened_out`.

**Why (reasoning only, with one worked example from our data, strong evidence for the costs):** the four-leg monthly
NIFTY condor's best measured gross was +978 a trade (seen data) and +408 (holdout) against Rs 810-940 a round trip
(response 92), so its expected net was +153 and -406; on the conservative bound (the holdout) the screen stops it,
and the 2x warning flags both periods. This is hindsight: the costs were not measured this precisely before
experiment 1.

**Correction (16 Oct 2026, story R1; strong evidence: response 92 l.39-40 recomputed with
`fno/forecast_v4/student_t.py`).** The paragraph above applies the rule's averages, not its conservative bound.
- The inputs: n 33, mean gross +978, SD 2,667, cost Rs 824; and n 57, +408, SD 3,403, Rs 814.
- On the means, the nets are +154 (+153 from the unrounded means) and -406.
- The rule's conservative bound for a measured distribution is the lower one-sided 90% bound of the mean (t 1.3086 and
  1.2969). That gives +370.5 and -176.5, so the expected nets are -453.5 and -990.5.
- The screen therefore stops the condor on **both** periods, discovery included, not only on the holdout.
- The 2x warning flags both (ratios 1.19 and 0.50).
R1's `CostWall` test pins these figures.

## 3. `exploratory_shadow`

An `exploratory_shadow` is a forward, costed decision record of an idea that is not (yet) a candidate: it is recorded
daily like a shadow (experiment 2 model), never placed in a book, and counted in the trial total. Used when G2 says the
data is exploratory, when G3's sample plan is above 3 years, or for V-ideas before their forecast passes rung 1.

**Rules (all binding; each is checked by the judge at the shadow's verdict).**
1. **Frozen before collection.** The rule (entry, exit, size, structure, costs), the decision horizon (its frozen
   sample: a number of decisions or a date), the pass mark, the research question it belongs to and the ledger row
   are committed before the first recorded decision. Records made before that commit never count.
2. **It passes G1 first.** A shadow is cost-screened like any idea; a `screened_out` idea is not shadowed unless a
   registered counterexample study does so.
3. **Cumulative Holm family per registered research question.** Each shadow names one registered research question
   (for example "selling protected premium when the volatility forecast is well below implied"). The Holm family of
   that question is **every shadow ever registered on it: active, stopped, retired, already judged, and new**.
   - Holm is recomputed with the full cumulative membership at every confirmatory decision on the question.
   - A shadow that has not reached its frozen sample, or was stopped or retired before it, enters the family with
     **p = 1**.
   - Earlier verdicts stay recorded as given and are never relabelled when the family grows.
   - Why: a family that reset at each judgement would give every new batch a fresh 5% chance; one limited to running
     shadows would let someone register 20, stop the 19 weak ones and judge the survivor alone.
4. **One judgement per hypothesis, at its frozen sample.** A shadow is judged once, when its decision horizon is
   reached; no interim re-judging of an attractive early result. The only exception is an alpha-spending rule (for
   example O'Brien-Fleming boundaries) registered before collection, with its looks and their alpha written down.
5. **Stopping is recorded.** A shadow stopped before its frozen sample keeps its row, its records and its place in the
   family (p = 1), with the date and reason of the stop.
6. **A change after looking is a new idea.** Looking at a shadow's records and then changing anything frozen in rule 1
   (rule, threshold, structure, sample, pass mark, question) makes a new idea card and a new ledger row; the old shadow
   is stopped (rule 5) or runs on unchanged. Records of the old shadow never count for the new one.
7. **No promotion without its gates.** A V-idea shadow is never promoted, and never paper-eligible, until its forecast
   has beaten its baseline (rung 1) and its own economic test has passed. Any other shadow is promoted only through
   its registered pass mark plus the "second, independent test" of section 5.

## 4. G2 data spend

`research/DATA_SPEND.md` holds one row per data set. A test on a data set marked `spent` or `exposed` for the
quantity the test measures is labelled **exploratory** and cannot pass G6; it can at most justify a fresh test
(forward, or on a data set still `fresh`). Every registration adds or updates its data-spend rows in the same commit
as its ledger row.

## 5. Multiple testing across the factory

- Within a registered batch: Holm across the batch's primary tests.
- Judged shadows: the cumulative family of section 3, rule 3.
- Every factory report shows "trial k of K" and the number of false passes expected by chance at the pass level (for
  example 53 trials at 1% one-sided: about 0.5 expected false passes).
- A single pass among many fails is treated as "needs a second, independent test" before paper.
