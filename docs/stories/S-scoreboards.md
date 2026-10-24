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
(D6); output `research/scoreboards/B/<date>.json` (deterministic) for P2 and S4.

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

**Expected design** (revision 1, 15 Oct 2026; REPLAN.md:48 moves the code into slice B because S1 v1 cannot freeze
until it exists; it reports only once books 2 and 3 trade). New modules under `fno/scoreboard/`, beside S2's, no new
composition root (`fno/scoreboard/wiring.py`, as E2c leaves it):

1. **The day's actions** (`matched_actions.py`). For each session and book, the decision is the run E3's decisions step
   recorded (the first original run, D3b; `committed_runs.py` already reads it). For each opportunity of E2's common
   set (`fno/desk/opportunity_set.py`) the book's action comes from its D3 record for that opportunity (the day's
   `no_trade` record, `NO_TRADE_ID`, is not an opportunity and is ignored):
   - **take**, when `decision.action` is a trade (`chosen`), or when the record is `not chosen` and every refusal is an
     account limit, which scoreboard A removes (S1 `scoreboard_a_standardisation`: "no cash, slot or margin limits").
     Account limits are the slot and cash rules (`allocation.py:18`, `max_open_trades`, `margin_room`), the
     account-state caps in `risk.verdicts` (`bucket_cap`, `open_risk_cap`, `new_risk_per_day`, `drawdown_brake`), the
     account-wide stress and exposure checks (`stress_loss`, `exposure_limit`: they add the book's other open positions,
     `fno/risk/rules.py:45-47, 82-84`, and are not in the books' profile today, `config.yaml` `risk.profiles.books`), and
     the "unproven:" open-trade limit (`allocation.py:72-77`). Counting these as account limits is chosen over
     re-checking the one-lot trade against an empty book: it needs no second risk run, and A drops account state
     anyway (judge 168);
   - **skip**, when `decision.action` is "no trade" for any other reason: the rule did not fire; no valid trade; a C4
     block (the action reads "no trade" even when `decision.outcome` reads "chosen", `decision_record.py:76-79`); or a
     `not chosen` refused by `max_loss_per_trade`, the one rule that judges the trade alone;
   - **not observed**, never scored and always counted (criterion 3):
     - no run collected for that book that day (late, `no_decision.json`, "AI unavailable" or a missed run);
     - a collected run with no record for that opportunity (for example a version paused during the day, which Book
       1's gate drops before deciding: the desk's gate, not the book's judgement);
     - a risk verdict whose reason starts "refused, input not usable" (`fno/risk/manager.py:66`: bad data, not
       judgement), or a `paper_account` refusal (a wrongly opened account: an operations fault);
     - a decision D6 leaves unscored;
     - a day with no valid execution snapshot (no book is scored that day).
   Research candidates (`shadow: ...`) are not in the common set and never appear. Book 3's actions come from F7's
   `shadow_decisions.json` through a port, `MatchedShadowDecisions`. Until F7 exists the port returns nothing, so every
   Book 3 day is "not observed: F7 not built", counted apart from misses (design 6). F7's text does not yet say that each entry must name its structure and the
   day's `common_pack_sha256`; F7 must add both before Book 3 can be scored (Depends).
2. **The standard unit** (`standard_unit.py`), the one valuation F9 reuses ("valued like scoreboard A"; shared through
   the orchestrator, no second copy):
   - one lot of each leg of the action's candidate structure (the record's legs; its lot count is ignored), entered at
     the day's execution snapshot (the same snapshot
     ID for every book, from the run log) by E4's pricing (`fno/desk/pricing.price_leg`, the touch, all units or none),
     with C1's charges;
   - an entry leg that does not fill makes the action "not filled": scored 0 and listed. It is the same for every book
     that took it, since the snapshot is shared;
   - exit by the version's time exit (the last trading day at least `exit_days_before_expiry` days before the expiry,
     `fno/playbook/opportunities.py:44`), the only exit code enforces today (`fno/playbook/exit_terms.py`), at that
     session's execution snapshot. A leg without a valid quote is retried at
     each next snapshot (E4's rule). A leg still open at expiry is settled by E7 (`fno/desk/settlement.py`);
   - an action not yet exited is "open": listed, never scored.
3. **Scores** (`matched.py`). A take's result is its one-lot net in rupees and its one-lot maximum loss at entry,
   recomputed from the one-lot entry fills by the maximum-loss function the candidates use (never the record's
   `worst_rs`, which is negative, priced at the pack's mids and for the book's lot count). A skip is 0 and 0. Actions
   still open are cut from both sums and listed, never counted as 0. Every take has a fixed maximum loss, because C4
   refuses any position whose maximum loss is not fixed at entry (design v2 03 item 3). A take whose one-lot maximum
   loss cannot be computed (a missing input) is listed apart as "maximum loss unknown" and not scored.
   - **Series days:** a book's series holds every session of the period on which it is observed, from the period's
     first session to the last decision day whose actions have all closed. Days with only skips, or with no
     opportunity, are in the series as (0, 0). Not-observed days are left out, never set to 0. The sample rule's 120
     days and the bound's 20-day minimum count these observed sessions.
   - **Per book:** net per unit of maximum loss at entry, Σ net ÷ Σ maximum loss over closed takes. This is S1's
     scoreboard A measure (`scoreboard_a_standardisation`), not S2's net per risk-day: A has no daily marks. Its series
     puts each action on its decision day (net, maximum loss), so S2's `uncertainty.lower_bound`, a ratio of sums over
     moving blocks, computes exactly this measure's bound, with S1's block, seed and resamples (no second bootstrap).
     A claim also needs the sample rule and the whole-period net above zero (S1 `uncertainty_criterion`).
   - **Paired, X against Y:** on the decision days both books are observed and all their actions closed, the daily
     difference of their one-lot nets in rupees (S1: "for X beats Y, the paired daily difference"). The statistic is
     the mean difference: the same moving-block resampler on a series whose risk column is 1 on every day (the ratio
     of sums is then the mean). A claim also needs the whole-period difference above zero and the sample rule.
   - **Holm across the claims made at one review** (S1). `lower_bound` has a fixed 5%, so it cannot apply Holm.
     `uncertainty.py` is split into the resampler (the sorted resampled values, unchanged) and two readers:
     - S2's lower bound (unchanged);
     - a one-sided bootstrap p-value, the share of resampled values at or below 0.
     Holm then runs on the p-values: sorted ascending, the i-th of m claims passes while p < 0.05 / (m − i + 1); the
     first failure stops the rest. The family is fixed (review 120, response 200 fix 1): each book's claim and every
     directional pair; a member not testable at a look enters with p = 1. For a single claim, p < 0.05 holds exactly when the nearest-rank 5th percentile is
     above 0, so it agrees with S2's bound. Each book's not-observed days are printed beside
     every pair.
   - Reported per D6 segment and overall (S2's `EntryDecisions` segments), with pilot before the common start apart, as
     S2 does.
4. **Output:** the board as canonical JSON, written where E2c writes board B (Drive). A one-lot fill at the touch,
   with marks, is the per-contract data E2c keeps out of the public record. CLI: `python -m fno scoreboard a`.
5. **S6's share** (criterion 5) lands with S6's code, which is built after this code: the measures and the do-nothing
   view (a) on these series.
6. **The miss cap** is computed here from scoreboard A's own actions, so it does not wait for S6. A book's misses are its
   days with no run collected (late, `no_decision.json`, "AI unavailable", missed), and its D6-unscored days on which
   another book was scored on the same common pack (review 120, response 200 fix 2). Days D6 leaves unscored for every
   book, days with no valid snapshot and Book 3's days before F7 are counted apart, outside the cap. The cap is 10% (G9's figure, owner row 170); S6's S1
   item `missed_runs` freezes it.

**Acceptance criteria:**
1. The same opportunity set and the same snapshot are used for all books on a day (hash test). Every book's record
   names the same `common_pack_sha256` (the common pack holds E2's set), and the snapshot is the run log's one
   execution snapshot ID for the day. A record naming another pack hash is refused and listed, never scored.
2. A constructed example with known outcomes reproduces the expected paired differences exactly:
   - 2 sessions and 2 opportunities, on fixture snapshots, with hand-computed fills and C1 charges;
   - Book 1 takes O1 (a closed one-lot result and maximum loss by hand), Book 2 skips everything, Book 3 is not
     observed;
   - on day 2, Book 1 takes O2, whose short leg has too little size at the touch: "not filled", scored 0 and listed,
     with its maximum loss out of the sum;
   - expected: Book 1's net per unit of maximum loss and the Book 1 − Book 2 daily differences to the paisa, with
     Book 3 absent from every pair and counted.
3. "AI unavailable", late, missed and unscored decisions are excluded from judgement scores and counted separately;
   above S1's `missed_runs` cap (missed decisions over 10% of the book's eligible sessions in the period) the
   book's scoreboard A verdict reads "undecided, operations" (owner, 15 Oct 2026, row 170; story S6). Boundary: exactly
   10% missed is not over the cap; one more missed session is.
4. No report or dashboard field combines scoreboard A and B into one figure (schema test).
5. Each book's matched results carry S6's `measures` and `do_nothing` view (a), computed by S6's functions (no second
   implementation), with the same known answers as S6's criteria 2, 3 and 5. This is delivered and tested with S6's
   code.
