# Response 163: story RM1, the real-money gate (story text, draft gate and the owner's questions)

Builder session: session_01CHxE3ywfyCMxFLx6HGLwRo · Orchestrator: session_01VG1RqxLFUVdvvPuMRYZtDH · Branch:
`story/rm1-real-money-gate` · Issue #107 · Lane 1, JUDGE.md rule 9 (judge, then ChatGPT, then the owner).

Files: `docs/stories/RM-real-money.md` (story text), `research/evaluation/REAL_MONEY_GATE.md` (draft gate),
`docs/WORK_REGISTER.md` (row). No code. Nothing here places or enables any order.

## 1. Claims for the judge's story check

| # | Claim | Evidence |
|---|---|---|
| 1 | Every 8.3 condition (1-7) and 8.4 element has one gate item with an exact rule (table in section 2) | strong evidence (read side by side) |
| 2 | No decided owner number is changed: Rs 20,000 stop, pad + Rs 0.50, 2× pad over 5 trades, 1 lot, 6 months, R = 60 fills, 31.2% tax, prediction interval, condition 5 always | strong evidence |
| 3 | Reusing S1's freeze (one more `frozen_files` entry, the freezer refusing an undecided gate) meets "frozen and hashed before the first counted paper decision" without a second freeze tool, because S1's `order` check already proves the freeze precedes each book's first counted decision | some evidence (read of `fno/evaluation/freeze.py`, `order.py`; not yet tested) |
| 4 | Judge 158's open point (several books' `beats_index_after_tax`) is answered: the gate reads one record, Book 1 or the version's shadow account | reasoning only |
| 5 | Condition 6's fact: at NIFTY lot 65, a Rs 5,000 cap allows about 76 points of maximum loss per unit; a single bought ATM monthly option usually costs more, so mainly spreads fit | some evidence (lot from `config.yaml`; premium from general market levels, not measured here) |

## 2. Trace: source → gate item

| Source | Gate item |
|---|---|
| 8.3 c1 (S1 lower bound, whole-period net, registered sample) | `paper_evidence` |
| 8.3 c2, decision 168 | `index_benchmark` |
| 8.3 c3, principle 4 (2020 and 2024 crashes) | `loss_caps` |
| 8.3 c4 | `fill_honesty` |
| 8.3 c5, decision 8 amended | `selection_adjustment` |
| 8.3 c6 | `real_cap_fit` |
| 8.3 c7 | `owner_approval` |
| 8.4 account, cap, 1 lot | `real_test_account` |
| 8.4 duration | `real_test_sample` |
| 8.4 paired test, prediction interval, slippage pad + Rs 0.50 | `real_test_pass` |
| 8.4 Rs 20,000 stop, 2× pad over 5 trades | `real_test_stops` |
| hard line; scaling and automation decisions | `scope` |

## 3. Questions for the owner (through the orchestrator; none answered by the builder)

Background: decision 8 says the account size and cap are confirmed in writing before RM1 freezes. The other
questions are gaps 8.3 and 8.4 leave open; each needs an exact rule before the freeze (ChatGPT review 98).

| Q | Question | Options | Recommendation (label) |
|---|---|---|---|
| Q1 | Real account size | (a) Rs 2,00,000; (b) Rs 1,50,000; (c) Rs 3,00,000 | (a), as 8.4 (reasoning only) |
| Q2 | Per-trade cap, all charges included | (a) Rs 5,000 (2.5%); (b) Rs 4,000 (2%) | (a): at lot 65, Rs 4,000 leaves about 61 points per unit and fewer spreads fit; the Rs 20,000 stop is then 4 full losses (some evidence) |
| Q3 | Real test minimum trades (with 6 months, the later) | (a) 20; (b) 30; (c) 12 | (a) 20; honest: even 20 finds only a large shortfall (some evidence) |
| Q4 | Condition 5 default route | (a) second untouched forward period; (b) level 0.05 ÷ trial count; (c) each registration chooses, no default | (a): cleaner; (b) at 50 ideas needs a 99.9% bound set by about 10 resamples (some evidence) |
| Q5 | Prediction interval side | (a) one-sided 95% lower; (b) two-sided 95% | (a): only real underperformance should fail (reasoning only) |
| Q6 | t-based lower bound for real money | (a) a pass condition here (both bounds above zero); (b) a warning only, as on scoreboards (decision 167) | (a): stricter only; few skewed positions make the bootstrap claim too often (some evidence) |
| Q7 | Crash-replay cap | (a) the real cap at 1 lot; (b) the paper cap Rs 10,000 | (a): the replay asks whether the real trade would have broken its cap (reasoning only) |
| Q8 | Discipline: minimum share of cards the owner places | (a) 80%; (b) 90%; (c) none, report only | (a) (reasoning only) |
| Q9 | Rs 20,000 stop measured from | (a) cumulative net from the first real entry; (b) peak to trough | (a): simplest and stricter early; (b) stops later after early gains are given back (reasoning only) |
| Q10 | May S1's owner-decided `frozen_files` list add the gate file and `fno/evaluation/gate.py`? | (a) yes, one freeze; (b) no, a separate gate freeze record and command | (a): one freeze, one order check, no duplicate tool (some evidence) |

## 4. Coordination

- Work register: no row covered RM1 (read on main at 35e999af). Overlap to agree: S6 (builder 0185gR5DmoDh2zBAvgRU4CEB)
  will later change `PROTOCOL.md` and `fno/evaluation/protocol.py`; RM1's code changes `completeness.py`,
  `freeze.py`, `cli.py` and one line of `PROTOCOL.md`'s `frozen_files`. Different lines; order of merging to be set by
  the orchestrator.
- Next: judge story check → ChatGPT (rule 9) → the owner's answers to Q1-Q10 → code.
