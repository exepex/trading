# Implementation plan: every story for the finished product (70 stories)

Status: **revision 3, agreed by ChatGPT (reviews 26-27) and approved by the owner on 12 Oct 2026** ("A, approve the
plan and recreate the issues"; responses 32-34). GitHub issues #22-#80 were created from the table below on 12 Oct 2026 (one per story built in this repository;
issue title = story ID and title; done stories closed); the old issues #3-#21 were closed as duplicates of their
replacements. Stories X1, W1-W7 and K1-K3 are created in their own repositories; step-by-step guide:
`docs/MIGRATION_PLAN.md`. Source: `docs/DESK_DESIGN.md` sections 1-13
(all approved by the owner; section 13 revision 3 on 12 Oct 2026) and `docs/DESK_DECISIONS.md`. This plan replaces the
28-story plan agreed in review 14: approved stories are carried over (updated where the three books, section 13 or
the clean slate changed them), new stories cover the rest of the finished product (design 13.1). After ChatGPT and
the owner approve it, GitHub issues #3-#21 are closed as replaced and a clean issue set is created from this table.

## Story format

Every story in `docs/stories/` has:
- **heading**: ID and title;
- **repository**: where it is built (`trading` = this repository; `dashboard`, `platform`, `agentic-stock-prediction`
  are specified here and built in their own repositories, design 13.8);
- **description**: "As a <role>, I want <what>, so that <why>";
- **context and why**: the design sections, decisions, facts and current code the story rests on, so that an agent can
  implement it without asking;
- **scope**: what is in and what is out;
- **expected design**: modules, interfaces, inputs, outputs, file formats, where it is wired;
- **acceptance criteria**: numbered and testable;
- **test plan**, **judge verifies** (how the independent judge checks the claim);
- **depends, size, status**. Sizes: S = under a day, M = 1-3 days, L = more. Status: done, built (awaiting judge),
  doing, next, later.

**Definition of done (every story, in addition to its own criteria):** tests, `ruff check fno tests tools` and
`python tools/check_imports.py` pass; no Python file or class over 350 lines; new behaviour behind an interface,
concrete classes wired only in `fno/composition.py` or `fno/storage/wiring.py`; fixed strings and environment-variable
names in `fno/constants.py`; settings only through allowed `config.yaml` keys (`fno/config.py`); docs updated; any
research trial registered in `research/LEDGER.md` and `research/ledger.csv` before its result is read; never an order
function, never a credential in a file; committed records pass the public-record scan (O5) while the repositories are
public; the other AI judges the result in the repository (`docs/JUDGE.md`). Stories in
other repositories follow that repository's rules as well.

## How the stories cover the finished product (design 13.1)

| 13.1 item | Stories |
|---|---|
| 1 Data | A1-A8, C3, O5 |
| 2 Research | B1-B7, B5 (experiment 1), B6 (discovery) |
| 3 Playbook and decisions | D1-D6, C4, F4 (judge, overrides) |
| 4 Three paper books | E1-E6, C1, C2, C4 |
| 5 AI layer | F1-F9 |
| 6 Forecasts | G1-G5 |
| 7 Scoreboards A and B | S1-S3 |
| 8 Owner surfaces | P1-P4, X1, W1-W7, K1-K3, S4 |
| 9 Research feedback | S5, S4 |
| 10 Operations | O1-O5 |

## Milestones and order

Dependency order for the cross-repository part (design 13.8): canonical F&O records -> read-model schema and publisher
-> Azure platform contract -> dashboard read path -> F&O screens -> migration and cutover -> automated operations.

