# A21. Rates and same-day first-seen: RBI's T-bill and repo rates daily, NSE announcements before 14:00

**Repository:** trading · **Lane:** 1 (new story; outside services RBI and NSE; schedules) · **Judge:** F ·
**Response number:** 270 (reserved) · **Owner rule (16 Oct 2026):** data must be up to date, and every failure alerts
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
- **Part 2: same-day announcements (`fno/announcements_live/`, new).** A poll of NSE's day list every 15 minutes from
  09:00 to 14:00 IST on every NSE session. Each new `seq_id` becomes one row with the time we first saw it.
- Commands, a schedule for each part, checks, and a reader for each part's consumers.

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
  - An `AnnouncementSource` interface has one adapter, `NseAnnouncementsSource`. It uses A12's URL template with
    today's date in both fields.
  - Each poll keeps every `seq_id` not already recorded today. A row is `seq_id, symbol, isin, desc, an_dt,
    exchdisstime, attachment_url, first_seen_at, run_id`. `first_seen_at` is the poll's request time.
  - The first poll that sees an item wins. A later poll never rewrites it.
  - The raw responses and the day's part files are stored under O9, as for the rates.
  - `AnnouncementsAsOf(day, cutoff)` gives F2 the items with `first_seen_at` at or before the cutoff.
    `exchdisstime` is shown beside the first-seen time, never used in its place.
- **Failures (the owner's rule):** every failure posts one #fno-desk line and appends one O10 row
  (`research/ops/capture_errors.csv`, `job` `rates` or `announcements_live`, `kind` named). The failures:
  - a source not reachable, or refused (for example a 403 from NSE);
  - a page whose expected field is missing: the parser names the field;
  - **stale:** no new T-bill auction release within 8 calendar days of the last one (the auctions are weekly), or no
    successful announcements poll for 60 minutes inside the window on a session day;
  - **disagreement:** the home page's 91-day figure differs from the latest auction release's 91-day YTM;
  - **a repo-rate change** is posted as information (old value, new value, first-seen time) and recorded as a row; it
    is not a failure.
- **Schedules** (GitHub Actions, lane 1), each added to O10's capture-watch list:
  - `rates-daily.yml` at about 08:40 and 18:40 IST every day. The second run catches each Wednesday's auction results
    the same day.
  - `announcements-live.yml` every 15 minutes, 09:00-14:00 IST, on NSE sessions only (A7's calendar decides; a run on a
    closed day exits with "not a trading day").
  - GitHub's schedule is best effort and can start late (reasoning only). A late run is recorded as late: its
    first-seen time is the real fetch time, never the scheduled time, so lateness can cost coverage but never truth.
- Every file stays under 350 lines. Concrete classes are wired only in `fno/rates/wiring.py` and
  `fno/announcements_live/wiring.py`.

**Acceptance criteria.**
1. The T-bill parser reads the 14 Oct 2026 release (a committed copy as a test fixture): date 2026-10-14, release
   2026-2027/1325, 91-day YTM 5.7281, 182-day 6.2896, 364-day 6.4891.
2. The home-page parser reads Policy Repo Rate 5.50 and the 91-day figure 5.7281 from a committed copy.
3. A missing field, a changed title or a changed layout is refused with the field named, an alert and an O10 row.
   Nothing is written to the table.
4. `RatesAsOf` never returns a value first seen after its cutoff (planted rows on both sides).
5. A second run on the same day adds no row for an unchanged release or rate. A changed repo rate adds one row and
   one information alert.
6. Stale and disagreement checks: planted cases give exactly one alert and one O10 row each; a clean day gives none.
7. Announcements:
   - two polls with overlapping items keep the first poll's `first_seen_at` for the shared `seq_id`s;
   - `AnnouncementsAsOf(day, cutoff)` drops items first seen after the cutoff, even when their `exchdisstime` is
     earlier.
8. A closed day (A7) makes no announcements request and writes "not a trading day".
9. Every page and response is stored once in Drive under O9 with its receipt. No data file is committed to the
   repository.
10. Both workflows are in O10's capture-watch list (its own test passes), post one #fno-desk line on failure, and use
    only `FNO_SLACK_BOT_TOKEN`.
11. Nothing in A12, A19, G13, S6, C2 or C4 changes; their tests pass untouched.

**Test plan.** Committed fixture copies of the two RBI pages and one NSE response, with fakes for the HTTP session,
Drive, the clock and the alert sender. Each criterion gets a positive case, a negative case and an empty case:
- a release, a changed layout, no release in 8 days;
- an announcement poll, a refused poll, a closed day.

**Judge verifies (judge F).** Runs the parsers on today's live pages and compares them with the numbers above. Plants a
layout change and a stale week. Checks that `RatesAsOf` and `AnnouncementsAsOf` never look ahead, and that no A12 file
or consumer default changed.

**Open points (answers being sought before code):**
- A12 has no active owner (its builder session has ended). The orchestrator is asked to agree the boundary: a new
  package that imports A12's URL template and changes no A12 file.
- O10's `CaptureErrorLog` is not on `main` yet. A21's code waits for it, or is built on its branch.
- A19's owner confirmed no overlap (16 Oct 2026). A19 stores RBI press-release headlines through the RSS feed, and
  A21 stores parsed yields from the HTML list. Reading RBI through A19 would turn any A19 outage into an A21 failure.
  A19 never fetches NSE announcements. A12's next-day day file still keeps the whole day with `exchdisstime`; A21 adds
  only the same-day copy with first-seen times.

**Depends:** O9 step 1 (done), O10 (in progress), A7 (done), A12 (done). **Size:** M (two rounds: rates, then
announcements).
