# Judge 101: T1 daily trade card v1: `story/t1-daily-card` 3e705bf7ece247d31e4d1251c4ce10b7b30f0a98 (lane 1, response 101)

Fresh judge session for orchestrator session_01VG1RqxLFUVdvvPuMRYZtDH; no shared context with the builder.

**What I did:**
- read the story text at this SHA, design 04 sections 4.1 and 4.4, 6.5, REPLAN's T1 paragraph, response 101 and every
  new file under `fno/cards/`, plus the `fno/alerts/sender.py` and `fno/constants.py` diffs;
- ran the gates on the exact SHA and on a trial merge with `origin/main` (ecf66f4, which includes the quality rules);
- checked the live test post **read-only**: the Slack message, the Drive record and the committed delivery file;
- ran the real CLI in dry runs, and with `--post` with no token and no Drive, in a scratch worktree I never pushed;
- planted 16 code mutations and 8 data scenarios of my own;
- checked positive, negative, boundary and empty cases per criterion, as the owner's quality rule 5 asks.

## Gates

- **Exact SHA:** full history, Slack token unset: **3,253 passed**. `ruff check`, `ruff format --check` (730 files) and
  `check_imports` (740 files) are clean.
- **Trial merge with `origin/main` ecf66f4:** merges cleanly; 3,253 passed; ruff, format and imports clean.
- **Sizes:** the largest new file is `tests/cards/test_issue.py`, 224 lines; the largest module is about 120 lines.
- **Frozen files:** no frozen file changed. `fno/constants.py` is hashed only in experiment 1's finished freeze, which
  has changed since by design (judge 53).

## The live test post (criterion 16a), checked read-only

| Witness | My check |
|---|---|
| Slack | #fno-desk message at ts **1792025414.919329**, by the F&O bot, equals the stored `ts`. First line "TEST — PAPER ONLY: a one-off check of live delivery, not the day's card." |
| Card hash | I re-ran the e5dcf69 dry run for 15 Oct and prefixed the TEST banner. Its SHA-256 is **995fdaa6...86f73c7**, equal to the stored `card_sha256`, and the Slack text matches line for line |
| Drive | `cards/2026/10/2026-10-15_1792025414919329_test.json`: 7,323 bytes, `test: true`. The SHA-256 of its `text` equals `card_sha256`, and every fact equals the committed delivery file |
| Delivery file | `research/cards/deliveries/2026/2026-10-15-a1.json`: no card line (0 matches for PAPER ONLY, Status:, a question line), no token. GitHub clock `skew_seconds: null`, with no reason stored (the `line` key arrived after e5dcf69) |
| Point in time of that post | It used `scores/2026-10-15.json`, a same-day report. The builder discloses this; the code now uses the latest report dated before the day (my T2 mutation caught) |
| Half (b), GitHub's push receipt | Due at the merge check, as the criterion says |

## Per criterion

