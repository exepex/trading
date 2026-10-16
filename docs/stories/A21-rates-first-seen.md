# A21. Rates and same-day first-seen: RBI's T-bill and repo rates daily, NSE announcements before 14:00

**Repository:** trading · **Lane:** 1 (new story; outside services RBI and NSE; schedules) · **Judge:** F ·
**Response number:** 272 (claims file) · **Owner rule (16 Oct 2026):** data must be up to date, and every failure alerts
and is recorded.

**Description:** As the owner, I want the cash rate and the policy rate captured from RBI every day, dated and with the
time we first saw them, and NSE's company announcements copied during the day with the time we first saw each one.
Then the valuation record (G13) and the cash benchmark (S6) use the real rate instead of a constant, and the AI team's
equity analyst (F2) reads only what was public before its cutoff.

**Context and why (strong evidence: `main` read and the sources fetched on 16 Oct 2026, unless marked):**
- **The rates are constants today.**
  - `config.yaml:38` `risk_free_rate: 0.065`, read by C2's risk inputs, the forecasts and C4's validity settings.
  - S6's cash benchmark has `cash_rate: float = 0.055` with "placeholder until the S1 freeze sets the 91-day T-bill
    yield" (`fno/scoreboard/do_nothing.py:17,37`).
  - `research/evaluation/PROTOCOL.md:345-349` (owner, 16 Oct): on the S1 freeze date, "the latest 91-day T-bill
    yield from RBI's published auction result" replaces 5.5%.
  - G13's text (branch `story/g13-price-distribution`) uses the 6.5% config rate "until a daily 91-day T-bill and repo
    capture lands", and then switches with a new `method_version`.
  - No T-bill, repo-rate or FBIL money-market client exists in the repository.
