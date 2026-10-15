# Response 119: story A9b, NSE downloads: one retry policy and a named failure everywhere (builder's claims)

Branch `story/a9b-nse-retry`. Story text passed at ad0c9ae (judge 119). Lane 1 (shared NSE download code, a workflow,
the A8 evidence log). Judge's diff base: `git merge-base origin/main HEAD`.

## Verdict first

Every one of the 22 NSE source classes now follows one policy (`fno/storage/retry_policy.py`, used by
`NseArchiveSource._response`):
- 2xx is used at once, unchanged;
- 404 means "not published";
- dropped connections, 429 and every 5xx are retried: at most 4 tries, waits of 5, 15 and 45 s, stretched by NSE's
  `Retry-After` up to 120 s;
- anything else is refused at once (`RawFileRefused`);
- a paused host stops at once (`RawSourceCoolingOff`).

No `requests.HTTPError` or `SourceCoolingOff` leaves a source any more, and every command names the final failure.

Real check (rule 6): through the new code, NSE's index-close file of 14 Oct 2026 took **1 request**, 17,614 bytes,
`Last-Modified` 2026-10-14 17:50:10 UTC, and its SHA-256 **equals the manifest row**. Success is unchanged.

What the owner should know:
- **A cool-off now stops a long pass with one line.** Before, each file slept 65 s into the paused host and then
  failed. The fix of the review's first finding means the monthly participant-OI sweep (1,929 files) stops at a
  pause with "N file(s) not read: run again after the pause", instead of listing every file as no answer.
- **`market daily` stops that day's publication when NSE does not answer the revision re-read of a session file.**
  Before, the failure was dropped silently. This follows the story's table ("a problem line") and judge 49's reason
  (NSE's latest version cannot be confirmed). It is a new way to lose a day: **for the judge to confirm** (reasoning
  only that stopping is the safer side).
- **The A8 start times go to a side log** (`release_check_starts.csv`), per the orchestrator's decisions 37 and 49;
  the check log `release_checks.csv` keeps its name and header (addendum 1 below; the first design, a
  `release_checks_v2.csv`, is withdrawn).

## Per criterion

