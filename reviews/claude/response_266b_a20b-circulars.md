# Response 266b: A20b, NSE and SEBI circulars kept point in time (builder's claims)

**Story:** `docs/stories/A20-rules-and-dates.md` (part b) · **Branch:** `story/a20b-circulars` (built on the text
branch, 6487dc7e; independent of A20a's code) · **Builder:** session_013u1Ac2N9eRQ8XCYPjwpaat · **Lane:** 1 (NSE,
SEBI, Drive, Slack, a workflow)

## What it does

`python -m fno circulars [--day D]` (workflow `circulars.yml`, hourly 08:00-22:00 IST, every day: NSE and SEBI also
publish on holidays):
1. reads the circulars already listed: Drive `data/circulars/list/` parts through O9's verified Drive cache (every
   byte checked against its receipt). If that fails, nothing is captured (it would list everything again) and the run
   alerts;
2. NSE: `www.nseindia.com/api/circulars` for yesterday and today; SEBI: its latest circulars page (25);
3. every circular whose link was not seen before becomes a row (source, number, issued_on, department(s), category,
   subject, link, fno_relevant, first_seen_at in UTC). For each F&O-relevant one, the file (NSE PDF or zip, SEBI page)
   is saved FIRST to `data/circulars/files/<source>/<YYYY>/<MM>/`. If the file fails, the circular is not listed and
   the next run tries again;
4. the run's new rows form one part `data/circulars/list/<YYYY>/<MM>/<date>.<run_id>.csv` (O9 `PartTable`,
   write-once). The receipts are committed by O9's receipts committer (the same one the A16 routine uses live);
5. any problem (a feed refused or unreadable, a file not saved, a SEBI page with nothing seen before, earlier parts
   unreadable, receipts not committed) makes ONE #fno-desk alert naming every problem, and the run exits 1. The alert
   goes through `StepOutputAlerts`, so the workflow's own line speaks only on a crash. O10 writes the error row.

## Claims and evidence

| # | Claim | Evidence |
|---|---|---|
| 1 | NSE read whole from today's real answer; refused, HTML, malformed, empty-shape and unreachable answers are `FeedFailed`, never an empty list | `fno/circulars/feeds.py`; `tests/circulars/test_feeds.py` |
| 2 | NSE lists a circular once per department (70 items, 63 circulars on 15-16 Oct): merged into one row keeping every department, so an F&O department is never lost | `_merged`; `test_nse_lists_every_circular_of_the_dates_with_its_department` (NSE/CMTR/76963 keeps "Futures & Options") |
| 3 | SEBI's page read whole (25 rows, number from the link, title unescaped); a page without rows is `FeedFailed` | `SebiCircularList`; tests |
| 4 | Relevance: exactly the 4 F&O circulars of 15-16 Oct on NSE (none of NSE's commodity or currency "derivatives"); SEBI's derivatives circular kept | `fno/circulars/relevance.py`; `test_relevance_keeps_fno_department_and_fno_subjects_only` |
| 5 | New rows carry the first-seen time; relevant files saved, others not; a second run with the same list writes no part | `tests/circulars/test_capture_and_job.py` first two tests |
| 6 | A failed file leaves its circular unlisted for the next run; a failed feed does not stop the other feed | the next two tests |
| 7 | A SEBI page with nothing seen before alerts a possible gap (and still lists the page) | `test_a_latest_page_with_nothing_seen_before_is_a_possible_gap` |
| 8 | Unread earlier parts stop the capture (nothing listed twice); one alert names every problem; receipts not committed is a problem; a clean run sends nothing | the job tests |
| 9 | **Live run against real NSE and SEBI** (16 Oct 17:00 IST, a local folder in place of Drive, two runs): run 1 `nse: 63 listed, 63 new, 2 file(s) saved`, `sebi: 25 listed, 25 new, 3 file(s) saved`; run 2 `0 new` on both; no problems. That run found the department-merge bug (claim 2) before the fix; the fixed code gives NSE 4 relevant (tests) | this session's log |
| 10 | Gates on the unshallow clone: 7392 passed; ruff check and format clean; imports and records clean | this session's log |

## Honest limits

- **SEBI relevance is wide on purpose.** On 16 Oct it kept 3 of 25, including 2 commodity-derivatives circulars
  ("derivative" in the title). A false positive costs one small saved page; a false negative loses a rule change.
- **NSE relevance misses an F&O rule filed under another department with none of the F&O words.** Every circular is
  still listed, so it can be found later; only its file would not be pre-saved.
- **First-seen time is the run's time**, so hourly at best; before the first run there is no first-seen time at all
  (the list starts at the first run, back to yesterday for NSE and the latest 25 for SEBI).
- The first run lists about 90 circulars and saves about 5 files; later runs a handful.
- First user of O9's `PartTable` in a live job (O9 step 2b is later); the store, receipts and cache are O9's tested code.
- `fno/alerts/run_location.py` is shared with A20a (the same file, byte for byte, on both branches).
- O10's `capture-watch.yml` must list `circulars` (asked of O10's builder via the orchestrator).
