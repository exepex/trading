# Epic T: the daily trade card (layer 6)

Roles: risk manager (owner), F&O trader, statistician, behavioural finance. Goal: one short, honest message every NSE
session that the owner can read on a phone: what the desk decided, why, how sure the forecasts are, and what is missing,
built only from committed records (design v2 `04_layers_card_monitor_learning.md` sections 4.1 and 4.4, `06_risk_and_alerts.md`
section 6.5, `REPLAN_new_stories.md` T1). Story template and definition of done: `docs/IMPLEMENTATION_PLAN.md`.

---

## T1. Daily trade card v1 (`NO TRADE` and forecasts)

**Repository:** trading

**Description:** As the owner, I want one card in Slack #fno-desk every NSE session with a 15:00 market that says
PAPER ONLY, gives the
desk's status (v1: always `NO TRADE`, with its reason), the market weather, the forecasts on record with their track
records, and the SHA-256 of every record it used, so that I see each day what the desk knows and how sure it is, and so
that every forecast the card shows has an issuance time no one can back-date.

**Context and why:** The design replaces the old P4 publishing story with a daily card (REPLAN T1, slice A). Nothing has
passed yet: the playbook registry holds no version at `paper` and the three paper accounts hold zero trades, so the
honest card is `NO TRADE`. The card's second job is evidence: design 04 section 4.4 makes the card's Slack post the
issuance time of every forecast it shows (committer time is never evidence; GitHub's push receipt is the second
witness). The owner decided on 15 Oct 2026 that card records are kept in Google Drive only (`docs/DESK_DECISIONS.md`).

**Scope.** In:
- `python -m fno card daily [--on YYYY-MM-DD] [--post]`: builds the card for a session and prints it. Without `--post`
  it is a dry run: nothing is posted, saved or written. With `--post` it posts to #fno-desk, saves the card record to
  Drive and writes the delivery metadata to the repository.
- `--post --test`: the one live delivery check (criterion 16), marked TEST on its first line and in its records.
- `python -m fno card witness --on YYYY-MM-DD`: prints both issuance witnesses of that day's cards (Slack's server
  timestamp from the delivery metadata, GitHub's push receipt of the commit that added it).
- Status: `NO TRADE` with a reason code; v1 never shows a trade. Reason codes: `no_approved_strategy` (no version at
  `paper`), `trade_fields_not_built` (a version is at `paper` but card v1 cannot show trade fields: T1 slice B; the
  owner is pointed to the desk's records), `data_check_failed` (the registry or an account could not be read).
- Weather: M1 is not built and no production code for response 94's v0 rule exists (it lives only in the research
  study `research/2026-10-14-weekly-weather/`), so the card says "Weather: not yet scored (M1 pending)". Never a colour.
- Forecasts: the latest committed live G1 capture (`research/forecasts/live_v2/<YYYY>/<d>_forecasts.csv`, on or before
  the card's day) and, for each question, the house forecast with its record from the latest committed G4 score report
  (`research/forecasts/scores/<d>.json`): the calibration bin that holds today's probability ("said 0.5-0.6 on 551
  days, happened on 62%") and its mean Brier score, labelled as back-fill history, not live; the live record is "not
  enough data yet" until G4 scores live days (V1 needs the unbuilt A16 recorder). The house forecast is the past average (`baseline_b_base_rate`) on all five questions, labelled as the fallback (orchestrator, 15 Oct 2026): G1 v1-v3 name no primary yardstick for any question; the base rate is the only baseline defined on all five and uses no model or market input; it matches REPLAN's "baselines until something passes" and the owner's signed-off Forecast lab mockup (37), whose main yardstick is "Past average". It was never chosen by its scores. It is a display choice only and changes no scoring. When protocol v4 merges, its own primary baselines (design 05 section 5.3) replace this for the V questions.
  One line counts the other forecasters ("N other forecasters recorded; none has passed its test yet"); their full
  list belongs on the dashboard, not the card.
- Footer: path and SHA-256 of every record used; issuance-time line; valid-until time.
- The owner-unavailable line: "If you cannot act by 15:25 IST, the paper record assumes: no action (nothing is opened or
  closed)." E8's availability calendar is not built; the line says so.
- Missing input: the card still goes out and names what is missing.
- The previous delivery's failures (Slack not sent, Drive not saved) are named on the next card.
- Clock contract: every stored time is UTC with its offset; the card shows IST; the host clock is checked against
  Slack's server timestamp of the post and GitHub's server `Date`; a skew above 5 seconds is a WARNING.

Out: scheduling (the owner decides later); `TRADE` and `WATCH` fields (slice B); the devil's advocate (T2, T3); the
house-forecast rule (design 07 section 7.4, frozen separately); weather scoring (M1); protocol v4 forecasters (G6, not
merged: they plug in as a new `ForecastSource`); the dashboard renderer.

**Design note (judge 101, owner "3 A", 15 Oct 2026):** design 04's "a card exists every trading day" is read as "a
card every session with a 15:00 market": regular and special sessions. A muhurat-only session (the one-hour Diwali
session; 21 Oct 2025 ran 13:45-14:45) has no 15:00 market and no forecast capture (`fno/forecast/capture.py` skips it),
so it gets no card, as in A4.

**Design:**
- Package `fno/cards/`, composition root `fno/cards/wiring.py` (design 04 section 4.1 names `fno/cards/wiring.py`).
- `CommittedRecords` (interface; `GitHeadRecords` reads `git show HEAD:<path>` bytes): the card reads only committed
  records, so an edited or untracked file is never on a card.
- Sections, each behind an interface: `StatusSource` (`RegistryStatus`), `WeatherSource` (`PendingWeather`),
  `ForecastSource` (`LiveCaptureForecasts`). Each returns a `CardSection` (lines, records used, missing). `CardBuilder`
  calls each; a source that raises becomes a named missing item, never a lost card.
- `CardRenderer` (`SlackTextRenderer`): plain text, PAPER ONLY on the first line.
- `CardPoster` (`SlackCardPoster`, `NoCardPoster`): returns Slack's `ts` (its server timestamp) or the failure; one
  retry. The HTTP post is shared with the existing `SlackChannelAlerts` (one function, `slack_post`).
- `CardRecordStore` (`DriveCardRecords`, `NoCardRecords`): the full card record (text, sections, hashes, Slack receipt)
  goes to Drive's `cards` area, written once (`RawFileStore` rules: the same bytes again change nothing, different
  bytes are refused).
- `DeliveryLog`: non-sensitive delivery metadata in `research/cards/deliveries/<YYYY>/<d>-a<n>.json` (status, reason
  code, card SHA-256, record hashes, Slack `ts` and outcome, Drive outcome, host clock, skew checks). Never the card
  text, never a strike or entry range. One file per attempt; existing files are never rewritten.
- `ServerClock` (`HttpDateClock` for GitHub) and `skew_check`.
- `IssuanceWitness`: Slack `ts` plus GitHub's push receipt (`fno/ai/receipts.py`'s `PushReceipts`, reused).

**Acceptance criteria:**
1. Every card's first line says PAPER ONLY; no card text tells the owner to place an order.
2. Status is `NO TRADE` with a reason code and a plain reason; with an empty registry the reason is
   `no_approved_strategy` and the card states the paper trade count (0); with a version at `paper` the card is still
   `NO TRADE` (`trade_fields_not_built`); an unreadable registry or paper account gives `data_check_failed`. No trade is ever invented.
3. Weather: "Weather: not yet scored (M1 pending)", followed by "No new trades while the weather reading is missing
   (owner rule)." (owner "4 A", 15 Oct 2026), and no colour word (GREEN, AMBER, RED) anywhere on a v1 card.
4. Forecasts: for each question of the latest committed live capture on or before the day, only the house forecast
   (past average, labelled as the fallback), plus one line counting the other forecasters, each line with its
   back-fill record (calibration bin, count, observed share, Brier) labelled "back-fill, not live", and "live: not enough
   data yet" until live days are scored; the bin is G4's own (`calibration_bin`); the score report used is the latest
   dated before the card's day (point in time: a same-day report may hold that day's later data); a question with no
   past-average record, an unreadable report and a late capture are each named missing; no forecasts on record gives "forecasts: none on record yet"; a
   capture older than the day is labelled with its date.
5. Built only from committed records: an uncommitted or edited working-tree file is never read (the reader reads
   `HEAD`); each record used is listed in the footer with its path and SHA-256, and the hash equals the committed bytes.
