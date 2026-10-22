# Story: receipts reach

- Owner session: 013xqaNTCbSBytKgqpfaYFqZ, assigned by the orchestrator on 22 Oct 2026. The owner session also
  builds G11/F1, so `fno/ai/receipts.py` is its own code.
- Lane 1, judged by Judge J.
- Branch: `story/receipts-reach`.
- Deadline: on main before 30 Oct. That is the first day a G13b seal could be wrongly stored as EXPIRED.
- This story takes in the former row "G13b evidence vs late" (orchestrator, 22 Oct).

## The defect

All measurements below are strong evidence: read-only GETs to `GET /repos/exepex/trading/activity` on 22 Oct.

`GitHubActivityReceipts` read GitHub's push log newest first and stopped after `MAX_PAGES` = 10 pages of 100. This
repository pushes about 270 times a day: 1,903 pushes in the last week, and 3,503 since its first push on 11 Oct. So
the reader saw only about the last 32 hours. At 23:15 UTC its oldest push was from 21 Oct 15:10 UTC. A receipt older
than that was "no push of … in GitHub's activity log", for these reasons:

- The 7-day reach assumed in `time_period=week`, in seals.py `LOG_REACH`, and in the health window's comments was
  never real. With 1,903 pushes a week, the week needs 20 pages.
- GitHub keeps more than a week. With no `time_period`, the log returned every push back to the repository's first.
  GitHub's documentation states no retention limit.

## Who it hit (each caller, today)

The survey read every call chain; the line numbers below are on main as of 22 Oct.

| Caller | Asks about | Age when asked | Effect of the blind spot | After this story |
|---|---|---|---|---|
| `ai collect` (forecast-capture.yml) | today's commitment and reveal | 1-15 min | none in normal runs. A manual `--day <past>` after about 32 h wrote a permanent LATE / NOT_REVEALED | found back to the commit's date |
| `card witness --on D` (manual) | D's card-delivery commit | same day to weeks | "none yet" for any D older than about 32 h | found |
| v4 pack `build_commitment_times` | v4 rows against 15:10 | n/a: no production caller yet | none | found |
| `health check`, 17:51 IST daily | every session of the last 6 days | 2.5 h to 6 d 8 h | `unknown` for every session older than about 32 h, every evening (see the measurement below) | found |
| G13b seals (`seal_recent`) | each live 15:45 receipt | minutes (same run) to about 70 h (a refused step, then a weekend) | a seal missed the same day: pending, then stored EXPIRED on day 8, permanently | found; only answers are stored |
| G13d seals (live from 23 Oct) | the 15:30 issue receipt | **about 24 h at best** (it seals yesterday back); Friday to Monday is about 72 h | Friday's record, from its very first day: stored EXPIRED on day 8 | found; only answers are stored |

Health check, measured (strong evidence). The new reader found the push of each NIFTY `.canonical` file in 24 pages:
16 Oct 09:36, 19 Oct 09:28, 21 Oct 09:27 and 22 Oct 09:31 UTC. Read at 23:15 UTC, the old reader reached back only
to 21 Oct 15:10, so all but the 22 Oct push were unknown to it. At the check's 17:51 IST run it would have reached back
about 32 hours, so every session older than one day was `unknown`. That is consistent with the 9-10 "problems" in
every `research/ops/health_runs.csv` row from 18 to 22 Oct. Those rows do not keep each finding, so the share caused by
this is not proven.

Records already wrongly stored: none (strong evidence: Drive read on 22 Oct). G13b went live on 22 Oct. Both of its
seals so far, NIFTY and BANKNIFTY 2026-10-22 1545, are stored on time (sealed 09:53:56 UTC, deadline 23 Oct 09:15 IST).
G13d goes live on 23 Oct. No EXPIRED seal can exist before 30 Oct.

## The design

**Reading the log** (`fno/ai/activity_log.py`, a new unit):
- It reads newest first, with no `time_period`, and only as far back as a question needs.
- It keeps its pages, so a later question reads only the pages it still lacks.
- `pages` counts the pages read.
- `PAGE_CAP` (2,000 pages, about two years here) is only a guard against a next link that never ends. It never sets
  the reach.