| Milestone | Stories | Outcome |
|---|---|---|
| M1 Data and experiment 1 | A1, A3, A5, A6, A7, B1, B2, B3, B5, C1 (A2, A4, B4 done) | Experiment 1 run on discovery (2024-26) and challenge (2019-23) data under its frozen protocol: a strategy passes or "no strategy passed" is documented |
| M2 Decision machinery and Book 1 | B7, C2, C3, C4, D1, D2, D3, D6, E1, E2, E4, E3, E5, E6, O5 | Book 1 decides and paper-trades daily (or records "no approved strategy") |
| M3 Forecasts | G1, G2, G3, G4 | Forecast protocol, baselines, scoring engine and Book 1's forecasts running (forecasts start before trading, 12.11); AI books' forecasts come with M5 (G5) |
| M4 Publishing and the shared dashboard | S1, S2, P1, P2, X1, P3, P4, W1, W2, W3, W4, O1, O2 | The owner sees Book 1, scoreboard B and forecasts on the F&O screens and in Slack every day; the F&O launch does not wait for the stock migration |
| M5 AI books | D4, D5, F1-F9, G5, S3 | Books 2 and 3 decide in isolated sessions; all three books on both scoreboards |
| M6 Review, cutover and operations | S4, S5, O3, O4, K1, W6, W7, K3, W5, K2 | Monthly reports and the first scheduled review; stock dashboard moved; MotherDuck retired |
| M7 Research expansion | B6, A8 | Discovery scan and positioning data feed new research questions |

**Order inside M1 (as agreed in reviews 12-14):** A1 (calendar and coverage), A3, then B1, B2, B3; finish A5, A6 and
C1 judging before B5 runs; B5's challenge run only after its freeze. **If no strategy passes,** books 1 and 2 record
"no approved strategy" every day (a result, not an error) while research continues (S5, B6); Book 3 can still run as a
pilot once M5 exists; the owner's rule applies: if paper trading shows no net profit, the tools are shut down.

## All stories