- **The official numbers today differ from both constants.**
  - RBI's press release "91-Day, 182-Day and 364-Day T-Bill Auction Result: Cut-off" (Date: Oct 14, 2026; Press
    Release 2026-2027/1325; `rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=63803`) gives the 91-day cut-off
    price ₹98.5920, YTM 5.7281%.
  - RBI's home page, "Current Rates": Policy Repo Rate 5.50%. The same box repeats the 91-day T-bill as 5.7281%,
    "cut-off at the last auction".
  - So 6.5% overstates the cash rate by about 0.8 points. G13 measured that a 1-point change moves option prices by
    about 0.1% at 38 days (G13's text, some evidence).
- **NSE announcements have no same-day copy with a first-seen time.**
  - A12's day lists run only up to yesterday (`fno/filings/runs_cli.py:155`).
  - Its day-list manifest has no fetch time (`research/data/manifests/announcements.csv`: `date,url,status,sha256,
    size_bytes`).
  - A19's text leaves "a same-day NSE copy before 14:30" to A12.
  - F2 admits an item only if its "first-seen time ... is at or before the cutoff; a content date never stands in for
    it" (F2's text, `story/f2-analyst-cards`).
  - NSE's API answers the whole day in one call: `corporate-announcements?index=equities&from_date=16-10-2026
    &to_date=16-10-2026` returned 295 items, each with `seq_id`, `symbol`, `desc`, `an_dt` and NSE's dissemination time
    `exchdisstime` (00:17:31 to 16:56:04).
- **What A21 reuses:**
  - O9's write-once Drive store: `fno/storage/data_wiring.py` `build_data_store`, `DataStore.put`, `PartTable`, and
    receipts in the repository.
  - O10's failure record `research/ops/capture_errors.csv` (`CaptureErrorLog`, branch `story/o10-capture-health`).
  - The alert sender (`fno.composition.build_alert_sender`, #fno-desk only).
  - A7's NSE session calendar.
  - A12's announcement URL template (`fno/filings/sources.py:53`, imported, never copied).
  - The design follows A17's capture (`fno/global_cues/`: a source interface, adapters, a table with `first_seen_at`,
    checks, verify).

**Scope.** In:
- **Part 1: rates (`fno/rates/`, new).**
  - Two rates: `tbill_91d_cutoff` (each weekly auction's 91-day YTM at the cut-off price) and `policy_repo` (the
    policy repo rate).
  - The 182-day and 364-day yields come in the same release and are stored with it, because they cost nothing extra.
- **Part 2: same-day announcements (`fno/announcements_live/`, new).** A poll of NSE's day list at each of A16's
  15-minute marks from 09:15 to 14:00 IST on every NSE session. Each new `seq_id` becomes one row with the time we
  first saw it.
- Commands, checks, and a reader for each part's consumers; a schedule for the rates; the announcements poll rides in
  A16's recorder routine (design below).

Out (each with where it goes):
- Changing `config.yaml`'s `risk_free_rate` or S6's `cash_rate`. Each consumer switches when its own owner decides:
  - G13, with a new `method_version`;
  - S6, at the S1 freeze (S1's owner);
  - C2 and C4, if their owners want it.
  A21 only provides the data and the reader.
- A back-fill of past auctions: no consumer needs one. A past value would carry a back-filled first-seen time and could
  never be used point-in-time.
- Announcement attachments, XBRL and content: A12 archives the files. A21 keeps the list row only.
- News feeds, RBI's press-release RSS included: A19.
- FBIL. RBI's own releases are the source the owner named. FBIL's site also limits commercial use
  (`research/data/global-cues/README.md:72`).

**Expected design.**
- **Rates (`fno/rates/`):**
  - A `RateSource` interface has two adapters:
    - `RbiTbillAuctionSource` reads RBI's press-release list page. It keeps only releases titled exactly "91-Day,
      182-Day and 364-Day T-Bill Auction Result: Cut-off", opens each new one, and parses the release date, the
      release number and the three YTMs.
    - `RbiCurrentRatesSource` reads RBI's home page "Current Rates" box for the Policy Repo Rate. It also reads the
      box's 91-day T-bill figure, but only to check it.
  - Each observation is one table row: `rate, value_date, value_pct, release_no, source_url, source_sha256,
    first_seen_at, provenance`.
    - `value_date` is the auction date, or the observation date for the repo rate. The home page gives no effective
      date, so the row says "as shown by RBI's home page".
    - `provenance` is `live`.
  - Every fetched page is written once to Drive's `data` area under O9: `rates/rbi/YYYY/MM/DD/HHMMSS_<name>.html`,
    with its receipt in the repository.
  - The table is written as O9 part files (`rates/YYYY/MM/<day>.<run_id>.csv`).
  - `RatesAsOf(cutoff)` returns each rate's latest value first seen at or before the cutoff, never a later one.
- **Announcements (`fno/announcements_live/`):**
  - An `AnnouncementSource` interface has one adapter, `NseAnnouncementsSource`. It calls A12's URL template
    (`fno/filings/sources.py:53`) with today's date in both fields: one GET per poll on a paced session with `PublicData`'s
    headers (`fno/providers/public.py`, imported). The GET has **a hard timeout of 5 s, connect plus read, and no retry
    or cookie warm-up inside the mark** (A16 owner's condition). `PublicData.nse_json` itself is not used, because its
    three tries and 20 s timeouts could hold A16's commit. A failed poll is simply retried at the next mark.
    `docs/DATA_SOURCES.md` keeps NSE calls outside A9b's retry policy, so the poller catches everything (`requests`
    errors, HTTP 403 or 429, a timeout, bad JSON) and turns it into a named failure.
  - **The seen set (judge 355 SF2).** Each run is a fresh process. Before its first poll of the day it loads today's
    rows from today's receipted part files, read through O9's verified Drive cache. If that load fails, the run stops
    with one alert and one O10 row (`kind` `seen_set_unreadable`) and polls nothing, so an item is never re-recorded
    with a later time. Within a run, the set is kept in memory and grows with each poll. The read-back happens once
    per run (A16's hourly fire), at its first in-window mark.
  - Each poll keeps every `seq_id` not in the seen set. A row is `seq_id, symbol, isin, desc, an_dt, exchdisstime,
    attachment_url, first_seen_at, run_id`. `first_seen_at` is the poll's request time. The first run that sees an
    item wins, and a later run never rewrites it.
  - Every poll also writes one poll-log row: `requested_at, mark, status (ok | failed), kind, items, new_items`. The
    staleness and episode rules read it.
  - The raw responses and the day's part files are stored under O9, as for the rates.
  - `AnnouncementsAsOf(day, cutoff)` gives F2 the items with `first_seen_at` at or before the cutoff. `exchdisstime`
    is shown beside the first-seen time, never used in its place.
- **The clock for announcements (judge 355 SF1).** GitHub's cron cannot deliver the window on this repository: about 3
  runs in 48 fifteen-minute slots (participant-oi-watch, judge 350), and morning runs 4 h 40 min to 5 h 01 min late
  (judge 351). The one process alive in the window is A16's 15-minute recorder: a Claude routine with hourly fires
  09:00-15:00 IST, each looping over its marks. On its first live day, 16 Oct 2026, it settled 23 of 26 marks with a
  running process. From 09:15 to 14:00 that was 17 of 20 marks (10:00 onwards; the first fire did not run, so
  09:15-09:45 are `missed`; `research/data/intraday/slots/2026/10/16/`) [strong evidence for one day].
  - **Design (agreed, 16 Oct 2026, with A16's owner 01VK88Lx and LM1's builder 012eM7Ti):** the poller plugs in
    behind A16's `MarkObserver` port (`fno/intraday/observer.py`, merged, judge 265 add. 1), as one member of A16's
    fan-out (below).
  - On each `after_mark` with mark 09:15-14:00 IST, the poller makes one poll, whatever the mark's status (NSE's list
    does not depend on Groww's quotes). A mark after 14:00 returns at once.
  - **Time budget per mark (A16 owner and LM1 builder's condition):** the GET's 5 s, then the Drive writes of that
    poll's raw response and its new rows, each with its own hard timeout, 10 s per mark in all. A write that does not
    finish is a named failure. Its items stay unrecorded and are recorded at the next poll with that later time: later
    than the true sighting, which is safe for a cutoff, never earlier.
  - **The fan-out is A16's:** `ObserverGroup(MarkObserver)` in `fno/intraday/observer.py`, built by A16's owner.
    Each member is isolated: a failing member never skips the next, and each failure line names the member's class.
    Members get the same `(day, mark, document, status)` and share nothing. A16's `wiring.py` becomes
    `observer=ObserverGroup(_observers())`; LM1 and A21 each add their own member in their own branch, LM1 first.
  - **Coverage is visible (A16 owner's condition):** the day's poll log lists the window's 20 marks (09:15-14:00),
    each `polled ok`, `polled failed (kind)` or `no poll (no mark)`. A gap shows as a gap, never as "no
    announcements".
  - **A day whose window had no successful poll:** at the first mark after 14:00 (any status), the poller writes one
    `missed_window` poll-log row and one O10 row, and posts one alert.
  - **No successful poll by 10:00:** at the first mark at or after 10:00, if today's poll log has no `ok` row, one
    alert and one O10 row (`kind` `no_poll_by_1000`).
  - **Said plainly:** if A16's routine does not run at all, A21's poller does not run either. Nothing in A21 then
    alerts during the day; A16's own heartbeat-silence check and O8's daily health check are the witnesses. A21 adds
    no host of its own; that would be an owner decision (judge 352 SF1's platform question).
  - The poll runs inside the recorder's process, before its commit. Its cost is at most the 10 s budget per mark; today's
    live calls took under 2 s [some evidence]. A16's snapshot is taken before any observer runs, so the marks' on-time
    measure is not touched (A16 owner).
  - **Network (Known limit):** the A16 routine's environment must allow `www.nseindia.com`. The owner set that
    environment's policy, so the first dry run inside the routine proves it, or names the refusal.
- **Failures (the owner's rule):** every failure posts one #fno-desk line and appends one O10 row
  (`research/ops/capture_errors.csv`, `job` `rates` or `announcements_live`, `kind` named).
  - **Rates (at most one alert per run, two runs a day):** a source not reachable or refused; a page whose expected
    field is missing, with the field named.
  - **Announcements, one alert per episode:** an episode starts at a failed poll whose previous poll-log row today was
    `ok` (or at the day's first poll), and ends at the next `ok` poll, which posts one "recovered" line. Failed polls
    inside an episode write poll-log rows and no new alert or O10 row.
  - **Stale (rates):** the latest T-bill auction release is more than 8 calendar days before today. The auctions are
    weekly, and a holiday moves one by a day.
  - **Stale (rates):** no successful home-page read in the last 48 hours. If neither of a day's runs starts, the next
    run that does start alerts.
  - **Stale (announcements):** at a mark inside the window, the latest `ok` poll is more than 60 minutes before the
    mark.
  - **Disagreement, with a grace rule (judge 355 SF3):** the home page's 91-day figure must equal the 91-day YTM of the
    newest release. When the newest release was first seen less than 24 hours ago, the release before it is accepted
    too. A figure that matches neither is one alert and one O10 row. RBI may update the home-page box later than it
    posts the release [reasoning only], and this keeps that lag from alerting every Wednesday.
  - **A repo-rate change** is posted as information (old value, new value, first-seen time) and recorded as a row. It
    is not a failure.
- **Schedules** (GitHub Actions, lane 1): `rates-daily.yml` at about 08:40 and 18:40 IST every day, added to O10's
  capture-watch list.
  - Lateness of up to about 5 hours (judge 351) only delays the first-seen time. That time is always the real fetch
    time, never the scheduled one.
  - The announcements poller has no workflow: it runs in A16's routine (above).
- Every file stays under 350 lines. Concrete classes are wired only in `fno/rates/wiring.py` and
  `fno/announcements_live/wiring.py`.

**Acceptance criteria.**
1. The T-bill parser reads the 14 Oct 2026 release (a committed copy as a test fixture): date 2026-10-14, release
   2026-2027/1325, 91-day YTM 5.7281, 182-day 6.2896, 364-day 6.4891.
2. The home-page parser reads Policy Repo Rate 5.50 and the 91-day figure 5.7281 from a committed copy.
3. A missing field, a changed title or a changed layout is refused with the field named, one alert and one O10 row.
   Nothing is written to the table. A refused or unreachable RBI page gives the same, one per run.
4. `RatesAsOf` never returns a value first seen after its cutoff. Planted rows: at the cutoff, one second before and
   one second after; no rows gives "no rate".
5. A second run on the same day adds no row for an unchanged release or rate. A changed repo rate adds one row and
   one information alert.
6. Rates staleness, boundaries included:
   - the last auction 8 days before today is clean, and 9 days stale (one alert, one O10 row);
   - the last home-page read 48 hours before the run is clean, and 48 hours plus 1 second stale;
   - no table at all (first run) is clean, not stale.
7. Disagreement and its grace rule:
   - home page equal to the newest release: clean;
   - equal only to the release before, with the newest first seen 23 h 59 min ago: clean;
   - the same, with the newest first seen 24 h ago: one alert;
   - matching neither: one alert and one O10 row.
8. Announcements first-seen across runs (judge 355 SF2):
   - run 1 polls, then a separate run 2 (a new process with only Drive's parts) polls an overlapping list; the shared
     `seq_id`s keep run 1's `first_seen_at` and only new items are added;
   - a seen set that cannot be read stops run 2 with one alert and one O10 row, and polls nothing.
9. `AnnouncementsAsOf(day, cutoff)` drops items first seen after the cutoff, even when their `exchdisstime` is
   earlier. At the cutoff: kept. One second after: dropped. No rows: an empty list.
10. The window and the clock:
    - marks 09:15 and 14:00 poll;
    - mark 14:15 does not poll, and on a day with no `ok` poll it writes one `missed_window` row and one alert;
    - a first `ok` poll at 10:00 is clean, while no `ok` poll by the 10:00 mark gives one `no_poll_by_1000` alert;
    - the last `ok` poll 60 minutes before a mark is clean, and 60 minutes plus 1 second is stale.
11. Episodes and isolation:
    - three failed polls in a row (a 403, a 429, a timeout) give one alert, one O10 row and three poll-log rows, and
      the next `ok` poll posts one "recovered" line;
    - a fake source that sleeps past 5 s gives the named timeout failure within the budget, and A16's commit still
      runs;
    - a planted exception in A21's member leaves LM1's member called and the recorder's rows and commit untouched;
    - the day's coverage lists all 20 window marks, with a `no poll (no mark)` line for each mark A16 did not reach.
12. A closed day (A7) makes no announcements request and writes "not a trading day".
13. Every page and response is stored once in Drive under O9 with its receipt. No data file is committed to the
    repository.
14. `rates-daily.yml` is in O10's capture-watch list (its own test passes), posts one #fno-desk line on failure, and
    uses only `FNO_SLACK_BOT_TOKEN`.
15. Nothing in A12, A19, G13, S6, C2 or C4 changes; their tests pass untouched. A16 changes only by A16's own fan-out and
    A21's one member line in its wiring.

**Gap list (quality rule 2).**

| Requirement (source) | Where |
|---|---|
| Data up to date (owner, 16 Oct) | Criteria 6 and 10 (staleness, missed window, no poll by 10:00) |
| Every failure alerts and is recorded (owner, 16 Oct) | Criteria 3, 6, 7, 8, 10, 11 and 14: each failure gives one alert and one O10 row |
| Daily 91-day T-bill yield, dated, with first-seen time (orchestrator's brief) | Criteria 1, 4, 5 |
| Policy repo rate, dated, with first-seen time (orchestrator's brief) | Criteria 2, 4, 5 |
| Official RBI or FBIL source (brief) | RBI pages: criteria 1-2. FBIL is out (commercial-use limit, Out list) |
| "The latest 91-day T-bill yield from RBI's published auction result" (PROTOCOL.md S6 row) | Criterion 1 reads the auction release itself, never the home page alone; criterion 7 cross-checks |
| G13 replaces the 6.5% config rate (brief) | Out: G13's own switch (`method_version`). `RatesAsOf` (criterion 4) is what it reads |
| S6's cash benchmark (brief) | Out: S1's owner sets it at the freeze. `RatesAsOf` (criterion 4) gives the value |
| A12 filings gain a first-seen time and a same-day poll before 14:00 (brief) | Criteria 8-10 |
| F2: "first-seen time ... never a content date" (F2's text) | Criterion 9 |
| Agree with A12's owner; A19 leaves the gap to A12 | Settled below (orchestrator, A19's owner); criterion 15 |
| Failures in O10's record (brief) | Criteria 3, 6-8, 10, 11, 14 |
| Storage under O9's Drive rule (brief; CLAUDE.md) | Criteria 8 (seen set through the Drive cache) and 13 |
| NSE callers catch everything (`docs/DATA_SOURCES.md`); bounded time inside A16's mark (A16 owner, LM1 builder) | Criterion 11 |
| A gap in coverage is visible (A16 owner) | Criterion 11 (coverage list) |
| A16's routine may not allow NSE's host (A16 owner) | Known limit; the first dry run in the routine proves it |
| F&O output only to #fno-desk with `FNO_SLACK_BOT_TOKEN` (CLAUDE.md) | Criterion 14 |
| No real orders (CLAUDE.md) | No order path is touched; criterion 15 |
| Quality rules 5, 6, 8 (boundaries, real sample, live run) | Criteria 4, 6, 7, 9, 10 (boundaries); the test plan and claims (sample and live run) |

**Test plan.**
- Committed fixture copies of the two RBI pages and one NSE response, with fakes for the HTTP session, Drive, the
  clock and the alert sender.
- Each criterion gets a positive, a negative, a boundary and an empty case, as listed above.
- Criterion 8 uses two separate run objects that share only a fake Drive.
- Each criterion's code is broken on purpose once, and its test must fail (quality rule 4).
- Claims file:
  - a real output sample: today's table rows from a dry run against the live pages, and one announcements poll's
    rows for one stock, redacted to symbol, time and type;
  - a first live run of each part, with its command and result (quality rules 6 and 8).

**Judge verifies (judge F).** Runs the parsers on that day's live pages and compares them with the claims. Plants a
layout change, a stale week and a late home page. Runs two separate poll runs. Checks that `RatesAsOf` and
`AnnouncementsAsOf` never look ahead, and that no A12 file or consumer default changed.

**Settled before code:**
- A12 has no active owner (its builder session has ended). The orchestrator agreed the boundary (16 Oct 2026): A21
  adds a new package, `fno/announcements_live/`, imports only A12's URL template and changes no A12 file.
- O10's `CaptureErrorLog` is not on `main` yet: O10 part 1 is being fixed after judge F's review. A21's code is built
  against its branch's interface and rebased onto `main` once O10 lands (orchestrator, 16 Oct 2026).
- A19's owner confirmed no overlap (16 Oct 2026). A19 stores RBI press-release headlines through the RSS feed, and
  A21 stores parsed yields from the HTML list. Reading RBI through A19 would turn any A19 outage into an A21 failure.
  A19 never fetches NSE announcements. A12's next-day day file still keeps the whole day with `exchdisstime`; A21 adds
  only the same-day copy with first-seen times.

**Depends:** O9 step 1 (done), O10 (in progress), A7 (done), A12 (done), A16's mark observer port (done) and A16's `ObserverGroup` (A16's owner builds it after the orchestrator's go). **Size:** M (two rounds: rates, then
announcements).
