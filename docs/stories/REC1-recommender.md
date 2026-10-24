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

Made by `python -m fno recommend decide` as the daily-run step `recommend`, after `quotes_done` and before `card`
(about 15:20 IST). A muhurat-only session gets none (as T1). Each recommendation holds two separate answers:

- **Real money.** `DO_NOT_TRADE_REAL_MONEY` unless at least one version is eligible under RM1 (section 4) on that day;
  then `ELIGIBLE_FOR_YOUR_OWN_REVIEW`, naming the version and pointing to its RM1 report. There is no "buy" value: the
  enum has exactly these two members (a test proves no input reaches a third).
- **Paper.** What the system itself books on paper today and why:
  - `PAPER_TRADE`: a version at evidence rung 1 or higher (section 2) took a trade through the desk or the school; the
    record names the version, structure, worst loss after C1 costs, exit plan, and the source decision record by
    path and SHA-256. The recommender never makes a trade itself: it only reads decisions already made and sealed.
  - `NO_TRADE`: with one reason code from a closed set, first match wins: `data_check_failed` (an input unreadable,
    missing or its hash wrong), `step_problems` (O1's problem steps, as T1e), `quote_gate_failed` (the day's capture
    or road gate failed), `weather_red` (M1's recorded colour red), `risk_cap` (C2/C4 or a school safety law refused),
    `brake` (a drawdown brake or daily stop holds), `no_proven_version` (no version above rung 0), `no_candidate`
    (versions above rung 0, none of them traded today).
  - **Measurement trades** of rung-0 versions (school drivers and controls, desk versions at `research` or `shadow`)
    are listed apart as "measurement, not a recommendation" with their count only (assumption A2).

### 2. Confidence is an evidence rung, a stated rule, never a free number

Per version, from frozen forward records only (S1's order rule: the decision's commit has the freeze record as a
strict ancestor; R1's data spend). Backtests, the simulator, rehearsals and uncounted days never count (planted
test each).

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

- **#fno-desk card:** a new `RecommendationStatus(StatusSource)` replaces `RegistryStatus` inside `RuledStatus`
  (one line in `fno/cards/wiring.py`); T2's rule checks and T1e's warning stay above it, unchanged. Line 1 stays
  "PAPER ONLY ..."; the status lines become "Real money: DO NOT TRADE (no proven edge)" and "Paper: NO TRADE
  (no_proven_version)" or the trade, then the rung line.
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
- **Evening check:** `python -m fno recommend check` in the evening routine after `lab close` writes
  `recommend/<YYYY>/<MM>/<day>.check.json` once: for `PAPER_TRADE`, the result after C1 costs (from desk marks or the
  school dashcam, never a new price); for `NO_TRADE`, what the day's candidates and the matched controls made
  (school tickets' three counts) as "abstaining saved Rs X" or "abstaining cost Rs X", "not known yet" until their
  exits close. A check never edits the recommendation.
- **Weekly:** LR1's post-mortem gains one section: answers by reason code, abstention net, rung changes, and the
  calibration line under section 2's threshold.

### 6. Honesty guarantees (each a criterion with a planted failure)

- No proven version means real money `DO_NOT_TRADE_REAL_MONEY` and paper `NO_TRADE` or measurement only.
- A missing, unreadable or hash-mismatched input is `data_check_failed`, never a pass and never skipped.
- No recommendation is posted without its receipt pushed; a failed push posts the problem line instead.
- The recommender never writes a decision, a fill or a price; it reads sealed records only.

## Parts, files and dates (dates are scenarios, reasoning only)

| Part | What | Main files (new unless said) | Target |
|---|---|---|---|
| REC1a | contracts (`Recommendation`, two answer enums, reason codes, `EvidenceRung`), the rung rule, its R1 card and D6 row, the record codec, dashboard contract fields | `fno/recommend/contracts.py`, `rungs.py`, `codec.py`, `research/recommend/CARD_REC1.md`, `fno/constants.py` names | 27-28 Oct |
| REC1b | `recommend decide`, the daily step, Drive store + receipt, card `RecommendationStatus` | `fno/recommend/decide.py`, `inputs.py`, `store.py`, `wiring.py`, `cli.py`; `fno/constants_operations.py` (one row), `fno/daily/wiring.py`, `fno/cards/wiring.py` (one line each) | 28-30 Oct |
| REC1c | `recommend check` and the evening routine step | `fno/recommend/check.py`, CLAUDE.md evening step | 2-5 Nov |
| REC1d | morning and evening sections read the record | `fno/school/reports/` adapter (MS-P1g owner agreed) | 5-9 Nov |
| REC1e | LR1 weekly section | `fno/learning/recommend_section.py` (LR1 owner agreed) | 9-11 Nov |
| RM1x | RM1 covers driver versions (only after the owner's yes to A3) | `research/evaluation/REAL_MONEY_GATE.md` | after A3 |

**Release 1 (orchestrator, 25 Oct: every day it runs is a day of recorded, checkable verdicts): REC1a and REC1b are
judged and go live first**, target the week of 26 Oct (merge about Fri 30 Oct, first live session Mon 2 Nov at the
latest; a judge round or a REC1a card freeze that slips moves it, it is not shortened). REC1a's R1 card is frozen
before REC1b's first live day. Release 2 (REC1c-e) follows, about 9-13 Nov; until it, the record holds each day's
verdict and the evening check is built later from the same records, so no day is lost. `daily.live_from.recommend`
stays null until the owner's go. Each part is one judge (none fills or exits); the orchestrator names a second
judge if it judges otherwise. No merge 14:00-16:15 IST on a session day.

## Acceptance (each with good, bad, boundary and empty cases and a planted failure the tests catch)

1. **Two answers, closed sets.** The real-money enum has exactly two members and the paper answer one of `PAPER_TRADE`
   or `NO_TRADE` with exactly one code from section 1's set. Plant: a third member or an unknown code fails a test.
2. **Reason order.** With several conditions true, the first in section 1's order wins (one test per adjacent pair).
3. **Rungs.** 0 / 1 / 29 / 30 valid sessions give rungs 0 / 1 / 1 / 2 (2 only with P2's review recorded); rung 3 only
   with all three of its conditions (each removed in turn gives 2). Backtest, simulator, rehearsal and pre-freeze
   records count 0 (one planted record each). Empty history: rung 0.
4. **Day conditions only lower.** Each of the three conditions lowers by one, never below 0; none raises.
5. **Real money.** No RM1-eligible version gives `DO_NOT_TRADE_REAL_MONEY` (today's registry and an empty registry);
   an eligible one gives `ELIGIBLE_FOR_YOUR_OWN_REVIEW` naming it; RM1 unreadable gives `DO_NOT_TRADE_REAL_MONEY` with
   `data_check_failed`.
6. **Reads only sealed records.** A trade answer cites its source decision by path and SHA-256; a changed byte in the
   source gives `data_check_failed`. The recommender module imports no fill, order or desk-writing code (an import
   test).
7. **Write-once and receipt first.** Same day twice: same bytes, no-op; different bytes refused and alerted; a failed
   receipt push means no Slack post and one problem line to #fno-desk.
8. **Card.** With today's main data the card reads "Real money: DO NOT TRADE (no proven edge)" and "Paper: NO TRADE
   (no_proven_version)"; T2 and T1e lines unchanged (golden files); a missing record gives `data_check_failed`.
9. **Evening check.** Trade, no-trade, exits not closed ("not known yet") and missing record cases; it never edits the
   recommendation (hash unchanged) and never reads a price not already recorded.
10. **Calibration line.** 99 outcomes or 59 sessions print "not enough outcomes to calibrate"; 100 over 60 print 5 bins.
11. **Clock and day.** A holiday or muhurat-only day writes nothing; a rehearsal writes under Drive `dryrun/` only (REH1).
12. **Real output sample** in Claims from a dry run on a recorded day (status and reason only, no strikes).

## Gap list (each requirement of the design: a criterion, or out with its reason)

| Requirement | Where |
|---|---|
| daily decision paper/no trade with reason | 1, 2 |
| confidence from a stated rule | 3, 4, 10 |
| "do not trade" alert when not sure | 5, 8 |
| every decision recorded write-once | 7 |
| checked every evening, no-trade included | 9 |
| learning through scheduled reviews | REC1e (LR1 section); rule changes stay new versions (R3), never daily |
| never invents an edge | 3 (plants), 6 |
| books 2 and 3 as recommenders | out: their trading job (F5, F6, F1t) is not built (DESK_DECISIONS 25 Oct (1)); they plug in as more versions with rungs, no change here |
| real orders | out: hard line |
| dashboard screen | out: UI pause; contract fields only |
| futures and stock options | out: not in the pilot (327 P3+) |

## Questions for the owner (each with the recommended answer; the text assumes it)

- **A1. Answered** (owner, 25 Oct: build fully now): switched on as soon as judged; the 30-session review is what
  first moves a rung.
- **A2.** Keep booking measurement paper trades of unproven versions, labelled "measurement, not a recommendation",
  while the recommendation says `NO TRADE`. Recommended: yes; without them no evidence ever accrues. (The owner's 22
  Oct words "will not place a paper trade" read literally would stop the school.)
- **A3.** Extend RM1 unchanged to school driver versions. Recommended: yes, else nothing the school learns can ever
  become eligible.
- **A4.** Keep 327's thresholds exactly (30 sessions; 100 outcomes over 60 sessions; one-sided 95% after adjustment;
  a second window). Recommended: yes, frozen before the first counted day.

What the owner will see, plainly: every session for months, "Real money: DO NOT TRADE (no proven edge)". Rung 2 is
possible from about mid-January 2027 if the pilot starts counting in late November; rung 3 needs a second untouched
window, realistically mid-2027 or never. That is the measurement, not a fault.

## Claims

None yet (text round 1).
