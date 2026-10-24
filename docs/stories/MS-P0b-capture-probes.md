# MS-P0b. Market school capture probes (futures quotes and stock-option chains, Groww and NSE, at a study pace)

**Lane 1** (outside services: Groww, NSE, Drive, Slack; capture records). Not a money piece: it decides no trade, so
one code judge (judge named by the orchestrator). Builder: session_01KJLFK1oqfytQkHapDCHJh9; orchestrator:
session_01Mt6dcBU5kp2htdPN2KmiZH. Branch `story/ms-p0b-capture`. Text first; code only after the judge's PASS on this
text. Work register row "MS-P0b capture probes".

**Description:** As the data and backtesting engineer and the market-microstructure analyst, I want one small, slow,
read-only capture of near-month futures quotes and stock-option chains from Groww and from NSE for 5 sessions, so that
the owner can decide on measured facts (completeness, empty bid/ask share, refusals, latency, Drive writes, effect on
A16 and v4) whether the school's capture can grow (response 327 section 4, P0b: "5 clean sessions, then capture volume
grows within the terms").

## 1. The owner's decision, recorded as theirs

- **P0 probe 2** (`research/school/probes/2026-10-22-p0-2-terms-automated-reading.md`) found that NSE's Terms of Use
  ban "any systematic or automated data collection" with no personal-use or volume exception **[strong evidence: the
  clause]**, and that Groww's terms say API connectivity is "only" for automating buying and selling, which a
  read-only tool does not literally fit **[some evidence]**. It recommended no new NSE reads.
- **The owner decided otherwise on 25 Oct 2026** (DESK_DECISIONS, 25 Oct row, point 5), in their words: "fetch it,
  store it, and we fetch from Groww as well. It is a private research tool ... Just do not bombard it or overload it.
  Just read it as a study pace". This story runs on that decision. It is the owner's call on their own private
  research tool; the builder does not claim the terms allow it. Probe 2's finding stays on record unchanged, and the
  probe note of this story repeats it in one line.
- **What this story adds to honour the decision:** an explicit, tested pace (section 3), an honest User-Agent, a
  daily cap, a stop at the first sign of a block, and no attempt to get round one (no browser disguise, no rotating
  addresses, no second key, no proxy change).
- Futures **trading** is on hold (owner, same row, point 6). A futures **quote** capture is capture only and in scope.

## 2. What is captured (fixed list, never widened by this story)

| Kind | Instruments | Groww calls per slot | NSE calls per slot |
|---|---|---|---|
| Near-month futures | NIFTY, BANKNIFTY, RELIANCE, HDFCBANK, INFY, SBIN | 6 `get_quote` (carries ltp, bid, ask, depth) | 6 `/api/quote-derivative?symbol=` |
| Stock option chains, near month | RELIANCE, HDFCBANK, INFY, SBIN | 4 `get_option_chain` + 40 `get_quote` legs (ATM ±2 strikes, call and put: P0-1 found the chain has no bid or ask) | 4 `/api/option-chain-equities?symbol=` (bid and ask per strike) |
| Session start | | 6 `get_expiries` once a day | 1 page visit per slot (`/option-chain`, for the session cookie) |
| **Total** | | **50 a slot, 206 a day** | **11 a slot, 44 a day** |

- "Near month" is the first **listed** expiry on or after the session (Groww's `get_expiries`; NSE's own answer), never
  a computed date. The ATM strike is the listed strike nearest the future's ltp (from the same slot's future quote).
- The lot is A20a's dated lot (`fno/school/roads/lots.py`, `ArchivedLots`, read-only); a missing lot makes the row's
  quality `lot_unknown`, never a guessed lot.
- Groww is read only through A16's `ReadOnlyGroww` (`fno/intraday/read_only.py`), **unedited**: `get_quote`,
  `get_option_chain` and `get_expiries` are already on its allow-list; `get_ltp` is not and is not added.

## 3. The study pace (the owner's "do not bombard it")

One `StudyPace` per source, built in the composition root from named constants (a constants module of the package,
not `config.yaml`):

| Rule | Groww | NSE |
|---|---|---|
| Requests in flight | one at a time | one at a time |
| Minimum gap between request starts | 1.0 s (Groww's Live Data limit is 10 a second, 300 a minute: we stay at or under 60 a minute) | 3.0 s (three times the project's `SHARED_PACER` 1.0 s) |
| Daily cap (counted across reruns of the day) | 240 | 50 |
| HTTP 429 | the first 429 stops Groww for the day, no retry (orchestrator's Groww audit, 24 Oct: the owner's "never exceed its rate limit") | wait 60 s, retry that one request once; a second 429 the same day stops NSE for the day |
| Sign-in | one sign-in per run; a failed sign-in is kept and stops Groww for the run, never retried per call (audit: `GrowwProvider.api` retries on every call, `fno/providers/groww.py:139-145`, fixed globally by session_01GsPm29fZzfH3DiErKAdBVk) | none |
| HTTP 403, or an empty 200 body where JSON is expected | the source stops for the day at once, no retry | same |
| 5xx or timeout (20 s) | one retry after 30 s; then that row is `missing` and the slot goes on | same |
| A source stopped on 2 sessions | the probe stops for that source for good; the owner decides | same |
| User-Agent | the SDK's own (Groww's client, not ours to set) | `OmenixFnO-research/1.0 (personal, read-only, paced)`, fixed; never a browser string |