| ID | Story | Repository | Depends | Size | Status |
|---|---|---|---|---|---|
| [A1](stories/A-data-foundation.md#a1-raw-nse-archive-complete-and-checked) | Raw NSE archive complete and checked | trading | - | M | done (judge passed) |
| [A2](stories/A-data-foundation.md#a2-one-reader-for-both-fo-formats) | One reader for both F&O formats | trading | - | M | done |
| [A3](stories/A-data-foundation.md#a3-nifty-option-chain-panel) | NIFTY option-chain panel | trading | A1, A2 | M | built; awaiting judge |
| [A4](stories/A-data-foundation.md#a4-daily-3-pm-quote-recorder) | Daily 3 pm quote recorder | trading | - | M | done (judge passed) |
| [A4b](stories/A-data-foundation.md#a4b-raw-groww-quotes-in-google-drive-only-the-public-repository-keeps-hashes-counts-and-derived-values) | Raw Groww quotes in Google Drive only | trading | A4, A9 | M | story text for the judge (15 Oct 2026) |
| [A4c](stories/A-data-foundation.md#a4c-the-other-index-options-at-3-pm-all-fo-recording-part-8a) | The other index options at 3 pm (all-F&O recording, 8a) | trading | A4, A4b, A5 | M | story text for the judge (15 Oct 2026) |
| [A5](stories/A-data-foundation.md#a5-monthly-expiry-identity-in-the-package) | Monthly-expiry identity in the package | trading | - | S | done (judge passed) |
| [A6](stories/A-data-foundation.md#a6-events-calendar) | Events calendar | trading | - | S | done (judge passed; criteria 4-5 moved to B1, B5) |
| [A7](stories/A-data-foundation.md#a7-every-component-uses-the-session-calendar) | Every component uses the session calendar | trading | A1 (calendar) | S | done (judge passed) |
| [A8](stories/A-data-foundation.md#a8-positioning-data-source-participant-open-interest) | Positioning data source (participant open interest) | trading | A1 | M | partly built; waiting on the owner's Drive upload and 20 measured release days |
| [A9](stories/A-data-foundation.md#a9-drive-uploads-as-the-owner-and-the-historical-data-librarian) | Drive uploads as the owner, and the historical-data librarian | trading | A1, A8 | M | built; awaiting judge |
| [B1](stories/B-research-engine.md#b1-feature-library) | Feature library | trading | A3, A6 | M | later |
| [B2](stories/B-research-engine.md#b2-cycle-simulator) | Cycle simulator | trading | A3, A5 | M | built; awaiting judge |
| [B3](stories/B-research-engine.md#b3-policy-runner-and-verdict) | Policy runner and verdict | trading | B1, B2, B4 | M | later |
| [B4](stories/B-research-engine.md#b4-ledger-guard) | Ledger guard | trading | - | S | done (judge passed) |
| [B5](stories/B-research-engine.md#b5-experiment-1) | Experiment 1 | trading | B1-B4, A1, A3, A5, A6, C1 | M | done: no policy passed (judge 56) |
| [B6](stories/B-research-engine.md#b6-candidate-scan) | Candidate scan | trading | B3 | L | later |
| [B7](stories/B-research-engine.md#b7-live-3-pm-feature-versions-and-their-validation) | Live 3 pm feature versions and their validation | trading | B1, A4, A7 | M | later |
| [C1](stories/C-code-roles.md#c1-cost-and-tax-accountant-three-ledgers) | Cost and tax accountant: three ledgers | trading | - | S | done (judge passed) |
| [C2](stories/C-code-roles.md#c2-risk-manager) | Risk manager | trading | B2 | L | done (judge 43) |
| [C3](stories/C-code-roles.md#c3-data-checks-before-every-decision) | Data checks before every decision | trading | A3, A4, A7, E2 | S | done (judge 81, merged e3506ec) |
| [C4](stories/C-code-roles.md#c4-hard-validity-checks-judge-part-1) | Hard-validity checks (judge part 1) | trading | C2, D3 (D4 and D5 for the Book-2 envelope check and the Book-3 mode) | M | done for Book 1 (judge 83, merged dafbebe, b03c4ef); criteria 6-7 wait for D5/D4 |
| [D1](stories/D-playbook-decisions.md#d1-playbook-format) | Playbook format | trading | B5, B7 | M | done (judge 67) |
| [D2](stories/D-playbook-decisions.md#d2-rule-evaluation-and-allocation) | Rule evaluation and allocation | trading | D1, C2, B7 | M | done (judges 69 and 74, merged 662784f, a0a8eef) |
| [D3](stories/D-playbook-decisions.md#d3-decision-record) | Decision record | trading | D2, E2 | M | done (judge 80, merged f314254) |
| [D4](stories/D-playbook-decisions.md#d4-book-2s-authority-envelope) | Book 2's authority envelope | trading | D1 | S | later |
| [D5](stories/D-playbook-decisions.md#d5-book-3s-constitution-and-strategy-registry) | Book 3's constitution and strategy registry | trading | B4 (git-ancestry pattern), C2 | M | later |
| [D6](stories/D-playbook-decisions.md#d6-version-registry-and-evaluation-segments) | Version registry and evaluation segments | trading | D3 | S | done (judge 78, merged c12137e) |
| [E1](stories/E-paper-desk.md#e1-paper-accounts-per-book-with-a-single-writer-lock) | Paper accounts per book, with a single-writer lock | trading | C1 | M | done (judge passed) |
| [E2](stories/E-paper-desk.md#e2-common-market-pack-and-book-private-packs) | Common market pack and book-private packs | trading | A3, A4, A6, A7, D1, E1 (D4 and D5 for the private packs of books 2 and 3) | M | done (judge 72, merged b4f1e1b) |
| [E3](stories/E-paper-desk.md#e3-daily-timetable-deadline-execution-snapshot-and-exits) | Daily timetable: deadline, execution snapshot and exits | trading | A4, A7, C3, C4, D3, E1, E2, E4 | L | done (judge 82); not live (no routine yet) |
| [E4](stories/E-paper-desk.md#e4-fill-model-and-exits) | Fill model and exits | trading | A4, C1, C2, E1 | M | done (judge 68) |
| [E5](stories/E-paper-desk.md#e5-book-1-pure-rules) | Book 1: pure rules | trading | C4, D2, D3, E2, E3 | S | done (judge 84, merged 58f5781); not live |
| [E6](stories/E-paper-desk.md#e6-strategy-paper-scorecard-and-pause-rules) | Strategy paper scorecard and pause rules | trading | C1, D1, E4 | M | done (judge 73, merged 374ad67) |
| [E7](stories/E-paper-desk.md#e7-expiry-settlement) | Expiry settlement | trading | A2, C1, C2, E1, E4 | S | done (judge 71, merged f655612) |
| [F1](stories/F-ai-layer.md#f1-isolated-ai-book-sessions) | Isolated AI book sessions | trading | D3, D6, E2, E3 | L | forecast part done (judges 62, 88, 90); trading part later |
| [F2](stories/F-ai-layer.md#f2-analyst-roles-and-finding-cards) | Analyst roles and finding cards | trading | F1 | L | text rewritten 16 Oct 2026 |
| [F3](stories/F-ai-layer.md#f3-red-team) | Red team | trading | F1, F2 | M | later |
| [F4](stories/F-ai-layer.md#f4-ai-judge-parts-2-and-3-owner-overrides-and-the-monthly-audit) | AI judge (parts 2 and 3), owner overrides and the monthly audit | trading | C4, F1, F2 | M | later |
| [F5](stories/F-ai-layer.md#f5-book-2-ai-decisions-inside-the-envelope) | Book 2: AI decisions inside the envelope | trading | C4, D2, D4, F1, F2, F3, F4 | M | later |
| [F6](stories/F-ai-layer.md#f6-book-3-the-fully-ai-system-and-its-pilot) | Book 3: the fully AI system and its pilot | trading | C2, C4, D5, D6, F1, F2, F3, F4, G1 | L | later |
| [F7](stories/F-ai-layer.md#f7-matched-shadow-decisions-for-scoreboard-a) | Matched shadow decisions for scoreboard A | trading | E2, F6 | S | later |
| [F8](stories/F-ai-layer.md#f8-ai-usage-and-cost-attribution) | AI usage and cost attribution | trading | C1, F1 | S | minimal part done (judge 104, merged 757c20d); part 2 later |
| [F9](stories/F-ai-layer.md#f9-role-value-evaluation-does-each-ai-role-earn-its-cost) | Role-value evaluation (does each AI role earn its cost?) | trading | F1, F2, F8, S1, E4 | M | later |
| [G1](stories/G-forecasts.md#g1-forecast-protocol-and-the-30-day-atm-implied-volatility-estimator) | Forecast protocol and the 30-day ATM implied-volatility estimator | trading | A1, A3, B1, B4 | M | done: v1-v3 frozen (judges 47, 64); v4 is G6 |
| [G2](stories/G-forecasts.md#g2-frozen-baselines) | Frozen baselines | trading | G1, A3, A4 | M | done (judge 54) |
| [G3](stories/G-forecasts.md#g3-book-1-forecast-capture) | Book 1 forecast capture | trading | G1, G2 | S | done (judge 54); live since 14 Oct |
| [G4](stories/G-forecasts.md#g4-forecast-scoring-and-reports) | Forecast scoring and reports | trading | G1, G3 (G5 for books 2 and 3) | M | done (judge 58 passed) |
| [G5](stories/G-forecasts.md#g5-ai-books-forecast-capture) | AI books' forecast capture | trading | G1, G3, F1 | S | done (judge 62); live since 14 Oct |
| [S1](stories/S-scoreboards.md#s1-evaluation-protocol) | Evaluation protocol | trading | B4, D6, E3 (S1 freezes the methods written in F8 and F9; it needs their story text, not their code) | S | Draft, not frozen. Tooling merged (judge 85); owner batch 1 FAILed (judge 94); the freeze waits for S3, F9 and E8 code (owner option A, REPLAN) |
| [S2](stories/S-scoreboards.md#s2-scoreboard-b-whole-systems) | Scoreboard B: whole systems | trading | C1, D6, E1, E4, S1 (F8 for the AI books' allocated cost) | M | done (judge 87, merged a9a3cd1) |
| [S3](stories/S-scoreboards.md#s3-scoreboard-a-matched-decisions) | Scoreboard A: matched decisions | trading | E2, E4, F7, D6, S1 | M | later |
| [S4](stories/S-scoreboards.md#s4-monthly-report-and-scheduled-reviews) | Monthly report and scheduled reviews | trading | S2, S3, G4, F4, F8, F9 | M | later |
| [S5](stories/S-scoreboards.md#s5-research-feedback-loop) | Research feedback loop | trading | S4, D1, D4, D5, D6 | S | later |
| [S6](stories/S-scoreboards.md#s6-scorecard-measures-do-nothing-gate-trade-luck-checks-t-check-warning-missed-runs-random-control) | Scorecard measures: do-nothing gate, trade-luck checks, t-check warning, missed runs, random control | trading | S1, S2, E3, E4, A13 | M | story text |
| [P1](stories/P-publishing.md#p1-fo-read-model-contract) | F&O read-model contract | trading | D3, S2 (S3 for the scoreboard A page) | M | later |
| [P2](stories/P-publishing.md#p2-read-model-builder) | Read-model builder | trading | P1, E3, S2, G4 (S3 for the scoreboard A page) | M | later |
| [P3](stories/P-publishing.md#p3-atomic-publisher-to-azure) | Atomic publisher to Azure | trading | P2, X1, A1 | M | later |
| [P4](stories/P-publishing.md#p4-slack-daily-message-and-alerts) | Slack daily message and alerts | trading | P2 | S | later |
| [X1](stories/X-cross-repository.md#x1-azure-database-for-postgresql-server-schemas-roles-and-tests) | Azure Database for PostgreSQL: server, schemas, roles and tests | platform | owner's Azure access | M | later |
| [W1](stories/X-cross-repository.md#w1-shared-dashboard-repository-copy-of-the-stock-dashboard) | Shared dashboard repository (copy of the stock dashboard) | dashboard | - | M | later |
| [W2](stories/X-cross-repository.md#w2-azure-read-path-for-fo-publication-aware-reads-and-contract-checks) | Azure read path for F&O: publication-aware reads and contract checks | dashboard | W1, X1, P3 | M | later |
| [W3](stories/X-cross-repository.md#w3-fo-screens) | F&O screens | dashboard | W2, P1 | L | later |
| [W4](stories/X-cross-repository.md#w4-access-and-freshness-contract-tests) | Access and freshness contract tests | dashboard | W2, W3 | S | later |
| [W6](stories/X-cross-repository.md#w6-stock-reads-on-azure-and-parity) | Stock reads on Azure and parity | dashboard | W2, K1 | M | later |
| [W7](stories/X-cross-repository.md#w7-dashboard-writes-on-azure-inbox-assistant-and-control-state) | Dashboard writes on Azure (inbox, assistant and control state) | dashboard | W1, X1 | M | later |
| [W8](stories/X-cross-repository.md#w8-the-signed-off-app-frame-in-the-real-app) | The signed-off app frame in the real app | dashboard | W1 | L | next |
| [W9](stories/X-cross-repository.md#w9-the-signed-off-home-screen-in-the-real-app) | The signed-off Home screen in the real app | dashboard | W8 | M | later |
| [W10](stories/X-cross-repository.md#w10-api-contract-and-data-catalog-for-the-frame-and-home-small-independent-endpoints) | API contract and data catalog for the frame and Home (small independent endpoints) | dashboard | 30, 31 sign-off | M | done (judge passed) |
| [K4](stories/X-cross-repository.md#k4-stock-backend-publishes-one-read-model-per-home-and-frame-block) | Stock backend publishes one read model per Home and frame block | agentic-stock-prediction | W10 | L | later |
| [P5](stories/X-cross-repository.md#p5-fo-read-models-for-the-frame-contracts-quotes-order-rules-and-books) | F&O read models for the frame: contracts, quotes, order rules and books | trading | W10, P1, A4 | M | later |
| [MA1](stories/X-cross-repository.md#ma1-the-manual-paper-account-the-owners-own-paper-trades) | The Manual paper account (the owner's own paper trades) | dashboard | W8, X1, W7 | L | later |
| [W5](stories/X-cross-repository.md#w5-cutover-and-rollback) | Cutover and rollback | dashboard | W1-W4, W6, W7, K1, K3 | S | later |
| [K1](stories/X-cross-repository.md#k1-stock-backend-publishes-to-azure-dual-publication-and-parity) | Stock backend publishes to Azure (dual publication and parity) | agentic-stock-prediction | X1 | M | later |
| [K2](stories/X-cross-repository.md#k2-retire-motherduck) | Retire MotherDuck | agentic-stock-prediction | W5, W7, K3 | S | later |
| [K3](stories/X-cross-repository.md#k3-stock-backends-inbox-readers-switch-to-azure) | Stock backend's inbox readers switch to Azure | agentic-stock-prediction | W7, X1 | S | later |
| [O1](stories/O-operations.md#o1-the-daily-desk-routine) | The daily desk routine | trading | E3, P3, P4, A7 | S | later |
| [O2](stories/O-operations.md#o2-failure-handling-end-to-end) | Failure handling, end to end | trading | E3, E4, P3, P4 (F1, F4 for the AI-book cases, added in M5) | M | later |
| [LM1](stories/LM1-position-monitor.md) | Position monitor, alert only | trading | A16, E1, E4, T1, O1 | M | story text |
| [O3](stories/O-operations.md#o3-cross-repository-integration-tests) | Cross-repository integration tests | trading | P3, X1, W2, W3, O1 (W6, W7, K3 for test 4) | M | later |
| [O4](stories/O-operations.md#o4-runbook-and-documentation) | Runbook and documentation | trading | O1, O2 | S | later |
| [O5](stories/O-operations.md#o5-public-record-safety-scan) | Public-record safety scan | trading | - | S | done (judge passed) |

## Removed or merged from the previous plan

- **E4 (retire or separate the old live desk):** removed by the clean slate; its per-account lock moved to E1.
- **Old E1 (daily 3 pm loop):** split into E1 (accounts and lock), E2 (packs), E3 (timetable), E4 (fills and exits),
  E5 (Book 1).
- **Old E2 (daily report):** now P4 (Slack) and W3 (screens). **Old E3 (paper scorecard):** now E6.
- **Old F1-F5:** rewritten for cloud routines and the three books (F1-F9); old F4 (role scorecards) is F9, old F5
  (per-call API cost) is F8 (allocated plan cost, 13.6).
- **Not included (not in the approved design):** a lessons memory shared across days, an AI-written daily summary and
  automated weekly research meetings (proposed as G1-G3 in the old re-evaluation, never approved). They can be
  proposed later as design changes.

## Questions for review

1. First, re-check section 13 revision 3 (response 31): atomic publication, Postgres roles, migration order, F&O
   freshness. The owner approved it on the understanding that you confirm these four changes here.
2. Is any part of the approved design (sections 1-13) not covered by a story, or any story not justified by it?
3. Is every story implementable by an agent from its text alone (context and why, expected design), and every
   acceptance criterion testable as written? Name any story where an implementer or the judge would have to guess.
4. Are the dependencies and milestones in the right order, including the cross-repository order of 13.8?
5. Are the corrections to approved stories right (C3's quote rule now follows A4; C4's two modes; D3's three-book
   fields; A1's calendar interface)?

**Revision 2 (ChatGPT review 26, all points applied; response 33):** F1 isolation is now preventive (no repository and
no network in AI sessions, an allowlisted export in, the output read from the session record with a server-side receipt
deadline, then a promotion deadline before the execution snapshot; unenforceable isolation means "not scored as an
independent comparison"); W2 split into W2 (F&O, M4) and W6 (stock parity after K1, M6); new W7 (dashboard writes
on Azure); C4 a hard dependency of E5 and F5 and of every fill (E3); G3 split into G3 (Book 1, M3) and G5 (AI books,
M5); a role matrix (`agents/roles.yaml`, F2); new O5 (public-record safety scan).

**Revision 3 (ChatGPT review 27, response 34):** new K3 (the stock tool's inbox readers move to Azure after W7; split
out of K1); O3 test 4 fully specified (W6, W7, K3 together before W5); F1's real isolation test covers every
network-capable tool and records the environment's network policy in the version.
