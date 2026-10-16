# A19. News and announcements, captured with their true first-seen time

**Repository:** trading · **Lane:** 1 (new story; outside services: news feeds, Drive, Slack; a GitHub workflow) ·
**Branch:** `story/a19-news-capture` · **Claims file:** `reviews/claude/response_265_a19-news-capture.md` (number given
by the orchestrator) · **Builder:** session_01Qj3wtYynDoNxVxFcqvZD9b · **Orchestrator:** session_01VG1RqxLFUVdvvPuMRYZtDH

**Description:** As the market research analyst, the macro economist and the devil's advocate, I want every market,
macro and Indian-company headline from a small set of allowed feeds stored with the moment we first saw it, so that
any later analysis, forecast or post-mortem uses only news that was really known before its cutoff.

**Context and why:**
- Gap audit (`docs/CORE_ENGINE_GAP_AUDIT.md`) Part A3 #1 and Part F #4: nothing captures news; the true first-seen
  time cannot be rebuilt later. Users: the AI team's analysts (F2, design `07_ai_team.md` 7.2), the devil's advocate
  (`fno/advocate`, T3), learning reviews (LR1, LR2).
- Owner, 16 Oct 2026 (`docs/DESK_DECISIONS.md`, last two rows): external data "must be up to date. That is
  non-negotiable"; "we must notify that something failed. Error case needs to be captured properly"; "I don't want
  any surprises. Every claim must be validated"; "do not over-engineer".
- Point in time: design 2.1 (`02_layers_data_forecast_weather.md`): the source's own time is kept apart from our
  `first_seen_at`; an input is used only if first seen before the cutoff.
- O9 (`docs/stories/O9-data-to-drive.md`): every data file is written once in Drive (`DataStore`), with its SHA-256
  receipt in `receipts/`; the repository holds no data file.

## Step 0: evidence (16 Oct 2026, 16:00-16:40 IST, read-only, from this cloud session)

**A12 already covers NSE corporate announcements.** `filings day-lists` (`fno/filings/sources.py:50-53`,
`runs_cli.py:155`) archives NSE's all-company announcement list (`api/corporate-announcements`) to Drive, one file
per day, up to yesterday. Each NSE row carries NSE's own dissemination time (`exchdisstime`), so its time is not lost
by a next-day archive. A19 does not fetch NSE announcements (no duplicate). The gap this leaves (no same-day copy
before a 14:30 cutoff) is A21's same-day copy (agreed with its builder, 16 Oct); listed under "Out".

**Candidate sources** (each fetched once; items, newest and oldest item; robots.txt and terms read on the site):

| Source (feed) | Items, span | Terms and robots | Verdict |
|---|---|---|---|
| Economic Times: Markets `markets/rssfeeds/1977021501.cms`, Economy `news/economy/rssfeeds/1373380680.cms` | 50 each; 7 h and 2 days | RSS terms (`/rss.cms`): "free service ... for personal, non-commercial use"; no "publish, distribute or otherwise disseminate"; copies only "for your individual/personal use". robots: only `rssarticleshow` disallowed | **In** (private Drive only) |
| Mint: Markets `rss/markets`, Economy `rss/economy` | 35 each; 10 h and 6 days | RSS terms (`/rss`): "within newsreaders for their personal, noncommercial use". robots: RSS allowed | **In** (private Drive only) |
| The Hindu BusinessLine: Markets, Economy (`<section>/feeder/default.rss`) | 60 each; 5 h and 3 h | "RSS feeds for personal and non-commercial use by the user". robots: allowed | **In** (private Drive only) |
| RBI press releases `pressreleases_rss.xml` | 10; 1.2 days; time without zone (IST) | Official, public | **In** |
| SEBI `sebirss.xml` | 30; date only (`16 Oct, 2026 +0530`); 24 recovery proceedings, 3 orders, 2 press releases, 1 circular | Official, public; robots allows all | **In**, except items under `/legal/circulars/` (A20b's; never stored twice) |
| NSE circulars `nsearchives.nseindia.com/content/RSS/Circulars.xml` | 40; date only | NSE's own RSS page offers it | **Out**: A20b owns NSE and SEBI circulars (NSE's JSON API, full metadata; orchestrator, 16 Oct) |
| Moneycontrol `rss/latestnews.xml`, `rss/marketreports.xml` | newest item **23 Apr 2024** | | **Out**: the feed is dead (the stale check below must catch such a feed) |
| Business Standard `rss/markets-106.rss` | 35; 18 h | No RSS terms found on its RSS page | **Out** until its terms are found |
| Google News RSS search | 100 | robots.txt disallows `/rss` for every agent | **Out** |
| PIB RSS | redirect, 0 items | | **Out** |
| Paid wires (Reuters, Bloomberg) | | paid | **Out** (no paid source without the owner) |
| The stock tool's news (market-brief) | | read-only for us; written by an AI routine, so its time is that routine's | **Out** (not a primary source) |

