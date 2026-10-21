# IL. Innovation Lab: one pipeline from idea to proven

**Status:** design text only, no code (owner, 21 Oct 2026, DESK_DECISIONS 93e01804: "design now, build later"; built
after the phase-1 review). **Owner of this text:** the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd).

**What it is.** One research and development pipeline above the forecast lab (FL1, G13, G13b) and the strategy work
(D1, R1, the books). All three families (rule-based, hybrid, AI) run candidates in the background. Nothing reaches the
owner until it has passed every gate. A **candidate** is a family, an output kind and a method version (its
`method_sha256`, or its playbook version fingerprint). Changing a rule or a setting makes a new candidate. The
selector ("which method when") is a candidate too, with the same gates. There is one registry (R1's ledger), one set
of gates (R1's gate log, extended) and one board, for all families. There are never three machines.

## 1. Stages and gates

| Stage | Gate to pass (all written before the data it judges is seen) | Existing piece |
|---|---|---|
| 0. Registered | Idea card and ledger row committed before any test; it becomes trial k of K, counted for life | R1 G0 (`fno/factory/registration.py`), B4 ledger guard |
| 1. History test | Screen, data spend and sample plan (R1 G1-G3), then the test on history with C1 costs; exploratory data never passes | R1 G1-G3; S3 standard unit; G4 bootstrap |
| 2. Held-out history | The last part of history, named in the sample plan before stage 1 runs, opened once, after the freeze (G4) | gap a |
| 3. Live sealed shadow | Every output sealed by GitHub push time before its outcome exists; paper only, in its own record or account; a minimum live sample per output kind (below) | G13b sealing, G10 commitment, F1 commitments, R3 shadow accounts |
| 4. Confirmation | A second, untouched forward period of the same version and the same sample size passes on its own; a judge audits the evidence; Holm within the question's family; K and the expected false passes are stated | RM1 condition 5, R1 G6 verdict, `fno/scoreboard/uncertainty.py`; judge results audit is gap c |
| 5. Proven | Shown to the owner: forecasts in #fno-forecast, signals on the card, warnings in #fno-desk. A strategy also needs D1's owner move to paper; real money still needs RM1 | D1 transitions, T1 card, FL1 report |
| 6. Demoted | Automatic return to shadow on decay, with the owner told. Coming back means a new stage 4 | E6 auto-pause (losses and drift only); LR3 CUSUM (designed); gap d |

**Each output's own success measure** (all after costs where money is involved, all against a baseline fixed at
registration):

| Output | Measure | Must beat |
|---|---|---|
| Forecasts and ranges | Proper scores: quantile score or pinball loss for ranges, Brier for P(up); coverage of the 50% and 90% bands inside their binomial limits | A named baseline (G13b's `no_change`, `rv20`): block-bootstrap lower bound of the score difference above zero (G4) |
| Trade signals | Net rupees per eligible opportunity, one standard unit, C1 charges, missed entries counted in the denominator (S1 item 10); worst loss within the caps | Do-nothing and the random control (S6), lower bound above zero; RM1's conditions for real money |
| Market warnings | Brier score of the warned event (for example a 2% NIFTY move), hit rate and false-alarm rate, lead time | The base rate (M1's v0 climatology) |
| Selector | The measure of the output it selects, on choices made after its own registration only | The best single member, fixed in advance, and the plain equal-weight mix |

**Minimum live samples (proposals for the owner):** forecasts 60 sessions for a first calibration read and 250 for
an edge claim; trade signals as RM1 sets them; warnings 20 warned events.

## 2. Map of existing pieces

| Piece | Files | Stage | State |
|---|---|---|---|
| R1 factory: idea cards, gate log, trial k of K, Holm per question family | `fno/factory/`, `research/ledger.csv`, `research/factory/gates.csv` | 0, 1, 4 | built (R1a-c merged); no question family registered yet |
| B4 ledger guard (registration by git ancestry) | `fno/research_engine/ledger.py` | 0 | built |
| D1 playbook statuses and owner-only moves | `fno/playbook/transitions.py`, `registry.py` | 5, 6 | built; covers strategies only |
| S1 protocol, freeze, review dates | `fno/evaluation/`, `research/evaluation/PROTOCOL.md` | 1-4 | partial: tooling built, protocol not frozen |
| RM1 real-money gate (second untouched period) | `research/evaluation/REAL_MONEY_GATE.md`, `fno/evaluation/gate.py` | 4, 5 | built; active once S1 freezes |
| S2 board B, S3 board A, S6 controls, Holm | `fno/scoreboard/` | 1, 4 | built; thresholds not frozen |
| Sealing by push time; receipts | `fno/price_ranges/sealing.py`, `seals.py`, `fno/health/evidence.py`, `fno/storage/receipts.py` | 3 | built (O9 step 2b not started) |
| v4 forecasts and scores (confirmatory family, looks) | `fno/forecast_v4_rules/`, `fno/forecast_v4/`, `fno/forecast_scoring/v4/` | 1, 3, 4 | partial: v4 not frozen, not live |
| G4 block bootstrap with Holm | `fno/forecast_scoring/block_bootstrap.py` | 1, 4 | built |
| G13, G13b, FL1-1 (ranges, sealed, scored per method version) | `fno/price_distribution/`, `fno/price_ranges/`, `fno/forecast_lab/` | 1, 3, 5 | built; live from 22 Oct |
| M1 weather (P of a 2% move) | `fno/weather/` | 1, 3 | partial: back-fill only, not live |
| M2 alerts, LM1 monitor (warnings to the owner) | `docs/stories/M-weather.md`, `LM1-position-monitor.md` | 5 | missing (text only) |
| Books: Book 1 rules, D4 envelope, D5 constitution and Book 3 registry | `fno/books/`, `fno/checks/validity_*.py`, `fno/book3/` | 0, 3 | built; D4 and D5 switched off; Book 2 decider missing (F5) |
| R3 forward shadows in their own accounts | `fno/desk/shadow_books.py` | 3 | part A built, part B waiting on E8 |
| F1/G5 AI forecasts, F8 meter, F9a role value | `fno/ai/`, `fno/budget/`, `fno/role_value/` | 3, 4 | built (F1t trading runner missing) |
| E6 scorecards and automatic pause | `fno/scorecard/pauses.py` | 6 | partial: losses and drift only |
| LR3 drift detection (CUSUM) | `docs/stories/LR-learning.md` LR3 | 6 | missing (text merged, code waiting) |
| LR1 weekly post-mortem | `fno/learning/` | 6 (input) | built |
| Judges | `docs/JUDGE.md` | 4 | partial: code and text review only, no results audit |
| Selector | none | all | missing |

## 3. The true gaps (and only these)

| Gap | What is missing | Size | Owner to agree with |
|---|---|---|---|
| a. Held-out history | R1's sample plan (G3) gets a held-out window and a one-look check at G4 | small | R1 (01XFXpbk) |
| b. One registry for every kind | Forecasters (G13b methods, v4 rules, M1, AI forecasters) are versioned by method SHA but are not ledger trials. Each new method version registers a ledger row with its kind, plus three new gate names in the gate log (shadow, confirmed, demoted). This is R1's ledger and gate log, not a new store. It first needs a fix of the ledger's id seam (below). | small to medium | R1, D5 (01SFDjjZ), G13b (01UkTaDe) |
| c. Results audit | A judge checklist in `docs/JUDGE.md`: registration ancestry, seal times, sample size, scoring code hash, no peeking at the held-out part | small (text) | orchestrator, judges |
| d. Demotion on statistical decay | LR3's CUSUM code (already designed), connected to E6's pause for strategies and to a "demoted" gate row for forecasters and warnings. It needs an owner answer (Q2). | medium (LR3's own build) | LR3 / D4-D5 builder (01SFDjjZ), E6 (0134MoC6) |
| e. Warnings output | M2's alert, scored as M1 is | medium (M2's own build) | M2 (0145TfSw) |
| f. The board | One read-only page that lists every candidate with its stage, measure and next gate, read from the ledger, the gate log and the existing score files (no new scoring) | small to medium | S2/S3 (0185gR5D) for the score readers |
| g. Selector | A candidate whose output is the chosen member's output, registered and sealed like any member; built last | medium, later | none yet |

**A seam bug found while mapping (fix before gap b; not mine to fix):**
- `fno/factory/registration.py:42` takes the next trial id as `int(max trial_id) + 1`.
- `fno/book3/registry.py:95` writes `book3:<id>` rows into the same `research/ledger.csv`.
- So the first Book 3 registration would make every later R1 registration raise `ValueError`.
- Also, K counts every ledger row, including retrospective trials and measurements.

Reported to R1's and D5's owners and the orchestrator.

**No new machinery beyond these.** Sealing, scoring, bootstraps, Holm, the freeze, the shadow accounts and the
real-money gate exist and are reused as they are.

## 4. Honest limits

- **False winners from many trials.**
  - At a 5% test level, K independent trials give about 0.05 × K false passes at stage 1.
  - A false winner must also pass the untouched second period, so about 0.0025 × K reach "proven". At K = 100 that
    is about 0.25: rare, not impossible. Reasoning only; it assumes independent periods.
  - RM1's owner decision (15 Oct) makes the second period the only luck control for real money, and rejects a
    0.05 ÷ m level. The Innovation Lab uses the same rule, plus Holm inside each question family and K stated on
    every verdict.
- **Evidence is slow.**
  - About 250 sessions a year. A daily forecast needs about 60 sessions for a first calibration read and 6-12 months
    for an edge.
  - A strategy that enters monthly gets about 12 trades a year, so its proof takes years.
  - The second period doubles every one of these.
  - Most candidates will take a year or more to be proven. Many never will, and that is the system working.
- **Selector overfitting.**
  - A selector that picks among N members carries their trial count too.
  - It is judged only on choices made after its registration, and needs more data than any member.
  - It should not be built before at least two members are proven.
- **AI cost.** There is no cap for now (owner). F8's meter reports it daily. AI shadows run for months at low odds
  of passing, so the cost is real even when nothing is proven.
- **The past is not the future.** Proof holds only while the market behaves as it did. Demotion catches decay late,
  by design: CUSUM needs evidence before it fires.
- **Shadow is not real execution.** Paper fills (E4, E8) are an estimate. RM1 stays the gate for real money.

## 5. Open questions for the owner

1. **Luck control:** keep RM1's rule (second untouched period only) for the whole lab, or add a correction over the
   trial count K? Recommendation: keep RM1's rule (some evidence: at 50 ideas a Bonferroni level needs a 99.9%
   bootstrap bound set by about 10 resamples, a noisy rule).
2. **Automatic demotion:** may statistical decay (LR3) move a proven candidate back to shadow without you, given that
   S1 says only the owner pauses for statistics? Recommendation: yes, back to shadow with an alert. Paper only, so
   nothing is lost, and you decide any return.
3. **Minimum live samples:** are 60 / 250 sessions for forecasts and 20 warned events for warnings right?
4. **Held-out share:** the last 25% of history, at least one year? Recommendation: yes.
5. **Selector:** wait until two members are proven? Recommendation: yes.
6. **Where "proven" shows:** #fno-forecast for forecasts, the card for signals, #fno-desk for warnings. Is that
   right?

## Dependencies (work register owners)

R1 (01XFXpbk), D1 and the playbook (via the orchestrator), S1 text and S3 (0185gR5D), RM1 (01CHxE3y), G13 and G13b
(01UkTaDe), M1 (013xqaNT), M2 and LR1 (0145TfSw), LR3, D4 and D5 (01SFDjjZ), E6b and F8 (0134MoC6), G8 and G10
(01VK88Lx), O9 (01WHmxEY), FL1 (01FWkBH4).
