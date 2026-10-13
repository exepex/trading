# Response 43: A9 Drive uploads as the owner, and the historical-data librarian (builder's claims)

Status: **built; awaiting judge**. Story: `docs/stories/A-data-foundation.md`, section A9. Builder session for N = 43.

Commits on `main`: `260454c` (store, librarian, wiring), `85d3bac` (SHA-256 manifests for every NSE dataset,
judge 18 minor 1), `a6efeb6` (Drive 403 rate-limit fix), and this claims commit.

## What was built

| Part | File | What it does |
|---|---|---|
| Shared Drive session | `fno/storage/drive_session.py` | Extracted from `GoogleDriveStore` (DRY): one fresh sign-in on a 401; growing waits (2, 8, 30, 60 s) on 429, 5xx, dropped connections and Google's 403 `rateLimitExceeded`/`userRateLimitExceeded`; errors name Google's reason code |
| Owner sign-in | `fno/storage/owner_token.py` | Swaps the refresh token for an access token; a refusal raises `DriveSignInRefused(<Google error code>)`, never a value |
| Writable store | `fno/storage/google_drive_upload.py` | `GoogleDriveUploadStore` (behind `RawFileStore`, extends the reader): folders made as needed, same bytes = no-op, different bytes = `RawFileConflict`, IDs reserved from Drive first so a retried create cannot duplicate (Drive answers 409 `fileIdInUse`, tested live), each upload checked against Drive's MD5 |
| Librarian | `fno/storage/librarian.py`, `librarian_cli.py` | `python -m fno data-librarian participant-oi`: for every session keeps a verified stored file, else fetches from NSE (paced), verifies (schema + manifest SHA-256), uploads; damaged stored files reported, never replaced; resumable |
| Fingerprints | `fno/storage/fingerprints.py`, `fingerprints_cli.py` | `python -m fno data-fingerprints <dataset> [--spot-check N]`: SHA-256 manifest of a dataset's files in Drive (read-only), never overwrites an existing manifest, compares a fixed-seed sample with NSE's live bytes |
| Wiring | `fno/storage/wiring.py` | `build_owner_drive_store` (all four settings or None), `RawFileLibrary` archives to Drive when they exist, `build_librarian`, `build_drive_reader`, every `COVERAGE_DATASETS` entry a `FingerprintCheck` |
| Test guard | `tests/conftest.py` | Tests never see real Drive keys (they were present in this container; before this, `build_nse_fo_library` in a test could reach real Drive) |

## Criteria

**1. A real upload works.** MET (strong evidence: live run).
- Code: `GoogleDriveUploadStore.put` `fno/storage/google_drive_upload.py:32`, `_create_file` `:59`, `_holds` `:70`.
- Test: `tests/test_drive_upload.py:78` (`test_a_file_is_saved_in_the_archive_tree_and_read_back_byte_identical`).
- Real run (13 Oct 2026, production classes, `fno-research/_probe/a9_probe.txt`):
  ```
  read back byte-identical: True 47 bytes
  probe Drive ID: 1NM97n35rYzFLZmw0etP70Ljh2ur3X4hq | _probe folder ID: 1Bux-ULqVk7WwEKirEgfh3bkNc0CFjp0c
  same bytes again: no error
  different bytes refused: _probe/a9_probe.txt already exists in Drive with different content
  unchanged after refusal: True
  items in _probe: ['a9_probe.txt']
  probe file deleted (allowed by criterion 1): 204
  ```
  The empty `_probe` folder is left in place: only the probe file may be deleted. Before building, a raw-HTTP probe
  (token, upload, read-back, delete) also passed. Live check of the retry design: creating a folder and a file twice
  with the same reserved ID gave `200` then `409 fileIdInUse`.

