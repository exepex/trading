# Epic S: scoreboards, evaluation and review

Roles: statistician, portfolio manager, risk manager, tax and cost accountant, head of desk. Goal: all three books on
both scoreboards with every detail (owner requirement, design 12.5), judged by a protocol frozen in advance, reviewed
on schedule, with failures fed back into research (design 12.5-12.8, 13.1 items 7 and 9). Story template, definition
of done and the full story index: `docs/IMPLEMENTATION_PLAN.md`.

---

## S1. Evaluation protocol

**Repository:** trading

**Description:** As the statistician, I want every rule of the comparison frozen before the first counted decision
(common start date, segments, uncertainty criterion, catastrophic-loss rule, review dates, cost allocation and
role-value method), so that no result can be reinterpreted after it is seen.

**Context and why:** Design 12.6 (common start predeclared; pilot evidence apart; versions; firewall), 12.8 (primary
verdict is net account result after execution and operating costs within the risk budget on both scoreboards; first
scheduled review after 6 months of common-start trading; six months is a review date, not proof; promoting or
combining needs the uncertainty criterion fixed here; immediate pauses only for the brake, a strategy-level
catastrophic loss rule, and data, integrity or safety failures), 13.5 timetable, 13.6 cost and role-value.

**Scope.** In: the protocol, its freeze record, registration in the ledger. Out: computing results (S2-S4).

**Expected design:** `research/evaluation/PROTOCOL.md` frozen with a FREEZE record (commit, hashes of the scoring code,
timetable, allocation formula, ablation schedule), registered in `research/ledger.csv` (B4). Contents: the common
start date (or the rule that sets it: the first session on which all three books can trade), the timetable times
(E3), segment rules (D6), the scoreboard A standardisation (S3), the uncertainty criterion for any promotion or
combination (e.g. a one-sided block-bootstrap lower bound above zero for net per unit of risk, with the block length
and seed), the catastrophic-loss rule per strategy and per book, review dates, the AI cost allocation formula (F8) and
the role-value schedule and minimum sample (F9).

**Acceptance criteria:**
1. The protocol's freeze commit precedes the first counted (non-pilot) decision of every book (checked by S2/S3).
2. Every item listed above has a value or an exact rule; "to be decided" is rejected by a check script.
3. A change after the freeze is only possible as a new protocol version with a new freeze; results are reported per
   protocol version.

**Test plan:** freeze-order check; completeness check script.

**Judge verifies:** runs the completeness check; confirms the commit order.

**Depends:** B4, D6, E3 (S1 freezes the methods written in F8 and F9; it needs their story text, not their code) · **Size:** S · **Status:** Draft, not frozen. Tooling merged (judge 85); owner batch 1 FAILed (judge 94); the freeze waits for S3, F9 and E8 code (owner option A, REPLAN) (claims: reviews/claude/response_86_s1-protocol.md)

---

## S2. Scoreboard B: whole systems

**Repository:** trading

**Description:** As the owner, I want each book's real paper account reported with every detail, so that I can see
which complete system made the most net money after all costs under the same risk budget.

**Context and why:** Design 12.5 scoreboard B: each book's real paper account under its own permitted universe and the
same owner risk budget; reported: raw account net, net per unit of risk used (maximum loss, stress usage,
margin-days), trades, gross, execution costs, AI and data costs (13.6 labels), net, each version segment separately;
pilot evidence apart; cash held after the common start counts as an outcome; overridden trades scored separately.

**Scope.** In: computation, per segment and overall, uncertainty per the protocol. Out: matched comparison (S3).

**Expected design:** `fno/scoreboard/whole_system.py` reading accounts (E1), fills (E4), ledgers (C1, F8), versions
(D6), overrides (F4); output `research/scoreboards/B/<date>.json` (deterministic) for P2 and S4.

**Acceptance criteria:**
1. Every number listed above is present for each book and segment.
2. Account net reconciles with the three ledgers (C1) to the rupee.
3. Pilot, unscored and overridden decisions are excluded from head-to-head figures and shown separately.
4. Rebuilding from the same records gives byte-identical output.

**Test plan:** fixture histories for three books with known answers; reconciliation test; determinism test.

**Judge verifies:** recomputes one book's monthly net and net per unit of risk from the records.