6. Section 4.4 issuance: the post's Slack server timestamp is the card's issuance time and is stored in the delivery
   metadata; `card witness` prints it beside GitHub's push receipt of the commit that added the metadata; committer
   time is never read.
7. Section 4.4 clock contract: stored times are UTC with offset (`+00:00`), shown in IST on the card; the host clock is
   checked against Slack and GitHub; a skew above 5 seconds (beyond the server clock's resolution) prints and stores a
   WARNING, and exactly 5 seconds does not. GitHub's time is trusted only from a 2xx or 3xx answer; any other answer,
   or one without a `Date`, is "clock NOT CHECKED" with its plain reason, stored as `checked: false`, and named on the
   next card.
8. Section 4.4 owner-unavailable line on every card, with E8's absence stated.
9. Card records go to Drive only: the Drive record holds the card text; the repository's delivery metadata holds no
   card text (a test checks the written repository file contains no line of the card's body).
10. The card always arrives: a failing or missing input (no capture, no score report, unreadable registry, a source that
    raises) still gives a card that names each missing item.
11. Slack down or no token: a post that surely did not reach Slack (connection failed, `ratelimited`,
    `service_unavailable`) is retried once; one that may have been posted (read timeout, unreadable answer) is never
    retried and says "Slack may still have posted it"; a Slack refusal (e.g. `channel_not_found`) is not retried.
    Then the CLI prints "alert NOT sent: <reason>", the Drive record and the delivery metadata are still written with
    the failure, and the next card names the miss. Drive down or not set:
    the card is still posted, "card record NOT saved to Drive: <reason>" is printed and stored, and the next card names
    it.
12. Dry run by default: without `--post` nothing is posted, saved or written, and no network call is made; `--post`
    is refused for any day but today (IST), so today's records are never issued as another day's card.
13. Secrets never in files or logs: the token is never printed, stored or put in a record; outputs name only the
    variable.
14. Non-session days (NSE calendar) and muhurat-only sessions (the one-hour Diwali session, as A4) print "not a trading day: no
    card" and do nothing; the previous-session check skips muhurat sessions; an unreadable earlier delivery record or
    a failed metadata write is named, never a lost card or lost result; a day the calendar cannot answer
    still gets a card that names the missing calendar.
15. Engineering rules: every source, store and sender behind an interface, wired only in `fno/cards/wiring.py` (listed
    in CLAUDE.md); no file or class over 350 lines; constants in `fno/constants.py` or at the top of their module.
16. Live delivery to #fno-desk verified once (orchestrator addendum, 15 Oct 2026; fakes cannot prove it):
    `python -m fno card daily --post --test` posts one card whose first line is "TEST — PAPER ONLY: a one-off check of
    live delivery, not the day's card.", marked `test: true` in the Drive record and the delivery metadata, and never
    counted as the session's card. `--test` without `--post` does nothing. Done only after the owner's yes, relayed
    by the orchestrator. Split by witness (orchestrator, 15 Oct 2026): (a) on the branch, the test delivery file is
    committed and pushed to the story branch and `card witness` shows Slack's `ts` (the judge checks it before the
    merge); (b) GitHub's push receipt is read only from pushes to `main`, so it is shown after the merge and the judge
    checks it in its merge check. The delivery file is never pushed to `main` by hand (it is not a scheduled job's
    output, so not lane 3). Until (a) is done this criterion is NOT MET; (b) is checked at the merge.

**Test plan:** fakes for Slack, Drive, the records and the clock. Positive: a full card from planted committed records
(empty registry, a capture, a score report). Negative: a registry with a `paper` version; an unreadable registry; a
source that raises; Slack `ok: false`, Slack raising, no token; Drive raising, Drive not set; a skew of 10 seconds.
Empty: no capture, no score report, no accounts. A real temporary git repository proves an edited working-tree file is
not read. A test checks the repository delivery file contains no card body line and no token. The CLI dry run on the
real repository prints a card.

**Judge verifies:** runs `python -m fno card daily` on the repository and checks each line against the committed
records and their hashes (`git show HEAD:<path> | sha256sum`); edits a capture file in the working tree and checks the
card does not change; plants a `paper` row; runs `--post` with a fake or no token and no Drive and checks the printed
failures and the delivery metadata; checks the delivery file for card text and secrets; checks no colour word appears.

**Depends:** D3, E2, G3, G4 (M1 for weather later) · **Size:** M · **Status:** done: judge 101 PASS (44fa45d,
merged f0c47ae; follow-ups 9d5310b and a84f92d, merged 860030c, addendum 5).

---

## T2 + T3. The devil's advocate on the daily card: rule checks (code) and objections (AI)

**Repository:** trading · **Issues:** #104 (T2), #105 (T3) · **REPLAN:** slice B · **Lane:** 1 (new story; Slack; a
routine) · **Revision 1** (judge 180: FAIL, 2 blocking and 3 should-fix, all accepted after checking the code)

**Description:** As the owner, I want every card to say plainly whether a registered rule stopped the trade, and on
every trade card to show up to three objections from an AI that tried to find what is wrong, so that I see each call
attacked before I read it, without that AI ever deciding anything.

**Context and why (design v2 `07_ai_team.md` 7.3, `04_...` 4.1; REPLAN T2, T3):**
- Design 7.3 has two parts: rule checks (code, can block) and objections (AI, cannot block).
- **Most of 7.3's rule checks already exist and already block, inside the desk** (strong: code read on `main`):
  - C4 (`fno/checks/validity_*.py`) refuses a proposed trade at the book's own decision (caps, margin room, maximum
    loss with charges, structure shape, the version's terms). Each failure is a row of
    `journal/<book>/validity_failures.csv`.
  - C3's data checks (`fno/checks/gate.py`) run at the desk's **execution snapshot**, the run log's `snapshot` step.
    No C3 check is recorded at decision time (checked: the decision run calls no data check; `DataGate` is used only
    by the desk's snapshot, fill and exit steps).
  - "No version at `paper`" is D1's registry, which T1's `RegistryStatus` already reads. Book 1 also commits its own
    `journal/book1_rules/decisions/<d>/no_approved_strategy.json`.
- Re-checking any of them in the card would be a second version of the rule (one builder per function). So **T2 checks
  nothing again**: it reads what those rules recorded and makes the card say the same thing, with the reason.
- **Those records become final at different times** (strong: `config.yaml` `desk.timetable`, `fno/desk/daily_run.py`):
  - today's books' decisions and C4 rows: at the run log's `decisions` step, after `decision_deadline` (15:12 now);
  - C3's execution check: at the `snapshot` step, `execution_snapshot` (15:15 now).
  - Design 4.1's card at about 15:08 is earlier than both, and G10 moves the times again. So T2 never assumes a time.
    It reads the times from the desk's own `Timetable` (`fno/desk/timetable.py`, from `config.yaml`; G10 changes them
    in one place). A record that is not final at the card's build time is shown as "not yet decided (final at
    HH:MM)", never as "no breach".
- **Real state today (strong):**
  - card v1 is always `NO TRADE`; no version is at `paper`; T1's trade fields (slice B) are not built;
  - the card is not yet posted daily: nothing runs T1 until O1 goes live (orchestrator, 15 Oct 2026).
  So T2 v1 sharpens the `NO TRADE` reason, and T3 has no trade card to object to until slice B's trade fields exist.

**Design 7.3's seven rule checks: where each one is (gap list, quality rule 2):**

| 7.3 check | Where it is enforced today | In this story |
|---|---|---|
| Cost wall at today's quotes | Nowhere: no code (judge 180's grep and mine) | Out: a new rule. It needs a definition (the version's registered net edge against today's costs) and becomes a C4 rule when a strategy needs it (owner, decision 2 A) |
| Bucket and account caps | C4 (`validity_caps`, `validity_limits`) | Reported: criterion 2 |
| Event inside the holding window | Nowhere as a block | Warning line only (owner, decision 2 A), with T1's trade fields: T2b, criterion 12. A block, if wanted, is a C4 rule |
| Stale data | C3, at the execution snapshot | Reported: criteria 3 and 4 |
| Physical settlement | Nowhere: no stock option is traded | Out: a C4 rule before the first stock-option strategy (design 6.3 already places it in C4) |
| Evidence label matching its rung | Nowhere: the card has no trade fields | With T1's trade fields: T2b, criterion 13, a card-side check (the card's label must equal the registry version's rung read through T1's `RegistryStatus`) |
| Variant of a failed idea | Nowhere: R1 is not built | Out: R1's registration check, not the card |