**The search** (`GitHubActivityReceipts.received_at`):
- It reads back to the commit's own committer date minus `CLOCK_MARGIN` (one day).
- The receipt is still GitHub's timestamp of the first push whose `after` contains the commit and whose `before` does
  not.
- A committer date set later than the real push finds no push and fails closed. Every later push's `before` already
  holds the commit, so a later time is never taken.

**Each kind of unknown has its own name:**
- `ReceiptUnavailable`: a failed read (network, HTTP). `ReceiptAccessDenied` (401/403) is a subclass of it.
- `ReceiptNotFound`: the log covers every moment the commit could have been pushed, and holds no push of it.
- `ReceiptOutsideLog`: the log ends before the commit could have been pushed.

All three are `ReceiptUnknown`, so every caller that catches `ReceiptUnknown` behaves as before.
`fno/health/evidence.py` keeps each answer's kind (`EvidenceNotPushed`, `EvidenceOutsideLog`, `EvidenceNotCommitted`).
All of them are `EvidenceUnknown`, so the health check is unchanged.

**Seals** (`SealCheck`, `Seals`, shared by G13b and G13d):
- A seal is stored only on an answer:
  - a known push time;
  - a log that no longer reaches the push (`OUTSIDE_LOG`, named);
  - no push found once the deadline has passed (`NOT_PUSHED`): any later push would be late.
- A failed read (any error that is not one of those answers) is read again twice within the run, 10 s apart
  (`SEAL_READ_ATTEMPTS` = 3, set in the wiring).
- If it still fails, the seal stays open (`waiting`). Each run retries it for `SCAN_REACH` = 7 days. That window is
  bounded by `deep_enough`'s 10 days of shallow-clone history, not by GitHub.
- After those 7 days, the outcome depends on the reason it is still open:
  - Unreadable evidence: the seal is **never stored late**. The run prints "seal NOT recorded, its evidence unreadable
    for 7 days", and readers keep computing the seal.
  - A receipt still not committed after 7 days: the seal is stored late.

## Claims

1. **Reach.** Strong evidence: tested and measured live.
   - A fake log of 3,000 pushes, with the commit 1,500 pushes back, is found in 17 pages, never all 30. A newer commit
     reuses those pages.
   - Live, a commit from 19 Oct was found in 14 pages (7.3 s), and the health files above in 24 pages.
2. **Named answers.**
   - A commit older than the log's end raises `ReceiptOutsideLog`. A commit no push brought raises `ReceiptNotFound`.
   - A forged later date fails closed (`tests/ai/test_receipts_reach.py`).
   - Evidence keeps each kind (`tests/health/test_evidence_answers.py`).
3. **Seals store only answers, on both sides** (`tests/price_ranges/test_seal_answers.py`, each run as G13b and as
   G13d):
   - a failed read is retried and then seals;
   - unreadable evidence stays open and is never stored late;
   - no push by the deadline is final and named;
   - a log that no longer reaches the push is final and named apart;
   - no push before the deadline stays open;
   - an answer is never retried.
4. **Revert plants: 8 of 8 caught.** Each was run alone:
   - a fixed 10-page reach;
   - no "outside the log" answer;
   - a later push's time accepted;
   - an unreadable seal stored late;
   - no retry within the run;
   - no push by the deadline left open;
   - an answer retried;
   - evidence losing the answer's kind.
5. **Rate limit.** Strong evidence: a header seen on 22 Oct.
   - This session's token shows 15,000 requests an hour. GitHub's Actions token has 1,000.
   - A search reads about 3 pages a day back. A full read of the whole log is now 36 pages and grows by about 3 a day.
   - The page count goes into every not-found and outside-log message, and `GitHubActivityReceipts.pages` exposes it.
     A found receipt prints nothing new: no caller had a log line to add it to.
6. **What is not covered, plainly.**
   - **GitHub's real retention.** GitHub documents no limit, and this repository is only 11 days old, so it cannot be
     measured here. `ReceiptOutsideLog` covers the day it starts to matter.
   - **The about-90-day figure** in the orchestrator's brief is not confirmed by GitHub's documentation.
   - **The per-finding share of the health check's daily problems** is not proven (see above).
7. **G13d's owner asked for its side to behave the same.** It does, and it is tested on that side. No signature changed
   for G13d: `SealCheck`'s new `now`, `attempts` and `pause` parameters all have defaults.
8. **Gates:** in the message to the judge.