**Depends:** C1, D6, E1, E4, S1 (F8 for the AI books' allocated cost) · **Size:** M · **Status:** done: judge 87 PASS (771d508), merged a9a3cd1

---

## S3. Scoreboard A: matched decisions

**Repository:** trading

**Description:** As the statistician, I want every book's decisions on the same common opportunities scored on a
standardised shadow account, so that I can see whose judgement is better, separately from whole-system results.

**Context and why:** Design 12.5 scoreboard A: same eligible opportunities, same approved strategy universe, same
cutoff, same fill model and costs; each book's decision committed independently and scored on a standardised shadow
account; Book 3 via its matched shadow decisions (F7); never merged with scoreboard B into one "AI beats rules"
claim; "AI unavailable" excluded from judgement scores (13.5).

**Scope.** In: the standardised shadow account, scoring per book, paired differences, uncertainty. Out: whole systems
(S2).

**Expected design:** `fno/scoreboard/matched.py`: for each common opportunity (E2) and book, the book's action (Book 1
and Book 2 real decisions or shadow-only actions; Book 3's F7 entry) is valued as **one standard unit** (one lot,
standard size, no account constraints) with the E4 fill model on that day's execution snapshot and exits under the
action's rule; paired differences between books by opportunity, with the protocol's uncertainty criterion; reported
per segment, with the same detail list as S2 where it applies.

**Acceptance criteria:**
1. The same opportunity set and the same snapshot are used for all books on a day (hash test).
2. A constructed example with known outcomes reproduces the expected paired differences exactly.
3. "AI unavailable", late and unscored decisions are excluded from judgement scores and counted separately.
4. No report or dashboard field combines scoreboard A and B into one figure (schema test).

**Test plan:** known-answer tests; schema test.

**Judge verifies:** recomputes one opportunity's standardised result for all three books.

**Depends:** E2, E4, F7, D6, S1 · **Size:** M · **Status:** later

---

## S4. Monthly report and scheduled reviews

**Repository:** trading

**Description:** As the owner, I want a monthly report with both scoreboards for all three books, forecasts, costs,
the judge and override audit and open research questions, and a scheduled review that applies the protocol's rules,
so that decisions about books and strategies follow evidence and dates fixed in advance.

**Context and why:** Design 12.8 (monthly report; first scheduled review after 6 months of common-start trading),
13.4 (report contents), 7 (judge audit monthly), 6 (paper gate).

**Scope.** In: the report file, the review procedure and its record. Out: the owner's decision itself.

**Expected design:** command `python -m fno report monthly <YYYY-MM>` writing `reports/<YYYY-MM>-scoreboard.md` from
S2, S3, G4, F8, F9 and F4's audit; on a review date, a review section applying S1's criteria per book and strategy
(keep, pause, retire, promote-to-combination candidate) and listing what needs the owner's decision; Slack headline
(P4).

**Acceptance criteria:**
1. The report contains every section listed in design 13.4 for all three books.
2. Every number in the report equals the source file it cites (test re-reads them).
3. Before the first review date, no keep/drop/promote verdict is produced; after it, verdicts follow S1 exactly.

**Test plan:** report generation tests on fixture months.

**Judge verifies:** checks five random numbers in a report against their sources.

**Depends:** S2, S3, G4, F4, F8, F9 · **Size:** M · **Status:** later

---

## S5. Research feedback loop

**Repository:** trading

**Description:** As the head of desk, I want each book's failures, scorecards and audit findings turned into registered
research questions, with any change reaching a book only as a new owner-approved version, so that the desk learns
without ever editing a live version.

**Context and why:** Design 4 (research loop feeds results back; fixed policy, dynamic decisions), 12.8 (where each
book fails becomes research questions), 12.10 (a combination is a new design tested on forward data it was not built
from), 13.1 item 9.

**Scope.** In: the question register, the path from question to a new version. Out: running the research itself
(epic B stories and research meetings).

**Expected design:** `research/QUESTIONS.md` (append-only register: date, source (report, audit, failure), question,
owner role, status, linked ledger trials); the monthly report (S4) proposes entries; a new playbook, envelope,
constitution or prompt version is accepted only through the research loop and D1/D4/D5/D6 registration with the
owner's approval; the dashboard shows open questions.

**Acceptance criteria:**
1. Every monthly report adds its proposed questions to the register (or states "none").
2. A version change without a linked question, evidence and owner approval is refused by the D1/D4/D5/D6 loaders.
3. Register rows are never edited; status changes are new rows.

**Test plan:** loader tests; register tests.

**Judge verifies:** traces one version change back to its question and approval.

**Depends:** S4, D1, D4, D5, D6 · **Size:** S · **Status:** later