**Scope.** In:
- **T2 now: `RuleOutcome`, read from committed records only** (`fno/cards/rule_checks.py`), each with the time it is
  final from the desk's `Timetable`:
  - `DecisionOutcome` (final after `decision_deadline`): the run log's `decisions` step (`journal/runs/<d>.json`):
    which books were recorded on time, late or not committed; plus each book's `validity_failures.csv` rows dated `d`
    → `hard_rule_breach` naming C4's checks;
  - `ExecutionOutcome` (final after `execution_snapshot`): the run log's `snapshot` step; `valid: false` →
    `data_check_failed` naming C3's reason. A card built before then shows today's as "not yet decided (final at
    HH:MM)" and also shows the **last session's** execution outcome, which is final ("last session: no valid
    execution snapshot, no fills").
  - "No version at `paper`" stays T1's `RegistryStatus` reading, unchanged: T2 adds no registry reader.
  - No run log for the day: "not yet decided: the desk has not run today". A run log or failures file that cannot be
    read: `data_check_failed` naming the file.
  - The card's reason, in order: `data_check_failed` (unreadable record or execution failure), then
    `hard_rule_breach`, then T1's own reasons. The "Rule checks" line lists every outcome: "no breach" only when
    every record is final and none failed, otherwise "not complete" with each pending record and its time.
  - T2 decides nothing: C3, C4 and D1 already refused the trades in the desk. The card only reports their records.
- **T2b, with T1's trade fields (slice B; built with T3, not now):**
  - the "event in window" warning: A6's `research/data/events/events.csv` scheduled rows dated inside the trade's
    holding window (from the day after the card to the trade's exit: the version's time exit, else expiry, both from
    the trade fields). One warning line; never a block;
  - the evidence-label check: a `TRADE` card's rung label must equal the version's rung in the registry (through
    T1's `RegistryStatus`); a mismatch makes the card `WATCH` with the reason.
- **T3: objections through `fno/advocate` (LR1's port; no second AI caller):**
  - Subject: the card's **public** lines (status, reasons, weather, forecasts and their records, the footer's
    hashes), written as `research/cards/advocate/<YYYY>/<d>.md`. Never strikes, entry ranges or prices: card records
    are Drive only (owner, 15 Oct 2026).
  - One routine, `Omenix F&O: card devil's advocate (triggered)`, fired by the card job right after the 15:00 pack is
    frozen, through `RoutineTrigger`. Its pointer holds only the day and the subject's SHA-256. Its environment is the
    AI books' environment: no credentials, `sealed_same_day` (F1's isolation).
  - It writes `<d>_objections.md`, checked by `ObjectionCheck`. `ObjectionCheck` gains two settings, made constructor
    arguments (LR1 keeps 1 to 5): T3 allows 0 to 3 objections, where 0 is the line `no material objection`, and each
    objection must contain `Effect:` followed by the effect it predicts (7.3).
  - Shown in a card section headed "Devil's advocate objections (AI; never a veto)". Not received or not passing by
    the card's post time: `advocate_unavailable` with the reason; the card goes out with T2's rule checks only and no
    objection is invented (4.1 timing contract).
  - Recorded for later scoring: the objections file is committed, with GitHub's push receipt as its issuance witness
    (4.4), and an adjudication record `shown_only` (7.3). An objection whose push receipt is after
    `decision_finalized_at` is marked `late: not scored`.
  - F8: one self-timed usage record per run (`--role "card devil's advocate"`). BG1 `stop` means the routine is not
    fired: `advocate_unavailable: budget stop`. LR1's `SignalFile` moves to `fno/budget/` so both read it from one
    place.
- Owner's setup checklist `docs/stories/T3-owner-checklist.md` (one routine, two secrets
  `FNO_ROUTINE_CARD_ADVOCATE_TRIGGER_ID` and `_TOKEN`, one hand run).

Out (each with where it goes):
- **New blocking rules** (cost wall, event in the holding window, physical settlement, failed-idea variants): see the
  gap list. Each is a new rule for C4 (or R1 for variants), decided when a strategy needs it, never in the card.
- **Weather RED and `not scored` blocking entries** (owner "4 A"): the desk must enforce them before a version reaches
  paper (M1 left enforcement out). Until then the card shows the colour and does not claim a block it does not have.
- Counterfactual scoring of objections (paired shadows, 7.3) and F9's value test: they need trades (S3, F9).
- Objections on the post-mortem (LR1, done), on idea registration (R1) and on promotion proposals (D-epic).
- Scheduling the card: O1.

**Design:**
- `fno/cards/rule_checks.py`: `RuleSource`, `RuleOutcome` (outcome, reason, `final_at`), `DecisionOutcome`,
  `ExecutionOutcome` and `RuleChecks` (the fixed order, the "not yet decided" rule). The desk's `Timetable` is
  injected. It plugs into T1's existing `StatusSource` and `CardSection`; no new status logic.
- `fno/cards/advocate.py`: `CardAdvocateSubject` (writes the public lines file) and `CardAdvocateFirer` (pointer,
  budget, fire log). The objections come through `Advocate`: `RoutineFileAdvocate` with T3's `ObjectionCheck`
  settings.
- Wiring: only `fno/cards/wiring.py`. Every file under 350 lines.

**Acceptance criteria (T2 now: 1-8; T3 and T2b later: 9-14):**
1. Every outcome's final time comes from the desk's `Timetable` (`config.yaml`); no time is written in T2's code. A
   test changes the timetable and the "final at" times follow.
2. Built after `decision_deadline`: a `validity_failures.csv` row dated `d` gives `NO TRADE`, `hard_rule_breach`,
   naming C4's checks; rows of other days are ignored; a book recorded late or not committed is named.
3. Built after `execution_snapshot`: a `snapshot` step with `valid: false` gives `NO TRADE`, `data_check_failed`,
   naming C3's reason.
