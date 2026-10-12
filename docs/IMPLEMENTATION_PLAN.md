# Implementation plan: desk design v2.1 as stories

Status: **agreed by Claude and ChatGPT** (ChatGPT review 14, 12 Oct 2026) as the implementation specification.
Agreement covers the specification only: each story's implementation is judged against its acceptance criteria. Source: `docs/DESK_DESIGN.md` v2.1 (owner-approved framework).
The owner started development on 12 Oct 2026; the AI layer (epic F) stays on hold until the owner says otherwise.

**Story format (agile):** every story in `docs/stories/` has
- **heading**: ID and name;
- **user story**: "As a <role>, I want <what>, so that <why>";
- **background**: the facts and decisions it rests on;
- **scope**: what is in and what is out;
- **expected design**: modules, interfaces, inputs, outputs, file formats, where it is wired;
- **acceptance criteria**: numbered, testable, "given ... when ... then ..." where it helps;
- **test plan**: which tests prove the criteria;
- **judge verifies**: how the independent judge checks the claim, with commands or evidence;
- **depends, size, status**. Sizes: S = under a day, M = 1-3 days, L = more.

**Definition of done (every story, in addition to its own criteria):** tests and `ruff` pass; no file or class over
350 lines; new behaviour behind an interface, concrete classes wired only in `fno/live/services.py` or
`fno/storage/wiring.py`; fixed strings in `fno/constants.py`; docs updated; any research trial registered in
`research/LEDGER.md` before its result is read; the other AI reviews the result in the repository.

## Milestones
| Milestone | Stories | Outcome |
|---|---|---|
| M1 Data and first experiment | A1-A6, B1-B5, C1 | Experiment 1 run on 2024-26 (discovery) and 2019-23 (challenge) with the frozen protocol |
| M2 Risk, playbook, validity | C2-C4, D1-D3 | A strategy that passed can be written as a playbook version and checked by code |
| M3 Code-only paper desk | E1-E4 | Daily 3 pm paper decisions on the first approved strategy, no AI |
| M4 AI layer (on hold) | F1-F5 | Only after the owner starts it; each role kept only if it adds net value |

Start now (review 12): **A4** (record real 3 pm quotes; only time builds that history) and **B4** (ledger guard), alongside
A1. Finish A5, A6 and C1 before experiment 1 runs; B5 runs only after A1, A3 and B1-B4 are verified. D3's schema comes
before C4 (C4 checks the decision record).

## Stories

- Epic A: [Data foundation](stories/A-data-foundation.md)
- Epic B: [Research and discovery engine](stories/B-research-engine.md)
- Epic C: [Code roles](stories/C-code-roles.md)
- Epic D: [Playbook and decisions](stories/D-playbook-decisions.md)
- Epic E: [Code-only daily paper desk](stories/E-paper-desk.md)
- Epic F: [AI layer (on hold)](stories/F-ai-layer.md)

| ID | Story | Depends | Size | Status |
|---|---|---|---|---|
| [A1](stories/A-data-foundation.md#a1-raw-nse-archive-complete-and-checked) | Raw NSE archive complete and checked | - | S | doing (tool done; owner's upload complete 12 Oct 2026, sample-checked; coverage command next) |
| [A2](stories/A-data-foundation.md#a2-one-reader-for-both-fo-formats) | One reader for both F&O formats | - | M | done (128 of 128 overlap days identical, 5,793,044 rows) |
| [A3](stories/A-data-foundation.md#a3-nifty-option-chain-panel) | NIFTY option-chain panel | A1, A2 | M | next |
| [A4](stories/A-data-foundation.md#a4-daily-3-pm-quote-recorder) | Daily 3 pm quote recorder | - | M | done (judge passed) |
| [A5](stories/A-data-foundation.md#a5-monthly-expiry-identity-in-the-package) | Monthly-expiry identity in the package | - | S | built; awaiting judge |
| [A6](stories/A-data-foundation.md#a6-events-calendar) | Events calendar | - | S | built; awaiting judge |
| [B1](stories/B-research-engine.md#b1-feature-library) | Feature library | A3, A6 | M | later |
| [B2](stories/B-research-engine.md#b2-cycle-simulator) | Cycle simulator | A3, A5 | M | later |
| [B3](stories/B-research-engine.md#b3-policy-runner-and-verdict) | Policy runner and verdict | B1, B2, B4 | M | later |
| [B4](stories/B-research-engine.md#b4-ledger-guard) | Ledger guard | - | S | done (judge passed) |
| [B5](stories/B-research-engine.md#b5-experiment-1) | Experiment 1 | B1-B4, A1, A3, A5, A6, C1 | M | doing (protocol v2.1 agreed, review 14; freeze after B1-B3 are built) |
| [B6](stories/B-research-engine.md#b6-candidate-scan) | Candidate scan | B3 | L | later |
| [C1](stories/C-code-roles.md#c1-cost-and-tax-accountant-three-ledgers) | Cost and tax accountant: three ledgers | - | S | built; awaiting judge |
| [C2](stories/C-code-roles.md#c2-risk-manager) | Risk manager | B2 | L | later |
| [C3](stories/C-code-roles.md#c3-data-checks-before-every-decision) | Data checks before every decision | A3, A4 | S | later |
| [C4](stories/C-code-roles.md#c4-hard-validity-checks-judge-part-1) | Hard-validity checks (judge part 1) | C2, D3 | M | later |
| [D1](stories/D-playbook-decisions.md#d1-playbook-format) | Playbook format | B5 | M | later |
| [D2](stories/D-playbook-decisions.md#d2-rule-evaluation-and-allocation) | Rule evaluation and allocation | D1, C2, B1 | M | later |
| [D3](stories/D-playbook-decisions.md#d3-decision-record) | Decision record | D2 | M | later |
| [E1](stories/E-paper-desk.md#e1-daily-3-pm-loop) | Daily 3 pm loop | C2, C3, C4, D1, D2, D3, A4 | L | later |
| [E2](stories/E-paper-desk.md#e2-daily-report) | Daily report | E1 | S | later |
| [E3](stories/E-paper-desk.md#e3-paper-scorecard) | Paper scorecard | E1, C1 | M | later |
| [E4](stories/E-paper-desk.md#e4-retire-or-separate-the-old-live-desk) | Retire or separate the old live desk | E1 | S | later |
| [F1](stories/F-ai-layer.md#f1-role-agents) | Role agents | E1 | L | on hold |
| [F2](stories/F-ai-layer.md#f2-red-team) | Red team | F1 | M | on hold |
| [F3](stories/F-ai-layer.md#f3-ai-judge-parts-2-and-3) | AI judge (parts 2 and 3) | C4, F1 | M | on hold |
| [F4](stories/F-ai-layer.md#f4-role-scorecards) | Role scorecards | F1, E3 | M | on hold |
| [F5](stories/F-ai-layer.md#f5-operating-cost-tracking) | Operating-cost tracking | C1 | S | on hold |

## Questions for review
1. Is anything in the approved design missing from these stories, or any story not justified by it?
2. Is every acceptance criterion testable as written? Which would you tighten?
3. Is the order right: data and experiment 1 first, then risk and playbook, then the paper desk, AI last?
4. A4 (recording real 3 pm quotes) is started early because only time builds that history: agree?
5. Is each story detailed enough that an implementing agent knows exactly what to build and the judge knows exactly
   what to check? Name any story where either would have to guess.