- The day's request count is kept in the day's counts file (section 5), so a rerun cannot pass the cap.
- A stop is one plain line, posted to #fno-desk (`FNO_SLACK_BOT_TOKEN`, through the existing `AlertSender`), and one
  O10 row in `research/ops/capture_errors.csv` (job `school-p0b`, kind `blocked`, `rate_limited` or `cap_reached`).
  The line names the source, the status and the slot; never a value, a header, a cookie or a token.
- Two sources never run at the same time: Groww's part of a slot, then NSE's.

## 4. When it runs (IST)

- Slots **10:07, 11:37, 13:07, 14:07**, on NSE trading days (A7 calendar). A slot that cannot start by slot + 2 min
  is skipped; a running slot stops hard at slot + 6 min (2 min before the next A16 mark), its unread rows `missing`.
- Clear of: A22 pre-open (08:36-09:12), A16's marks (:00, :15, :30, :45, about 45 s each), v4's capture (14:30-14:40),
  the 3 pm recorders (14:55-15:13), the 15:30 mark, A16b (from 15:33), A4h's close read.
- **Never on 26 Oct or an A16h probe day** (27 Oct, and 28 Oct if A16h slips): A16h's question 3 compares that day's
  429s with clean days, and P0b's Groww calls would spoil it. The days are a named constant; a later A16h day is a
  one-line lane-1 change agreed with its owner.
- **Run by hand** by the builder, one command per session started before 10:07; no stored schedule, no
  `DAILY_RUN_STEPS` row (question 2). 5 sessions, then it stops: a sixth session is refused unless the owner widens it.

## 5. Records (write-once, O9)