| # | Criterion | Code | Tests | Evidence |
|---|---|---|---|---|
| 1 | The policy for every source class, GET and HEAD | `retry_policy.py` (`verdict`, `retry_after_seconds`, `RETRY_WAITS`, `MAX_RETRY_AFTER_SECONDS`, `UNBUILDABLE`); `raw_source.py` `_response`, `_retry_wait`, `_failed`, `_stamp` | `tests/nse_retry/test_policy.py`: all 22 classes x GET/HEAD for success, 404, 503 x2 then 200, 503 x4, refusals (403, 400, 401, 410, 451, 1xx, 3xx, 600, 0) and cool-off; every retried status and dropped connections; 429 then 429 through the real pacer stops at the second with waits [5]; `Retry-After` 30/3/120/121, an HTTP date, malformed, past, empty, non-ASCII digit; an unbuildable request; an unreadable or zoneless `Last-Modified`; an empty 200 | strong |
| 2 | No `HTTPError`/`SourceCoolingOff` leaves a source; no code catches them around a read | `raw_source.py`; callers changed to `RawSourceUnavailable` / `RawFileRefused` | the policy tests; `test_no_http_error_catch.py` reads every function in `fno/` and `research/` that calls `fetch`, `fetch_published` or `last_written`, and refuses any `except` naming `HTTPError`, `RequestException` or `SourceCoolingOff` (a planted catch is found) | strong |
| 3 | Every command names a final failure | `revision_source.py` (reasons, stop on cool-off); `revisions_cli.py`; `fingerprints.py` and `fingerprints_cli.py`; `market_read_models/cli.py` (`_archive_session` keeps every problem, `_take_snapshots` goes on after a refused list, `_archive_revisions`, `_look_up`); `filings/librarian.py` (a refused file is that company's failure; unavailable stops the run); `vix_history/sweep.py` and `cli.py`; `research_data/write_sweep.py` and `participant_oi_cli.py` | `test_callers.py` (13) and `test_commands.py` (9), run with 503 x4, 403 and a pause: data-librarian, data-snapshot, data-revisions sweep, data-fingerprints, participant-oi check-once (alert through a **fake sender**, judge minor 1), watch and sweep, vix-history fill and sweep, filings archive (goes on after a 403, stops when down), filings day-lists (the second list runs), market archive (all three problems kept, every list taken), market look-up | strong |
| 4 | Successful downloads unchanged | the 2xx branch returns the response untouched | the policy tests (one request, no wait, same bytes and `Last-Modified`); the real download above | strong |
| 5 | Docs | `docs/DATA_SOURCES.md` "Politeness" (the table, the cap's reason, the worst case, `PublicData`); `research/data/participant_oi/README.md` (the side log of start times, the sweep reads files in full) | n/a | the HEAD-only line was wrong and is corrected |
| 6 | Quality rules 1-9 | below | | |

## Judge 119's minors

1. **Fake alert sender:** `test_participant_oi_check_once_alerts_when_nse_is_down` uses `FakeSender`, and no test
   posts to Slack. The command tests also replace `build_nse_source`, so they make no network call (see the
   self-review: one test briefly reached NSE before that was fixed).
2. **The 120 s cap, reasoning only:** past two minutes NSE is blocking, not hiccuping, and the pacer's 15-minute pause
   plus the next scheduled run are the right retry. Worst case per file: 65 s, or 3 x 120 s of waits, plus up to four
   60 s timeouts. A12's `filings archive --max-minutes` checks its deadline before each file, so only the file in
   flight runs over (twice that for a truncated file's second download). This is stated in the story, in
   `retry_policy.py` and in `DATA_SOURCES.md`.
3. **`PublicData` is safe today:**
   - `NseLevelSource` records any failure;
   - A12's indexes turn a list failure into that company's failure, and a cool-off into a stop;
   - a new caller must do the same.
   This is stated in the story and in `DATA_SOURCES.md`.
4. **A8 release time:**
   - `checked_at` is when the answer came, and `started_at` when the check began
     (`fno/research_data/release_times.py`);
   - tested with 503 then 200: started 19:00:00, checked 19:00:05;
   - also tested (addendum 1): an answer at once (equal times), NSE down after 65 s (unreachable at the time it gave
     up), checks before A9b read unchanged without a start, a lost side log losing start times only, a wrong header
     refused and an empty file given its header (either file).

## Quality rules

- **Rule 1:** story text first, passed at ad0c9ae.
- **Rule 2:** the gap list is in the story.
- **Rule 3, self-review by two independent agents** (a criterion reviewer and an adversarial tester); decisions below.
- **Rule 4:** 36 planted mutations, **36 of 36 caught**, each by a named test.
  - The 35 were run against `tests/nse_retry`, `filings`, `research_data`, `vix_history`, `test_revisions.py`,
    `test_storage.py` and `market_read_models`.
  - One of them (an `HTTPError` catch planted in the VIX sweep) was caught by a `NameError`, so it was planted again in
    the filings librarian. There the code-reading test caught it.
- **Rule 5:** good, bad, boundary and empty cases per criterion (table above).
- **Rule 6, real output:**
  - the real download above;
  - failure lines made with a fake NSE (labelled test output: NSE cannot be made to fail on purpose):

```
[503 x4] RawSourceUnavailable: NSE archive: nse/indices/index-close/2026/10/ind_close_all_14102026.csv: HTTP 503 after 4 tries
[403] RawFileRefused: NSE archive: nse/indices/index-close/2026/10/ind_close_all_14102026.csv: HTTP 403 after 1 try
[429 Retry-After 300] RawSourceUnavailable: NSE archive: .../ind_close_all_14102026.csv: HTTP 429 (Retry-After 300) after 1 try
[paused] RawSourceCoolingOff: NSE archive: .../ind_close_all_14102026.csv: nsearchives.nseindia.com refused requests (HTTP 403); not calling it for 15 minutes
data-librarian: stopped: NSE archive: .../ind_close_all_14102026.csv: HTTP 503 after 4 tries. Run the same command again later to resume (only missing files are fetched).
data-revisions sweep: no answer: <path>: NSE archive: <path>: HTTP 403 after 1 try (check again next sweep)
data-revisions sweep: STOPPED: NSE archive: <path>: nsearchives.nseindia.com refused requests (HTTP 403); not calling it for 15 minutes; 3 file(s) not read: run again after the pause
```

- **Rule 7:** the orchestrator's check is next.
- **Rule 8:** after the merge, one real `data-librarian index-close` run on a recent day.
- **Rule 9:** no money path, so no ChatGPT review (stated in the story).
- **Gates:** `python -m pytest -q` (4,355 passed on the merged tree); `ruff check` and `ruff format --check`; `tools/check_imports.py`. The largest changed file is
  `raw_source.py` at 255 lines. No frozen file is changed.

## Self-review: findings and decisions

Adversarial tester:

| # | Finding | Decision |
|---|---|---|
| 1 | A revisions problem is lost when snapshots fail; a 403 on one list stops the other lists | **Fixed**: every problem kept; a refused list is named and the others go on (test) |
| 2 | One failed re-read now blocks `market daily` | **Kept, for the judge** (above): it matches the story's table; documented in the story and `DATA_SOURCES.md` |
| 3 | Statuses outside 2xx/4xx/5xx returned as data | **Fixed**: only 2xx is data; 1xx, 3xx, 600 and 0 are refused (tests) |
| 4 | A second 429 still waited before stopping | **Fixed**: a second 429 in a row stops at once (`REFUSALS_BEFORE_PAUSE` from the pacer), waits [5] (test) |
| 5 | A non-ASCII digit in `Retry-After` escaped as `ValueError` | **Fixed** (test) |
| 6 | A bad or zoneless `Last-Modified` escaped (existed before this story) | **Fixed**: unreadable gives `None`, zoneless is read as GMT (tests) |
| 7 | The participant-OI sweep gave no reason | **Fixed**: it names why, and stops on a pause (tests) |
| 8 | Code errors (`InvalidURL` and similar) were retried as "NSE down" | **Fixed**: not retried, "(not sent)" (test) |
| 9 | The code-reading test only knew `HTTPError` | **Fixed**: `RequestException` and `SourceCoolingOff` too, matched by exact name; no offender found |
| 10 | A zero-byte v2 file was refused; the legacy name could be written | **Fixed** (tests) |

Criterion reviewer:

| # | Finding | Decision |
|---|---|---|
| 1 | A cool-off lost the rest of a long sweep | **Fixed**: `RawSourceCoolingOff`; the revision, participant-OI, VIX and fingerprint passes stop with one line (tests) |
| 2 | Criterion 3 not tested end to end for several rows | **Fixed**: `test_commands.py` (9 command runs) |
| 3 | One 429 waited into a pause | **Fixed** (as tester 4) |
| 4 | The A12 deadline worst case was imprecise | **Fixed**: the file in flight, waits plus timeouts, twice for a truncated file |
| 5 | Non-ASCII `Retry-After` | **Fixed** |
| 6 | Nothing stopped writing the legacy name | **Fixed**; the test paths renamed |
| 7 | The market publication is stopped by a re-read | **For the judge** (as tester 2) |
| 8 | Clean code: alias, `verdict(404)`, a type hint, a variable reused | **Fixed** (`verdict` returns `not published` for 404; alias gone) |
| 9 | The participant-OI sweep reason | **Fixed** |
| 10 | Story status line stale; README count; the actions v2 header file | **Fixed** |
| 11 | Real download and mutations not yet in the branch | **Done** (above) |

A finding of my own: one command test first reached NSE for real. `fno/composition.py` imports `build_nse_source` by
name, so patching the wiring module did not reach it. It fetched the public participant-OI file of 12 Oct once and
wrote only to a test folder. The fixture now patches both places, and the tests make no network call.

## Addendum 1: judge 119 addendum 1 (FAIL on f90e18b) and the orchestrator's decision 49

**Should-fix: the A8 Claude routine commits the check log by path.** Its prompt (response 40, line 199) says:

> 3. Commit `research/data/participant_oi/release_checks.csv` and push to `main` (`git pull --no-rebase` first).

With the v2 file, its rows after the merge would have stayed uncommitted in its container and been lost silently.

The workflow does not cover it, checked against the files:
- `participant-oi-release.yml` commits its folder (`git add "$EVIDENCE"`, with `EVIDENCE: research/data/participant_oi/actions`);
- that folder is O6's side-by-side copy, which the availability rule does not read;
- `participant-oi-watch.yml` writes the rule's log, but every 15 minutes, against the routine's 5.

So the routine's rows are not a free duplicate: losing them would coarsen the rule's evidence.

**Fixed in the design, not by relying on the routine.**
- The check log keeps its name and header (`release_checks.csv`: `day, checked_at, outcome, sha256, last_modified`).
- Each check's start goes to a side log beside it, `release_check_starts.csv` (`day, checked_at, started_at`), joined
  on `day` and `checked_at`.
- A writer that commits only the check log (the routine) loses start times, never a check. This is tested: the side
  log deleted, the checks and the measured first-seen time unchanged.
- The watch workflow commits both files: `git add "$LOG" "$STARTS" "$REREADS"`, with the side log committed with its
  header so `git add` never fails (tested).
- `.gitattributes` merges both side logs by union.
- The v2 files, wiring and workflow change are withdrawn.

**Owner item** (the orchestrator puts it on the owner's list): update the routine's prompt to commit
`research/data/participant_oi/` (so its start times are kept too), or retire it now that the two workflows run.
Scheduled tasks are the owner's; neither the orchestrator nor I may edit them.

**Minor 1, the code-reading test.**
- It now resolves module-level exception tuples named in an `except`, the `LIST_ERRORS` pattern (a planted tuple
  catch is found).
- Its docstring states its limits plainly: an imported alias, a tuple built in a function, a method alias of a read,
  `except Exception` or a bare `except`, and a catch one call up.

**Minor 2, no real network in tests.** `tests/conftest.py` `no_real_network` (autouse) guards every socket connect in
the test process:
- a connect to anything but this machine raises `RealNetworkBlocked`. It is a `RuntimeError`, so no library retries
  it or wraps it as a connection error;
- the proxy settings are removed, and a connect to the proxy's own address is blocked. A cloud session's proxy
  listens on 127.0.0.1, so "loopback only" alone let a request reach NSE through it: the first version of the guard
  showed exactly that;
- `tests/test_network_guard.py` proves it: a direct connect (by IP and by name), `connect_ex`, and `requests.get` to
  NSE all fail loudly; the proxy address is blocked; a local server still answers;
- limit: a subprocess a test starts is not guarded (the credential guard keeps it without keys).

**Gates and proofs for addendum 1:**
- `python -m pytest -q`: 4,611 passed, with the network guard on for the whole suite (so no test needs a real host);
- ruff, format and the import check are clean;
- 8 new planted mutations, **8 of 8 caught**: a start not written, not joined, `checked_at` taken at the start, a
  side-log header not checked, the workflow not committing the side log, the tuple not resolved, the guard off, and
  the proxy allowed;
- in the "guard off" mutation, the test's direct connect to 93.184.215.14 really went out from this cloud container,
  and it failed there. This was the mutation run only, never the suite.
