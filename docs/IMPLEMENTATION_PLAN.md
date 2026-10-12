# Implementation plan: desk design v2.1 as stories

Status: **draft for ChatGPT review** (12 Oct 2026). Source: `docs/DESK_DESIGN.md` v2.1 (owner-approved framework).
The owner started development on 12 Oct 2026 ("we can start development"); the AI layer (epic F) stays on hold
until the owner says otherwise.

**Every story's definition of done:** tests and `ruff` pass; no file or class over 350 lines; new behaviour behind an
interface, concrete classes wired only in `fno/live/services.py` or `fno/storage/wiring.py`; fixed strings in
`fno/constants.py`; docs updated; any research trial registered in `research/LEDGER.md` before its result is read;
the other AI reviews the result in the repository.

Sizes: S = under a day, M = 1-3 days, L = more. Status: done / doing / next / later / on hold.

## Milestones
| Milestone | Stories | Outcome |
|---|---|---|
| M1 Data and first experiment | A1-A6, B1-B5, C1 | Experiment 1 run on 2024-26 (discovery) and 2019-23 (challenge) with the frozen protocol |
| M2 Risk, playbook, validity | C2-C4, D1-D3 | A strategy that passed can be written as a playbook version and checked by code |
| M3 Code-only paper desk | E1-E4 | Daily 3 pm paper decisions on the first approved strategy, no AI |
| M4 AI layer (on hold) | F1-F5 | Only after the owner starts it; each role kept only if it adds net value |

Start now, because only time builds it: **A4** (record real 3 pm bid/ask quotes every trading day).

## Epic A: data foundation (data and backtesting engineer)
| # | Story | Acceptance criteria | Depends | Size | Status |
|---|---|---|---|---|---|
| A1 | Raw NSE archive complete | Laptop tool fetches current F&O (2024+), old F&O (2019 to 5 Jul 2024), index closes incl. India VIX (2019+); originals unchanged in Drive; a coverage command lists missing days per dataset and checks zip integrity | - | S | doing (tool done; owner downloading) |
| A2 | One reader for both formats | Old and current files read into the same columns; proven identical on all overlap days; damaged files refused whole | - | M | done (128/128 days) |
| A3 | Option-chain panel | From raw files (Drive first): every NIFTY option row per day, all strikes and expiries, with underlying from the index close; each value carries its availability time (end of day); rebuilt deterministically; derived file kept with the research, not in `raw/` | A1, A2 | M | next |
| A4 | 3 pm quote recorder | Each trading day at about 3 pm, record bid, ask, last price and time for NIFTY monthly options near the money through the existing `Provider` interface; stored as raw files; never places orders | - | M | next (start early) |
| A5 | Expiry identity in the package | `monthly_as_of` moved from research into `fno` with its tests; research imports it | - | S | next |
| A6 | Events calendar | `events.csv` of RBI policy announcements, Union Budgets and general-election results, 2019-2026, each with its official source; committed before experiment 1 reads results | - | S | next |

## Epic B: research and discovery engine (quant, statistician, modeller)
| # | Story | Acceptance criteria | Depends | Size | Status |
|---|---|---|---|---|---|
| B1 | Feature library | Each feature (implied vs past realised volatility, VIX level, event in window, more later) is a small class with a name, inputs, availability time; a test proves no feature reads data after its decision time | A3, A6 | M | later |
| B2 | Cycle simulator | Monthly cycle per protocol: decision day, next-day close entry, exit at 21+ days, Rs 1 pad per leg, real charges, settlement price for untraded legs (flagged), "bad prices" rule, width rule for the Rs 10,000 cap; tested on hand-worked examples | A3 | M | later |
| B3 | Policy runner and verdict | Runs registered policies and controls (coin toss, opposite), computes metrics, cycle bootstrap and the protocol's pass/fail; outputs a deterministic results file | B1, B2 | M | later |
| B4 | Ledger automation | A trial cannot run unless registered in the ledger first; counts trials per experiment | - | S | later |
| B5 | Experiment 1 | Protocol frozen after review; discovery run 2024-26 published; challenge run 2019-23 once A1 is complete; results reviewed by ChatGPT | B1-B4 | M | doing (protocol in review) |
| B6 | Candidate scan | Systematic feature x structure x action combinations on discovery data, each counted; stricter bar as trials grow; survivors go to the roles | B3 | L | later |