**Terms consequence:** the repository is public, so headlines, summaries and links never enter it, Slack or any
dashboard page. They live only in the owner's private Drive; the repository gets SHA-256 receipts (O9) and failure
records that name the feed, never an item. Article bodies are never fetched (that is scraping beyond the feed).
**Owner's answer (16 Oct 2026, `docs/DESK_DECISIONS.md` row "News: ET, Mint and BusinessLine RSS headlines are
captured for the owner's personal research use, in private Drive only"):** yes, for personal research; headlines,
links and times in private Drive only; article bodies never fetched; never in the repository, Slack or dashboards.
The publisher feeds stay switchable off in config (`news.publisher_feeds: false`), leaving the official feeds (RBI,
SEBI).

**GitHub's schedule is not reliable here** [strong]: `participant-oi-watch.yml` has 28 cron slots a day, yet only 3
scheduled runs exist in total (14-15 Oct, GitHub's run list); the audit found other crons starting 4-5 h late. A cron
every 5 minutes would therefore give first-seen times off by hours. Design answer below: one long run polls in a loop
and starts its successor itself.

**GitHub's own terms (judge 352 SF1)** [some: quoted; how they apply is reasoning only]: GitHub's Additional Product
Terms, "Actions", say Actions should not be used for activity that places a disproportionate burden on its servers
("for example, don't use Actions as a content delivery network or as part of a serverless application"), nor, on
GitHub-hosted runners, for "any other activity unrelated to the production, testing, deployment, or publication of
the software project"; sanctions include disabling the repository, which would stop every capture job, not only
news. A day-long poller is the clearest case in this repository (filings-archive's 355-minute runs every 6 h lean
the same way). **Owner's answer (16 Oct 2026, `docs/DESK_DECISIONS.md` row "News poller runs on GitHub only 07:00-23:00 IST"):**
poll on GitHub 07:00-23:00 IST only (`news.active_window`), a third less load than 24/7; an item published overnight
is first seen about 07:00, still before the 09:15 open and every cutoff, and its `previous_poll_at` shows the honest
window. Options declined: 24/7 on GitHub, a poller off GitHub, session hours only.

## Scope

**In:**
1. `NewsSource` port (`fetch() -> FeedFetch`: status, answer bytes, the server's `Date` header, our request and
   response times) with one adapter, `RssFeedSource`, over `fno/http_pacing.py` (at most one request a second per
   host), sending `If-None-Match`/`If-Modified-Since` so an unchanged feed costs one short answer.
2. Feed list in `config.yaml` (`news.feeds`: id, publisher, kind `publisher` or `official`, url, time format, the two
   stale limits of scope 8, optional excluded URL paths), validated by `fno/config.py`; `news.publisher_feeds` (true
   or false) switches every `publisher` feed off at once, leaving the official ones; `news.active_window` (IST start
   and end; 07:00-23:00, the owner's SF1 answer). Time formats are a strategy (`PublishedTimeFormat`): RFC 822, RBI's no-zone IST
   and SEBI's `16 Oct, 2026 +0530`; each states its precision (`second` or `day`).
3. Parser: RSS 2.0 items to `NewsItem` (title, link, feed's own summary as plain text, published time as given and
   parsed, precision). An answer that is a web page, not XML, has no items or cannot be parsed is a failure.
4. **Records: one part per 15-minute flush, always written** (also when nothing is new: it carries the heartbeat),
   through O9's `DataStore` to Drive `data/news/parts/YYYY/MM/DD/<run_id>-<n>.jsonl`, with its receipt. Two line
   kinds:
   - `poll` (the heartbeat, one per poll, no item text): poll time, and per feed its outcome (`new`, `nothing_new`,
     `not_modified`, `failed:<kind>`), items listed and items new;
   - `item`: `item_id` (SHA-256 of the canonical URL), `version` (SHA-256 of title, summary and published time),
     `publisher`, `feed`, `url`, `title`, `summary`, `published_raw`, `published_at` (UTC ISO or null),
     `published_precision`, `first_seen_at` (the poll's response time, our clock, UTC with offset),
     `previous_poll_at` (that feed's last successful poll from the heartbeat: the true first sighting lies between
     the two), `server_date`, `clock_skew_s`, `run_id`, `same_headline_as` (an earlier item's id or null), and two
     honesty flags: `bootstrap` (stored by the first run ever: first seen at capture start, not at publication) and
     `beyond_window` (scope 6).
5. Dedup: the same canonical URL (lower-case host, no fragment, no `utm_*` or known tracking parameters; other query
   parameters kept: RBI's `?prid=` is the id) is one item, however many feeds list it; a changed title, summary or
   published time of a known item is a new version row, never an overwrite (A11's rule). The same normalised
   headline (case-folded, punctuation and spaces collapsed) from another publisher within 24 h is kept as its own
   item with `same_headline_as` set (both first-seen times matter; no fuzzy merging).
6. **The poller and its memory.** `python -m fno news run` polls every feed every 5 minutes while inside
   `news.active_window`, until 340 minutes or the window's end, whichever is first. The seen set lives in memory and
   in a **seen snapshot**, `data/news/seen/YYYY/MM/DD/<run_id>-<n>.json` (item ids, versions, headline keys of the
   last 24 h, each feed's last successful poll and last new item, for the last **14 days**), written every 2 hours
   and at exit. A run starts from the newest receipted snapshot plus the receipted parts after it (through O9's
   `DriveCache`). 14 days is about 2.5 times the longest span measured in step 0 (Mint Economy, 5.7 days; judge 352
   re-measured it). Loud check: an unseen item published more than 13 days ago is stored with `beyond_window: true`
   and starts a `beyond_window` episode (the feed now reaches past our memory: the window must grow). With no news
   receipts at all, the run is the first ever and marks its items `bootstrap`; with receipts but no readable
   snapshot or part, the run stops with a `seen_set_load` failure instead of storing known items again with false
   times. Receipts are committed with every flush and at exit (also after an exception) through O9's committer
   (`build_receipt_committer`).
7. **Schedule** (judge 352 SF2):
   - `.github/workflows/news-capture.yml`: `concurrency: news-capture` (never two pollers); probe, then the loop;
     at its end, if the loop ran at least 10 minutes and the window is still open, it dispatches its successor
     (`workflow_dispatch` with `GITHUB_TOKEN`, `actions: write`). The loop ends before the job's `timeout-minutes:
     355`, so this step runs.
   - `.github/workflows/news-capture-kick.yml`: the only other starter, triggered by six crons spread over the
     window and by `workflow_run` (news-capture, `completed`). It dispatches news-capture only when the window is
     open **and no news-capture run is queued or in progress** (GitHub's run list), so a cron never queues behind a
     live poller and is never cancelled. After a completed run it acts only on a non-success one: if that run lasted
     at least 10 minutes it dispatches a restart; if it ended sooner (a failure at start: probe, install, Drive,
     credentials) it dispatches nothing, writes one `restart_stopped` row and alerts once, and the crons retry later
     (at most six short runs a day; O10 builder's caution). A run **cancelled by GitHub before any step ran**
     (superseded in the concurrency queue: it never polled) is ignored by the kick and counted as replaced, not
     failed, by O10's watcher (agreed with the O10 builder).
   - Whether a `workflow_run`-started dispatch counts toward GitHub's three-level `workflow_run` chain limit is not
     verified [reasoning only]; the self-dispatch path does not use `workflow_run`, and the crons restart a broken
     chain either way.
   - Both workflows are in `capture-watch.yml`'s list. `python -m fno news probe` prints per feed only its status,
     size, item count and newest item time (run logs are public), never a title or link.
8. Failures (each episode one O10 row and one alert; scope 9):
   - per feed: no answer or HTTP error after the pacer's tries, a web page or unparseable answer, no items, every
     item without a parseable time, `beyond_window`, and **stale** (judge 352 SF5): no new item or version from the
     feed for longer than its limits, counted two ways at once: **session hours** (time inside 09:00-18:00 IST on NSE
     session days, from A7's calendar) beyond `stale_session_hours`, or **all hours** beyond `stale_any_hours`. A
     Sunday, a holiday or a night adds no session hours, so a quiet weekend never trips the session limit and Monday
     09:15 is not "stale" from Sunday's silence. Starting values (all-hours limits at least ten times each feed's mean gap
     between items in step 0; session-hour limits a tighter guess, reasoning only): ET, Mint and BusinessLine Markets 3 session h / 24 h; ET and
     BusinessLine Economy 6 / 36; Mint Economy 24 / 72; RBI 24 / 96; SEBI 24 / 120. After 10 sessions of capture,
     `python -m fno news quiet-spells` reports each feed's longest gap between new items by day type (session day
     inside hours, session night, closed day) from the stored parts, and the limits are reset to 1.5 times the
     measured longest gap in a follow-up config change (lane 1), the evidence cited beside each value;
   - per run: Drive write failed, receipt commit failed, `seen_set_load`, clock skew over 5 s against the feed's
     `Date` header (as A16's clock rule), the successor dispatch failed;
   - **coverage gap** (judge 352 SF4): at start, the time from the last heartbeat poll to now, counting only time
     inside `news.active_window`; above 15 minutes, one gap record with its start and end (items first seen after it
     are late by up to that gap; `previous_poll_at` shows it per item). A quiet hour has heartbeats, so it is never a
     gap.
9. Episodes, records and alerts: an episode alert goes once when a feed or step turns failing and once when it
   recovers (never every 5 minutes). Alert text names the feed, kind and since-when, never an item. Records use
   O10's committed capture-error log (`research/ops/capture_errors.csv`, `fno/health/capture_errors.CaptureErrorLog`;
   one format; orchestrator, 16 Oct): one row when an episode starts (`job` news-capture, `step` the feed or run
   step, `kind`, a one-line message from names only, the run's URL) and one `<kind>_recovered` row when it ends,
   naming its length and failed polls; `git add research/ops/capture_errors.csv` by name with the next flush. **The
   episode state is the log itself** (judge 352 minor 2): at start a run reads the open episodes (an opening row with
   no later `_recovered` row for the same step and kind) and neither re-records nor re-alerts them. Alerts go through
   `AlertSender`; `alert NOT sent` is printed and named in the row's message.
10. Reader for consumers and checks: `python -m fno news list --until <IST time> [--since ...]` prints the items
    (from receipted parts through the cache) whose `first_seen_at` is at or before the cutoff, each item's latest
    version first seen by then. Point-in-time is enforced in the reader, not left to callers. It prints item text to
    the terminal of whoever runs it; no workflow runs it.
11. Composition root `fno/news/wiring.py`; constants in `fno/constants.py`; owner checklist lines (the workflow needs
    the four Drive settings and `FNO_SLACK_BOT_TOKEN` already in the repository's secrets).

**Out (with reason):**
- NSE corporate announcements (A12 has them with NSE's own time); the same-day copy is A21's (agreed with its
  builder, 16 Oct).
- NSE and SEBI circulars (A20b), and SEBI RSS items under `/legal/circulars/`. RBI's T-bill numbers (A21 reads them
  itself, agreed).
- Article bodies (terms; scraping), paid sources (owner approval), non-English feeds, social media.
- Reading or classifying news (relevance, sentiment, company tagging): the analysts' (F2) job, on top of the reader.
- The economic calendar (A20c).
- A watchdog that alerts within minutes when no run is alive: GitHub's cron cannot carry it (step 0). The kick
  workflow restarts killed runs by event; O10's watcher records them; O8's daily check gets a row "newest news
  receipt not older than 30 minutes" (O10 builder proposes it to O8's owner); the coverage-gap row records every gap
  when the next run starts.
- Any UI or UI-facing API.

## Acceptance criteria

1. **Sources behind a port.** `NewsSource` and `RssFeedSource`; adding a feed is one config entry, adding a new kind
   of source is one class plus one line in `fno/news/wiring.py`. Conditional GET: an answer `304` counts as a
   successful poll with nothing new.
2. **Parsing and times.** Each of the three time formats parses its step-0 sample to the right UTC time and precision;
   a date-only time keeps `day` precision (never invented as midnight-exact); an item whose time cannot be read is
   kept with `published_at` null. Web page, empty feed, broken XML and zero items each give their named failure.
3. **Record fields.** Every stored item has the fields of scope 4; `first_seen_at` is the poll's response time from
   an injected clock; `previous_poll_at` comes from the heartbeat and is null only for a feed's first poll ever.
4. **Dedup and versions.** Same canonical URL across two feeds and across polls: one item; tracking parameters
   ignored, RBI's `prid` kept; a changed title gives a second version row and keeps the first; the same headline from
   another publisher sets `same_headline_as`; at 24 h exactly and just over, the link is set and not set.
5. **Write-once storage, nothing public.** Parts and snapshots go only through `DataStore` (Drive then receipt);
   nothing of an item is written to the repository, Slack or the printed lines of `news run` and `news probe` (a test
   greps the repository's changed files and the printed lines of a fixture run for a fixture headline and URL).
   Every flush writes one part, with heartbeats even when nothing is new.
6. **Memory across restarts** (SF3). Across a restart through snapshot plus later parts: an item first seen 2 days
   plus 1 minute ago, and one first seen 9 days ago, still listed by the feed, are not stored again; an unseen item
   published 13 days ago is not flagged, 13 days plus 1 minute is flagged `beyond_window` with one episode; no news
   receipts gives `bootstrap` items; receipts with an unreadable snapshot stop the run with `seen_set_load` and store
   nothing.
7. **Continuous run.** Polls every 5 minutes inside the window and none outside it; stops at 340 minutes or at the
   window's end; flushes (part, receipts, O10 rows) every 15 minutes and at exit, also after an exception.
8. **Failures recorded and alerted, once.** Each failure kind of scope 8 starts an episode: one O10 row and one
   alert; repeats add none; recovery adds one `_recovered` row and one alert; a restart with an open episode in the
   log adds no row and no alert (minor 2); `alert NOT sent` is printed and named.
9. **Stale by calendar** (SF5). For a markets feed (3 / 24) and an official feed: a session afternoon at, just under
   and just over 3 session hours; a session night (no session hours added); a Sunday and an NSE holiday (A7 fixture
   calendar) silent for 20 h (no stale), then 24 h exactly (no) and 24 h plus 1 minute (stale); Monday 09:15 after a
   silent weekend (not stale). `news quiet-spells` on fixture parts gives each feed's longest gap per day type.
10. **Coverage gap** (SF4). A quiet hour with heartbeats but no items: no gap. A start 15 minutes after the last
    heartbeat: no gap; 15 minutes plus 1 second: one gap row and one alert. A start at 07:00 after a last poll at
    22:55 with the window 07:00-23:00: no gap.
11. **Clock.** Skew over 5 s against the feed's `Date` header is recorded on the item and as a failure record; 5 s
    exactly is not.
12. **Reader is point in time.** `news list --until T` returns no item first seen after T and shows each item's
    latest version first seen by T (planted later version and later item).
13. **Workflows** (SF2). `news-capture.yml`: the concurrency group, the probe, the loop, the successor dispatch (only
    after at least 10 minutes and inside the window), `permissions` limited to `contents: write` and `actions:
    write`, secrets only through `env`, a failed job alerting #fno-desk as A12's workflow does. The kick's decision is
    a tested function: the planted sequence "poller running, cron fires, poller ends and dispatches" gives no
    dispatch from the cron and no row or alert; a run cancelled before any step: ignored; a failed run of 10 minutes
    exactly: restart; 9 minutes 59 seconds: `restart_stopped` row and one alert; outside the window: nothing.
14. **Polite and allowed.** At most one request a second per host (pacer test); each run reads each feed at most once
    per 5-minute poll; the feed list holds only the step-0 "In" feeds (a test pins it against this story's table);
    with `news.publisher_feeds: false` only RBI and SEBI are read; SEBI items under `/legal/circulars/` are never
    stored.
15. **Real run before the judge.** One `news run` of 20 minutes on the real feeds and Drive from this session (or a
    `workflow_dispatch` on the branch): the claims file shows counts per feed, parts, snapshot and receipts written,
    one deliberate failure (a planted bad URL in a dry-run config) recorded and alerted, never an item's text.

## Test plan

Offline only, fixtures from step 0's real answers (trimmed, headlines replaced by neutral text so no publisher text
enters the public repository): a fake `NewsSource`, a fake Drive (`RawFileStore` in memory), a fake clock, a fake
`AlertSender`, a fixture NSE calendar and a fake GitHub run list for the kick. Every criterion has a good case, a bad
case, the boundary (at, just under, just over each limit: 5 s skew, 15-minute gap, 24 h headline link, 13-day window,
10-minute restart rule, both stale limits) and the empty case (no feeds configured, an empty feed, no earlier parts).
Gates: the full suite, ruff, ruff format, `tools/check_imports.py`, `tools/check_records.py`; no file or class over
350 lines. Builder self-review agents (correctness, silent failures) and one deliberate break per criterion, shown in
the claims file.

## Gap list (design requirements to criteria)

| Requirement | Where |
|---|---|
| Headline, source, URL, published time, first-seen time, hash (orchestrator's brief) | scope 4; criteria 2, 3 |
| Source time apart from our `first_seen_at` (design 2.1) | scope 4; criterion 3 |
| Use only inputs first seen before the cutoff (design 2.1) | criterion 12 |
| Revisions kept as versions, never overwritten (A11) | criterion 4 |
| Dedup across sources, and across restarts | criteria 4, 6 |
| Behind an interface with a composition root (CLAUDE.md "Design for change") | criterion 1 |
| Data write-once in Drive with receipts; no data file in the repository (O9) | criterion 5 |
| Raw bodies only if terms allow | Out (not allowed; step 0) |
| Up to date, every failure alerted and recorded, no false alerts (owner, 16 Oct) | criteria 7, 8, 10, 13 |
| Stale feed detected, by the NSE calendar | criterion 9 |
| Schedule frequent enough in market hours, justified | scope 6-7 (5-minute polls in the window; step 0's cron evidence); criteria 7, 13 |
| News sites' terms and robots; official or RSS; no paid source | step 0 table; criterion 14; owner's answer |
| GitHub's Actions terms (judge 352 SF1) | step 0; owner's answer (07:00-23:00 IST); `news.active_window`; criteria 7, 13 |
| No duplicate of A12, A20 or A21 | step 0; Out; criterion 14 |
| Publisher feeds switchable off (owner's answer, 16 Oct) | scope 2; criterion 14 |
| Errors in O10's one format, episode state kept there (orchestrator; judge 352 minor 2) | scope 9; criterion 8 |
| Clock contract (A16 4.4: skew over 5 s flagged) | criterion 11 |
| Public run logs carry no item text (judge 352 minor 1) | scope 7; criterion 5 |
| Tests offline with fixtures | test plan |
| Real output sample (quality rule 6) | criterion 15 |
| Silence when no run is alive | scope 7 kick by event; criterion 13; Out: a minutes-level watchdog (O10/O8 backstop) |

## Judge verifies

Re-fetches two feeds and checks parsed times against the raw `pubDate`; plants a duplicate URL with tracking
parameters, a revised title, a 9-day-old known item across a restart, a stale feed on a session afternoon and a
silent Sunday, a web-page answer, a quiet hour, a 16-minute gap, a 6 s skew and the cron-behind-a-live-poller
sequence; checks that no headline or URL reaches the repository, Slack or logs; reads both workflows' permissions
and chain; checks one real part in Drive against its receipt.

**Depends:** O9 step 1 (merged), A9 pacer, A7 calendar, `AlertSender`; O10 part 1's `CaptureErrorLog`, after O10
part 1 passes its re-judge and merges (judge 352 minor 3) · **Size:** M · **Status:** story text, revised after
judge 352 (FAIL, 5 should fix, 3 minor); SF1 answered by the owner
