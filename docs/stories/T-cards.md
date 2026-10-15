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

**Depends:** D3, E2, G3, G4 (M1 for weather later) · **Size:** M · **Status:** built on `story/t1-daily-card`; one live TEST
post made 15 Oct (ts 1792025414.919329); awaiting the judge.