## Epic C: code roles (deterministic)
| # | Story | Acceptance criteria | Depends | Size | Status |
|---|---|---|---|---|---|
| C1 | Cost and tax accountant | Three ledgers: trade P&L after charges and pads; account result after operating costs (AI, data bills entered as actual amounts); yearly tax at 31.2% on net F&O profit with losses offset within the year | - | S | later |
| C2 | Risk manager | Per-trade cap Rs 10,000 incl. costs; at most 3 open; drawdown brake Rs 30,000 below the closed-equity high (blocks entries only, owner restart, re-arm rule); portfolio stress with full repricing (NIFTY +/-5% and +/-8%, IV x2 and x0.5, joint shocks, time, replays of 23 Mar 2020, 4 Jun 2024, Feb 2026); exposure limits as configurable values; margin tracked apart from loss | B2 | L | later |
| C3 | Data checks | Data present, fresh and consistent before any decision; stale prices marked and never used as fills | A3, A4 | S | later |
| C4 | Hard-validity checks (judge part 1) | Dates, contracts, arithmetic, funding and owner limits re-checked independently of the code that proposed the trade; a failure blocks the trade and cannot be overridden | C2 | M | later |

## Epic D: playbook and decisions (portfolio manager, options strategist)
| # | Story | Acceptance criteria | Depends | Size | Status |
|---|---|---|---|---|---|
| D1 | Playbook format | Versioned YAML per design section 5 (payer, edge family, structure, entry conditions, size and width rule, funding, exits, evaluation plan, evidence links, status); loader validates every field; a changed parameter needs a new version | B5 | M | later |
| D2 | Rule evaluation and allocation | Evaluates approved rules on the day's measured inputs; fixed allocation rule when several fire (expected net per rupee of risk after constraints, against no trade); an unproven strategy holds at most 1 of 3 slots | D1, C2 | M | later |
| D3 | Decision record | One record per opportunity (observations with availability times, forecast as the rule's tested P&L distribution, legs, value, account room, reasons); stored with the data it used | D2 | M | later |

## Epic E: code-only daily paper desk
| # | Story | Acceptance criteria | Depends | Size | Status |
|---|---|---|---|---|---|
| E1 | 3 pm daily loop | Data check, rules, risk, validity, paper fill after a fresh quote check, protection bought first and sold last, open-trade review; wired in `services.py` | C2-C4, D1-D3, A4 | L | later |
| E2 | Reports | Daily #fno-desk message with each step's reasons; no F&O output to #market-brief | E1 | S | later |
| E3 | Paper scorecard | Measures each strategy against its evaluation plan; pause rules as written; three ledgers | E1, C1 | M | later |
| E4 | Old live desk | The old intraday desk (whose kill switch closes everything) is switched off or clearly separated, so two desks never trade the same paper account | E1 | S | later |

## Epic F: AI layer (on hold until the owner starts it)
| # | Story | Acceptance criteria | Depends | Size | Status |
|---|---|---|---|---|---|
| F1 | Role agents | One agent per AI role with a fixed finding-card format; independent first reports; "not applicable" allowed | E1 | L | on hold |
| F2 | Red team | Different model from the author; attacks each thesis | F1 | M | on hold |
| F3 | AI judge (parts 2 and 3) | Research sufficiency and interpretation checks; monthly audit with seeded known-answer cases | C4, F1 | M | on hold |
| F4 | Role scorecards | Paired shadow decisions with and without each optional role, after its own cost; mandatory controls scored on correctness | F1, E3 | M | on hold |
| F5 | Operating-cost tracking | Actual AI and data bills feed the account ledger | C1 | S | on hold |

## Questions for review
1. Is anything in the approved design missing from these stories, or any story not justified by it?
2. Are the acceptance criteria testable as written? Which would you tighten?
3. Is the order right: data and experiment 1 first, then risk and playbook, then the paper desk, AI last?
4. A4 (recording real 3 pm quotes) is started early because only time builds that history: agree?