- Each source's raw answers of a slot: one gz JSON Lines file in Drive through O9's `DataStore`, area
  `school/p0b/<source>/<session>/`, one file per slot (8 a day; P0-3: far below Drive's limits). Its receipt goes to
  `receipts/`. No raw Groww or NSE answer enters the repository.
- Each captured row (response 327) carries: instrument, contract, expiry, dated lot, source time (the answer's own
  timestamp, or `none` when it has none), first-seen time (our receipt time, UTC), the raw answer's SHA-256, and a
  quality status (`ok`, `empty_bid_ask`, `one_sided`, `lot_unknown`, `missing`, `stale`).
- The counts file `research/school/probes/p0b/<session>.json` (counts and times only, no price): requests per source,
  refusals by status, rows by quality, latency median and 95th percentile per source and kind, Drive writes ok and
  failed, the stop line if any.
- The command commits and pushes only its own paths (`receipts/` rows of its area, the counts file, the O10 row):
  `git pull --no-rebase origin main`, then `git push origin HEAD:main`, record scan on, never `--no-verify`.
- Capture-only rows create no ticket, position or strategy claim and spend no registered outcome window (327).

## 6. Measured over 5 sessions (the probe note)

`research/school/probes/<date>-p0b-capture.md`, written by hand from the counts files, one row per session and source:
completeness (rows `ok` / rows asked), empty bid/ask share, 429s and blocks, latency, Drive writes, and the neighbour
check: that session's A16 ledger (429s, missing quotes, status per mark) and the v4 and A4 sidecars (`complete`) set
beside the two sessions before P0b started. Every figure labelled. The note ends with the decision asked of the owner:
grow, keep or stop, per source.

## 7. Acceptance criteria (each: code, a test that fails when the code is broken, good, bad, boundary, empty)

1. **Pace:** `StudyPace` never lets a request start sooner than the gap after the last start (fake clock: 1.0 s
   Groww, 3.0 s NSE; boundary exactly at the gap; a second caller waits; zero requests: no wait).
2. **Cap:** the 241st Groww and 51st NSE request of a day is refused before it is sent, with one named line; the
   count includes an earlier run's counts file (rerun boundary; empty file: count 0).
3. **Refusals:** on Groww the first 429 stops it for the day with nothing more sent; on NSE a 429 waits 60 s and
   retries once, and a second 429 that day stops it; any 403 or an empty 200 body stops the source for the day, sends one alert and writes one O10 row; nothing more reaches that source (fake source counts
   calls). A 5xx retries once after 30 s, then `missing`.
4. **Sign-in:** one run signs in to Groww at most once; a failed sign-in stops Groww's part of the run with one line
   and no second sign-in (fake provider counts sign-ins: good, failed, never-called on a day with no Groww slot left).
4b. **Stop for good:** a source stopped on 2 sessions is refused on the third, with its line.
5. **Times:** refuses a non-trading day, 26 Oct and each A16h day, a slot more than 2 min late, and a sixth session;
   a slot stops hard at slot + 6 min with its unread rows `missing`.
6. **Read-only:** the Groww source holds only `ReadOnlyGroww`; no module of the package names `GrowwAPI`
   (A16's import-closure test extended to `fno/school/probes/`). No module sends anything to NSE but GET.
7. **User-Agent:** every NSE request carries exactly the fixed honest User-Agent; a test fails on any browser token
   (`Mozilla`, `Chrome`, `Safari`).
8. **Rows:** every row carries the eight fields of section 5; a missing lot gives `lot_unknown`; a quote with no bid
   or no ask gives `empty_bid_ask` / `one_sided`; an absent answer gives `missing` (good, bad, boundary, empty answer).
9. **Write-once:** one gz file per source and slot through `DataStore`; a rerun of a slot with the same bytes is a
   no-op, with different bytes `RawFileConflict` stops that slot with a named line; a failed Drive write leaves no
   receipt and counts as a failed write.
10. **Nothing secret or priced in the repository or Slack:** a test over every printed, posted and committed line and
    the counts file finds no price, token, cookie or header value.
11. **Commit:** only the story's own paths are staged (a fake git records the paths).
12. **Gates:** full suite, `ruff check fno tests tools`, `tools/check_imports.py`, code size (no file or class over
    350 lines).
13. **Real output sample** in Claims: the command's lines and a counts file from a dry run against recorded fake
    answers (no live value); and, after the first live session, its printed lines.

## 8. Gap list (response 327 P0b and the orchestrator's brief)

| Requirement | Where |
|---|---|
| One futures quote and LTP probe on a small fixed list | section 2 (ltp from `get_quote`), criteria 8 |
| One stock-option chain probe on a small fixed list | section 2, criterion 8 |
| 5 sessions | section 4, criterion 5 |
| Completeness, empty bid/ask share, blocks and 429s, latency, Drive writes | sections 5-6, criteria 3, 8, 9 |
| Effect on A16 and v4 receipts | section 6 (neighbour check, by hand from committed files) |
| Row fields: instrument, contract, expiry, dated lot, source time, first-seen time, raw hash, quality | section 5, criterion 8 |
| No tickets, positions, claims, outcome window | section 5, last line; nothing in the package writes to `fno/school` ledgers |
| Never touching v4 or the pilot | section 4 times; no import of `fno/forecast_v4*` or the fleet (import test, criterion 6) |
| Explicit pace: one at a time, minimum gap, backoff on 403/429, daily cap, clear User-Agent | section 3, criteria 1-4, 7 |
| Raw answers write-once in Drive (O9) | section 5, criterion 9 |
| Stop and alert on any block | section 3, criterion 3 |
| Owner's decision recorded as theirs | section 1 |
| One builder per function (A16h) | section 4, register row |
| **Out of scope:** growing the list or the slots; any NSE disguise; adding `get_ltp`; the school's use of the rows (a later story with an R1 card and a DATA_SPEND update); O6's existing browser User-Agent (flagged below, not touched). |

## 9. Known limits and open risks

- Groww's purpose clause stays unasked in writing (P0-2); the owner's decision covers the use. Open risk, not a
  blocker. **[reasoning only]**
- NSE may serve nothing to an honest User-Agent (P0-2 saw an empty 200 body to a plain client). Then NSE's part stops
  on day 1 by rule 3, and the note says so. **[some evidence]**
- Groww's `get_option_chain` was probed on indices only (P0-1); a stock chain may be refused or shaped otherwise. The
  first live slot shows it; a refusal there is a finding, not a failure. **[reasoning only]**
- Groww's limits may be per user, not per key, so P0b shares A16's budget; the slots sit between A16's marks for that
  reason. **[some evidence: P0-1]**
- Flagged, not touched: `fno/providers/public.py` (O6) already sends a browser User-Agent to NSE; the owner may want
  the same honest rule there (a separate story).

## 10. Questions answered (orchestrator, 24 Oct 2026)

1. NSE refuses the honest User-Agent: stop NSE's part and report; never disguise. O6's browser User-Agent is recorded
   as an existing fact (section 9), untouched.
2. Run by hand, by this builder, 5 sessions; no stored schedule and no `DAILY_RUN_STEPS` row.
3. A missing lot or expiry is never guessed (`lot_unknown` / not captured).
4. Groww's written question stays unasked; an open risk (section 9).
5. Blackout days 26 and 27 Oct (28 Oct if A16h slips), confirmed by the orchestrator (A16h's owner out of reach).
6. **Groww load audit (orchestrator, 24 Oct):** binding limits 300 quote calls a minute and 150 sign-ins per 24 h,
   no limiter shared across sessions; A16's marks take about 85 s from :00/:15/:30/:45. The slots 10:07, 11:37, 13:07
   and 14:07 at <=60 a minute with a hard stop at slot + 6 min sit clear of every mark and window: kept. Two
   conditions, now in section 3 and criteria 3-4: one sign-in per run with a failed sign-in kept, and Groww stops for
   the day at its first 429.

## Claims

(None yet: text round. Code claims, plants and the real output sample come with the code round.)