6. **The standard unit:**
   - an entry leg with too little size at the touch gives "not filled", scored 0;
   - the exit is on the last trading day at least `exit_days_before_expiry` days before the expiry (a holiday on that
     day moves it earlier, as the opportunity code does);
   - a leg without a quote on the exit day exits at the next snapshot where it has one, dated the day it fills, never
     backdated;
   - a leg still open at expiry is settled at E7's price;
   - an action still open on the report day is listed and unscored.
7. **Actions**, one fixture record per case:
   - `chosen`: a take;
   - `not chosen` refused by `bucket_cap` only, or by "unproven:": a take;
   - `not chosen` refused by `stress_loss` only: a take; by `exposure_limit` only: a take;
   - `not chosen` refused by `max_loss_per_trade`: a skip, and by `max_loss_per_trade` with `bucket_cap`: a skip;
   - "input not usable": not observed;
   - a C4 block with `decision.outcome` "chosen": a skip;
   - `no trade`: a skip;
   - the `no_trade` day record: ignored;
   - a collected run missing one opportunity's record: not observed for that opportunity;
   - a day without a valid snapshot: not observed for every book;
   - a `shadow: would trade` record never appears.
   Before F7, every Book 3 day is "not observed: F7 not built", outside the miss cap, and Book 3's verdict reads
   "undecided, F7 not built".