4. Built before a record is final (for example 15:08 with today's timetable): that outcome shows "not yet decided
   (final at HH:MM)", the line says "rule checks: not complete", and the last session's execution outcome is shown.
5. No run log for the day: "not yet decided: the desk has not run today", never "no breach".
6. "Rule checks: no breach" only when every record is final and none failed; an unreadable record gives
   `data_check_failed` naming the file.
7. T2 adds no registry reader and recomputes no rule: an AST test finds no import of `fno.checks` rule modules or
   `fno.playbook.registry` in `rule_checks.py` (the registry stays T1's `RegistryStatus`).
8. T2 never changes the desk: it writes nothing under `journal/`.
9. T3: the subject file holds only public lines (a planted strike in the private trade fields is absent).
10. T3: fired once per `TRADE` or `WATCH` card with only the pointer; BG1 `stop`, missing configuration or
    `FireFailed` give `advocate_unavailable: <reason>`, and the card still goes out.
11. T3: objections pass `ObjectionCheck` with T3's settings (0 to 3, `Effect:` required, numbers only as whole tokens
    of the subject, no links or mentions), or `advocate_unavailable: <first failed rule>`. They never change the status,
    a reason or a number. Each shown objection has an adjudication record `shown_only`; one pushed after
    `decision_finalized_at` is marked `late: not scored`. LR1's tests still pass with the settings in the constructor.
12. T2b: one event warning line per scheduled `events.csv` row inside the holding window; none outside it; it never
    changes the status.
13. T2b: a `TRADE` card whose rung label differs from the registry's version rung becomes `WATCH` with the reason.
14. T3 and T2b are built only after T1's trade fields and O1 (owner, decision 3 A).

**Test plan:** fakes for the run log, failures files, timetable, trigger, advocate, budget and Slack.
1. Timing: the same records built at 15:08, 15:13 and 15:16 with today's timetable, and at G10's times: each outcome is
   pending or final as criteria 2-4 say.
2. Positive: a C4 row; an execution failure; all final with no failure ("no breach").
3. Negative: another day's C4 row (ignored); an unreadable failures file; a late book.
4. Empty: no run log (criterion 5); no failures file (no breach for that book, once final).
5. AST and writes: criteria 7 and 8.
6. Later (T3, T2b): the cases of criteria 9-13.

**Known limits:**
- Until T1's trade fields exist and a version reaches `paper`, every card is `NO TRADE` and T3 has no trade card to
  object to (question 1).
- The card's post time is O1's to set. With today's timetable a card before 15:12 shows the books' decisions as "not
  yet decided"; posting after the decisions step (and after 15:15 for C3) shows them final. Recommendation for O1
  (reasoning only): post after `decision_deadline` plus the collection step.
- T3's window (pack to card) depends on that same post time; under G10's 14:32 pack it is ample (judge 180 note).
- Objections are checked for form and numbers, not for being right; scoring them needs trades.
- The subject is public lines only, so the objections cannot see the strikes (privacy rule). A private subject would
  be one new adapter behind `Advocate` (Drive), and only if the owner wants it.

**Owner's decisions (15 Oct 2026, `docs/DESK_DECISIONS.md` af2019c8: A, A, A).** The three questions as asked:
1. **When T3 runs:** (A) only on `TRADE` and `WATCH` cards, so no AI minutes on `NO TRADE` days (none today); (B)
   every card day. **Recommendation: A** (reasoning only: an objection to "no strategy has passed" teaches little and
   costs about 250 runs a year).
2. **New rules from 7.3** (event in the holding window, stock-option settlement, failed-idea variants): (A) each
   becomes its own C4 or R1 rule when a strategy that needs it is proposed; until then the card shows an "event in
   window" warning line only; (B) T2 blocks on them now. **Recommendation: A**: blocking in the card would be an
   unregistered filter (7.3's own argument), and a block must live where the desk enforces it.
3. **Build order:** (A) T2 now (small: sharper `NO TRADE` reasons on today's cards), and T3's code after T1's trade
   fields and O1; (B) both now. **Recommendation: A** (reasoning only: T3 built now would run against nothing).

**What the decisions mean for the build:**
- T2's two rule outcomes (decisions with C4, execution with C3) are built now.
- T3 runs only on `TRADE` and `WATCH` cards, and its code comes after T1's trade fields and O1.
- The "event in window" warning (decision 2) needs a trade's holding window, so it is T2b, built with T1's trade
  fields (scope and criterion 12).

**Depends:** T1, C3, C4, D1, E3 (run log and `Timetable`), A6 (events, for T2b), LR1 (`fno/advocate`), F1 (routine
pattern), F8, BG1 · **Size:** T2 S, T3 M ·
**Status:** text PASS (judge 180 add. 1); T2 code on `story/t2-t3-advocate`, with judge E; T3 and T2b wait for T1's
trade fields and O1; owner's decisions A, A, A recorded

## T1c. The card shows the market weather from M1's record

**Repository:** trading · **Found by:** the O11 replay (orchestrator, 16 Oct 2026) · **Lane:** 1 (the card decides
what the owner sees about a trade)

**Description:** As the owner, I want the daily card to show the market weather that M1 recorded for the day: its
colour, the chances behind it and how proven it is. A missing or unscored reading must keep saying that it blocks new
trades. Then the card no longer says "M1 pending" now that M1 exists.

**Context and why (strong evidence: code on `main` read on 16 Oct 2026):**
- M1 is merged.
  - `fno/weather/records.py` `WeatherRecords` writes one record a day: `research/forecasts/v4/weather/<YYYY>/<d>.json`.
  - Each record holds `colour`, `status`, `label`, `operative`, `proof`, `probabilities`, `v0_colour`, `day` and
    `drivers`. The private US flag is kept out of it.
  - M1's text leaves showing it on the card to "a follow-up T1 change, after M1 merges" (`docs/stories/M-weather.md`,
    Out).
- The card still uses `PendingWeather` (`fno/cards/weather.py`, wired in `fno/cards/wiring.py`). That class always
  prints "Weather: not yet scored (M1 pending)", even on a day with a scored record. No story wires M1 into the card.
- Today's committed records are back-fills (`label: backfill_exploratory`, up to 14 Oct). Live records start when
  `weather capture` runs daily, which is O1's and v4's freeze's job. So T1c must also show an honest line on a day with
  no record.

**Scope.** In:
- A new `WeatherSource` adapter, `RecordedWeather`, in `fno/cards/recorded_weather.py`. It reads the day's weather
  record through the card's `CommittedRecords`: the committed bytes, the same as every other section, so the record
  goes into the card's SHA-256 footer (`UsedRecord`). It takes the record's path from M1's `WeatherRecords.path`, so
  the path has one source.
- Wiring: one line in `fno/cards/wiring.py`, `RecordedWeather` in place of `PendingWeather`. `PendingWeather` is then
  dead code and is removed.

Out:
- **Blocking a trade on RED or a missing reading at the desk's entry gate:** a story of its own (M1's Out names it).
  The card only says it.
- **The card's status reading the weather:** today the status is always `NO TRADE` (no version at `paper`), so a
  `TRADE` card beside a RED line cannot happen. That is T1 slice B, with the trade fields.
- **M1's record format and its writer:** M1's; T1c only reads them.
- **Intraday colours:** LM1 and M1's intraday rule.

**Design:** the card's lines, by the day's record (constants at the top of the module):
1. **No record, an unreadable file, or a record whose `day` is not the card's day:**
   - "Weather: no reading for <d>";
   - "No new trades while the weather reading is missing (owner rule).";
   - missing: "weather record for <d>".
   A record that is not `live` gives "Weather: no live reading for <d> (the record is <label>, not today's weather)",
   the same "no new trades" line and missing "live weather record for <d>" (criterion 5).
2. **`colour` "not scored", or `status` other than "scored":** (M1 writes `status` as "scored" or
   "not scored: <what is missing>", `fno/weather/day.py`)
   - "Weather: not scored for <d> (<what is missing>)";
   - the same "no new trades" line;
   - missing: "weather not scored for <d>".
3. **GREEN, AMBER or RED:**
   - "Weather: <colour> (<operative>, <proof>)";
   - "Chance of a 2% NIFTY move: next session <p> (base rate <b>); within 5 sessions <p5> (base rate <b5>)", using the
     operative forecaster's probabilities and the base rate, with one decimal (self-review: on 23 Oct whole percents
     showed 2.9% and 2.7% both as "3%");
   - "Checklist v0: <v0_colour>", or "Checklist v0: not scored (<v0_status's reason>)" when v0 itself is unscored;
   - for RED only, "RED: no new entries (owner rule)".
   - The record is added to the card's used records with its committed SHA-256.

The adapter never shows a driver (this keeps the private US flag out) and never computes a colour. The "not scored"
string is M1's `WeatherColour.NOT_SCORED`, imported from `fno/weather/constants.py`, never copied.

**Acceptance criteria:**
1. On a day with a committed scored record, the card shows the record's colour, operative forecaster, proof, chances,
   base rates and v0 colour, and lists the record with its SHA-256 among the used records.
2. On a day with no record, an unreadable record, or a record for another day, the card says "no reading" and the
   "no new trades" line, and names the record as missing. It never shows a colour.
