# Story REC1: the recommender, one honest daily answer

Lane 1 (it decides what a trade would be, writes evaluation records and posts to Slack). Builder:
session_016KHNh1grWa9CyHE1mLwj5A; orchestrator session_01Mt6dcBU5kp2htdPN2KmiZH. Branch `story/rec1-recommender-text`
(text), then `story/rec1<part>-<short>` per part. **Text first: no code starts before the judge passes this text.**
Research and paper trading only: nothing here places, modifies or cancels an order, and nothing switches live until
the owner's go sets `daily.live_from.recommend`.

## Why (owner's words and the decisions it rests on)

- Owner, 22 Oct 2026 (DESK_DECISIONS "Product direction: recommend, record, learn"): "the system should recommend ...
  I'm not a financial expert. I cannot make decisions when to buy, when to sell"; "If the system is not sure, it
  alerts the user, do not buy a real trade"; "Every decision must be recorded so that later on we could analyze what
  went wrong".
- Owner, 25 Oct 2026 (via the orchestrator): the recommender is built fully, not partly.
- Response 327 (approved 22 Oct) keeps "the recommender with its banner" in the target design, banner red or amber
  only, "a future green would mean eligible for the owner's own review, never buy" (item 9), and no licence without a
  sample-size plan, a one-sided 95% lower bound above zero after multiple-test adjustment and a second forward window
  (item 4). DESK_DECISIONS 23 Oct ("AI drivers start after j") put the recommender after the 30-session review.
  **How the two fit (A1, answered by the owner's 25 Oct decision, orchestrator 25 Oct):** the recommender is built and
  switched on now, and the 30-session review is the first thing that can raise its confidence. Nothing in 327's
  statistics changes.

## What exists today (strong evidence: code on main 142e745)

| Piece | What it says | Limit |
|---|---|---|
| T1 card (`fno/cards/status.py`, `RegistryStatus`), live from 26 Oct | always `NO TRADE`: `no_approved_strategy`, `trade_fields_not_built`, `data_check_failed` (+ T1e `step_problems`) | reads only `playbook/registry.csv` (one version, `b0-monthly-sc` v1 at `research`); can never say anything else; no confidence |
| Desk Book 1 (E3, D3 `fno/playbook/decision_record.py`) | one decision record per session (`journal/book1_rules/decisions/<day>/`) | decides, never tells the owner; no confidence |
| School banner (MS-P1g, `fno/school/reports/banner.py`) | RED (a shown road closed, or no candidate) or AMBER (paper only); GREEN does not exist | behind `school.reports: false`; the school itself `school.enabled: false` |
| RM1 (`research/evaluation/REAL_MONEY_GATE.md`) | when a Book 1 version is "eligible to put to the owner" | Book 1 only; no school driver version can ever reach it |
| LR1 weekly review | forecasts, weather, data health | no decision or abstention review |

Gaps: no single recommendation; no confidence rule; no write-once recommendation record; no evening check of a
`NO TRADE`; card, banner and desk can disagree; RM1 does not reach the school; no weekly review of decisions.

## The rule (what "fully built" means)

### 1. One recommendation per NSE session, two answers

Made by `python -m fno recommend decide` as the daily-run step `recommend`, right after `school` (orchestrator's
ruling, 25 Oct: the record must hold the school's sealed decisions of the day, or the evening check of a `NO_TRADE`
is biased by omission, judge 620 S3). The chain, measured (GW1's builder via the orchestrator, 25 Oct; judge 641 SF2 and
641.2 m3): E3 is asked from 15:17:00 and its worst capture ends 15:19:57; the snapshot step ends about 15:20:10 (about
15:21:10 with one 60 s pause); then `quotes_done`; then the school step, starting about 15:21:30-15:22:30 under its own
`SCHOOL_STARTS_BY` of 15:25 (`fno/daily/wiring.py`) and taking up to 6 min 13 s on a cold cache (MS-P1j's 23 Oct
rehearsal; 77 s warm); then `recommend`, about 15:23-15:29 IST. On a day that needs E3's retry the school can be
refused (`school:TOO_LATE`); then, as whenever the school does not run, the record's school source is `unavailable`
(section 5), never complete. The recommend step's own timing never depends on the market being open: it reads
sealed records only, so it runs when reached on a session day and is never refused for being after 15:30. A muhurat-only session gets none (as T1). Each recommendation holds two separate answers:

- **Real money.** `DO_NOT_TRADE_REAL_MONEY` unless at least one version is both eligible under RM1 (section 4) on that
  day and at rung 3; then `ELIGIBLE_FOR_YOUR_OWN_REVIEW`, naming the version and pointing to its RM1 report. If RM1 and
  the rung disagree (eligible below rung 3), the answer is `DO_NOT_TRADE_REAL_MONEY` with `data_check_failed` and an
  alert naming both. A day stopped by `data_check_failed`, `step_problems`, `quote_gate_failed` or `weather_red` is
  `DO_NOT_TRADE_REAL_MONEY` too, never eligible, with the condition named (orchestrator's ruling on judge 654 m2). There is no "buy" value: the
  enum has exactly these two members (a test proves no input reaches a third).
- **Paper.** What the system itself books on paper today and why:
  - `PAPER_TRADE` (a recommendation): **only a version at rung 3, "Established"** (section 2), took a trade through
    the desk or the school; the record names the version, structure, worst loss after C1 costs, exit plan, and the
    source decision record by path and SHA-256. "Proven" in this story means rung 3 and nothing less (judge 620
    S1; response 327 item 4). The recommender never makes a trade itself: it only reads decisions already made and
    sealed.
  - `NO_TRADE`: with one reason code from a closed set, first match wins: `data_check_failed` (an input unreadable,
    missing or its hash wrong), `step_problems` (O1's problem steps, as T1e), `no_established_version` (no version at
    rung 3: the honest main reason, so it comes before the day's conditions), `quote_gate_failed` (the day's capture
    or road gate failed), `weather_red` (M1's recorded colour red), `risk_cap` (C2/C4 or a school safety law
    refused), `brake` (a drawdown brake or daily stop holds), `no_candidate` (a version at rung 3, none of them
    traded today). While no version is at rung 3 only the first three can occur.
  - **Paper trades of versions at rungs 0-2** (school drivers and controls, desk versions at `research`, `shadow` or
    `paper`) are never a recommendation: each is listed apart as "paper, not a recommendation: <version>, rung <n>
    (<name>), <its numbers>" (assumption A2). Controls (N0, RC1, REF, PS5, KL1) are counted, not listed.

### 2. Confidence is an evidence rung, a stated rule, never a free number

Per version, from frozen forward records only (S1's order rule: the decision's commit has the freeze record as a
strict ancestor; R1's data spend). Backtests, the simulator, rehearsals and uncounted days never count (planted
test each).

**Point in time (judge 620 S2).** A rung made at `made_at` on day d counts only sessions before d whose outcome
record's receipt time is strictly before `made_at`. The receipt time is GitHub's push receipt of the commit that
brought the outcome's receipt to `main` (`PushReceipts` in `fno/ai/receipts.py`, the project's rule; protocol v4
1.6), never a commit's own time (set by whoever commits) and never a file's own field (judge 620.2 m2). A receipt
GitHub cannot answer (`ReceiptUnknown`) fails closed: that outcome does not count that day, so the rung can only be
lower, never higher. Day d itself never counts, even if an outcome of day d were already receipted. The record
carries this cutoff (`evidence_cutoff`, UTC) and, per version, the counted sessions' first and last dates and count,
so a reader can recount it.

| Rung | Name | Rule (all numbers from response 327, frozen in REC1a's R1 card before the first counted day) |
|---|---|---|
| 0 | Unproven | fewer than 1 valid counted forward session |
| 1 | Exploratory | 1-29 valid counted sessions |
| 2 | Watching | 30 or more valid counted sessions and the descriptive review against the matched control (P2) done; the lower bound may include zero |
| 3 | Established | a sample-size plan met, one-sided 95% lower bound above zero after the frozen multiple-test adjustment, and a second untouched forward window that agrees |

- Day conditions can only lower a version's shown rung for that day (`quote_gate_failed`, `weather_red`, a scheduled
  event day as M1's weather record names it: one rung down, never below 0); nothing raises it.
- A calibrated probability ("said 70%, happened 68%") is shown only at 100 or more outcomes over 60 or more sessions,
  in 5 bins, as a descriptive check (327 item 4); before that the line says "not enough outcomes to calibrate".
- The rung is printed with its numbers: "Exploratory: 12 of 30 valid sessions, net Rs -3,400 vs control Rs -1,100,
  not established".

### 3. Where it goes (one record, every surface reads it)

- **#fno-desk line (REC1b; orchestrator's ruling, 25 Oct).** After the record's receipt is pushed, the step posts one
  short message to #fno-desk through the existing alert sender (`FNO_SLACK_BOT_TOKEN`; no new Slack sender). It
  says it is the recommender's answer, not the card's (judge 641 m2): the card above it shows the desk's own status
  ("NO TRADE (no_approved_strategy)") and the two can differ, for example a `PAPER_TRADE` line beside a card that
  stays NO TRADE until T1 slice B. An `ELIGIBLE_FOR_YOUR_OWN_REVIEW` line names the version (a version ID such as
  `school:CS1@1` is not a strategy internal) and says "for your own review, never a buy". For
  example: "PAPER ONLY. Recommender (not the card) for 02 Nov 2026. Real money: DO NOT TRADE (no version has passed). Paper: NO
  TRADE (no_established_version). Candidates: desk 1, school 42. Paper, not a recommendation: 16 trades of unproven
  versions. Record <receipt path>, SHA-256 <first 12>." It names no strike, price or strategy internal. A source
  that is unavailable is named ("school candidates: unavailable (not_live)"). No receipt pushed: no line, one problem
  line instead (criterion 9).
- **The card (not in REC1b; orchestrator's ruling, 25 Oct).** The card keeps its place in the run and its status.
  Moving it after the school would cost the owner reading time before the close every day for months, while the
  real-money answer can only be DO NOT TRADE (no version can reach rung 3 before the P2 review), so it would buy no
  information. Putting the recommendation on the card is a separate decision with the card's owner when rung 3
  becomes reachable. The card owner's conditions for that change (session_017q19WnkrRJvfQoXBLCy3hA, 25 Oct), each
  checked against the card code on main, stay agreed:
  - **Reason codes stay inside the pinned dashboard contract** (`contracts/omenix-dashboard/api/schemas/fno-card.yaml`
    2.14.0, closed enum). The card's code is a mapping of the record's code, same meaning only:
    `no_established_version` -> `no_approved_strategy` (no version has passed), `quote_gate_failed` -> `data_check_failed`
    (the day's inputs are unusable), and `data_check_failed`, `step_problems`, `weather_red` as they are. `risk_cap`,
    `brake` and `no_candidate` have no same-meaning code: they need a contract addition and re-pin (as W3i did for
    T1e), asked of the owner through the orchestrator (the 16 Oct UI pause allows contract reason lists, exception
    a). They cannot occur while no version is at rung 3; until the re-pin lands, one of them reaching the
    card gives `data_check_failed` and an alert "reason not in the dashboard contract", never a wrong code.
    `card_codes()` in `tests/cards/test_card_contract.py` reads the codes the card can actually emit after the
    mapping and guard, never the full paper-reason table (else the contract test is red until the re-pin and blocks
    every merge); after the re-pin, the three codes' mapping, the guard's removal and their entry into the emitted
    set land in one change. The guard's alert goes to #fno-desk through the card's existing alert path: no second
    Slack sender in `fno/cards/`.
  - **Line 1 of the section is a placeholder status line**, which `RuledStatus` replaces with "Status: <status>
    (<code>)" after T2's severity order (data_check_failed > hard_rule_breach > step_problems > this code); then
    "Real money: DO NOT TRADE (no proven edge)", "Paper: NO TRADE (<plain reason>)" or the trade's name, the rung
    line, and T1's paper trade count line.
  - **The card's status stays NO TRADE** (CardBuilder, card v1). A `PAPER_TRADE` day names the trade on its "Paper:"
    line only; showing `TRADE` with fields is T1 slice B, built by the card's owner, needed before any version
    reaches rung 3.
  - T1's criteria hold (PAPER ONLY on line 1, code plus plain reason, trade counts), and T1e's warning and T2's rule
    lines are unchanged.
  - **The record is read as a committed record:** through its receipt and the verified Drive cache, its path and
    SHA-256 in the card's "Records used"; in a rehearsal the `dryrun/` record (REH1), on T1f's rehearsal clocks once
    T1f is merged.
  - No dead code: `RegistryStatus`'s registry and trade-count reading is imported, not copied; if nothing uses
    `RegistryStatus` afterwards, it and its tests go in the same change.
  - The `fno/cards/` and `tests/cards/` diff goes to the card's owner before judge I.
- **08:50 "Today" and 20:05 "How did today go"** (MS-P1g sections, #fno-forecast): the morning shows the standing
  real-money answer from the latest rungs, labelled "standing; today's answer at about 15:20"; the evening shows the
  day's recommendation and its check (section 5). Agreed with MS-P1g's owner before REC1d's code.
- **Dashboard:** not in this story (UI pause, 16 Oct); REC1a publishes the contract fields only, status-only.

### 4. RM1 reaches driver versions (assumption A3)

RM1's text is unchanged except "Version" also covers a school driver version (MS-P1h's card plus its D6 row), with
its own counted paper record. Lane 1 (a rule document touching the real-money line), its own judge, owner decision
first (327 item 9 named it a separate owner decision).

### 5. Recorded write-once, checked every evening

- **Record:** `recommend/<YYYY>/<MM>/<day>.json` in Drive through O9's `DataStore` (written once; same bytes again a
  no-op, different bytes refused), receipt under `receipts/data/recommend/` committed and pushed **before** any post.
  Holds: schema version, session, made-at (UTC), code commit, config SHA-256, every input by path and SHA-256, each
  version's rung with its numbers, each gate's result, both answers, the reason code and its plain text. Strikes and
  prices live only in Drive (privacy rule); the repository gets the receipt and a status-only line.
- **Candidate set, fixed at decision time (judge 620 S3).** The record lists every candidate of the day as the
  decision saw it: each version's and control's decision record (version, path, SHA-256), traded or not, in one
  sorted list; an empty list is written as empty, never left out.
- **Candidate sources (orchestrator's ruling, 25 Oct).** The record also lists each candidate source (`desk:book1`,
  `school`) as `complete` or `unavailable`. **`complete` is defined positively** (judge 641 SF1): the source's own
  record shows it ran. For `school`: the run's `SessionRun.status` is `""` (it ran the session), and every sealed
  decision of the session was read and its hash checked. For `desk:book1`: Book 1's decision record of the day is
  present and its hash checked. Everything else is `unavailable` with the step's status and reason code, for example
  `ok` with `school:OFF` (today: `school.enabled` is false and the step exits 0 having run nothing), `ok` with
  `school:NOT_A_SESSION`, `school:TOO_LATE`, `not_live`, `not_built`, `exercised`, `failed`, `refused` (O1's statuses; there is no `frozen`), or
  the step missing from the run log. An `ok` status alone never makes a source complete. An unavailable source contributes no candidates, and the record says so; it never
  reads as "no candidates from that source". The evening check reports an unavailable source by name, and its total
  for the day is "incomplete: <source> unavailable", never a full total. An unavailable source that holds a rung-3
  version makes the paper answer `data_check_failed`; whether a version is at rung 3 is read from its own rung records
  (its counted outcomes and reports, section 2), never from the source that could not be read (judge 641 m1) (a recommendation cannot rest on decisions it could not read);
  while no version is at rung 3 it changes neither answer. This adds one field to REC1a's record (`candidate_sources`,
  required, sorted), made in REC1b before any record is written, so the schema stays version 1.
- **Evening check:** `python -m fno recommend check` in the evening routine after `lab close` writes
  `recommend/<YYYY>/<MM>/<day>.check.json` once, reading the candidate set from the recommendation record only
  (never a new search of the day's decisions): for `PAPER_TRADE`, the result after C1 costs (from desk marks or the
  school dashcam, never a new price); for `NO_TRADE`, what every listed candidate and matched control made (school
  tickets' three counts), each one and the total, as "abstaining saved Rs X" or "abstaining cost Rs X". The total
  is "not known yet" until every listed candidate has closed; a listed candidate whose record is missing or whose
  hash differs makes the check `data_check_failed`, never a smaller total. A check never edits the recommendation.
- **Weekly:** LR1's post-mortem gains one section: answers by reason code, abstention net, rung changes, and the
  calibration line under section 2's threshold.

### 6. Honesty guarantees (each a criterion with a planted failure)

- No version at rung 3 means real money `DO_NOT_TRADE_REAL_MONEY` and paper `NO_TRADE`, with any paper trades of
  lower rungs shown only as "paper, not a recommendation".
- A rung counts only outcomes receipted before the decision, never day d; the evening check reads only the candidate
  set fixed at decision time.
- A missing, unreadable or hash-mismatched input is `data_check_failed`, never a pass and never skipped.
- No recommendation is posted without its receipt pushed; a failed push posts the problem line instead.
- The recommender never writes a decision, a fill or a price; it reads sealed records only.

## Parts, files and dates (dates are scenarios, reasoning only)

| Part | What | Main files (new unless said) | Target |
|---|---|---|---|
| REC1a | contracts (`Recommendation`, two answer enums, reason codes, `EvidenceRung`), the rung rule, its R1 card and D6 row, the record codec **with the candidate set and `evidence_cutoff` from the first live day** (judge 620.1: release 2's evening check reads release 1's records), dashboard contract fields | `fno/recommend/contracts.py`, `rungs.py`, `codec.py`, `research/recommend/CARD_REC1.md`, `fno/constants.py` names | 27-28 Oct |
| REC1b | `recommend decide`, the daily step after `school`, the candidate sources, Drive store + receipt, the #fno-desk line (no card change) | `fno/recommend/decide.py`, `inputs.py`, `store.py`, `post.py`, `wiring.py`, `cli.py`; `fno/recommend/contracts.py` (`candidate_sources`); `fno/constants_operations.py` (one row), `fno/daily/wiring.py`, `fno/daily/reason_codes.py`, `config.yaml` (`daily.live_from.recommend: null`) | 26-29 Oct |
| REC1c | `recommend check` and the evening routine step | `fno/recommend/check.py`, CLAUDE.md evening step | 2-5 Nov |
| REC1d | morning and evening sections read the record | `fno/school/reports/` adapter (MS-P1g owner agreed) | 5-9 Nov |
| REC1e | LR1 weekly section | `fno/learning/recommend_section.py` (LR1 owner agreed) | 9-11 Nov |
| RM1x | RM1 covers driver versions (only after the owner's yes to A3) | `research/evaluation/REAL_MONEY_GATE.md` | after A3 |

**Release 1 (orchestrator, 25 Oct: every day it runs is a day of recorded, checkable verdicts): REC1a and REC1b are
judged and go live first**, target the week of 26 Oct (merge about Fri 30 Oct, first live session Mon 2 Nov at the
latest; a judge round or a REC1a card freeze that slips moves it, it is not shortened). REC1a's R1 card is frozen
before REC1b's first live day. Release 2 (REC1c-e) follows, about 9-13 Nov; until it, the record holds each day's
verdict and the evening check is built later from the same records, so no day is lost. `daily.live_from.recommend`
stays null until the owner's go. Judges (orchestrator's ruling, 25 Oct): **REC1b (the
daily verdict that can name a paper trade) and RM1x (the real-money gate) get two judges each**, under JUDGE.md's
two-judge rule; REC1a, REC1c, REC1d and REC1e one judge each. No merge 14:00-16:15 IST on a session day.

## Acceptance (each with good, bad, boundary and empty cases and a named plant the tests must catch; judge 620 m1)

1. **Two answers, closed sets.** The real-money enum has exactly two members and the paper answer one of `PAPER_TRADE`
   or `NO_TRADE` with exactly one code from section 1's set. Plant: a third enum member, and an unknown code in a
   record, each fail a test.
2. **Reason order.** With several conditions true, the first in section 1's order wins (one test per adjacent pair).
   Plant: swap two adjacent entries of the order table; a test fails.
3. **Rungs.** 0 / 1 / 29 / 30 valid sessions give rungs 0 / 1 / 1 / 2 (2 only with P2's review recorded); rung 3 only
   with all three of its conditions (each removed in turn gives 2). Backtest, simulator, rehearsal and pre-freeze
   records count 0 (one planted record each). Empty history: rung 0. Plant: the rule's 30 changed to 29; a test fails.
4. **"Proven" is rung 3 only (S1).** One test per rung 0, 1, 2, 3: a trade of a rung 0-2 version gives paper
   `NO_TRADE` (`no_established_version`) and a "paper, not a recommendation" line with its rung; a rung-3 trade gives
   `PAPER_TRADE`. Plant: the `PAPER_TRADE` threshold lowered to rung 1; the rung-1 test fails.
5. **Point in time (S2).** An outcome receipted 1 second before `made_at` counts; one at `made_at` or after does not;
   a day-d outcome receipted before `made_at` does not; the record's `evidence_cutoff` equals `made_at`. Plant: a
   receipted day-d record that must not count; removing the day-d exclusion makes a test fail.
6. **Day conditions only lower.** Each of the three conditions lowers by one, never below 0; none raises. Plant: a
   condition that adds one; a test fails.
7. **Real money.** No version both RM1-eligible and at rung 3 gives `DO_NOT_TRADE_REAL_MONEY` (today's registry and an
   empty registry); one gives `ELIGIBLE_FOR_YOUR_OWN_REVIEW` naming it; RM1-eligible below rung 3, or RM1 unreadable,
   gives `DO_NOT_TRADE_REAL_MONEY` with `data_check_failed`. Plant: dropping the rung-3 condition; a test fails.
8. **Reads only sealed records.** A trade answer cites its source decision by path and SHA-256; a changed byte in the
   source gives `data_check_failed`. The recommender module imports no fill, order or desk-writing code (an import
   test). Plant: one changed byte in a source decision; and an import of `fno.desk` fills added to the module.
9. **Write-once and receipt first.** A receipted day is never written again: a later run re-sends that day's own stored
   line, labelled "Re-sent", so a run that stopped after its receipt and before its post loses no line (judge 654 m1);
   a record on Drive without a receipt is adopted and the first record stands; other bytes are never written over; a
   failed receipt push means no Slack post and one problem line to #fno-desk. Plant: the receipt push made to fail; a test
   proves nothing was posted.
10. **The #fno-desk line and the sources (REC1b).** With today's main data the line reads "Real money: DO NOT TRADE
   (no version has passed)" and "Paper: NO TRADE (no_established_version)"; it carries no strike, price or strategy
   internal (a test scans it against the record's private fields); it is posted only after the receipt is pushed. The
   step runs after `school` in `DAILY_RUN_STEPS`. A school step `not_live`, `failed`, `refused`, `ok` with `school:OFF` or `school:NOT_A_SESSION`, or
   missing from the run log gives `school: unavailable (<status>, <reason code>)` in the record and the line, never an
   empty complete source; `complete` only when `SessionRun.status` is `""` and every sealed decision's hash checks; with a rung-3 version
   in that source the paper answer is `data_check_failed`. The card's output is the same with the step on and off by
   construction: the card runs before the step and no card module imports `fno.recommend` (an import-graph test,
   judge 653 m1 and 654 S2). The line says "Recommender (not the card)" and names an eligible version. Plants: an unavailable school
   written as `complete` with no candidates; "school off" (`ok`, `school:OFF`) read as complete; each fails a test.
11. **Candidate set from day one (S3, judge 620.1; REC1a).** The codec round-trips the candidate set (version, path,
   SHA-256; empty written as empty) and `evidence_cutoff`; a record without either is refused by the codec. Plant:
   the candidate field made optional; a test fails. The release-1 record of a recorded day carries both.
12. **Evening check (S3).** Trade, no-trade, a candidate not closed ("not known yet") and missing-record cases; each
   listed candidate reported and the total equals their sum; the check never edits the recommendation (hash
   unchanged) and never reads a price not already recorded. Plant: a losing candidate removed from the check's
   input after the decision; the check must give `data_check_failed`, never a smaller total.
13. **Calibration line.** 99 outcomes or 59 sessions print "not enough outcomes to calibrate"; 100 over 60 print 5
   bins. Plant: the threshold changed to 99; a test fails.
14. **Clock and day.** A holiday or muhurat-only day writes nothing; a rehearsal writes under Drive `dryrun/` only
   (REH1). Plant: a holiday in the calendar fake with the step run; a test proves no write.
15. **Real output sample** in Claims from a dry run on a recorded day (status and reason only, no strikes).

## Gap list (each requirement of the design: a criterion, or out with its reason)

| Requirement | Where |
|---|---|
| daily decision paper/no trade with reason | 1, 2, 4 |
| confidence from a stated rule | 3, 5, 6, 13 |
| "do not trade" alert when not sure | 4, 7, 10 (the #fno-desk line) |
| every decision recorded write-once | 9 |
| checked every evening, no-trade included, no hindsight | 10 (sources), 11, 12 |
| learning through scheduled reviews | REC1e (LR1 section); rule changes stay new versions (R3), never daily |
| never invents an edge | 3, 4, 5 (plants), 8 |
| books 2 and 3 as recommenders | out: their trading job (F5, F6, F1t) is not built (DESK_DECISIONS 25 Oct (1)); they plug in as more versions with rungs, no change here |
| real orders | out: hard line |
| dashboard screen | out: UI pause; contract fields only |
| the recommendation on the card | out of REC1b (orchestrator, 25 Oct): a separate decision with the card's owner when rung 3 becomes reachable; the card owner's conditions in section 3 stay agreed for it |
| dashboard reason codes `risk_cap`, `brake`, `no_candidate` | contract addition and re-pin, owner via the orchestrator, before the recommendation reaches the card |
| the card showing `TRADE` with fields | T1 slice B, the card owner's story, before any version reaches rung 3 |
| futures and stock options | out: not in the pilot (327 P3+) |

## Questions for the owner (each with the recommended answer; the text assumes it)

- **A1. Answered** (owner, 25 Oct: build fully now): switched on as soon as judged; the 30-session review is what
  first moves a rung.
- **A2.** Keep booking paper trades of versions below rung 3, labelled "paper, not a recommendation", while the
  recommendation says `NO TRADE`. Recommended: yes; without them no evidence ever accrues. (The owner's 22
  Oct words "will not place a paper trade" read literally would stop the school.)
- **A3.** Extend RM1 unchanged to school driver versions. Recommended: yes, else nothing the school learns can ever
  become eligible.
- **A4.** Keep 327's thresholds exactly (30 sessions; 100 outcomes over 60 sessions; one-sided 95% after adjustment;
  a second window). Recommended: yes, frozen before the first counted day.

What the owner will see, plainly: every session for months, "Real money: DO NOT TRADE (no proven edge)". Rung 2 is
possible from about mid-January 2027 if the pilot starts counting in late November; rung 3 needs a second untouched
window, realistically mid-2027 or never. That is the measurement, not a fault.

## Claims

Text round 2 (answers to judge 620, judge J; the orchestrator agreed all three should-fixes):
- **S1 accepted** (my rung-1 `PAPER_TRADE` was a real flaw: it would have presented an unproven version as a
  recommendation). "Proven" is rung 3 only; the code is `no_established_version`; rung 0-2 trades are "paper, not a
  recommendation" with their rung; the real-money answer also needs rung 3 (RM1 and rung disagreeing gives
  `data_check_failed`). Section 1, section 6, criteria 4 and 7.
- **S2 accepted.** Point-in-time rule: outcomes receipted (GitHub's push receipt, judge 620.2 m2 accepted: a commit's
  time is set by its committer; `ReceiptUnknown` fails closed) strictly before `made_at`,
  never day d; `evidence_cutoff` in the record. Section 2, criterion 5 with the day-d plant.
- **S3 accepted.** The candidate set (version, path, SHA-256) is fixed in the record; the check reads only it, reports
  each and the total, "not known yet" until all closed, a missing or changed one gives `data_check_failed`. Section 5,
  criteria 11 (the codec carries it from the first live day, judge 620.1) and 12 with the dropped-loser plant.
- **m1 accepted.** Every criterion 1-14 names its plant.
- **Judges:** the orchestrator's ruling written in (REC1b and RM1x two judges; the rest one).
- Also in this round: the card owner's seven conditions (section 3, criterion 10), and release 1 (REC1a+b) dated the
  week of 26 Oct.

### REC1a Claims (round 1, branch `story/rec1a-contracts`; the SHA is in the commit that carries this text)

Files: `fno/recommend/` (`constants.py`, `rungs.py`, `contracts.py`, `codec.py`), `research/recommend/RUNG_RULE.md`,
`tests/recommend/` (102 tests). Every file is at most 160 lines.

| Criterion (REC1a's part) | Code | Test | Plant (caught) |
|---|---|---|---|
| 1 closed sets | `constants.py` `RealMoneyAnswer`, `PaperAnswer`, `NoTradeReason` | `test_constants.py` | a `BUY` member; an unknown code in a record (`test_an_unknown_code_is_refused`) |
| 2 reason order (declared here; applied in REC1b) | `NoTradeReason` in priority order | `test_the_reasons_are_the_story_s_set_in_its_priority_order` | two reasons swapped |
| 3 rungs | `rungs.py` `rung_for`, `evidence` | `test_rungs.py` (0/1/29/30/31 sessions, review, each rung-3 condition removed, backtest/simulator/rehearsal, refused outcome, empty) | 30 -> 29; rung 3 without the review; simulator counts; a refused outcome counts |
| 4 "proven" is rung 3 (record level; the decision is REC1b's) | `contracts.py` `_paper_consistent`, `_real_money_consistent`, the candidate-rung check | `test_a_trade_below_rung_3_can_never_be_a_recommendation`, `test_a_candidate_cannot_carry_a_higher_rung_than_its_evidence`, `test_with_no_established_version_only_the_first_three_reasons_can_occur` | the trade threshold at rung 1; the candidate's rung trusted; any reason allowed with no rung 3 |
| 5 point in time (S2, m2) | `rungs.py` `_counts`: `session < day`, `receipt_at < made_at`, `None` fails closed; `evidence_cutoff == made_at` in the record | `test_the_receipt_must_reach_main_strictly_before_the_decision` (1 s before / at / 1 s after), `test_day_d_never_counts_even_with_an_early_receipt`, `test_an_unknown_receipt_fails_closed` | day d counts; `<=` at `made_at`; an unknown receipt counts; the cutoff check dropped |
| 6 day conditions only lower | `rungs.py` `lowered` | `test_day_conditions_only_lower_one_step_each_never_below_zero` | `+` in place of `-` |
| 7 real money (record level) | `_real_money_consistent`: eligible only for a version at rung 3 in the record's own evidence | `test_only_an_established_version_can_be_eligible` (rung 1, rung 0, an unknown version) | eligible below rung 3 |
| 11 candidate set from day one (620.1) | `codec.py`: missing field refused; canonical bytes only; sorted unique candidates | `test_a_record_without_a_field_is_refused[candidates]`, `[evidence_cutoff]`, `test_an_empty_candidate_set_is_written_as_empty_never_left_out`, `test_an_extra_field_at_any_depth_is_refused` | the two fields made optional; the canonical check dropped; candidates unsorted |
| 13 calibration threshold | `rungs.py` `calibration_shown` | 99/60, 100/59, 100/60 | 100 -> 99 |

**The 24 plants:** `sh <scratchpad>/plants.sh` mutates one line at a time and runs `tests/recommend`. All 24 were
caught; a comment-only control plant survived, as it should. The first run gave false results: a mutant of the same
size, restored within the same second, kept Python's stale bytecode. The runs counted here use
`PYTHONDONTWRITEBYTECODE=1` with the `__pycache__` folders removed. A card plant (`watching_sessions` 30 -> 25 in
`RUNG_RULE.md`) fails both card tests.

**Deviation from the passed text (accepted by the orchestrator, 25 Oct; for the judge).** The text said "its R1 card and
D6 row". A D6 row cannot exist: `is_known_book` (`fno/books/version_registry.py:26`) accepts only the three books and
`school:<driver>@<n>`, and the recommender is not a book. A ledger trial would also be wrong: the rung rule tests no
hypothesis, it reads trial 99's measurement and RM1. Instead `research/recommend/RUNG_RULE.md` holds every number. Its
SHA-256 is pinned in `rungs.py` (`RUNG_RULE_SHA256`), `test_rung_rule_card.py` checks the hash and that the code's
values equal the card's, and each record carries `rung_rule_sha256`. Still to come in REC1b: refusing to record when
the card's hash differs from the pinned one, and the git-ancestor proof that the card's commit precedes the first
record.

**Moved to REC1b, so nothing is built without a caller (no dead code):**
- the dashboard contract fields;
- the plain texts' use, though `REASON_TEXT` is defined here and tested complete.

The names live in `fno/recommend/constants.py`, not in `fno/constants.py`. That file has 350 lines, the limit, so this
follows the school's `fno/school/constants.py`.

**The record's own rules (all in `Recommendation.__post_init__`, so no reader ever meets a broken record):**
- times in UTC, one spelling per instant;
- `inputs`, `versions` and `candidates` sorted and unique;
- every candidate's rung equals its version's evidence rung;
- `PAPER_TRADE` only for a traded rung-3 candidate of the day;
- `ELIGIBLE_FOR_YOUR_OWN_REVIEW` only for a rung-3 version;
- with no rung-3 version, only `data_check_failed`, `step_problems` or `no_established_version` can be the reason; with
  one, `no_established_version` never can.

**Self-review (quality rule 3).** An independent review agent read the first commit (961ccbf6) and reported 3 blocking,
4 should-fix and 3 minor findings. I checked each one against the code and fixed them at 54451406:
- **Blocking, all fixed.** (1) The candidate's own rung was trusted, so a rung-1 version tagged established could be
  sent as a trade; it is now tied to the record's evidence. (2) The eligible version was not tied to rung 3. (3) The
  codec ignored extra fields inside nested objects.
- **Should-fix:**
  - wrong-type values (`traded: "no"`) are now refused by type checks plus the canonical-bytes rule;
  - IST spellings of an instant are refused: UTC only;
  - repeated or unsorted `inputs` and `versions` are refused;
  - the spec mismatch is the deviation above. Its "pre-freeze records count 0" part is the counting rule's `counted`
    flag (MS-P1h's `CountingRule` and S1's order rule decide it); REC1b's input adapter sets it and is tested there.
- **Minor:**
  - a naive receipt time is now refused when made;
  - the malformed-hash test now matches on its message;
  - `rung_rule_sha256` is not compared with the pinned hash inside the record on purpose: an older record keeps the
    card it was made under, and REC1b refuses to make a record under a changed card.

**Real output sample** (committed code, a dry construction; status only, no strikes). It is today's truth for every
school driver, since `school.first_counted` is unset and no forward session is counted. A planted day-d outcome,
receipted 3 hours before the decision, also stays out:

```
VersionEvidence(version='school:CS1@1', rung=<EvidenceRung.UNPROVEN: 0>, counted_sessions=0, first_session=None, last_session=None)
VersionEvidence(version='school:CS1@1', rung=<EvidenceRung.UNPROVEN: 0>, counted_sessions=0, first_session=None, last_session=None)
```

**Gates (at 54451406, code unchanged since):** full suite `pytest -q -n auto`: 16666 passed, 1 skipped, 14 xfailed;
ruff check and format, `check_imports` and `check_records` clean.

### REC1a Claims, round 2 (judge 629 FAIL round 1: one should-fix, S1)

**S1 accepted, fixed at the root.** A version's rung was a free label. Judge J built `VersionEvidence(rung=ESTABLISHED,
counted_sessions=0)` and it went through the codec to `PAPER_TRADE`. The fix:
- `VersionEvidence.__post_init__` (`rungs.py`) refuses any rung other than `rung_for(counted_sessions, reports)`. That
  is the rule applied to the version's own count and its own reports, not a ceiling only. A label can then never claim
  more than its evidence, and a lower label is refused too, so each count has one truth.
- `first_session` and `last_session` are None exactly when the count is 0; otherwise first <= last, and the count fits
  in the span.
- The reports are references, not flags. The old `EstablishedTest` booleans are replaced by `EvidenceReports`: one
  `RecordRef` (path, SHA-256) per frozen report, named only when it passed:
  - `review` (P2) for rung 2;
  - `sample_plan`, `lower_bound` and `second_window` as well for rung 3.
  - A rung-3 version without all four references is refused. Their SHA-256 values are checked with the record's other
    hashes.
  - Beyond the orchestrator's (b), rung 2 also needs its review reference: it is the same flaw one rung down. A
    "Watching" label with no review behind it was just as possible.
- Thresholds: `rung_for` uses `WATCHING_SESSIONS`. That is the card's own value, pinned equal to `RUNG_RULE.md` by
  `test_the_code_s_numbers_are_the_card_s_values`, whose hash is pinned too, so no number is free in the code.
  `RUNG_RULE.md` is unchanged; its hash is the same.
- `lowered()` is unchanged. It works on the day's shown rung, never on a stored `VersionEvidence`.
- `RecordRef` moved to `fno/recommend/refs.py`: the rungs and the record both use it, and the old place would have
  made an import cycle.

New tests for J's round-2 plants:
- `test_a_rung_that_its_own_count_and_reports_do_not_give_is_refused`: rung 3 with 0 sessions, rung 2 with 29, rung 2
  without a review, rung 1 with 0, rung 0 with 5.
- `test_a_rung_3_label_with_one_report_missing_is_refused`: each of the four references.
- `test_first_and_last_must_fit_the_count`: first after last, and the None cases.
- `test_a_proven_label_without_evidence_cannot_reach_a_record`: J's exact case, through the codec.
- `test_a_malformed_report_hash_is_refused`.

Plants: 29, all caught. The 5 new ones: the rung tie removed; the span check removed; first after last allowed; one
rung-3 report made optional; the report hashes left unchecked. Tests: 122 in `tests/recommend`.

Gates at 12df90b1 (code unchanged since): full suite 16689 passed, 1 skipped, 14 xfailed; ruff check and format and
`check_imports` clean.

### REC1b text amendment (orchestrator's ruling, 25 Oct; for the judge before REC1b's code)

Changed from the passed text, each from the ruling:
- **The step runs after `school`, not before `card`** (section 1). Reason: the record must hold the school's sealed
  decisions of the day (judge 620 S3); measured run times are in section 1. Its timing never depends on the market
  being open.
- **REC1b leaves the card unchanged and posts its own #fno-desk line** (section 3, criterion 10).
  - The card source moves out of REC1b: it becomes a separate decision with the card's owner when rung 3 becomes
    reachable.
  - The card owner's conditions stay agreed for that later change.
  - The card's output stays byte-identical (golden file).
- **Candidate sources** (section 5, criterion 10).
  - An unavailable source is recorded as unavailable with its step status, never as an empty complete list.
  - An unavailable source holding a rung-3 version gives `data_check_failed`.
  - This adds the required field `candidate_sources` to REC1a's record. It is made before any record exists, so the
    schema stays version 1.
- REC1b's files and dates are in the parts table (26-29 Oct). Live target unchanged: Mon 2 Nov.

**Round 2 of the amendment (judge 641: 2 should-fix, 2 minor, all accepted; SF2 with the orchestrator's correction):**
- **SF1.** `complete` is now defined positively: the source's own record shows it ran (`SessionRun.status == ""`
  with every sealed decision hash-checked; Book 1's decision record present and hash-checked). `ok` with
  `school:OFF` or `NOT_A_SESSION`, and every other status, is `unavailable` with its status and reason code. New
  plant: "school off read as complete" (section 5, criterion 10).
- **SF2.** The arithmetic is fixed. The chain is capture end (~15:20), then `quotes_done`, then school (starting
  15:19-15:23 under `SCHOOL_STARTS_BY` 15:25; up to 6 min 13 s cold), then `recommend` at about 15:25-15:30. A refused
  school (`TOO_LATE`) is `unavailable`. The orchestrator confirms with GW1's builder that the school's start stays
  before 15:25.
- **m1.** The rung-3 test reads the version's own rung records, never the unread source.
- **m2.** The line says "Recommender (not the card)"; the card shows the desk's status, and the two can differ.
  `ELIGIBLE` names the version, "for your own review, never a buy".

### REC1b Claims (round 1, branch `story/rec1b-daily-record`; the SHA is in the commit that carries this text)

New files are in `fno/recommend/`; each is at most 125 lines:
- `ports.py`, `gather.py`, `decide.py`;
- `desk_source.py`, `school_source.py`, `evidence.py`, `conditions.py`;
- `store.py`, `post.py`, `run.py`, `cli.py`, `wiring.py`.

Changed elsewhere:
- `fno/recommend/contracts.py` and `constants.py`: `candidate_sources`;
- `fno/constants_operations.py`: one row;
- `fno/daily/wiring.py`: the step and its live key;
- `fno/daily/reason_codes.py`: the `recommend` codes;
- `fno/cli.py`: one parser;
- `config.yaml`: `daily.live_from.recommend: null`;
- the tests that pin the step tuple, the live keys and the receipt builders (they now name `recommend`).

Nothing in `fno/cards/` changes.

| Criterion | Code | Tests | Plants (all caught) |
|---|---|---|---|
| 2 reason order | `decide.py` `_reason`, `_without_trade` | `test_decide.py` (one test per adjacent pair, plus step problems and no established version) | established ignored |
| 4 "proven" is rung 3 | `decide.py`, the contract | `test_a_trade_below_rung_3_is_never_a_recommendation`, the rung-3 trade | (REC1a's plants) |
| 7 real money | `decide.py` `_eligible`, no eligibility before an RM1 report | `test_real_money_needs_rung_3_and_rm1`, data check | - |
| 9 write-once, receipt first | `store.py`, `run.py` | `test_run.py` (refused push posts nothing; receipt before post; same day not written or posted again; a half-finished save adopted; foreign bytes never overwritten) | post before the receipt; already recorded posted again; adoption overwritten |
| 10 line and sources | `post.py`, `school_source.py`, `desk_source.py`, `gather.py` | `test_school_source.py`, `test_desk_source.py`, `test_gather.py`, `test_post.py`, `test_run.py` (scan for strike or price) | school off read as complete; unavailable written as complete; missing seal tolerated; manifest checked one way; hash unchecked; shadow counted; price in the line |
| inputs fail as inputs | `ports.open_run_log`, each adapter | unreadable run log, decision file, seal, weather | failed input passes; missing weather passes; backfill weather passes; unrated version guessed |
| evidence point in time | `evidence.py` | `test_evidence.py` | day d read; closed road counted; desk paper version rated silently |
| the step | `fno/daily/wiring.py` | `test_daily_step.py` (after `school`; null means not live; no pathspec; one alert; every last line has its code) | step moved; status alerts twice |
| rung card pinned | `run.py` | `test_a_changed_rung_rule_makes_no_record` | hash unchecked |

**Plants:** 22, all caught. A comment-only control plant survived, as it should. They ran with
`PYTHONDONTWRITEBYTECODE=1` and no `__pycache__`.

**Self-review (quality rule 3).** An independent agent reviewed f646e2c9. I checked every finding against the code;
all are fixed at 25860aca except the notes below.
- **Should-fix:**
  1. A file listed in `records.sha256` but missing was dropped silently. The manifest is now checked both ways.
  2. Two alerts went out for one failure, the second with "alert sent" as its reason. Now `status_alerts=False`
     (a raise is still alerted), and the command prints its outcome line last.
  3. `made_at` sits inside the bytes, so a rerun after a half-finished save could never succeed. A record on Drive
     with no receipt is now adopted (as the dashcam's `recover`), and the first record stands. A receipted day is
     never written or posted again. Programming errors keep their traceback.
  4. Unreadable inputs crashed the step. Each adapter now raises `InputFailed`, which becomes `data_check_failed`.
- **Minor:** criterion 10's `<status>, <reason>` format; the `recommend:*` public codes; `STEP_OK` used.
- **Found by me while fixing:** Book 1's records write action `trade` for a research shadow too
  (`decision_record.py:51`). "Traded" is now `Decision.CHOSEN` in `book` mode only.
- **Not fixed, stated plainly:**
  - The run-log reference in `inputs` is the log as read at decision time. Later steps rewrite that file, so the hash
    verifies against the run's commit after the school step (O1 commits each step), not against the final file.
  - A GitHub outage makes receipts unknown. A rung-3 version could then read lower that day, and an unavailable
    school would no longer force `data_check_failed`. This cannot happen before rung 3; it is a question for the
    rung-3 story.
  - `risk_refused` and `braked` have no reader yet, so `risk_cap` and `brake` cannot occur. Their readers come with
    the first rung-3 version, as does the desk's evidence reader. Until then a desk version at `paper` fails loudly.

**Real output sample.** A dry run on the committed records of Fri 23 Oct. Real: desk source, run log, M1 weather,
D6 versions, playbook registry. The school step is absent from that day's log. Fakes: only the Drive store and Slack.
```
PAPER ONLY. Recommender (not the card) for 23 Oct 2026. Real money: DO NOT TRADE (no version has passed). Paper: NO
TRADE (no_established_version: no version has passed: none is established on forward paper results). Candidates:
desk:book1: 1 candidate(s); school: unavailable (missing, the school step is not in the run log). Paper, not a
recommendation: 0 trade(s) of versions below rung 3. Record recommend/2026/10/2026-10-23.json, SHA-256 <12 hex>.
```
The record rated 13 versions: `book1_rules` and the 12 registered school versions, all at rung 0.

**Timing:** judge 641.2 m3 notes the school's start of about 15:21:30-15:25:30; GW1's measured chain is in section 1 now (round 2). The orchestrator was getting GW1's
measured chain, and the text will be updated when it comes. A refused school (`TOO_LATE`) is recorded `unavailable`.

**Gates at 25860aca (code unchanged since):** full suite 16856 passed, 1 skipped, 14 xfailed; ruff check and format,
`check_imports` and `check_records` clean. `tests/recommend`: 252 tests.

### REC1b Claims, round 2 (judge 653 PASS with 2 minors, judge 654 FAIL with 2 should-fix and 2 minors; all accepted)

Each finding was checked against the code first; every one held.
- **654 S1:** the RM1 and rung disagreement is now built.
  - `decide.disagreeing`: RM1 naming a version below rung 3 gives `data_check_failed`, `DO_NOT_TRADE_REAL_MONEY`
    and no eligible version.
  - `gather` alerts it by name: "RM1 names <v> eligible, but its rung is <n>: the two gates disagree".
  - Tests: `test_rm1_naming_a_version_below_rung_3_is_a_failed_data_check` (rungs 0, 1 and 2) and
    `test_rm1_and_the_rung_disagreeing_is_alerted_by_name`.
- **654 S2:** the three untested criteria now have tests.
  - Criterion 8: `test_reads_only.py` scans every module's imports against the writers and traders (desk, books,
    playbook, school execution, accounts, fleet, safety, drivers, tickets, simulator, providers, risk, checks, daily).
    Only four named readers are allowed. J's plant `from ..desk import exits` is caught, and a test proves it.
  - Criterion 14: `test_cli.py` runs a weekend, a holiday (26 Jan) and the coming muhurat-only Sunday 8 Nov 2026,
    each printing the one line and building nothing. The calendar test separates them from a session day.
  - Criterion 10's card part: the criterion now states the construction argument (K's m1), proved by
    `test_no_card_module_reads_the_recommender` and the plant "card reads the recommender".
- **654 m1:** a receipted day is never written again, and a later run re-sends that day's own stored line, labelled
  "Re-sent: … an earlier run may have stopped after its receipt and before its line". So no line is ever lost
  silently. Criterion 9's text says so.
  - Found while testing: a run that finds the day already recorded used to alert its own discarded answer's input
    problems. Only the record that stands is reported now (plant "dropped answer's problems alerted").
- **654 m2 (orchestrator's ruling):** a day stopped by `data_check_failed`, `step_problems`, `quote_gate_failed` or
  `weather_red` is DO NOT TRADE for real money too, never eligible.
  - The line names the condition.
  - The contract refuses ELIGIBLE on such a day.
  - Section 1 has the one line.
  - `quote_gate_failed` is added beside the ruling's two: it is the same kind of day condition, and leaving it out
    would let a day whose quotes failed read "eligible". Judges, please check this addition.
- **653 m2:** `test_a_book_entry_without_a_run_is_unavailable`.
- **641.2 m3 (orchestrator's message):** GW1's measured chain is in section 1. The school starts about
  15:21:30-15:22:30 and `recommend` runs about 15:23-15:29. A day needing E3's retry can make the school `TOO_LATE`,
  which is then recorded `unavailable`.

**Plants this round: 10, all caught.** Each judge's surviving plant (J's S1, X19 and X23; K's m2) is among them. One
earlier result line was hidden by my own script and was re-run alone; it was caught. Tests: 276 in `tests/recommend`.

### REC1c text amendment (before code; orchestrator's rulings, 25 Oct)

What changes or is made exact in the passed text for REC1c, each named:

1. **The brake rule first** (orchestrator's ruling on judge 654.1's open point, the safer reading): a version under its
   own drawdown brake is never `ELIGIBLE_FOR_YOUR_OWN_REVIEW`.
   - `decide` and the record's contract both refuse it.
   - The real-money line names the brake.
   - Test and plant: a rung-3, RM1-eligible version that is braked gives `DO_NOT_TRADE_REAL_MONEY`.
   - It cannot occur before rung 3. It is built now so that it is in place before rung 3 is reachable.
2. **Where it runs** (orchestrator, 25 Oct; judge 658 S1). Step "3b" of CLAUDE.md's evening section: `python -m fno
   recommend check`, after step 3 has committed and pushed the edition's receipts and the release logs, so it never
   races them.
   - Its own command commits and pushes only its own receipts (`receipts/data/recommend/`), in its own commit.
   - Step 4's notes cover its alert, its exit 1 and any "alert NOT sent" line.
   - The CLAUDE.md line ships on REC1c's branch and is judged with it, in lane 1, because it changes a routine's
     steps. The owner's routine prompt is unchanged: it already reads that section.
   - **It never fails the evening edition.** It runs after `lab close` has posted. On its own error it alerts
     #fno-desk and exits non-zero, and the edition's receipts are committed before it, as today.
   - **"Never fails" also covers the readers after it** (judge 658 m2): LR1's weekly section and REC1d's 08:50 section
     read a missing or `data_check_failed` check as exactly that, by name, and post their edition all the same.
3. **What it reads**, all sealed records; it never reads a price, and never searches the day's decisions afresh.
   - The recommendation record of the session being checked.
   - Each **listed** candidate's outcome:
     - A school candidate (`<seal path>#<road>`): its `OutcomeRecord` in the school dashcam's sealed `outcomes`
       files from its session up to the check's day. The record names the same `decision_sha256`, `driver_id` and
       `road`. Its `net` is after C1 costs. An outcome with `is_ticket` is reported apart, as a ticket, never as a
       trade.
     - **One live outcome per candidate** (judge 658 S2). Corrections are resolved first: a record whose SHA-256 a
       later record names in `corrects` is replaced and drops out. Exactly one live record means closed; none means
       open; two or more live records, or a `corrects` naming a record that is not there, mean `data_check_failed`
       for the day, alerted. (Partly accepted: an outcome naming the candidate's seal under another driver or road
       is not a fault. One sealed decisions file holds every driver's decisions on every road of the session, so
       other drivers' outcomes rightly carry the same `decision_sha256`; the match is on all three: seal, driver,
       road.)
     - A candidate that did not trade contributes zero, shown as "no trade".
     - A desk candidate that traded: the desk's outcome reader is not built, as with REC1b's desk evidence. That
       candidate makes the check `data_check_failed` with that reason. It cannot occur before a desk version reaches
       `paper`.
4. **What it writes.** `recommend/<YYYY>/<MM>/<day>.check.json`, written once with its receipt pushed, with:
   - per listed candidate: its key, `closed` / `open` / `no trade` / `ticket`, and its `net` when closed;
   - `closed so far`, the sum over the closed trades, with the counts of the open ones (judge 658 m1). Until the day is
     final it is not the day's total, and it appears in no line;
   - the day's verdict: `not known yet` while any listed candidate is open, even when a source was unavailable;
     `complete` when all have closed; `incomplete: <source> unavailable` when all listed candidates have closed but a
     source was unavailable at decision time (final, written once, not re-checked; judge 658 S3); `data_check_failed`
     when a listed candidate is still open at the 60th session's check ("never closed in 60 sessions"), final and
     alerted (judge 658 S3), or when an outcome cannot be resolved to one live record;
   - for a `NO_TRADE` day, "abstaining saved Rs X" or "abstaining cost Rs X" once complete.
   A check of a day already checked as complete is never written again. A day still `not known yet` is checked again
   on later evenings: each check is its own write-once file, `<day>.check.<check day>.json`, so no file is ever
   rewritten.
   - Which sessions it checks: every session with a recommendation record whose latest check is not final
     (`complete`, `incomplete`, `data_check_failed`), from the last 60 sessions. A monthly option closes within about
     35 days; the 60th session's check is the last and is always final.
5. **Where it shows.**
   - One #fno-desk line per newly completed day, "Recommender check for <day>: ...".
   - The 08:50 "Today" section shows the latest checks (REC1d). The 20:05 edition cannot show tonight's check,
     because the check runs after it; this is stated, not hidden.
6. **Criteria for REC1c.** Criterion 12 as passed (trade, no trade, a candidate not closed, a missing record, each
   candidate plus the total, never editing the recommendation, the dropped-loser plant), plus:
   - (a) the brake test;
   - (b) a school ticket never counted as a trade;
   - (c) a source unavailable at decision time gives `incomplete`, never a total;
   - (d) a check error never touches the edition's receipts (the command's own commit only);
   - (e) the CLAUDE.md step text.

### REC1c Claims (text round 2 for judge 658, and the code; branch `story/rec1c-evening-check`)

**Judge 658 (text round 1).** Every point was checked against the code.
- **S1 accepted.** The check is step 3b, after step 3's push, committing only its own receipts; step 4 covers its
  alert. It is in CLAUDE.md on this branch.
- **S2 accepted in part.** Corrections are resolved to one live outcome per candidate (`outcomes._live`, reusing the
  school's `record_sha256`).
  - None live means open.
  - Two or more live records, or a `corrects` naming a record that is not on file, means `data_check_failed`, alerted.
  - **Not accepted:** "an outcome naming the candidate's seal under another driver or road is a fault". One sealed
    decisions file holds every driver's decisions on every road of the session (`fno/school/dashcam/store.py`, one
    file per session and slot), so other drivers' outcomes rightly carry the same `decision_sha256`. The match is on
    all three: seal, driver, road. The tests show another driver's or road's outcome never matches.
- **S3 accepted.**
  - The 60th session's check is the last. A candidate still open then gives final `data_check_failed` ("never closed
    in 60 sessions"), with a line.
  - A day unreadable at its last check is written final too, so no day leaves the window silently.
  - `incomplete` is final only once its listed candidates have closed; until then the day is `not known yet`.
- **m1 accepted.** `closed so far` (the `closed_so_far` field) appears in no line until the day is final.
- **m2 accepted.** LR1's and REC1d's readers name a missing or `data_check_failed` check and post their edition all
  the same. This is their parts' criterion.

**Self-review (quality rule 3).** An independent agent reviewed 7b177c12. Its findings 2, 3 and 7 were already fixed
by the round-2 work above. The rest are fixed at ca2e8358:
- **1 (blocking):** the real Drive reader raises `StaleSeal`, and the run did not catch it, so one bad file stopped
  every day without an alert. Every read is now wrapped, and each day, including its "is it final" read, has its own
  guard. A damaged check file is that day's problem.
- **4:** an open school ticket (untraded, no outcome yet) read as "no trade", and the day went final without it. It
  now keeps the day open, known from its own sealed decision (`SealedOutcomes.ticket`), so it is reported once it
  closes. "Open" now counts open positions, trades and tickets.
- **5:** an untraded decision with a trade's sealed outcome is a disagreement, so the check fails.
- **6:** `recommend check` writes nothing on a day that is not a trading session (criterion 14).
- **8:** `braked_versions` holds only established versions (`decide`, and the contract refuses others). The line
  says "no established version is eligible; under their own brake: ...".

**Plants: 32, all caught.**
- 3 for the brake, 13 for the check, 6 for round 2 (J's "a correction counted twice" among them), 7 for the
  self-review fixes, and 3 more that each first survived and then got the test that catches it.
- A comment-only control survived. All plants ran with `PYTHONDONTWRITEBYTECODE=1`.

**Tests:** 331 in `tests/recommend`.

**What the check cannot do yet, stated plainly:**
- A traded desk candidate fails loudly: the desk's outcome reader is not built, and none can occur before a desk
  version reaches `paper`.
- The 20:05 edition never shows the same day's check, because the check runs after it.
- REC1d (the 08:50 section) and REC1e (LR1) read these files; they are not built here.

### REC1c Claims, code round 2 (judge 658.1 J: 1 should-fix and 1 minor; judge 660 K: the same should-fix and 1 minor; all accepted)

- **S1 (J and K):** a missed evening on the 60th session dropped a day silently.
  - `_recorded_days` now reads every receipted recommendation up to the check day, however old, not a calendar
    window. A day 60 or more sessions old gets `last=True`, so its next evening's check is final: `data_check_failed`,
    "never closed in 60 sessions", alerted.
  - J's plant "the last evening missed" is `test_the_last_evening_missed_still_ends_the_day_final`.
- **J m1:** records that disagree are written final at once, with one alert: two live outcomes, an orphan correction,
  an untraded decision with an outcome. They raise `DataDisagrees`, a subclass of `InputFailed`. Read errors are still
  retried and are final only at the last check. Tests: `test_records_that_disagree_are_written_final_at_once` and
  `test_a_read_error_is_retried_not_written_final`.
- **K m1:** a catch-up with `--on <past day>` counts only the check files made on or before that day (`_checked_on`
  from the file name). Test: `test_a_catch_up_for_a_past_day_sees_only_the_checks_made_by_then`.
- `_recorded`, now unused, is removed (no dead code).
- **Plants this round: 4, all caught:** windowed days ("the last evening missed"), a disagreement retried, a read error
  written final, later checks counted. Tests: 335 in `tests/recommend`.
- **Known cost:** each evening reads the latest check of every receipted day. It is cheap through the verified Drive
  cache, and grows by one small read per session.

### REC1d text amendment (round 2: judges 663 J and 664 K; placement agreed 25 Oct by the orchestrator for MS-P1g's builder, who is out of reach, and for FL1's owner on the reserved call; conditions from MS-P1j's builder, current owner of `fno/school/reports/`)

What section 3's "08:50 and 20:05" bullet and REC1c item 5 become exact as, each named:

1. **Placement: a wrapper of its own, outside the school's (J's S1 and K's SF1, accepted).**
   - Round 1 put the recommender's block inside `build_school_maker`. That function returns the plain maker when
     `school.reports` is false (`fno/school/reports/wiring.py`), so the block would have vanished with the school's
     switch.
   - The fix: the recommender wraps the lab's maker itself. `fno/recommend/report_guard.py` has
     `with_recommend_section(maker, config)`, and `fno/recommend/report_section.py` has its two sections.
   - `fno/forecast_lab/page_wiring.py` changes only its reserved call, to wrap the school's wrapper:
     `with_recommend_section(with_school_sections(...))`. This is the orchestrator's yes, for FL1's owner.
   - `report_guard.py` imports nothing of the recommender at load time, as `guard.py` does. A failure to set it up
     gives the plain edition plus one alert naming the exception class.
   - `fno/school/reports/` is not changed at all. MS-P1j's builder reviews the reserved line before the judges.
2. **Each section under its own switch.**
   - The recommender's section shows only from `daily.live_from.recommend`, and the school's only with `school.reports`.
     Neither key is read by the other's wrapper.
   - With the recommender's switch off, `with_recommend_section` returns the maker it was given, unchanged.
3. **Isolation.**
   - The two wrappers are separate. The recommender's section raising never stops the school's section or the edition:
     it gives one alert, "recommender <edition> section not made (<Class>); the edition was posted without it", with
     the exception class and never its message. The school's failure handling is unchanged.
   - Tests: a failing recommender section with the school's section still posted, and the reverse.
4. **Order and text.**
   - The school's sections render exactly as today, in the same place. The recommender's comes after them, because its
     wrapper is the outer one.
   - All of `tests/school/reports/` passes untouched.
5. **08:50, "Recommender, PAPER ONLY":**
   - The standing real-money answer and each rated version's rung, from the latest recommendation record before
     today, labelled "standing; today's answer at about 15:20" and naming that record's day.
   - **The checks of the previous NSE session only (K's SF2 and J's m1).** "Last evening" means the previous NSE
     session by the session calendar, never the previous calendar day.
     - Every check line names its check date, in the check's own words (`check_text`).
     - Only check files dated that previous session are shown. An older check is never shown, dated or not.
     - When recorded days are still not final and no check file is dated the previous session, the section says "the
       previous session's check did not run" and names the waiting days.
     - A `data_check_failed` check is named with its problem. Neither case ever fails the edition.
   - No record yet gives one line, "no recommendation recorded yet". A record that cannot be read is named as not
     read, by its path and the exception class only.
6. **20:05, "Recommender, PAPER ONLY":**
   - Today's two answers with their codes, in REC1b's line words, without the receipt part.
   - Then one fixed line: "tonight's check runs after this edition; it is on #fno-desk and in tomorrow's 08:50". No
     stale check is ever shown as today's (orchestrator, 25 Oct).
   - On a session with no record (the step did not run or did not post), it says "no recommendation recorded for
     <day>". It adds the run log's `recommend` status and reason code only, never the step's printed lines (K's m1).
   - That status is read through a port in the shape of MS-P1j4's `DayInputs.school_step`, never by opening the run
     log inside the section (MS-P1j's builder, 25 Oct).
7. **Words and their guard.**
   - The section names no strike, price, range or strategy internal. Its only amounts are the check's after-cost
     rupee totals, which REC1c already posts to #fno-desk.
   - Its own guard: every line is built only from `post.py`'s and `check_text.py`'s templates and this module's fixed
     lines. A test checks each line against those templates.
   - It is never routed through the school's LEAK or rupee checks, which would withhold it.
   - No line carries a record hash: the edition is not a record.
8. **Tests on an explicit config.** `config.yaml` has `school.reports: true`, so every new test passes its own config
   and never builds the real school inputs.
9. **Criteria for REC1d**, each with a plant:
   - (a) **All four switch pairs** (school off or on, recommender off or on), each with a golden file of both editions:
     - both off is byte-identical to the plain maker, with the real recommender wrapper in place;
     - school only is byte-identical to today's school golden;
     - recommender only shows the plain edition plus the recommender's block;
     - both show the school's sections, then the recommender's.
     Plants: the recommender gated by `school.reports`, and the recommender's block always added.
   - (b) A data_check_failed check is named, and the edition still posts. Plant: a raised reader error is swallowed
     silently.
   - (c) The morning never shows today's record as standing. Plant: `<=` in place of `<`.
   - (d) One failing wrapper never removes the other's section. Plant: the recommender's `try` around the inner maker.
   - (e) An empty history gives the "no recommendation recorded yet" line.
   - (f) Every line matches an allowed template. Plant: a candidate's decision path added to a line.
   - (g) Only the previous session's checks are shown, each with its date. Waiting days with no check dated the
     previous session give "the previous session's check did not run". Plant: an older check shown without its date.
   - (h) The 20:05 no-record line carries only the status and reason code. Plant: the step's printed line appended.

### REC1d Claims (code round 1, branch `story/rec1d-sections-code`; the SHA is in the commit that carries this text)

**Files.**
- New: `fno/recommend/report_guard.py` (the lab's one entry; imports nothing at load time),
  `report_maker.py` (the outer wrapper and its set-up failure maker), `report_section.py` (the two sections and their
  ports), `report_words.py` (the words and the problem guard), `report_wiring.py` (the switch, the ports, the run log's
  status and code), `shelf.py` (the receipts shelf, shared with REC1c's check run).
- Changed:
  - `fno/forecast_lab/page_wiring.py`: the reserved call, `with_recommend_section(with_school_sections(...))`.
  - `fno/recommend/check_run.py`: it uses the shelf. There is no change of behaviour, and REC1c's tests are unchanged
    and pass.
  - `fno/recommend/post.py`: two private functions made public, `real_money_text` and `paper_text`, so the sections
    use REC1b's own words (DRY).
  - `fno/recommend/constants.py`: `RECOMMEND_STEP`.
- Tests: `tests/recommend/test_report_section.py`, `test_report_maker.py`, `test_report_words.py`,
  `test_report_wiring.py`, `report_fakes.py`, and eight golden files in `tests/recommend/golden/`.

**Deviations from the text, each stated.**
1. Item 4 said `tests/school/reports/` passes untouched. One line was added to
   `test_the_real_report_maker_is_built_through_the_school_guard`. That test pins `build_report_maker`'s return as
   the school wrapper's own. With the outer wrapper this is no longer true, and on the real config it would build
   the real ports.
   - The line stubs `with_recommend_section` as identity, so the test still pins the school guard exactly.
   - My own test `test_the_lab_wraps_the_school_s_maker_in_the_recommender_s` pins the outer order.
   - Asked of MS-P1j's builder with this SHA.
2. An added line, `NOT_KNOWN`: "<n> position(s) still open, so the day is not known yet."
   - REC1c's `answer_text` is written for final checks only. On a check that is not final, it would have said
     "No candidate traded, so abstaining cost nothing", which is wrong.
   - The morning shows `not_known_yet` checks dated the previous session, so they need their own words: the open
     count, never a total.
   - Found in self-review; test `test_a_day_not_known_yet_gives_its_open_count_never_an_answer_or_a_total`.
3. The run log's status and reason are shown only when they read as O1's words and codes (`[a-z_]+` and
   `<step>:<CODE>`). Otherwise they read "unknown". Logs before 22 Oct hold free-text reasons, so this carries
   judge 664 m1's "code only" into the port itself.

**Criteria and their plants.** Each plant was run with bytecode off and `__pycache__` removed. Every one fails a test
in `tests/recommend` or `tests/school/reports`, and a comment-only control plant passes.

| Criterion | Plant |
|---|---|
| (a) | gated by `school.reports`; block always added; live date ignored |
| (b) | a reader error returns nothing |
| (c) | `<=` for the standing record |
| (d) | a failure drops the inner sections; the exception message put in the alert |
| (e) | an empty history returns nothing |
| (f) | a decision path appended to a line; a check problem shown unguarded |
| (g) | an older check shown; the check line undated; waiting days not named |
| (h) | the run log's free text shown |
| self-review | a not-final check given an answer |
| wiring | the lab's maker not wrapped |

**Real output sample.** No real recommendation record exists yet: Mon 26 Oct is the first. Run on main's real wiring
on Sun 25 Oct, the morning section would say "No recommendation recorded yet."
- The golden files `tests/recommend/golden/*_recommender_on.txt` are the sections over test records. Each one was
  read line by line.
- A real sample follows as soon as 26 Oct's record exists: the 27 Oct 08:50 edition.

**Gates.** The full suite passed: 17505, 1 skipped, 13 xfailed. `ruff check`, `ruff format --check` and
`check_imports` are clean. Every new file is under 350 lines; the largest is `report_section.py`.

**Known limits.**
- The 08:50 section reads every waiting day's latest check, about 60 small files at most.
- Not verified in a rehearsal (REH1). The sections read Drive through `build_drive_cache`, as REC1c's check does.
  Whether a rehearsal points that cache at its `dryrun/` records is not checked here.