**2. Same bytes change nothing; different bytes raise `RawFileConflict` and change nothing.** MET (strong evidence).
- Code: `fno/storage/google_drive_upload.py:32-45` (fresh lookup, compare, refuse, create only if absent).
- Tests (fake Drive): `tests/test_drive_upload.py:89` (same bytes = no create; different = conflict, original kept),
  `:100` (another writer's file is found despite a cached "absent"; no twin folders), `:112` (a create retried after a
  dropped connection makes no second copy), `:120` (Drive's MD5 differs = `StoredCopyDamaged`).
- Real check: criterion 1 output above (same bytes no error; different bytes refused; unchanged).

**3. Participant OI complete in Drive, SHA-256 matching the manifest.** MET (strong evidence: live run).
- The librarian run, 2019-01-01 to 2026-10-12 (about 1 h 55 min, NSE paced at 1 request/s):
  ```
  nse/derivatives/participant-oi 2019-01-01 to 2026-10-12: 1929 sessions, 0 already there and verified, 1929 uploaded, 0 with a sourced exception
  result: complete
  ```
- `python -m fno data-coverage --to 2026-10-12` (the participant-OI validator is `FingerprintCheck` against
  `tools/nse_raw_download/manifest_participant_oi.csv`, `fno/storage/wiring.py`, `COVERAGE_DATASETS`):
  ```
  nse/derivatives/fo-bhavcopy-legacy   2019-01-01 2024-07-05     1367    1366       0       0
  nse/derivatives/fo-bhavcopy          2024-01-01 2026-10-12      690     690       0       0
  nse/indices/index-close              2019-01-01 2026-10-12     1929    1929       0       0
  nse/derivatives/participant-oi       2019-01-01 2026-10-12     1929    1929       0       0
  excepted nse/derivatives/fo-bhavcopy-legacy 2021-03-30: ... (A1's sourced exception)
  result: complete
  calendar sha256 6101c8746fe17926498fbfcac895b7aad5218c4653982bba82337b6b5dea3961
  ```
- Before uploading I checked that the calendar's sessions equal the manifest's files exactly: 1,929 and 1,929, none on
  either side only.

**4. The librarian is resumable.** MET (strong evidence).
- Code: `fno/storage/librarian.py:66-90` (stored file first; only missing files are fetched).
- Test: `tests/test_librarian.py:96` (`test_a_stopped_run_restarted_uploads_only_what_is_missing`: stopped after 2,
  restart fetches only the other 2).
- Real rerun after the upload: `data-librarian participant-oi --from 2026-09-01 --to 2026-10-12` gave
  `28 sessions, 28 already there and verified, 0 uploaded`.

**5. An expired or refused token gives a clear error and an alert naming the fix, never a silent skip.** MET (strong
evidence for the code path; the real expiry has not happened yet).
- Code: `raise DriveSignInRefused` `fno/storage/owner_token.py:38`; `except DriveSignInRefused` with the alert
  `fno/storage/librarian_cli.py:60` (message `SIGN_IN_REFUSED` `:16`: Google's code, then
  `python3 tools/gdrive_oauth_setup.py <client_secret JSON>`, the new `FNO_GDRIVE_OAUTH_REFRESH_TOKEN`, and publishing
  the OAuth app as the lasting fix). Alert goes through `build_alert_sender` (#fno-desk, `FNO_SLACK_BOT_TOKEN`).
- Tests: `tests/test_librarian.py:131` (refusal at sign-in: exit 1, one alert naming `invalid_grant`, the tool and the
  setting), `:145` (refusal midway, as on a 401 re-sign-in: alert too), `tests/test_drive_upload.py:182` (error code
  only, never free text or a value).

**6. No credential value in any file, log or message.** MET (strong evidence).
- Test: `tests/test_librarian.py:131` greps the printed output and the alert for the three fake secret values;
  `tests/test_drive_upload.py:182` for the exception text.
- Real check (values compared by the shell, never printed): each of the four Drive secrets found 0 times in the last
  50 commits' trees and 0 times in every run log of this session. `python tools/check_records.py`: clean.
- `tests/conftest.py` removes all Drive secrets from every test's environment.

**7 (added by the orchestrator from judge 18, minor 1). SHA-256 manifests for every NSE dataset in Drive.** MET (strong
evidence).
- Code: `fno/storage/fingerprints.py`; wiring `fno/storage/wiring.py:146-150` (all four datasets `FingerprintCheck`).
- New manifests read from Drive (read-only): `tools/nse_raw_download/manifest_fo_bhavcopy_legacy.csv` (1,366 files)
  and `manifest_index_close.csv` (1,929 files), header `date,url,status,sha256,size_bytes` (status 200 rows only: a
  Drive-made manifest says nothing about days without a file). The current format keeps the laptop tool's
  `manifest.csv` (now wired; it was not before).
- Tests: `tests/test_fingerprints.py:26`, `:35` (read back by the coverage check), `:52` (a live difference is
  reported as an NSE rewrite, archive kept), `:60` (every dataset checks a committed manifest).
- Coverage: output under criterion 3 (0 damaged in all four).
- Spot-check of 10 files against NSE's live bytes (fixed seed 13102026): all 10 `identical`
  (fo-bhavcopy 2024-08-05, 2025-10-09, 2026-09-21; legacy 2020-03-12, 2022-07-25, 2024-06-14; index-close and
  participant OI 2020-03-12, 2025-05-06). No NSE rewrite found.

## Checks

`python -m pytest -q`: 598 passed. `ruff check fno tests tools`: all checks passed. `python tools/check_imports.py`:
clean. `python tools/check_records.py`: clean. No file over 350 lines (`tests/test_code_size.py` passes; largest new
file `fno/storage/librarian.py`, about 120 lines).

## Doubts and limits (stated plainly)

- **The refresh token may expire in 7 days** if the owner's Google app is still in "Testing" (not verified from here).
  The alert path is tested, but a real expiry has not been seen. Lasting fix for the owner: publish the OAuth app.
- **`manifest.csv` ends on 9 Oct 2026**, so the current-format file of 12 Oct 2026 is checked by content only, not
  SHA-256. Extending it means editing the laptop tool's manifest; I left it as it was.
- **A Drive 403 seen live** during my parallel read runs (five processes at once) crashed the readers with a bare
  403. I could not capture Google's reason afterwards (the files read fine and 600 quick listings gave no error). The
  fix retries Google's documented 403 rate-limit reasons and now names the reason on any error, so a different cause
  will show itself. The final coverage run, alone, passed with no error. Some evidence that this was a rate limit;
  not proven.
- **One writer at a time** is assumed. Lookups are refreshed before every create, and reserved IDs make retries
  safe, but two librarians started together could still both create the same new folder name in the same instant
  (the next read would then raise `RawFileConflict` "2 items named", never pick one silently).
- **Wiring change**: when the four upload settings exist, any `RawFileLibrary` (e.g. `nifty-panel`) now archives what
  it fetches from NSE into Drive instead of the local folder. That is what the story asks; it also means an expired
  token makes building such a library fail loudly.
- `LIBRARIAN_DATASETS` holds only participant OI: other datasets need their own story (A9 scope).
