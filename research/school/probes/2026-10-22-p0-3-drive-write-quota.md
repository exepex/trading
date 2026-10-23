# P0 probe 3: Google Drive write quota for about 1,000 small files a day

Market school stage P0 (response 327, section 4). Builder session session_01G5EqV95Wi7yHJ5Hgy2giaY, 22 Oct 2026.
Research note only: no upload test was run and nothing in Drive was touched. Labels: **strong evidence** (quoted
official Google page), **some evidence** (secondary source), **reasoning only**.

## Answer

- **The speed is fine.** 1,000 files a day in 4 bursts of 250 needs 0.83 writes a second if a burst must finish in 5
  minutes. Google's limit is 3 sustained writes a second per account, so the margin is 3.6 times. **[strong evidence
  for the limit; the arithmetic is exact]**
- **The item count is the real wall.** Google advises at most 500,000 files created or owned per user. At 1,000 a day
  that is reached in about 500 trading days (about 2 years), on top of what the archive already holds. **[strong
  evidence for the limit]**
- **Storage may come before either.** The owner's account is the writer (OAuth). At the high end, 1,000 files of 200 KB
  is 200 MB a day; a free 15 GB account would fill in about 75 days. Real files are likely smaller; measure in P0b.
  **[reasoning only]**
- **Proposal:** for P0b, keep one file per capture (it fits the current one-receipt-per-file design, story O9), paced at
  2 a second or slower, one dated folder per day. Before stock-option capture grows past P0b, decide on **one JSONL
  archive per slot** with a committed manifest of every inner record's SHA-256 (4 files a day instead of 1,000). That
  decision is lane 1 (it changes the record store). **[reasoning only]**

## Facts

| Fact | Quote | Source | Label |
|---|---|---|---|
| Sustained write rate | "avoid exceeding 3 requests per second of sustained write or insert requests, per account." "This rate limit can't be increased." | https://knowledge.workspace.google.com/admin/getting-started/google-drive-large-migration-best-practices (updated 20 Oct 2026; formerly support.google.com/a/answer/10445916) | strong |
| Per-minute quota (projects from 1 May 2026) | 1,000,000 quota units per minute per project; 325,000 per minute per user per project; a read costs 5, a list 100, a download 200, "Edit items, such as `files.update`" 50 | https://developers.google.com/workspace/drive/api/guides/limits | strong |
| No daily count limit | "Provided you stay within the per-minute quotas, there's no limit to the number of requests you can make per day." | same | strong |
| Older projects keep old quotas | "As of May 1, 2026, the usage limits for this API were updated." Projects that used the API from November 2025 to April 2026 "will continue with their previously set usage quotas" (the page does not give them) | same | strong |
| Older call quota | "The default quota limits for Drive API are 20,000 calls every 100 seconds, both per user and per project." | migration page above (may be the pre-May-2026 default) | strong (but which table applies to our project is unverified) |
| Daily upload volume | "Each user can upload and copy 750 GB to Drive within 24 hours." | https://support.google.com/a/answer/7338880 | strong for Workspace; some for a personal account |
| Items per folder | "There's a 500,000 item limit for folders, files, and shortcuts directly in a folder." | https://developers.google.com/workspace/drive/api/guides/handle-errors (`numChildrenInNonRootLimitExceeded`) | strong |
| Items per owner | users should not "create or own more than 500,000 files, folders, or shortcuts" | migration page above | strong (advice, not a hard error) |
| Hard item cap | "Each user can have up to 500 million items created by an account." | handle-errors (`activeItemCreationLimitExceeded`) | strong |
| Service accounts | "Service accounts don't have storage quota and can't own any files." | handle-errors | strong |
| Batching | "You're limited to 100 calls in a single batch request." "A set of n requests batched together counts toward your usage limit as n requests" "Google Drive doesn't support batch operations for media, either for upload or download" | https://developers.google.com/workspace/drive/api/guides/performance | strong |
| Rate-limit errors | 403 `userRateLimitExceeded`, 403 `rateLimitExceeded`, 429 `rateLimitExceeded` | handle-errors | strong |
| Backoff | truncated exponential backoff, `min(2^n + random_ms, maximum_backoff)`, "maximum_backoff is typically 32 or 64 seconds" | limits page | strong |

**So Google's batch API does not help.** Uploads cannot be batched, and batched calls still count one by one. "Batching
per slot" can only mean fewer, larger files.

## What our code already does (strong evidence: files)

- Uploads sign in **as the owner** (OAuth refresh token): "a service account cannot: it has no storage quota"
  (`fno/storage/google_drive_upload.py:1-2`). That matches Google's rule above.
- Each create uses an ID asked from Drive beforehand, so a retried create answers 409 and never makes a second copy
  (`google_drive_upload.py:5-7`). Retries wait 2, 8, 30 and 60 seconds on 429 and 5xx, and treat 403
  `rateLimitExceeded` / `userRateLimitExceeded` as temporary (`fno/storage/drive_session.py:13-16`).
- Before a create it looks the folder and file up again (`google_drive_upload.py:45-47`): about one list (100 units),
  one ID request (5 units) and one create per new file.

## Arithmetic for one burst of 250 files [reasoning only, on the limits above]

| | Value |
|---|---|
| Rate needed (250 in 5 minutes) | 0.83 a second (28% of 3 a second) |
| At 2 a second | 125 seconds a burst |
| Quota units, if all 250 land in one minute: list 100 + ID 5 + create (assumed 50, not listed by Google) | 250 x 155 = 38,750 units = 12% of 325,000 |
| Old quota table | 250-750 calls per burst vs 20,000 per 100 seconds |
| Items per year (about 250 sessions) | 250,000 files with option 2; about 1,000 with option 1 |

**Shared rate:** the 3 writes a second is per account. A16's intraday recorder, the librarian and the pre-open capture
write as the same owner. A slot burst that overlaps them shares the 3 a second. P0b should measure the combined rate,
not one job's.

## The two designs

| | (1) One JSONL archive per slot | (2) One file per capture, paced |
|---|---|---|
| Writes a day | 4 | 1,000 |
| Item cap (500,000 per owner) | never reached | about 2 years |
| Receipts in git | 4 a day plus a manifest | 1,000 a day |
| Reading one record | download the whole slot file (cache it) | one file |
| Late or retried capture | needs a second part file and a rule for which counts (write-once forbids appending) | its own file |
| Hash stability | sorted keys and fixed record order needed, or the same data hashes differently | natural |
| Fits current O9 store | no: a new record shape, lane 1 | yes |

**Recommendation [reasoning only]:** (2) for P0b's small fixed lists (tens of files a slot, not 250). Choose (1) before
any stage that writes hundreds of files a slot, through a lane-1 story.

## Not verified

- Which quota table our Google Cloud project has (old or the 1 May 2026 one). Check the project's Drive API quota page in
  the Cloud console. It does not change the answer: both are far above the need.
- The quota-unit cost of `files.create` (assumed 50).
- Whether the 3-a-second and 750 GB limits apply word for word to a personal (non-Workspace) account.
- The owner's Drive storage plan and free space. This decides the storage date above.
- No upload was timed. P0b measures real writes.
- Third-party reports used only as background: https://forum.rclone.org/t/google-drive-limit-write-or-insert-requests-per-second/42439