8. **Bounds:**
   - the per-book bound equals `uncertainty.lower_bound` on the decision-day series;
   - the pair bound equals it on the difference series with risk 1;
   - a series shorter than one block (19 observed days) gives null, while exactly 20 gives a bound;
   - a book with 25 sessions, 3 of them not observed and 10 skip-only, has a 22-day series holding the 10 skip-only
     days as (0, 0);
   - **Holm, known answer:** p-values 0.010, 0.030 and 0.040 for three claims: the first passes (0.010 < 0.0167), the
     second fails (0.030 ≥ 0.025), and the third is not tested;
   - p-value and bound agree: on one series, p < 0.05 exactly when `lower_bound` > 0;
   - a pair with no common observed day gives null with "no common day";
   - an action open on the report day ends the series before its day (design 3, series days): with a closed +1,000
     take on day 1, an open take on day 2 and a closed take on day 3, the series holds day 1 only; days 2-3 count once
     day 2's take closes. (Code revision: the text first said the day stays with the open take cut from its sums, which
     contradicted design 3 and would favour short holds.)
9. A rebuild from the same records gives byte-identical output.

**Gap list:**

| Requirement (source) | Where |
|---|---|
| Same eligible opportunities, universe, cutoff, fills and costs (design 12.5) | E2's set via the shared `common_pack_sha256` and the run log's snapshot ID (criterion 1); E4 pricing and C1 charges (design 2) |
| Each book's decision committed independently (design 12.5) | the D3 run E3 collected by the deadline (design 1) |
| Standardised shadow account: one lot, no account limits, no compounding (12.5; S1 item) | design 2; "not chosen" counts as a take (design 1) |
| Exit by the strategy's own rule recorded with the decision (S1 item) | the time exit, the only enforced exit (design 2) |
| Scored as net per unit of maximum loss; no trade = 0 (S1 item) | design 3 |
| Book 3 via F7 (12.5) | the `MatchedShadowDecisions` port; before F7, "not observed" (criterion 7) |
| "AI unavailable" excluded from judgement (13.5) | "not observed" (criterion 3) |
| Missed decisions on observed days, with the miss cap (row 170, S6) | design 6; criterion 3 |
| Paired differences, the uncertainty criterion and Holm (S1) | design 3; criteria 2 and 8 |
| Never merged with B (12.5) | criterion 4 |
| Per segment, pilot apart (S1 `segments`, `pilot_evidence`) | design 3 |
| S6's measures and do-nothing on A (rows 162, 168) | criterion 5, with S6's code |
| Private data stays out of the public record (E2c, decision of 15 Oct) | design 4 |
| F9 valued "like scoreboard A" (F9; S1 `role_value_schedule`) | `standard_unit.py`, shared |

**Known limits:**
- Profit, loss and event exits are free text today (D1 refuses them on paper), so the time exit is the only rule. A
  version that gains a coded exit adds it here in its own story.
- The rupee pair difference is not risk-normalised (response 144 item 23). One lot standardises size, but two
  structures' maximum losses can differ, and the per-book ratio is shown beside it.
- Counting an account-limited `not chosen` as a take credits a book for a trade its account could not hold. That is
  the point of A, and B shows what really happened.