| # | Criterion | Builder's claim | My own evidence (positive / negative / boundary / empty) | Result |
|---|---|---|---|---|
| 1 | PAPER ONLY first line; no order instruction | `render.py:11` | Real dry run, line 1 "PAPER ONLY. ... Information, no action.". My T8 (drop it) caught. No "order" anywhere on the card | MET |
| 2 | NO TRADE with reason codes | `status.py`, `card.py:78` | **Positive:** real repository, header-only registry: `no_approved_strategy`, "Paper trades so far: 0". **Negative:** a committed `paper` row gives `trade_fields_not_built` naming `nifty_condor-v1`, still NO TRADE. A bad status row gives `data_check_failed` naming `PlaybookError`. A removed account gives `data_check_failed`, "at least 0 (book2_hybrid unknown)". **Empty:** no registry gives `data_check_failed`. My T4 caught | MET |
| 3 | Weather "not yet scored", no colour word | `weather.py:10` | Present on every card I made; no GREEN, AMBER or RED | MET |
| 4 | House forecast per question, labelled fallback, back-fill vs live, point in time, missing named | `forecasts.py`, `track_record.py` | **Positive:** q1 0.59, bin 0.5-0.6 on 175 days, 57%, Brier 0.245 over 669; q5 0.69, 0.6-0.7 on 118 days, 84%, 0.217 over 630. I recomputed these from `scores/2026-10-13.json`'s `close_proxy` mode and the capture's `baseline_b_base_rate` rows: equal. **Point in time:** the report used is 2026-10-13 for a 15 Oct card (T2 caught), and a future capture or report is never used (T3 caught). **Late capture** named (19:27 IST). **Empty:** an empty capture names all five missing past-average rows; no capture gives "Forecasts: none on record yet". T11 (all forecasters as house) caught | MET |
| 5 | Committed records only; footer hashes = committed bytes | `committed.py` | All 7 footer hashes equal `git show HEAD:<path> \| sha256sum`. Appending to the capture and corrupting `registry.csv` in the working tree leaves the card byte-identical. **But my T12 mutation (read the index, `git show :<path>`, instead of `HEAD`) passes every test**, so a staged, uncommitted edit is not covered. See should-fix 3 | PARTLY |
| 6 | Slack `ts` is the issuance time; `card witness`; committer time never read | `posting.py`, `witness.py` | Live `ts` stored and equal to Slack's message. `witness.py` reads `first_commit_adding` and `PushReceipts`, never a commit date. The receipt half waits for the merge | MET (b at merge) |
| 7 | UTC stored, IST shown; host vs Slack and GitHub; > 5 s WARNING | `clock.py` | UTC with `+00:00` stored and IST shown: MET. Slack check live: 0.006 s. **GitHub: never succeeded live.** In my probe from this container, HEAD on `api.github.com` gives 400 and `/zen` 403, with no `Date` header, so it is "not checked (KeyError)", as the orchestrator found. Two defects (should-fixes 1 and 2): an error answer that carries a `Date` header (from a proxy) is taken as GitHub's time, and the 5-second boundary is untested | PARTLY |
| 8 | Owner-unavailable line, E8 absent stated | `card.py:16` | On every card I made | MET |
| 9 | Card records in Drive only; no card text in the repository | `record_store.py`, `issue.py` | Live record in Drive; the delivery file holds none of the card's lines (checked for the live file and for my no-token file) | MET |
| 10 | The card always arrives | `card.py` `_guarded` | **Empty**, with no calendar, registry, captures or score reports committed: a card still came out, with `data_check_failed`, "Forecasts: none on record yet", and Missing naming the calendar, registry, weather and capture | MET |
| 11 | Slack/Drive down: retry rules, printed, stored, next card names the miss | `posting.py`, `deliveries.py` | `--post` with no token and no Drive settings: "alert NOT sent: FNO_SLACK_BOT_TOKEN is not set", "card record NOT saved to Drive: ... (FNO_GDRIVE_*) are not set", delivery a2 written, exit 1. After committing a2, the 16 Oct card names both misses. Retry rules: my T9 (retry a maybe-posted) and B4 (two retries) caught | MET |
| 12 | Dry run by default, no network | `cli.py` | Dry run prints "nothing posted, saved or written" and writes no file (`git status` clean) | MET |
| 13 | Secrets never in files or logs | | No token in the diff (only `test-token-not-real`), none in either delivery file; errors are named by type | MET |
| 14 | Non-session and muhurat days: no card; unknown calendar still a card | `session.py` | 17 Oct (Saturday), 2 Oct (holiday) and 8 Nov 2026 (muhurat) print "not a trading day: no card". 5 Jan 2027 (beyond the calendar) gives a card naming "session calendar cannot answer". My T10 (muhurat gets a card) caught | MET |
| 15 | Interfaces, one root, sizes, constants | `wiring.py`, `CLAUDE.md` | Every source, store, poster and clock is chosen only in `fno/cards/wiring.py`, which is listed in `CLAUDE.md`. Constants are in `fno/constants.py` and at the top of modules | MET |
| 16 | Live delivery verified once | (a) on the branch, (b) at the merge | (a) checked above: MET. (b) at the merge check | (a) MET; (b) pending |

## Claims vs reality

| Builder's claim (response 101) | Reality |
|---|---|
| "43 of 43 planted breaks are caught" | Plausible; I did not rerun the builder's script. My own: 16 planted, **12 caught**. Survivors: T12 (index instead of HEAD), B1 (limit raised to 9.9 s), B2 (resolution ignored on the early side), T6 (next card's clock-warning line) |
| "prints correctly from the real repository" | True: hashes and numbers checked |
| "Each clock check now stores its line, e.g. 'not checked (ConnectionError)'" | True, but the line says only `KeyError`, not "HTTP 400, no Date header", and a non-2xx answer with a `Date` header is accepted (should-fix 1) |
| "The likely cause ... the routine's network blocks a plain HEAD to api.github.com" | Confirmed from this container: 400 with no `Date`. It is the proxy, as the orchestrator says |
| "A muhurat-only day gets no card, as A4 does" | True. See the orchestrator's question 4 below |
| "the house forecast ... changes no scoring" | True: nothing under `fno/forecast*` or `research/forecasts/` changed; the card only reads |
| "Missing items and previous misses are copied into the public metadata ... harmless" | True for v1: the strings are paths and error types, plus a source failure's message cut to 160 characters (`card.py` `_failed`). See minor 2 |
| "A retry after a lost Slack answer can post the card twice" | True and disclosed. `requests.ConnectionError` also covers a connection dropped after the request was sent, and that error is retried. Minor 3 |

## Findings

### Should-fix

