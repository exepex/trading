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
routine)

**Description:** As the owner, I want every card to say plainly whether a registered rule stopped the trade, and on
every trade card to show up to three objections from an AI that tried to find what is wrong, so that I see each call
attacked before I read it, without that AI ever deciding anything.

**Context and why (design v2 `07_ai_team.md` 7.3, `04_...` 4.1; REPLAN T2, T3):**
- Design 7.3 has two parts: rule checks (code, can block) and objections (AI, cannot block).
- **Most of 7.3's rule checks already exist and already block, before any card is built** (strong: code read on
  `main`). Stale or invalid data is C3's gate (`fno/checks/gate.py`, logged in the run log's `snapshot` step). Caps,
  margin room, maximum loss with charges, structure shape and the version's terms are C4
  (`fno/checks/validity_*.py`; each failure is a row of `journal/<book>/validity_failures.csv`). A trade only for a
  version at `paper` is D1's registry, which T1's status already reads.
- Re-checking them in the card would be a second version of each rule (one builder per function). So **T2 checks
  nothing again**: it reads what those rules decided that day and makes the card say the same thing, with the reason.
  The card is never `TRADE` when the desk's own records say a rule refused the trade.
- Three items of 7.3 have no rule in the code today: an event inside the holding window, physical settlement, and an
  idea that is a variant of a failed one. Each is new rule-making, so it stays out of T2's blocking (see Scope Out and
  question 2).
- **Real state today (strong):**
  - card v1 is always `NO TRADE`; no version is at `paper`; T1's trade fields (slice B) are not built;
  - the card is not yet posted daily: nothing runs T1 until O1 goes live (orchestrator, 15 Oct 2026).
  So T2 v1 sharpens the `NO TRADE` reason, and T3 has no trade card to object to until slice B's trade fields exist.

**Scope.** In:
- **T2: `RuleOutcome`, read from committed records only** (`fno/cards/rule_checks.py`):
  - `RuleSource` (interface) with one class per existing rule:
    - `DataGateOutcome`: the day's run log (`journal/runs/<d>.json`), `snapshot` step `valid: false` →
      `data_check_failed` with C3's failed check names;
    - `ValidityOutcome`: the day's rows of each book's `validity_failures.csv` → `hard_rule_breach` with C4's check
      names;
    - `RungOutcome`: a trade for a version not at `paper` in the committed registry → `WATCH`, never `TRADE`.
  - The card's status line takes the first reason in a fixed order: data, then rung, then validity, then T1's own
    reasons. Every reason found is listed in a "Rule checks" line, or "rule checks: no breach".
  - A rule's record that cannot be read gives `data_check_failed` naming the file, never "no breach".
  - T2 decides nothing: the trades were already refused by C3, C4 and D1. The card only reports their records.
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
- **New blocking rules** (event in the holding window without the version's permission, physical settlement of stock
  options, a variant of a failed idea): each is a new rule. It belongs in C4 (or R1's registration for variants),
  decided by the owner first (question 2), never in the card.
- **Weather RED and `not scored` blocking entries** (owner "4 A"): the desk must enforce them before a version reaches
  paper (M1 left enforcement out). Until then the card shows the colour and does not claim a block it does not have.
- Counterfactual scoring of objections (paired shadows, 7.3) and F9's value test: they need trades (S3, F9).
- Objections on the post-mortem (LR1, done), on idea registration (R1) and on promotion proposals (D-epic).
- Scheduling the card: O1.

**Design:**
- `fno/cards/rule_checks.py`: `RuleSource`, `RuleOutcome`, the three readers and `RuleChecks` (the fixed order). It
  plugs into T1's existing `StatusSource` and `CardSection`; no new status logic.
- `fno/cards/advocate.py`: `CardAdvocateSubject` (writes the public lines file) and `CardAdvocateFirer` (pointer,
  budget, fire log). The objections come through `Advocate`: `RoutineFileAdvocate` with T3's `ObjectionCheck`
  settings.
- Wiring: only `fno/cards/wiring.py`. Every file under 350 lines.

**Acceptance criteria:**
1. A run log with `snapshot` `valid: false` gives `NO TRADE`, reason `data_check_failed`, naming C3's failed checks.
2. A `validity_failures.csv` row for the day gives `NO TRADE`, `hard_rule_breach`, naming C4's checks; other days'
   rows are ignored.
3. A trade for a version not at `paper` gives `WATCH`, never `TRADE`.
4. With no failure, the line reads "rule checks: no breach"; an unreadable rule record gives `data_check_failed`
   naming the file.
5. T2 imports no `fno.checks` rule module and recomputes nothing: an AST test enforces it. It reads only the run log,
   the failures files and the registry.
6. The T3 subject file holds only public lines (a test plants a strike in the private trade fields and finds it absent).
7. The routine is fired once per card day with only the pointer. A BG1 `stop`, a missing configuration or a
   `FireFailed` each give `advocate_unavailable: <reason>`, and the card still goes out.
8. Objections pass `ObjectionCheck` with T3's settings (0 to 3, `Effect:` required, numbers only as whole tokens of
   the subject, no links or mentions), or the card shows `advocate_unavailable: <first failed rule>`.
