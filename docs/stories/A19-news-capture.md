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
before a 14:30 cutoff) is A12's to close when a consumer needs it; listed under "Out".

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
**Owner question (via the orchestrator):** is the owner's private research use, stored in their own Drive and never
published, "personal, non-commercial use" under these three publishers' RSS terms? Builder's recommendation: yes
(reasoning only; not legal advice). If no, the publisher feeds are switched off in config (`news.publisher_feeds: false`) and A19 runs on the official
feeds only (RBI, SEBI); the code is the same either way (orchestrator, 16 Oct).

**GitHub's schedule is not reliable here** [strong]: `participant-oi-watch.yml` has 28 cron slots a day, yet only 3
scheduled runs exist in total (14-15 Oct, GitHub's run list); the audit found other crons starting 4-5 h late. A cron
every 5 minutes would therefore give first-seen times off by hours. Design answer below: one long run polls in a loop
and starts its successor itself.

## Scope

**In:**
1. `NewsSource` port (`fetch() -> FeedFetch`: status, answer bytes, the server's `Date` header, our request and
   response times) with one adapter, `RssFeedSource`, over `fno/http_pacing.py` (at most one request a second per
   host), sending `If-None-Match`/`If-Modified-Since` so an unchanged feed costs one short answer.
2. Feed list in `config.yaml` (`news.feeds`: id, publisher, kind `publisher` or `official`, url, time format,
   `max_age_hours`, optional excluded URL paths), validated by `fno/config.py`; `news.publisher_feeds` (true or
   false) switches every `publisher` feed off at once, leaving the official ones. Time formats are a strategy (`PublishedTimeFormat`): RFC 822, RBI's no-zone IST and SEBI's
   `16 Oct, 2026 +0530`; each states its precision (`second` or `day`).
3. Parser: RSS 2.0 items to `NewsItem` (title, link, feed's own summary as plain text, published time as given and
   parsed, precision). An answer that is a web page, not XML, has no items or cannot be parsed is a failure.
4. Records: one JSON Lines part per poll that found something new, written through O9's `DataStore` to Drive
   `data/news/items/YYYY/MM/DD/<run_id>-<poll>.jsonl`, with its receipt. Fields: `item_id` (SHA-256 of the canonical
   URL), `version` (SHA-256 of title, summary and published time), `publisher`, `feed`, `url`, `title`, `summary`,
   `published_raw`, `published_at` (UTC ISO or null), `published_precision`, `first_seen_at` (our clock, UTC with
   offset), `previous_poll_at` (that feed's last successful poll: the true first sighting lies between the two),
   `server_date`, `clock_skew_s`, `run_id`, `same_headline_as` (an earlier item's id or null).
5. Dedup: the same canonical URL (lower-case host, no fragment, no `utm_*` or known tracking parameters; other query
   parameters kept: RBI's `?prid=` is the id) is one item, however many feeds list it; a changed title, summary or
   published time of a known item is a new version row, never an overwrite (A11's rule). The same normalised
   headline (case-folded, punctuation and spaces collapsed) from another publisher within 24 h is kept as its own
   item with `same_headline_as` set (both first-seen times matter; no fuzzy merging).
6. The poller: `python -m fno news run --max-minutes 340` polls every feed every 5 minutes, keeps the seen set in
   memory (loaded at start from the last 2 IST days' receipted parts through O9's `DriveCache`), writes parts, and
   commits receipts at most every 15 minutes and at exit through O9's committer (`build_receipt_committer`).
7. Schedule: `.github/workflows/news-capture.yml`: `concurrency: news-capture` (never two pollers); at its end a
   run dispatches the next run of itself (`workflow_dispatch` with `GITHUB_TOKEN`, `actions: write`), so capture is
   continuous. The loop ends itself (`--max-minutes 340`) before the job's `timeout-minutes: 355`, so the dispatch
   step runs; a second small workflow `news-capture-restart.yml` (on `workflow_run` of news-capture, `completed`)
   dispatches news-capture again when a run ended cancelled, timed out or failed, so a killed run restarts the chain
   by event, not by GitHub's unreliable cron (dispatch is not `workflow_run` chaining, so GitHub's three-level limit
   does not apply; the concurrency group drops a surplus run). Crons at six spread minutes a day remain a last
   backstop. `python -m fno news probe` runs first
   and prints each feed's answer from the runner.
8. Failures (each is one record and, per episode, one alert):
   - per feed: no answer or HTTP error after the pacer's tries, a web page or unparseable answer, no items, every
     item without a parseable time, and **stale** (newest item older than its `max_age_hours`: publisher feeds 6 h,
     official feeds RBI 168, SEBI 168; starting values from step 0, all in config);
   - per run: Drive write failed, receipt commit failed, the seen set could not be loaded, clock skew over 5 s
     against the feed's `Date` header (as A16's clock rule), the successor dispatch failed;
   - **coverage gap**: at start, if the newest receipted part is older than 15 minutes, a gap record names its start
     and end (items first seen after it are late by up to that gap; `previous_poll_at` shows it per item).
   An episode alert goes once when a feed or step turns failing and once when it recovers (no alert every 5
   minutes). Alert text names the feed, kind and since-when, never an item. Records use O10's committed
   capture-error log (`research/ops/capture_errors.csv`, `fno/health/capture_errors.CaptureErrorLog`; one format,
   no second one; orchestrator, 16 Oct): one row when an episode starts (`job` news-capture, `step` the feed or
   run step, `kind`, a one-line message, the run's URL) and one row when it ends naming its length and failed
   polls, committed with the next receipt commit. Alerts go through `AlertSender`. The run's own failure (killed,
   timed out) is O10's watcher's, through `capture-watch.yml`.
9. Reader for consumers and checks: `python -m fno news list --until <IST time> [--since ...]` prints the items
   (from receipted parts through the cache) whose `first_seen_at` is at or before the cutoff, each item's latest
   version first seen by then. Point-in-time is enforced in the reader, not left to callers.
10. Composition root `fno/news/wiring.py`; constants in `fno/constants.py`; owner checklist lines (the workflow needs
    the four Drive settings and `FNO_SLACK_BOT_TOKEN` already in the repository's secrets).

**Out (with reason):**
- NSE corporate announcements (A12 has them with NSE's own time); a same-day NSE copy before 14:30 is A12's to add
  when a consumer asks.
- NSE and SEBI circulars (A20b), and SEBI RSS items under `/legal/circulars/`.
- Article bodies (terms; scraping), paid sources (owner approval), non-English feeds, social media.
- Reading or classifying news (relevance, sentiment, company tagging): the analysts' (F2) job, on top of the reader.
- The economic calendar (A20c).
- A watchdog that alerts within minutes when no run is alive: GitHub's cron cannot carry it (step 0). The restart
  workflow (scope 7) covers killed runs by event; O10's watcher records them (`capture-watch.yml` lists
  news-capture); O8's daily check gets a row "newest news receipt not older than X" (O10 builder proposes it to
  O8's owner); the coverage-gap row (scope 8) records every gap when the next run starts.
- Any UI or UI-facing API.

## Acceptance criteria

1. **Sources behind a port.** `NewsSource` and `RssFeedSource`; adding a feed is one config entry, adding a new kind
   of source is one class plus one line in `fno/news/wiring.py`. Conditional GET: an answer `304` counts as a
   successful poll with nothing new.
2. **Parsing and times.** Each of the three time formats parses its step-0 sample to the right UTC time and precision;
   a date-only time keeps `day` precision (never invented as midnight-exact); an item whose time cannot be read is
   kept with `published_at` null. Web page, empty feed, broken XML and zero items each give their named failure.
3. **Record fields.** Every stored item has the fields of scope 4; `first_seen_at` is the poll's response time from
   an injected clock; `previous_poll_at` is null only for a feed's first poll ever.
4. **Dedup and versions.** Same canonical URL across two feeds and across polls: one item; tracking parameters
   ignored, RBI's `prid` kept; a changed title gives a second version row and keeps the first; the same headline from
   another publisher sets `same_headline_as`; at 24 h exactly and just over, the link is set and not set.
5. **Write-once storage.** Parts go only through `DataStore` (Drive then receipt); nothing of an item is written to
   the repository, Slack or stdout beyond counts (a test greps the repository's changed files and the printed lines
   of a fixture run for a fixture headline and URL). A poll with nothing new writes no part.
6. **Continuous run.** The loop polls every 5 minutes until `--max-minutes`, commits receipts at most every 15
   minutes and at exit (also after an exception), and the seen set survives a restart (loaded from receipted parts):
   a restarted run does not store a known item again.
7. **Failures recorded and alerted.** Each failure kind of scope 8 starts an episode: one O10 row (job, step, kind,
   message, run URL) and one alert; repeats in the same episode add no row and no alert; recovery adds one row and
   one alert;
   `alert NOT sent` is recorded and printed. Stale: at, just under and just over `max_age_hours`.
8. **Coverage gap.** A start more than 15 minutes after the newest receipted part records one gap with its start and
   end and alerts once; at 15 minutes exactly no gap.
9. **Clock.** Skew over 5 s against the feed's `Date` header is recorded on the item and as a failure record; 5 s
   exactly is not.
10. **Reader is point in time.** `news list --until T` returns no item first seen after T and shows each item's
    latest version first seen by T (planted later version and later item).
11. **Workflow.** `news-capture.yml` has the concurrency group, the probe step, the loop step, the successor
    dispatch (`if: always()`, so a failed run still restarts the chain), the restart workflow (dispatches only on a
    non-success news-capture run; a test reads both files), crons as backup, `permissions` limited to
    `contents: write` and `actions: write`, secrets only through `env`; a failed job alerts #fno-desk as A12's
    workflow does.
12. **Polite and allowed.** At most one request a second per host (pacer test); each run reads each feed at most once
    per 5-minute poll; the feed list holds only the step-0 "In" feeds (a test pins it against this story's table); with
    `news.publisher_feeds: false` only RBI and SEBI are read; SEBI items under `/legal/circulars/` are never stored.
13. **Real run before the judge.** One `news run --max-minutes 20` on the real feeds and Drive from this session (or a
    `workflow_dispatch` on the branch): the claims file shows counts per feed, parts and receipts written, one
    deliberate failure (a planted bad URL in a dry-run config) recorded and alerted, never an item's text.

## Test plan

Offline only, fixtures from step 0's real answers (trimmed, headlines replaced by neutral text so no publisher text
enters the public repository): a fake `NewsSource`, a fake Drive (`RawFileStore` in memory), a fake clock and a fake
`AlertSender`. Every criterion has a good case, a bad case, the boundary (at, just under, just over each limit:
5 s skew, 15-minute gap, 24 h headline link, `max_age_hours`) and the empty case (no feeds configured, an empty feed,
no earlier parts). Gates: the full suite, ruff, ruff format, `tools/check_imports.py`, `tools/check_records.py`; no
file or class over 350 lines. Builder self-review agents (correctness, silent failures) and one deliberate break per
criterion, shown in the claims file.

## Gap list (design requirements to criteria)

| Requirement | Where |
|---|---|
| Headline, source, URL, published time, first-seen time, hash (orchestrator's brief) | scope 4; criteria 2, 3 |
| Source time apart from our `first_seen_at` (design 2.1) | scope 4; criterion 3 |
| Use only inputs first seen before the cutoff (design 2.1) | criterion 10 |
| Revisions kept as versions, never overwritten (A11) | criterion 4 |
| Dedup across sources | criterion 4 |
| Behind an interface with a composition root (CLAUDE.md "Design for change") | criterion 1 |
| Data write-once in Drive with receipts; no data file in the repository (O9) | criterion 5 |
| Raw bodies only if terms allow | Out (not allowed; step 0) |
| Up to date, every failure alerted and recorded (owner, 16 Oct) | criteria 6, 7, 8, 11 |
| Stale feed detected | criterion 7 |
| Schedule frequent enough in market hours, justified | scope 7 (5-minute polls, continuous; step 0's cron evidence); criterion 11 |
| Terms and robots respected; official or RSS; no paid source | step 0 table; criterion 12; owner question |
| No duplicate of A12 or A20 | step 0; Out; criterion 12 |
| Publisher feeds switchable off (orchestrator, pending the owner's terms answer) | scope 2; criterion 12 |
| Errors in O10's one format (orchestrator) | scope 8; criterion 7 |
| Clock contract (A16 4.4: skew over 5 s flagged) | criterion 9 |
| Tests offline with fixtures | test plan |
| Real output sample (quality rule 6) | criterion 13 |
| Silence when no run is alive | scope 7 restart by event; criterion 11; Out: a minutes-level watchdog (O10/O8 backstop) |

## Judge verifies

Re-fetches two feeds and checks parsed times against the raw `pubDate`; plants a duplicate URL with tracking
parameters, a revised title, a stale feed, a web-page answer, a 16-minute gap and a 6 s skew; checks that no headline
or URL reaches the repository, Slack or logs; reads the workflow's chain and permissions; checks one real part in
Drive against its receipt.

**Depends:** O9 step 1 (merged), A9 pacer, `AlertSender`, O10 part 1's `CaptureErrorLog` (3dc1675f, merged first) · **Size:** M ·
**Status:** story text for the judge