3. A "not scored" record gives the not-scored line and the "no new trades" line, with no colour.
4. RED adds "RED: no new entries (owner rule)". GREEN and AMBER do not.
5. Only a `live` record is the day's weather. A back-fill (any other label) shows "Weather: no live reading for <d>
   (the record is <label>, not today's weather)" and the "no new trades" line, never a colour (M1's builder, 23 Oct
   2026: a back-fill is history, never today's reading; amended after judge 401).
6. No driver value appears on the card. Only committed bytes are read: a record on disk that is not committed reads as
   no record.
7. `PendingWeather` and its "M1 pending" text are gone, and the wiring builds `RecordedWeather`.

**Test plan:** fake `CommittedRecords` holding a record.
1. Positive: the real live GREEN record of 23 Oct 2026, AMBER and RED variants. Each gives its exact lines and its used
   record. Not live: the real back-fill of 14 Oct shows "no live reading" and blocks.
2. Negative: no record; a file that is not JSON; a record whose `day` is the day before.
3. Boundary: a probability of exactly 0.10, shown as "10.0%". A colour other than GREEN, AMBER or RED, or a chance
   that is not a number between 0 and 1, fails closed, and so does a weather source that raises (the guard keeps the
   "no new trades" line). A missing operative probability is
   treated as "not scored" and never as 0%. M1's `_status` never writes that case, so this is a guard only. A v0
   colour of "not scored" shows its `v0_status` reason.
4. Empty: an empty `probabilities` object, and a committed folder with no file for the day.
5. Wiring: `build_daily_card` builds `RecordedWeather`. One test runs the real committed record of 14 Oct 2026 through
   `GitHeadRecords`.

**Known limits:**
- Until `weather capture` runs daily (O1 and v4's freeze), live days have no record, so the card says "no reading" and
  "no new trades". That is true, and it is the owner's rule.
- The card's weather is the 14:30-cutoff reading; an intraday change is LM1's.

**Gap list:**

| Requirement | Where |
|---|---|
| M1: "the card shows the colour" (`M-weather.md`, Out and M2's Depends) | Criteria 1, 3 and 4 |
| Owner "4 A": a missing reading blocks new trades and the card says so | Criteria 2 and 3 |
| "Never a colour it did not score" (T1) | Criteria 2 and 3 |
| Privacy (no private driver) | Criterion 6 |
| The SHA-256 footer of every record used (T1) | Criterion 1 |
| Enforcing the block at the desk | Out (its own story) |

**Split:** M1's builder (session 013xqaNTCbSBytKgqpfaYFqZ) agreed on 16 Oct:
- the path is `WeatherRecords.path`;
- reading the committed bytes is right, because in O1's run the weather step commits before the card, and an
  uncommitted record must read as "no weather";
- the fields used here are stable, and `v0_status` was added today;
- `status` is exactly "scored" or "not scored: ...";
- they will warn T1c's owner before any move of these records to Drive (O9).

**Depends:** T1, M1 · **Size:** S · **Status:** done: text judge 401 PASS, code judge 555 PASS (e30ab3d0)

## T1d. The card names the steps that failed or were refused today

**Repository:** trading · **Asked by:** the orchestrator, 24 Oct 2026, after O1's R2 · **Lane:** 1 (judge I)

**Description:** As the owner, I want the daily card to name every desk step that failed or was refused today, so I
never read a card without knowing that part of the day did not run.

**Context and why (strong evidence: code on `main`, and R2 on `story/o1-r1r2-step-safety`, read 24 Oct 2026):**
- Until R2, any unexpected error in a step ended the whole run. Then there was no card, so a card meant the day had
  run.
- Since R2 (`fno/desk/daily_run.py` `_run_step`), such an error fails only its step. The step is logged
  `{"status": "failed", "reason": ...}` in the run log and the run goes on. A step that needs it, such as `fills`
  needing the snapshot, is logged `refused`. The card is still posted, and today it says nothing about this.
- O1 already defines the day's problem steps. `fno/daily/runner.py` lists every run-log step whose status is in
  `PROBLEMS = (STEP_FAILED, STEP_REFUSED)` for its last line, "day done with problems: <steps>".
- The run commits the run log after each step (`DailyRun._step`), so the card step sees every earlier step's status
  in the committed log.

**Scope.** In:
- **One shared rule, O1's.** The list comprehension in `fno/daily/runner.py` moves into one function,
  `problem_steps(steps) -> list[tuple[str, str]]` (step name, status). The function lives in O1's run-log module,
  `fno/desk/run_log.py`, beside `RunLog`, and both the runner's last line and the card call it. It is O1's file, so
  this is agreed with O1's builder first. The runner's text and behaviour do not change.
- **The card line.** It sits in the card's status section, after the rule checks:
  "Steps with problems today: snapshot (failed), fills (refused)" (the orchestrator's wording, 24 Oct), in run order. There is no line when
  none failed or was refused.
  - The card reads the day's committed run log through T2's existing `RunLogReader` (`fno/cards/rule_checks.py`), the
    reader the rule checks already use, and passes its steps to `problem_steps`. It parses no text.
  - A run log that cannot be read is already reported by T2's rule checks ("unreadable"), so T1d adds no second line
    for it.
- `not_live`, `ok` and every other status are not problems, exactly as O1's rule says.
- **T2's decisions check after R2** (judge 567 should-fix, checked: `fno/cards/rule_checks.py:97`).
  - Since R2, a decisions step that raises is committed as `{"status": "failed", "reason": "raised:<Type>"}`.
  - `DecisionOutcome` treats every key of the step's result as a book: `[b for b, r in result.items() if "run_id" not
    in r]`. On that result it gives `['status', 'reason']`, a substring test on a string. The card would then say
    "late or not committed: status, reason" as a final outcome, naming two non-books and hiding the failure.
  - Fix: a decisions result whose status is a problem under O1's rule (the same `problem_steps` status set) gives the
    final outcome "decisions step <status>: <reason>" (the orchestrator's wording, 24 Oct; the reason is the logged
    code, e.g. "raised:NotImplementedError") with code `CARD_DATA_CHECK_FAILED`, and is never read as books.
  - The snapshot check already fails closed ("no valid execution snapshot", `data_check_failed`), so it is
    unchanged.

Out:
- **Steps after the card in `DAILY_RUN_STEPS`** (G13's records and scores, the candles, the close reads) run after the
  card is posted, so their failures cannot be on it. They stay in the run's last line and in their own alerts.
- **The reason text:** under O1-status-only the committed log holds only a status and a reason code, and each failure
  is already alerted to #fno-desk with its reason. The card names the step and its status only.
- **The card's status (TRADE / NO TRADE):** unchanged. It is always NO TRADE until T1 slice B.

**Acceptance criteria:**
1. When the committed run log has steps logged `failed` or `refused`, the card shows one line naming each, with its
   status, in run order.
2. With no such step, including a day whose steps are all `ok` or `not_live`, the card has no such line.
3. With no run log yet (the desk has not run), there is no such line. T2's rule checks already say "not yet decided".
4. The runner's last line is unchanged ("day done with problems: <steps>"), and both the runner and the card use the
   same `problem_steps`.
5. The card reads the run log only through `RunLogReader` and `problem_steps`, never by matching text.
6. A `decisions` step logged `failed` (or `refused`) gives T2's decisions outcome "decisions step failed: <reason>"
   (or "refused: <reason>"), with code `CARD_DATA_CHECK_FAILED`. Any other step-level status is shown as it is, with no
   code. It never names a book "status" or "reason" (judge 567).

**Test plan:**
1. Positive: a planted committed run log with `snapshot` failed and `fills` refused gives the exact line, in order.
2. Negative: all `ok` and `not_live`, so no line. A reason code never appears on the card.
3. Empty: no run log gives no line.
4. Shared rule: the runner's existing tests pass unchanged, and a test shows that the runner and the card list the
   same steps for one log.
5. Decisions after R2: a planted committed run log with `decisions` = `{"status": "failed", "reason":
   "raised:NotImplementedError"}` gives "decisions step failed: raised:NotImplementedError" and `data_check_failed`, and neither "status" nor
   "reason" as a book. A normal per-book result is unchanged (T2's existing tests).
6. Plants: dropping `refused` from the rule fails test 1; a card that ignores the reader's steps fails test 1;
   removing the decisions status check fails test 5. Built: P1 to P13 in the code claims below.

**Known limits:**
- Failures in steps after the card are not on it (Out).
- The card is posted only once the owner sets `daily.live_from.card`.

**Split:** O1's builder (session_014zYLf18PgCzR7YoHs1X5Dp) owns `fno/daily/runner.py` and `fno/desk/run_log.py`. The
move of the rule into `problem_steps` is asked of them before code.

**Claims (for judge I):**
- The problem rule exists once today, inline in `fno/daily/runner.py:61` with `PROBLEMS` at line 19. T1d moves it,
  never copies it (strong: code read).
- R2's failed and refused results are run-log statuses (`STEP_FAILED`, `STEP_REFUSED` in
  `fno/constants_operations.py`), committed after each step before the card step runs (strong: `DailyRun._step`).
- The card's existing `RunLogReader` already reads that committed log for T2 (strong), so nothing new reads git.
- Gap list:
  - the orchestrator's ask (one line naming the failed steps, none when none failed) is criteria 1 and 2;
  - "through O1's own interface" is criteria 4 and 5;
  - refused steps are included because O1's own rule counts them as problems; the orchestrator confirmed this on
    24 Oct ("a refused fills step matters to the owner as much as a failed one");
  - Judge 567's should-fix is in scope as criterion 6 (T2's `DecisionOutcome` is mine, T2).
- Known limit, stated for the judge: steps after the card in `DAILY_RUN_STEPS` (G13's records and scores, the
    candles, the close reads) run after the card is posted, so a failure there is never on the card. It stays in the
    run's last line and its own alert.

**Code claims (for judge I; builder session_01Mt6dcBU5kp2htdPN2KmiZH from 24 Oct, replacing 0145TfSwzmpk):**
- **Built on R2's round 2.** `story/o1-r1r2-step-safety-b` at `2c80be430` (the orchestrator's choice; it supersedes
  `story/o1-r1r2-step-safety`, whose `f0bb2aa9c` was merged first) is merged in. `fno/desk/` and `fno/daily/` are
  O1's versions byte for byte (`git diff 2c80be430 -- fno/desk fno/daily` is empty). This branch's earlier `PROBLEMS`/`problem_steps` copy is gone. Beyond the merge, this branch
  changes only `fno/cards/`, `tests/cards/test_problem_steps.py` and this file (strong: diff).
- **One rule, O1's.** The card's line calls `run_log.problem_steps` (`fno/cards/problem_steps.py`), and
  `DecisionOutcome` decides "failed or refused" by calling the same `problem_steps` on its one step, never the
  `PROBLEMS` set or a copy (`fno/cards/rule_checks.py`, `outcome`). The late books are read from O1's
  `book_results(result)` (`_decided`) (strong: code).
- **O1 round 2's run-log shapes (strong: tests write the log with O1's own `RunLog.record`).** A failed step now
  carries `retry`. A failed step waiting for its retry (`retry: true`, for example `fills`) is still `failed` today,
  so the card names it, exactly as the runner's last line does. A step retried and then ok replaces its failed entry
  (it moves last in the log) and is no longer named. A failed decisions step with `retry: false` is unchanged
  (criterion 6). The reader accepts the new key: it checks only `name -> {"result": {...}}`. Tests:
  `test_a_failed_step_waiting_for_its_retry_is_named_as_failed`, `test_a_step_retried_and_then_ok_is_no_longer_named`.
- **A change from the earlier code, on odd shapes.** O1's `problem_steps` assumes `name -> {"result": {...}}`; the
  dropped copy tolerated `steps` that is not a mapping. Instead of a second, tolerant rule, T2's `RunLogReader` now
  refuses any other shape once, as "not readable (steps are not name -> {result: {...}})" with `data_check_failed`,
  so neither O1's rule nor a card rule meets it. The earlier test `test_odd_run_log_shapes_never_crash_the_rule`
  (which called the rule directly on a list) became `test_odd_run_log_shapes_are_unreadable_at_the_reader_never_a_crash`.
  Every committed run log, 17 to 23 Oct, has the accepted shape (reviewer 1 checked), so no real day turns unreadable.
- **Criterion 6, wording as built:** the decisions line keeps T2's C4 part on every path, so a failed decisions step
  reads "decisions step failed: raised:NotImplementedError, no C4 refusal" (or "..., C4 refused: book1_rules (caps)"),
  code `data_check_failed`. A step-level result with no reason reads "decisions step <status>". Any other step-level
  status is shown as it is: no code of its own, but a C4 refusal dated today still gives `hard_rule_breach`.
- **Gap list (each requirement of the passed text, judge 567 addendum 2):**

  | Requirement | Criterion | Code | Test (`tests/cards/test_problem_steps.py`) | Plant that fails it |
  |---|---|---|---|---|
  | One line naming failed and refused steps, with status, in run order | 1 | `ProblemSteps.line`, `RuledStatus.status` | `test_failed_and_refused_steps_are_named_with_their_status_in_run_order`, `test_boundaries_one_failed_one_refused_and_an_empty_log` | P1, P2, P9 |
  | No line when all `ok`/`not_live`, or no steps | 2 | `ProblemSteps.line` | `test_no_line_when_every_step_is_ok_or_not_live_or_the_desk_has_not_run`, `test_boundaries_...` (empty log) | P12 |
  | No run log gives no line | 3 | `ProblemSteps.line` (`steps or {}`) | `test_no_line_when_...` (`status_lines({})`) | P13 |
  | Runner's last line unchanged; runner and card share `problem_steps` | 4 | O1's `runner.py`, `run_log.problem_steps` | `test_the_run_s_last_line_and_the_card_share_o1_s_one_rule`, `test_the_runner_s_last_line_and_the_card_name_the_same_steps_for_one_log` (the real `DayRunner` line and the card's line from one log) | P1, P7 |
  | The card reads only through `RunLogReader` and `problem_steps`; wired in the app | 5 | `ProblemSteps`, `wiring.build_status` | `test_the_app_s_card_wires_the_problem_line`, odd-shape test | P2, P6, P8 |
  | A failed or refused decisions step: "decisions step <status>: <reason>", `data_check_failed`, never books | 6 | `DecisionOutcome.outcome`, `_decided` | `test_a_failed_decisions_step_is_...`, `test_a_refused_decisions_step_is_...`, `test_a_decisions_step_with_another_step_level_status_...`, `test_c4_refusals_are_read_on_a_step_level_decisions_result_too`, `test_a_decisions_status_that_is_not_a_string_...` | P3, P4, P10, P11 |
  | Snapshot check unchanged (fails closed) | Scope | `ExecutionOutcome`, `_verdict` (unchanged) | `test_a_failed_snapshot_fails_closed_with_its_raise_and_is_named_as_failed` | (unchanged code) |
  | Steps after the card; the reason text; TRADE / NO TRADE | Out | - | - | - |

- **Plants (rule 4), each run on `tests/cards`, `tests/daily`, `tests/timetable`, `tests/scoreboard` (475 tests), then
  restored:**
  - P1 `refused` dropped from O1's `PROBLEMS`: caught (10 failed).
  - P2 the card ignores the reader's steps (`problem_steps({})`): caught (5).
  - P3 the decisions status check removed (`if "status" in result` never true): caught (5).
  - P4 the `rule_checks.py:97` path of judge 570 addendum 1 (no status check, the raw result iterated as books):
    caught (5; it gives "late or not committed: status, reason").
  - P5 `book_results` dropped, status check kept: **survives, equivalent.** Every result `book_results` empties has a
    top-level `status`, which `_decided` has already taken. It is kept because it is O1's reader for per-book
    results (the orchestrator's step 2), not because a test needs it.
  - P6 the reader's shape check removed: caught (1).
  - P7 the runner keeps its own rule without `refused`: caught (5, two of them O1's own `test_day_run` cases).
  - P8 the wiring drops `ProblemSteps`: caught (1).
  - P9 the line shows the reason: caught (5).
  - P10 C4 refusals skipped on a step-level decisions result: caught (1).
  - P11 a failed decisions step not a data check failure: caught (3).
  - P12 a line even when nothing failed: caught (2).
  - P13 no run log handed to the rule as `None`: caught (1).
- **Cases (rule 5):** none (all `ok`/`not_live`, an empty log, no log), one failed, one refused, both in run order,
  a failed and a refused decisions step, another step-level status, a non-string status, a failed snapshot, a C4
  refusal on a step-level result, a failed step waiting for its retry, one retried and then ok, and four odd shapes (`steps` a list, a step a string, a `result` a list, no
  `result`).
- **Output sample (rule 6),** made by the committed code from the tests' planted logs (`status_lines` in
  `tests/cards/test_problem_steps.py`; the books are test names):

  ```
  Status: NO TRADE (data_check_failed)
  Reason: no strategy has passed
  Paper trades so far: 0
  Rule checks: a rule refused, or a record could not be read
  - decisions: late or not committed: book2_hybrid, no C4 refusal
  - execution: no valid execution snapshot (raised:NotImplementedError)
  Steps with problems today: snapshot (failed), fills (refused)
  ```
  and for a failed decisions step:
  ```
  - decisions: decisions step failed: raised:NotImplementedError, no C4 refusal
  Steps with problems today: decisions (failed)
  ```

**Builder self-review (quality rule 3):** two independent review sessions (correctness, session_013i9e85; silent
failures, session_014ubpsF), each given only the diff and this story's Scope, criteria and test plan.
- FIXED:
  - both: a step-level decisions result returned before C4's refusals were read, so a refusal dated today was lost
    (with a status other than failed or refused the card said "no breach"). Now read on every path (P10);
  - correctness: the failed check tested the `PROBLEMS` set itself, a second place for the rule; now it calls O1's
    `problem_steps`;
  - correctness: test plan 4 was half there (identity only); the real `DayRunner` last line and the card's line are
    now built from one log;
  - correctness: the failed-snapshot test asserted "no line says C3", which can never fail; replaced with the
    `data_check_failed` reason and the step's own raise;
  - silent failures: `{"status": None}` crashed the card (`"run_id" not in None`); any top-level `status` is now a
    step-level result.
- KEPT, with reasons:
  - correctness: `book_results` is redundant after the status check (P5, equivalent). Kept as O1's reader (above).
  - both: a malformed previous-day log makes today's execution line "not readable" with yesterday's path, and a bad
    shape hides the problem line. Both fail closed with `data_check_failed` and T2's line names the file; the
    stricter reader makes it a little more likely. Older than T1d (T2's `_last`), left to T2's next change.
  - silent failures: when only a non-ruled step fails (for example `exits`), the card still says "Rule checks: no
    breach" with T1's reason code, and the problem line comes last. That is the passed text (the status is
    unchanged, Out). **For the orchestrator:** whether a problem step should change the reason code is a story
    decision, not a code fix.
  - for O1's builder (correctness reviewer): `_refused` counted only `STEP_FAILED` inputs. Round 2 (`2c80be430`)
    now reads them through `problem_steps`, so a refused input refuses too: resolved on O1's side.

**Known limits:**
- A step that records its failure without a `status` (an exit review's per-book `error`, `trade_marks`
  `{"marked": False}`, `pack` `{"built": False}`) is not named, by the card or the run's last line: that is O1's rule.
  Each still sends its own alert to #fno-desk.
- Failures in steps after the card are never on it (Out).
- This branch touches no O1 file beyond the merges, so a newer O1 head merges cleanly unless O1 renames
  `problem_steps`, `book_results` or `RETRY`.

**Gates on the merged tree (code at `a432d5a91`, merged with `2c80be430`; this note added after):** `ruff check fno
tests tools` clean; `ruff format --check` 2445 files formatted; `check_imports` clean (2574 files); `check_records`
clean (8995 files); `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -p no:cacheprovider -n auto`: 15168 passed, 15
xfailed, 1 failed. The one failure, `tests/books/test_account_processes.py::test_a_live_holder_keeps_its_lock_after_its_lease_expires`,
is a timing test (a child process must take the lock within a 2-second sleep) in a file this branch does not touch,
run while the machine's load average was about 20 from other sessions' suites. Rerun alone: that file, 7 passed.
(Earlier, at `e26d7f9a3` merged with `f0bb2aa9c`: 15138 passed, 15 xfailed, 0 failed.)

**Depends:** T1, T2, O1 R2 (`story/o1-r1r2-step-safety-b`) · **Size:** S · **Status:** text PASS (judge 567); code
merged onto R2's round 2 at `2c80be430`, to judge I (session_01MvZneCLZqBuiGyNxawdVee); merges in one batch with
R2's -b head

---

## T1f. The card in a rehearsal: its clock checks are not live, and nothing after the post stops its records

**Repository:** trading · **Asked by:** the orchestrator, 24 Oct 2026 (its 23 Oct and 22 Oct rehearsals) · **Lane:** 1
(judge I: the card's Slack delivery and its records)

**Description:** As the owner, I want a rehearsal's card step to finish as the real one does, and a posted card to
always leave its Drive record and delivery metadata. Then a rehearsal proves the card, and a posted card is never
"no card on record".

**What happened (strong evidence: reproduced 24 Oct at `main`, nothing posted to Slack):**
- The orchestrator's rehearsal of 23 Oct (`daily run --rehearse --day 2026-10-23`, run `20261024T133643Z-76a4f5`)
  posted its labelled card to #fno-desk. Then the card step failed with exit 1. Its alert was only "step card failed:
  research/forecasts/scores/2026-10-22.json 6241c90b...; the run goes on", the last line of the card's "Records
  used" list.
- **Cause.** A rehearsing process installs REH1's HTTP guard (`fno/rehearsal/http_guard.py`). It refuses every host
  but Google's Drive API and Slack's posting calls. The card's issuer asks GitHub for the time after the post
  (`CardIssuer.issue` -> `check_server` -> `HttpDateClock.now`, a HEAD to `api.github.com`). The guard raises
  `RehearsalCallRefused`, a `RuntimeError`. `HttpDateClock.now` catches only `requests.RequestException`, and
  `check_server` only `ServerTimeUnknown`, so the error leaves `issue()`.
  - At that point the card is already posted. The Drive record is never saved and the delivery metadata is never
    written.
  - The CLI exits through the traceback (stderr), so the result lines are never printed.
- **Reproduced:**
  - `check_server` with the guard installed raises "RehearsalCallRefused - rehearsal: no live call (HEAD
    api.github.com/repos/exepex/trading)".
  - `CardIssuer.issue` with a fake poster that reports "sent": 1 post, Drive saved nothing, no delivery file, and
    `issue` raised `RehearsalCallRefused`.
  - The card text's last line was a `research/forecasts/scores/<d>.json <sha>` line, as in the alert.
- **Why the alert shows that line.** O1's `outcome` (`fno/daily/steps.py`) takes a failed command's reason from its
  last printed line, `lines[-1]`. The traceback went to stderr, which is kept only in the private log. So the reason
  was the card text's last line. This is O1's code (Out).
- **Live days.** The guard is installed only in a rehearsal (`fno/rehearsal/process.py`, when `FNO_REHEARSAL` is
  set), so this exact failure cannot happen on a live day. It is not "fails on its first live day". The class of
  failure is live, though: any error after the post that is not caught leaves a posted card with no record. T1's own
  design says each step after the post "is a printed line and a stored fact, never a stop" (`issue.py` docstring),
  and only the Drive save and an `OSError` on the metadata write keep that promise today.
- **A second rehearsal effect.** The rehearsal's clock is the replay clock (the replayed day), while Slack's `ts` is
  real. So the Slack skew check would always store a WARNING in a rehearsal. REH1c says the same for A16's check and
  replaced it with "rehearsal: replay clock, not checked against GitHub's and Slack's servers"
  (`fno/rehearsal/preopen_wiring.py`). The card was never given that hook.

**Scope.** In:
- **A rehearsal hook for the card's clocks (REH1c's pattern).** In a rehearsal, the issuer's clock checks are one
  unchecked line per server: "<server>: not checked (rehearsal: replay clock, not checked against GitHub's and
  Slack's servers)". REH1c's `NOT_CHECKED` text is imported from `fno/rehearsal/preopen_wiring.py`, never copied. No
  GitHub call is made, and no Slack skew is computed. A real run is unchanged.
  - **Agreed with REH1's owner (session_01GAACYjcfHWkC3hp33iiMXV, 24 Oct), with two conditions, both in scope:**
    1. The card's clocks join `guard.builders()` in `fno/rehearsal/guard.py` (a one-line edit agreed by REH1's
       owner), as REH1c did for "A16's clock check". The real builder is called and the rehearsal form is
       expected, so REH1's guard proves the card's clocks before any step. `tests/rehearsal/test_guard.py`'s
       "without the mode" map gains the real form, and its count of unlabelled services grows by one.
    2. In a rehearsal, no GitHub client is built at all. The HTTP guard stays the backstop, never the means.
  - **Design:** the issuer's clocks become one object behind an interface, `CardClocks` (`fno/cards/`), with two
    forms:
    - `ServerCardClocks`, the real run: today's Slack check from the post's `ts` plus `HttpDateClock` for GitHub,
      unchanged;
    - `RehearsalCardClocks`: one unchecked line per server, no client built.
    `build_card_clocks()` in `fno/cards/wiring.py` is the real builder. It returns
    `rehearsed_card_clocks(<real>)`, a function in `fno/rehearsal/card_label.py` beside `rehearsed_card_poster`, which
    picks the rehearsal form when `FNO_REHEARSAL` is set. The GitHub `HttpDateClock` is made only inside the real
    form's builder, so a rehearsal never constructs it. `CardIssuer` takes a `CardClocks` in place of its list of
    server clocks.
- **Nothing after the post stops the records (judge 592 finding 1).** Everything in `CardIssuer.issue` after
  `poster.post` returns is guarded, stage by stage, so a raise in one stage never skips the next. Every failure is
  named by error type only (T1's rule: no message reaches a log). The stages, in order (today's `issue.py:51-60`):
  1. **The clock checks** (the Slack check from the post's `ts`, then each server). A check that raises anything
     becomes `unchecked(<server>, "<Type>")`.
  2. **The facts** (`_facts`). If building them raises, the issuer uses **minimal facts** instead, then goes on:
     - `day`, `status`, `reason_code`, `card_sha256`, `test` and `code_commit`;
     - `slack: {sent, ts, channel, outcome, server_time_utc}` from the post's receipt;
     - `clock: []`, `missing: []`, `previous_misses: []`, `records_used: []`;
     - `failure: "facts not built (<Type>)"`.
     These are the keys the next card's `misses()` reads, so the next card can still name the day's miss and never
     crashes on it.
  3. **The Drive record** (`_section` for each section, `_record_name`, `_json(record)`, then `save`). Building it
     sits inside the same guard as the save. A raise anywhere here gives `saved: false` and "card record NOT saved
     to Drive: record not built (<Type>)".
  4. **The delivery metadata** (`_json(delivery)`, then the write). A raise of any kind, not only `OSError`, prints
     T1's "delivery metadata NOT written (<Type>); commit it by hand:" followed by the metadata. If even the metadata
     cannot be turned into JSON, it prints the minimal facts of stage 2 instead (always JSON: strings, booleans and
     null only).
  - **The exit code.** 0 only when the card was sent, the Drive record saved, the metadata written and no stage
    failed. Any failed stage gives exit 1: T1's rule plus stages 1-2. A clock that is merely unchecked is not a
    failure; a clock check that raised is one.
  - **Where a rehearsal's metadata goes (judge 592 finding 2).** In a rehearsal, the delivery file is written in the
    rehearsal's checkout. The run's commits go to its own branch, `rehearsal/<day>-<run_id>` (REH1,
    `fno/rehearsal/checkout.py`), never to `main`. T1f changes nothing there.
- **The CLI prints its result lines even when the issuer fails.** Today an unexpected raise after `out(text)` loses
  every result line. With the guard above, `issue()` returns on every path. A test plants a raising clock and a
  raising metadata store and checks that the last printed line is the delivery line, never a card line.

Out, with reasons:
- **O1's alert reason for a crashed command** (`fno/daily/steps.py` `outcome`: `lines[-1]` even when the command
  died with a traceback). That is O1's code, so it goes to O1's owner as a proposal: on a nonzero exit with stderr,
  the alert carries the last stderr line (the exception's type and message), and the committed log keeps only its
  code (O1-status-only). T1f makes the card's own failures print a result line, so the card no longer depends on
  it.
- **The witness in a rehearsal:** already REH1b's (`rehearsed_receipts`); unchanged.
- **A16's and A22's clock checks:** already REH1c's; unchanged.

**Acceptance criteria:**
1. In a rehearsal (`FNO_REHEARSAL` set), `card daily --post` builds no GitHub client and makes no call to GitHub. Its delivery metadata stores one
   unchecked entry per server ("Slack" and "GitHub"), each with the rehearsal line and `checked: false`, and no
   WARNING. A real run is unchanged: the same servers are asked, and T1 criterion 7 holds.
2. In a rehearsal, after a sent post, the Drive record is saved (the dryrun store) and the delivery metadata is
   written in the rehearsal's checkout. It is committed only to the rehearsal's branch, `rehearsal/<day>-<run_id>`,
   never to `main` (REH1's rule, unchanged). The step's exit code follows T1: 0 when sent and saved.
3. A clock check that raises any error (not only `requests`' errors) is stored as `unchecked(<server>, "<Type>")`.
   The issuer goes on to the Drive save and the metadata write.
4. A metadata write that raises any error prints "delivery metadata NOT written (<Type>); commit it by hand:" with
   the metadata (or the minimal facts, if the metadata is not JSON), and exits 1.
   - A raise while building the facts stores the minimal facts of stage 2, with `failure: "facts not built
     (<Type>)"`, in both the Drive record and the delivery metadata. It exits 1, and the next card reads that
     metadata without error.
   - A raise while building the Drive record gives "card record NOT saved to Drive: record not built (<Type>)", the
     metadata is still written, and the command exits 1.
   - The card is never posted twice: `issue` posts once, first.
5. On every path after the post, the CLI's last printed line is one of the issuer's result lines (the delivery line),
   never a line of the card's text.
6. With the HTTP guard installed and the hook removed, a test fails. The test asserts that in a rehearsal the stored
   GitHub entry carries the rehearsal line. Without the hook, criterion 3 still catches the refused call, so GitHub
   is stored as unchecked with "RehearsalCallRefused" in place of the rehearsal line, and the test's assertion
   fails. It also asserts that no `HttpDateClock` was built (P8).
7. REH1's guard lists the card's clocks: `guard.builders()` has "the card's clocks" with `build_card_clocks` and
   `RehearsalCardClocks`. In the mode it reports no problem; without the mode, `test_guard.py`'s map names the real
   form and the unlabelled count includes it.

**Test plan** (`tests/cards/test_rehearsal_issue.py`, new):
1. The reproduction: guard installed, the real `HttpDateClock` for GitHub, a fake sent poster.
   - With the hook: no GitHub call (the guard would raise), metadata written, Drive saved.
   - Without the hook: `issue` still returns, GitHub is unchecked with "RehearsalCallRefused", and the metadata is
     written (criterion 3).
2. A raising clock (`OSError`, `ValueError`) is unchecked by type.
3. A raising metadata store (`TypeError`, `PermissionError`) prints the NOT written line with the metadata, and the
   exit code is 1.
3b. Facts that raise (a fake `_facts` failure, and a receipt value that is not JSON): both files hold the minimal
   facts with `failure`, the exit code is 1, and the next day's `misses()` reads the file without error.
3c. A Drive record that cannot be built (a section that raises in `_section`, or `_json` on a non-JSON value): the
   NOT saved line with "record not built (<Type>)", the metadata still written, exit 1.
4. CLI: `cmd_card_daily` with a raising clock prints the delivery line last.
5. A real run (no `FNO_REHEARSAL`): the GitHub clock is asked as before (T1's tests unchanged).
6. Guard: `problems()` in the mode is empty with the card's clocks listed; without the mode the card's clocks are
   counted as unlabelled (REH1's `test_guard.py`, its map and count updated).
7. Empty and boundary cases: no clocks at all; a poster that did not send (no Slack time, so Slack is unchecked as
   today); a rehearsal with no Drive settings (`NoCardRecords`), which still writes the metadata.

**Planned plants:**
- P1: the hook returns the real clocks in a rehearsal (test 1).
- P2: the issuer's clock guard narrowed back to `ServerTimeUnknown` (tests 1 and 2).
- P3: the metadata write guarded for `OSError` only (test 3).
- P4: the CLI prints the result lines only on success (test 4).
- P5: the hook active in a real run (test 5).
- P6: the facts built outside the guard (test 3b).
- P6b: the Drive record built outside the save's guard (test 3c).
- P6c: the minimal facts without `clock` (test 3b: the next card's `misses()` crashes).
- P7: the card's clocks left out of `guard.builders()` (test 6).
- P8: the rehearsal form built from the real one, so a GitHub client is constructed in the mode (test 1: a builder
  spy counts zero `HttpDateClock`s in the mode).

**Gap list:**

| Requirement | Where |
|---|---|
| The rehearsal's card step finishes (no refused live call) | criteria 1 and 2 |
| A posted card always leaves its Drive record and metadata: every stage after the post guarded, the facts' fallback defined (judge 592.1) | criteria 2, 3 and 4; tests 3, 3b, 3c |
| A rehearsal's metadata only on the rehearsal branch (judge 592.2) | criterion 2 |
| The alert names the real problem, not a card line | criterion 5 (card side); O1's side is Out, proposed to O1's owner |
| No double post | criterion 4 |
| A real run unchanged | criterion 1, test 5 |
| REH1's conditions: the guard proves the card's clocks; no GitHub client in the mode | criteria 1 and 7, tests 1 and 6 |

**Answers to judge 592 (round 1), by number** (this round also carries REH1's owner's two conditions, `2d4e93719`):
1. **Accepted** (checked: `issue.py:54-57` builds `_section`, `_record_name` and `_json(record)` outside `save`'s
   guard). Every stage after `poster.post` is now named and guarded, the facts' fallback is defined field by field,
   with where it is stored and exit 1, and test 3b, test 3c and plants P6, P6b and P6c are added. Found while doing
   it: the fallback must keep `slack`, `drive` and `clock`, or the next card's `misses()` would crash on the record
   (P6c).
2. **Accepted.** Criterion 2 and the Scope say the metadata is committed only to `rehearsal/<day>-<run_id>`, never
   `main`.
3. **Accepted.** Criterion 6 states what the test asserts: the rehearsal line on GitHub's entry, which without the
   hook becomes "RehearsalCallRefused" (and no `HttpDateClock` built).

**Depends:** T1, REH1 (REH1c's hook pattern; REH1's owner agreed on `card_label.py` and `guard.py`, 24 Oct) · **Size:** S ·
**Status:** text round 2, to judge I