9. The objections never change the status, a reason or a number on the card; only T2's committed rule outcomes do.
10. Each shown objection has an adjudication record `shown_only`; one pushed after `decision_finalized_at` is marked
    `late: not scored`.
11. LR1's tests still pass with `ObjectionCheck`'s settings moved to the constructor (1 to 5, `Effect:` not required).

**Test plan:** fakes for the run log, failures files, registry, trigger, advocate, budget and Slack.
1. Positive: each rule outcome; no breach; objections passing (0, 1 and 3).
2. Negative: 4 objections; no `Effect:`; a number not in the subject; a late push; an unreadable failures file.
3. Empty: no run log for the day (the desk did not run: "not yet decided", never "no breach"); no routine
   configured; budget stop.
4. Order: data before rung before validity.
5. Privacy: planted private fields absent from the subject.
6. AST: no rule recomputation, no second AI caller (only `fno.pipeline.trigger` fires).

**Known limits:**
- Until T1's trade fields exist and a version reaches `paper`, every card is `NO TRADE` and T3 has no trade card to
  object to (question 1).
- The routine has about 5 minutes between the 15:00 pack and the card post (4.1 targets: advocate 15:05, card 15:08).
  If it is regularly late, the record will show it; the deadline is never stretched for it.
- Objections are checked for form and numbers, not for being right; scoring them needs trades.
- The subject is public lines only, so the objections cannot see the strikes (privacy rule). A private subject would
  be one new adapter behind `Advocate` (Drive), and only if the owner wants it.

**Questions for the owner (via the orchestrator):**
1. **When T3 runs:** (A) only on `TRADE` and `WATCH` cards, so no AI minutes on `NO TRADE` days (none today); (B)
   every card day. **Recommendation: A** (reasoning only: an objection to "no strategy has passed" teaches little and
   costs about 250 runs a year).
2. **New rules from 7.3** (event in the holding window, stock-option settlement, failed-idea variants): (A) each
   becomes its own C4 or R1 rule when a strategy that needs it is proposed; until then the card shows an "event in
   window" warning line only; (B) T2 blocks on them now. **Recommendation: A**: blocking in the card would be an
   unregistered filter (7.3's own argument), and a block must live where the desk enforces it.
3. **Build order:** (A) T2 now (small: sharper `NO TRADE` reasons on today's cards), and T3's code after T1's trade
   fields and O1; (B) both now. **Recommendation: A** (reasoning only: T3 built now would run against nothing).

**Depends:** T1, C3, C4, D1, E3 (run log), LR1 (`fno/advocate`), F1 (routine pattern), F8, BG1 · **Size:** T2 S, T3 M ·
**Status:** story text, waiting for the judge