- Pairs use the days both books are observed. If one book's outages fall on unusual days, the shared days are not a
  random sample, so each book's not-observed days are printed beside every pair.

**Test plan:** known-answer tests on fixture snapshots and D3 records; boundary tests; schema and determinism tests.

**Judge verifies:** recomputes one opportunity's standardised result for all three books.

**Depends:** E2, E4, E7, D3, D6, S1, S2 (bounds, segments), E2c (built after it: Drive board and shared download);
F7 later, through its port (its entries must name the structure and the `common_pack_sha256`) · **Size:** M · **Status:** text PASS (judge 168
add. 1); code PASS (judge 191 add. 1; claims response 179); merges after ChatGPT's review with S6 (branch
`story/s3-scoreboard-a`, session 0185gR5DmoDh2zBAvgRU4CEB)

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

---

## S6. Scorecard measures: do-nothing gate, trade-luck checks, t-check warning, missed runs, random control

**Repository:** trading

**Description:** As the owner, I want every scoreboard section to show whether the book beat doing nothing after tax,
how much of its result is one lucky trade or a lucky choice of direction and strike, whether a simpler statistical
check agrees with the bootstrap, and which desk runs were missed, so that a paper result is never mistaken for an edge
it does not have.

**Context and why:** Owner decisions of 15 Oct 2026 in `docs/DESK_DECISIONS.md`:
- **162, "Scorecard: S1's headline kept ...; four measures added":** S1's headline is kept (net per rupee of risk after every cost). Four measures are added on the
  scoreboards, never as the verdict.
- **167, "S1's t-based check is a printed warning":** the t-based check is a printed warning, not a pass condition.
- **168, "Do-nothing comparison shown on every scoreboard and a gate before real money":** the do-nothing comparison is shown on every scoreboard and is a gate before real money (design v2
  08:83, RM1 criterion 2). Cash and a NIFTY 50 index fund are measured on the same capital, horizon and tax scenario.
  Tax is labelled an assumption until verified.
- **169, "Largest loss share of gains" replaced:** "largest loss as a share of gains" is replaced by net without the best trade and the profit factor.
- **170, "Missed desk run: scoreboard A on observed decisions ...":** a missed desk run is scored on observed decisions with a miss cap on scoreboard A, and as it ran on
  scoreboard B.

The plan behind them is in `reviews/claude/response_144_noise-fairness-scorecard.md` (step 9; red team items 7, 19,
21, 24, 26-28), `response_147` items 3-7, judge 138 and ChatGPT review 112. Design v2
`03_layers_factory_desk.md:110-120` defines the two benchmarks. `REPLAN.md:47` lists them as S2's change.

What exists today:
- `fno/scoreboard/` (S2, merged) reports net, risk-days, net per unit of risk and the bootstrap lower bound.
- It reports no benchmark, drawdown, best-trade dependence, t-check, missed run or luck control.
- `fno/desk/daily_run.py:75` reviews exits only inside a run, so a missed run is not "flat".