1. **The GitHub clock check trusts any answer that has a `Date` header.** `HttpDateClock.now` (`clock.py:43-49`) never
   checks the status code. My plant: a fake HEAD answering **403 with the current `Date`** (what a proxy typically adds)
   gives "clock: host vs GitHub within 0.0 s", stored as `skew_seconds 0.0, warning false`. That is a missing witness
   read as "within skew", the exact case the orchestrator asked about. Today this proxy sends no `Date`, so the check
   fails safe, but only by accident. Fix: accept only a 2xx (or 3xx) answer from GitHub. Store the reason in plain
   words, for example "not checked (HTTP 400, no Date header)" rather than "KeyError". Add tests for a 403 with `Date`
   and a 400 without one.
2. **The 5-second boundary is untested.** Owner's rule 5 asks for tests at, just under and just over every limit. My
   B1 (limit raised to 9.9 s) and B2 (the 1-second resolution ignored on the early side) pass all tests; only 10 s and
   30 s skews are tested. Fix: at 5.0 s no WARNING, at 5.1 s (beyond resolution) a WARNING, on both sides.
3. **"Never an uncommitted file" is not pinned against the index.** My T12 (`git show :<path>`) passes the real-git
   test, because that test only edits the working tree. A staged, uncommitted edit would then reach a card, against
   criterion 5's "an uncommitted ... file is never read". Fix: in the real-git test, also `git add` an edited file and
   assert the card is unchanged.
4. **Criterion 7's GitHub half has never worked live, and nothing says so.** The routine's network answers 400 with no
   `Date`. So every real card will store GitHub "not checked", and the next card never names it (`misses` reads only
   `warning`). Fix: the next card names a server clock that was not checked, as it does a WARNING (also covers T6,
   which survived). The story's known limits must say that from this host the GitHub clock is never available until a
   route that returns GitHub's `Date` is found. This is a fact to report, not a code change in GitHub.

### Minor

1. **`--on` with `--post` can issue a card for another day from today's records.** Registry and accounts come from
   `HEAD` now, not as of that day. The delivery file then counts as that day's card in `misses`. Refuse `--post` unless
   `--on` is today (IST).
2. `_failed` puts a source exception's message (up to 160 characters) into the public delivery file. In v1 every source
   reads public committed files. Name by type only, as the stores do, before slice B adds trade fields.
3. Retrying `ConnectionError` can double-post when the connection drops after sending. Disclosed; harmless in v1.
4. The test post's file has no `line` in its clock entries (pre-fix code). It is append-only and correct as a record of
   that code; noted only.

## The orchestrator's questions

1. **GitHub clock.** The failure is named per check, but as "KeyError". A missing witness can read as "within skew"
   when the error answer carries a `Date`: should-fix 1. The unchecked state is never surfaced to the owner:
   should-fix 4.
2. **Point in time.** MET: the latest report dated before the card's day (T2 caught), never a later capture or report
   (T3 caught). The live test post itself used the same-day report (disclosed; pre-fix code).
3. **House forecast label.** On the card: "House forecast (baseline_b_base_rate): no primary named in G1; past average
   shown (orchestrator's fallback rule)". It changes no scoring (no scoring file touched). The figures equal G4's
   report.
4. **Muhurat: a justified choice, not a gap.** The forecast capture already skips muhurat (`fno/forecast/capture.py:87`),
   so the card would have no forecast to issue. There is no 15:00 market: even the 2025 session (13:45-14:45) closed
   before 15:00. A4 does the same. Design 04's "a card exists every trading day" reads best as every session with a
   15:00 market. Record that reading as a one-line design note, so the text and the code agree.
5. **Drive-only records.** MET: `research/cards/deliveries/` holds hashes, outcomes, missing items and clock facts, and
   no card line, strike or token (minor 2 is for later).
6. **PAPER ONLY and NO TRADE with a reason, incl. my own empty case.** MET. With the calendar, registry, captures and
   score reports all removed: "PAPER ONLY ...", `NO TRADE (data_check_failed)` with its reason, and every missing item
   named.

## Project rules

- Lane 1 is right: it touches Slack, Drive, an outside clock and the shared sender.
- `slack_post` is a behaviour-preserving extraction. `tests/test_alert_sender.py` passes, and it adds the non-dict
  guard (an `AttributeError` before).
- No orders; no Slack post by me (read only); no secrets.
- The quality rules (now on `main`) are met: the gap list, self-review, broken-code proof and a real NO TRADE sample.
  Rule 5's boundary cases are not (should-fix 2).

## Verdict: FAIL for 3e705bf7ece247d31e4d1251c4ce10b7b30f0a98

Four should-fixes, all in the clock contract and test coverage:
- the GitHub check trusts any `Date`;
- the 5-second boundary is untested;
- the staged-file case is untested;
- an unchecked GitHub clock is silent.

The card itself is honest and correct: every number traced to G4's report, the hashes equal the committed bytes, the
live post was verified in Slack and Drive, and the failure paths behave as claimed. A re-check needs `clock.py`,
`deliveries.py` `misses`, the tests named above and the story's known limits. Criterion 16(b) is checked at the merge.