**Scope.**
- **In:**
  - five new S1 protocol items;
  - the measures added to every S2 section;
  - one entry per book and strategy version on scoreboard B (the level RM1's gate needs), reconciled with E6's card;
  - the missed-run list on scoreboard B;
  - scoreboard A's share, as S3 text changes in this commit (S3 builds them): the measures and the do-nothing view (a)
    per book, and the miss rule.
- **Out:**
  - the real-money gate file and its freeze (RM1, which reads this story's `beats_index_after_tax`);
  - S2's other REPLAN change, the count of independent bucket-weeks (`REPLAN.md:47`): a different function (sample
    size, not a benchmark); no register row builds it yet, so the orchestrator assigns it;
  - net per rupee of entry maximum loss (response 144 item 22, not in the owner's rows);
  - the protocol's brake figure (Rs 30,000 in `PROTOCOL.md`, Rs 1,20,000 in `config.yaml`; REPLAN's
    `catastrophic_loss_book` change).

**Expected design:** this story extends S1 and S2 and builds nothing beside them. No new composition root:
`fno/scoreboard/wiring.py` wires the new source (`IndexLevels`). **Built after E2c** (text PASS, judge 148; code in
review), which moves scoreboard B to Drive and rewires `fno/scoreboard/wiring.py` with one shared download per run:
S6 adds its port to E2c's wiring and reads the books' records the way E2c leaves them, never the pre-E2c layout.

### 1. S1 (`research/evaluation/PROTOCOL.md`, `fno/evaluation/protocol.py`)

Five items are added to `REQUIRED_ITEMS`, so `python -m fno evaluation check` refuses a protocol without them.

| Item | Rule (from the owner's row) | Numbers, proposals the owner decides |
|---|---|---|
| `do_nothing_benchmark` | Row 168, a gate before real money. Per rupee-day of capital tied, as in section 4 below. | Index fund expense 0.05% a year. Cash rate: the latest 91-day T-bill yield on the S1 freeze date (RBI's auction result; owner, 16 Oct 2026), written as a number with its date and source. Tax: F&O 31.2% on each financial year's positive net, no loss carried forward; the fund is treated as sold at the section's last session, its gain taxed once at 20.8% if the section is under 12 months, else 13% above one Rs 1.25 lakh exemption, a loss untaxed; cash 31.2%. |
| `scorecard_measures` | Rows 162 and 169: net without the best trade, profit factor, maximum drawdown and worst day. All are descriptive. | none |
| `t_check` | Row 167: printed warning, never a pass condition. | Blocks of 20 sessions (`uncertainty_criterion`'s block), one-sided 95%. |
| `missed_runs` | Row 170. | Scoreboard A miss cap: 10% of the book's eligible sessions in the period (G9's figure). |
| `random_control` | Response 144 red team 7 and 26: descriptive, not in Holm, never a gate. | 1,000 runs, seed 20261014, strikes within 10 strike steps of the money (widened to include the real trade's strike), the per-trade and bucket caps replayed. |

`frozen_files` gains the new scoreboard files under option A (scoring code is hashed before the freeze), so that item
is not reopened. `PROTOCOL.md`'s open question 2 is closed by row 167.

### 2. Trade measures (new `fno/scoreboard/trade_measures.py`, added to `sections.section` as `measures`)

These cover completed positions, from C1 net (`line.net`). Open trades are left out and their count is printed.

- **Net without the best trade:** closed net minus the largest single trade net. It is undefined with no trade.
- **Profit factor:** the sum of winning nets divided by the absolute sum of losing nets.
  - It is `null` with reason "no losing trade" when nothing lost; never infinite.
  - It prints the winner and loser counts and the two totals. A trade netting exactly zero is in neither.
- **Maximum drawdown and worst day:** from the section's daily series. The drawdown is the deepest fall of the
  cumulative net below its running high, which starts at 0 before the first session; the worst day is the lowest
  daily net. Both are shown in rupees, as a share
  of the book's `drawdown_brake_rs` in `config.yaml`, and with their dates.
  - They are labelled "marked daily, not the brake's closed equity": the brake uses closed equity, these use marks.

### 3. t-check (new `fno/scoreboard/t_check.py`, added to `uncertainty` as `t_check`)

- **Blocks:** k blocks of 20 consecutive sessions, counted back from the section's last session. The oldest n mod 20
  sessions are left out of this check only, and their count is printed.
- **Estimate:** R = full blocks' net ÷ full blocks' risk-days, the headline measure on the same days.
- **Block value (the ratio estimator's linearisation):** z_b = (net_b − R × risk_b) ÷ mean(risk_b), so a block's
  varying risk is weighed, not averaged away.
- **Bound:** R − t(0.95, k−1) × sd(z) / √k.
  - The one-sided 95% t quantiles for 1-30 degrees of freedom come from a fixed table in the module, since scipy is
    not installed. Above 30, the 30 value is used (slightly wider, so cautious).
  - The bound is `null` below two blocks or with zero risk in the full blocks.
- **Output:** the bound, k, the left-out sessions, and `agrees_with_bootstrap` (whether both bounds are on the same side
  of zero; `null` when either bound is `null`).
  - When they disagree, the section's `uncertainty.reason` gets "t-check disagrees: warning".
  - `claim_allowed` never changes.

### 4. Do-nothing comparison (new `fno/scoreboard/do_nothing.py`, added to every section as `do_nothing`)

**Index source:**
- NSE's daily `ind_close_all` file, already archived (A13's source). It has no NIFTY 50 total-return row; it was
  checked on 14 Oct 2026, where it lists "Nifty 50", "Nifty 50 Futures TR Index" and others.
- The fund's daily return is therefore the "Nifty 50" closing change plus its "Div Yield" column ÷ 100 × calendar days
  ÷ 365, minus the 0.05% expense pro rata.
- This is labelled "approximate total return (trailing yield)", some evidence.
- It reads a port `IndexLevels` whose adapter reuses `read_index_figures` (`fno/market_read_models/nse_files.py:93`,
  which already reads "Div Yield") on the archived files. A missing index day makes the comparison "not computable".
  It is never filled.

**Capital tied per session:** each held trade's capital tied at entry (S2's `capital_tied`: broker margin plus premium
paid). This is the same basis as S2's margin-days. A section holding a trade with no recorded capital (S2's
`no_capital` list) gives "not computable" for view (a), naming the trade. A section with zero capital-days (no trade
yet, or the overridden section, empty until F4 exists) gives `null` with the reason "no capital tied", never 0 ÷ 0.

**Benchmark returns:** capital tied at the previous session's close earns:
- the index fund's change to this session's close (the fund);
- the cash rate for the calendar days between the two sessions (cash).

**View (a), per rupee-day of capital tied (the gate):**
- the section's `net_rs` (after the allocated AI cost) after F&O tax, divided by capital-days. When `net_rs` is null
  (AI cost unknown), the view is shown on `raw_account_net_rs` labelled "before AI cost" and the verdict is null;
- the fund's and cash's gains on the same capital-days, after their tax, divided by the same capital-days.
- `beats_index_after_tax` is true, false, or null when not computable. It is a point comparison with no interval
  (response 144 item 24), and it says so.

**View (b), whole account:**
- the account's net after tax, plus idle cash (account capital minus capital tied) credited at the after-tax cash rate;
- against the fund and against cash on the whole account capital, over the same sessions, after their tax.

**Labels:** every tax figure is labelled "assumption until verified (owner's scenario)". Each simplification leans
against the book, never for it: the fund keeps its Rs 1.25 lakh exemption; F&O losses are not carried forward to
later years (the law allows 8 years). One non-tax item leans for the book: see Known limits (capital at entry).

**Strategy versions (the gate's level):** RM1's criterion 2 is per strategy version (design v2 8.3). Each book's board
gains `strategies`: for each playbook version (`ScoredTrade.strategy`, `<name>-v<n>`) in that book, its closed trades,
pilot included (per-strategy evaluation comes before the common start, REPLAN section 4), with `measures` and
`do_nothing`. `beats_index_after_tax` there is the value RM1 reads; RM1 reads Book 1's value only, and other books'
values are shown, never combined (RM1, judge 158 add. 1 minor).
- **Why here and not on E6's card:** E6 (`fno/scorecard/`) is the same level (one version in one account) but has no
  capital tied, no index and no daily series, and its `review.py` is an S1-frozen file. Adding them there would build a
  second capital and index path; scoreboard B already has both.
- **No second count:** a criterion checks that each entry's trade IDs and closed net equal E6's card for that account
  and version (both from C1's trade ledger).

### 5. Missed runs

**Scoreboard B:** `committed_runs.py` gains `missed_runs(sessions)`, and the board's top level shows `missed_runs`. The
list is read from E3's committed run logs and the NSE session calendar; the desk writes no new file. Each session from
the account's first session to the report day is checked:
- per book: no run log, a log with no decisions step, or a decisions step naming no run of that book:
  `missed_decision`;
- with no exits step while any trade was held at the previous close: `missed_exit_review`.

Scoreboard B is otherwise unchanged ("as it ran"): the next run's exits step reviews every open trade at that run's
snapshot, dated that day and never backdated.

**Scoreboard A (S3 criterion 3, amended in this commit):**
- Missed decisions are not scored and are listed.
- Above the miss cap, the book's verdict reads "undecided, operations".

### 6. Random control (new `fno/scoreboard/random_control.py`, added to head-to-head sections and segments as `random_control`)

**The twins:** for each completed position, each of 1,000 runs draws a twin:
- the same entry and exit sessions, expiry, lots and structure shape;
- a random direction: PCS↔CCS, CDS↔PDS and LC↔LP each 50%; SF, SC and BF have none;
- a random first strike: uniform within 10 strike steps of the entry snapshot's at-the-money strike, the other legs at
  the trade's own widths;
- filled with E4's pricing (`fno/desk/pricing.price_leg`) on the entry and exit execution snapshots, with C1 charges.

All runs come from one `random.Random(20261014)` stream.

**Redraws:** a draw that is not quotable at both ends, or breaks the trade's maximum-loss cap at those lots, is
redrawn, up to 20 times. So is a draw that breaks the bucket cap (`config.yaml` `risk.profiles.books.bucket_cap_rs`,
Rs 30,000) given that run's own open twins: flipping PCS to CCS changes the twin's bucket, the one cap a flip really
moves. The open-risk and new-risk caps are not replayed (judge 158: a flip at the same widths and lots barely changes
them). Structure eligibility is shared by construction: every flip is to a mapped code. The strike window always
includes the real trade's own strike (widened if needed), so the real trade is one of its possible twins. A twin still missing is counted. Above 10% of twins missing, the percentile is "not
computable".

**Measure:** both the book and each run use closed-trade net per rupee-day of risk: Σ net ÷ Σ (maximum loss at entry
× sessions held). It leaves out operating costs, which are the same for both.

**Output:** the book's percentile among the runs (ties count half) and the runs' median. It is labelled "selection
luck only, same dates (not window luck); descriptive, never a gate".

It reads the committed execution snapshots through the existing `ExecutionSnapshotSource` (`fno/desk/snapshot.py:128`)
and snapshot IDs, as `fno/scoreboard/sources.py:57` already does.

**Build order:** the random control's code is built last, as its own commit. No paper fill exists yet, so it has
nothing to rank for months; its definition is in S1 now (response 144 red team 7).

### Gap list (every requirement of the cited sources, mapped)

| Requirement (source) | Where |
|---|---|
| Headline kept, measures never the verdict (row 162) | criterion 12 (no field changes `claim_allowed` or the headline) |
| Do-nothing vs NIFTY 50 fund and cash, after tax (row 162, design 03:110-115) | section 4; criteria 5, 6, 8 |
| Max drawdown and worst day, rupees and share of the brake (row 162, response 144 table) | section 2; criterion 3 |
| Random-strategy percentile, 1,000 seeded runs, same structures and sizes, random direction and strike (row 162, response 144 red team 7) | section 6; criterion 10 |
| Selection luck only, descriptive, not in Holm (response 144 item 26) | section 6 label; S1 item `random_control` |
| Random control shares dates, universe, entry delays, structure eligibility, caps, fills, charges (response 147 item 7) | section 6: same dates and expiry, flips only to mapped codes, E4 pricing, C1 charges; caps: per-trade and bucket only (Known limits) |
| t-check a printed warning, disagreement flagged beside every claim (row 167, response 147 item 5) | section 3; criterion 4 |
| Do-nothing on every scoreboard (row 168) | scoreboard B: section 4, criterion 12; scoreboard A: S3 text and S3 criterion 5 |
| Do-nothing a gate before real money, per strategy version (row 168, design 08:83 item 2) | `strategies` entries; criterion 11; RM1 reads it (out) |
| Same capital, horizon and tax scenario; tax an assumption (row 168, response 147 item 4) | section 4 labels; criterion 8 |
| Per rupee-day of capital tied, the index over the same rupee-days (design 03:118-120, REPLAN.md:47) | view (a); criterion 5 |
| Whole account, idle cash at the cash rate (design 03:116-118) | view (b); criterion 6 |
| Point comparison with no interval; one tax treatment per instrument (response 144 item 24) | view (a) label; S1 item `do_nothing_benchmark` |
| Net without the best trade and profit factor; PF undefined with no losses; counts printed (row 169, response 147 item 6) | section 2; criterion 2 |
| Missed run: scoreboard B as it ran, `missed_decision`, `missed_exit_review` (row 170, response 147 item 3) | section 5; criterion 9 |
| Catch-up exit at the next valid quote, never backdated (row 170) | section 5; criterion 9 (end to end) |
| Scoreboard A on observed decisions with the miss cap (row 170, response 144 item 21) | S3 criterion 3 (amended, with the boundary) |
| Zero-risk resample scores 0.0 (response 144 item 27) | note only, as the item says; unchanged |
| Net per rupee of entry maximum loss (response 144 item 22) | out: not in the owner's rows |
| Independent bucket-weeks (REPLAN.md:47) | out: different function; orchestrator assigns |
| Brake figure mismatch (response 144 item 25) | out: REPLAN's `catastrophic_loss_book` change |

### Acceptance criteria

1. **Protocol items:** `python -m fno evaluation check` fails on today's `PROTOCOL.md` without the five items and
   passes with them. Each item states its rule and its numbers as proposals; rows 167-170 are marked decided.
2. **Trade measures:** for the trade nets [+9,000, −4,000, +1,000, 0]:
   - net without the best trade = −3,000;
   - profit factor = 2.5, with 2 winners and 1 loser;
   - for [+500, +200]: profit factor null with "no losing trade";
   - no trade: every measure null.
3. **Drawdown and worst day:** a series of daily nets [+1,000, −3,000, +500, −2,000, +4,000] gives a maximum drawdown
   of Rs 4,500 and a worst day of Rs −3,000 (with their dates). The drawdown share is 4,500 ÷ 1,20,000.
4. **t-check:**
   - a known-answer series of 6 blocks with unequal block risk reproduces a hand-computed bound (t(0.95,5) = 2.015);
   - 39 sessions give one block and a null bound; exactly 40 give two blocks and a defined bound;
   - a case where the bootstrap bound is above zero and the t bound below prints the warning, and `claim_allowed` is
     unchanged.
5. **Do-nothing, view (a):** on real archived `ind_close_all` days (a stretch of October 2026), with Rs 1,00,000
   tied for 5 sessions and a book net of Rs 2,000, the fund's and cash's gains match a hand calculation from the
   files' closes and yields to the paisa. The verdict follows. A missing index day gives null, never true.
6. **Do-nothing, view (b):** on the same real October 2026 days, a Rs 20,00,000 account with Rs 1,00,000 tied for 5
   sessions and a book net of Rs 2,000: the account's after-tax net plus Rs 19,00,000 idle credited at the after-tax cash
   rate, against the fund and against cash on Rs 20,00,000, each matches a hand calculation to the paisa. Boundary
   cases:
   - no trade at all and no operating cost: the book's view (b) equals the cash benchmark exactly;
   - the whole Rs 20,00,000 tied: the idle credit is exactly 0.
7. **Empty sections:** an overridden section with no trade and a head-to-head section before its first trade give
   `do_nothing` null with "no capital tied" in view (a); view (b) still computes (all idle).
8. **Do-nothing, tax:**
   - a book net of −Rs 2,000 pays no tax;
   - a section of 12 months or more taxes the fund's gain once at 13% above one Rs 1.25 lakh exemption; one day under
     12 months uses 20.8%; a fund loss is untaxed;
   - a section crossing 31 March taxes each financial year's F&O net apart (a loss year then a profit year: tax on the
     profit year in full);
   - every tax figure carries the assumption label.
9. **Missed runs, scoreboard B:** in a fixture month,
   - a session with no run log is listed as `missed_decision` for every book; a decisions step naming Book 1's run but
     not Book 2's lists it for Book 2 only;
   - a log stopped before exits with a trade open is listed as `missed_exit_review`;
   - the same without an open trade is not;
   - a closed day is never listed.

   The next session's run then exits the open trade at that day's snapshot, dated that day (the E3 behaviour, checked
   end to end on the fixture).
10. **Random control:**
   - the same records give byte-identical output twice (seed);
   - a trade whose every draw within 10 steps is unquotable is counted missing;
   - exactly 10% missing is computable; one more twin missing (just over 10%) is "not computable";
   - a fixture whose entry snapshot allows exactly two twins per trade (the real one and a worse one) gives the
     percentile (runs below + ties ÷ 2) ÷ 1,000, with both counts read from the same seeded stream: the exact value is
     asserted, not "near the top";
   - a flip that would put a fourth Rs 10,000 trade in a full Rs 30,000 bucket is redrawn;
   - a real strike 12 steps from the money widens the window to include it.
11. **Strategy versions:** each book's `strategies` holds one entry per playbook version it traded; its trade IDs and
    closed net equal E6's card for that account and version, on a fixture with two versions and a pilot trade.
12. **Boards:** every S2 section (overall, pilot, head-to-head, segments, unscored, overridden) carries `measures` and
   `do_nothing`. Only judged sections carry `t_check` and `random_control`. No field changes `claim_allowed` or the
   headline (schema test). A rebuild is byte-identical (S2 criterion 4 still passes).
13. **Gates:** S2's existing tests pass unchanged. No file or class is over 350 lines.

**Test plan:** the known-answer tests above, built from the situations the desk really meets (closed days, a run that
stopped before exits, an all-winning month, a short first quarter) and from real archived index files. Every
criterion gets a broken-code proof (rule 4).

**Judge verifies:**
- recomputes one section's do-nothing views (a) and (b) from the index files by hand;
- re-runs the t-check example;
- confirms that `claim_allowed` is unaffected.

**Known limits (stated, not fixed):**
- **Do-nothing is a point comparison:** one lucky quarter can pass it. RM1's other criteria and the uncertainty
  criterion carry the statistics.
- **The yield approximation:** the trailing dividend yield is not the paid dividends. The error is a fraction of the
  about 1.3% a year yield (some evidence).
- **The random control:** it holds the real exit dates, so it ignores what exit rules would do on a different strike.
  It controls direction and strike luck only.
- **The tax figures** are the owner's scenario, not a verified personal tax position.
- **Capital at entry leans for the book:** margin is not re-marked when the exchange raises it, and C2's stress
  reserve is left out, so view (a)'s capital-days are understated and the book's return per rupee is overstated. View
  (b), on the whole account, does not have this bias.
- **The random control replays two caps only** (per-trade maximum loss and bucket); open-risk and new-risk are not
  replayed.
- **Scoreboard A has no view (b):** it has no account, only one-lot positions.

**Depends:** S1 (draft), S2 (merged), E2c (built first: Drive board and wiring), E3, E4, E6 (reconciled), A13's index
files; RM1 reads the gate; S3 builds scoreboard A's share · **Size:** M · **Status:** text PASS
(judge 158 add. 1); code built, judge pending (branch `story/s6-scorecard-measures`, claims response 180; session
0185gR5DmoDh2zBAvgRU4CEB); merges after ChatGPT's review with S3
