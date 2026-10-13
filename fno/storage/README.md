# Raw data archive (fno/storage)

All project files live under **one project folder** (`fno-research`), so nothing spreads across the rest of the
owner's Drive. Inside it, each kind of file has its own area; the tree is identical on disk and in Google Drive:

```
fno-research/                        local: the --keep-raw folder; Drive: the shared folder (FNO_GDRIVE_FOLDER_ID)
  raw/                               area: original downloads, never changed (wiring.RAW_AREA)
    <publisher>/<market>/<dataset>/  what the files are, readable from the path
      <YYYY>/<MM>/                   one folder per month of the file's date
        <original file name>         the publisher's own name, unchanged
  <other area>/                      future kinds of files (exports, backups...), each in its own area
```

Example: `fno-research/raw/nse/derivatives/fo-bhavcopy/2024/01/BhavCopy_NSE_FO_0_0_0_20240102_F_0000.csv.zip`.

Datasets so far (all from NSE's public archive, `raw_source.py`):

| Folder | Source class | Files | Dates |
|---|---|---|---|
| `nse/derivatives/fo-bhavcopy` | `NseDailyFoSource` | F&O, current UDiFF format | 1 Jan 2024 onwards |
| `nse/derivatives/fo-bhavcopy-legacy` | `NseLegacyFoSource` | F&O, old format (`fo02JAN2019bhav.csv.zip`) | up to 5 Jul 2024 |
| `nse/indices/index-close` | `NseIndexCloseSource` | daily index closes (NIFTY 50, NIFTY Bank, India VIX...) | 2017 onwards (2017-18: warm-up, A10) |
| `nse/derivatives/participant-oi` | `ParticipantOiSource` | participant-wise open interest (client, DII, FII, pro; story A8) | 2019 onwards |
| `nse/equities/cm-bhavcopy` | `NseEquityBhavcopySource` | capital-market file, UDiFF (every security's prices and volume; P6) | 1 Oct 2025 onwards |
| `nse/equities/security-delivery` | `NseDeliverySource` | security-wise file with delivery % (`sec_bhavdata_full_DDMMYYYY.csv`; P6) | 1 Oct 2025 onwards |
| `nse/equities/equity-list` | `EquityListSource` | the list of listed companies (`EQUITY_L.csv`), one copy per day fetched (P6) | 13 Oct 2026 onwards |
| `nse/indices/nifty500-list` | `Nifty500ListSource` | the Nifty 500's members and industries (`ind_nifty500list.csv`), per day fetched (P6) | 13 Oct 2026 onwards |

NSE's reference lists have no date in their name and are replaced in place, so each copy is filed under the day it was
fetched: `<dataset>/<YYYY>/<MM>/<DD>/<original name>` (`snapshot_source.py`; `python -m fno data-snapshot <name>`).

Both F&O formats are read into one record format by `fno/fo_bhavcopy.py` (originals stay unchanged); the old format's
missing underlying price for index options comes from the index-close file of the same day.

Rules:
- Nothing is written loose in the project folder: every store is wrapped in an `AreaStore` for its area.
- Each source declares its own `dataset` folder and builds paths with `RawFileSource.dated_path` (one place).
- Lower-case folder names, words joined by hyphens; publisher first (`nse`, `bse`, `groww`, ...), then the
  market (`derivatives`, `equities`, `indices`, ...), then the dataset.
- Raw files never change. Saving the same bytes again does nothing; different bytes at an existing path raise
  `RawFileConflict` and nothing is overwritten. Two Drive items with the same name in one folder also raise it.
- Paths are relative, with no empty, `.` or `..` parts.
- Derived files (extracts, results) live with the research that made them, not in the raw archive.

## Reading and writing Google Drive

- **Reads** use the service account (`GoogleDriveStore`, Viewer on the folder; `FNO_GDRIVE_SERVICE_ACCOUNT_JSON`).
- **Uploads** sign in as the owner (`GoogleDriveUploadStore`, story A9), because a service account has no storage
  quota. Settings: `FNO_GDRIVE_FOLDER_ID` plus `FNO_GDRIVE_OAUTH_CLIENT_ID`, `FNO_GDRIVE_OAUTH_CLIENT_SECRET` and
  `FNO_GDRIVE_OAUTH_REFRESH_TOKEN`, made once with `tools/gdrive_oauth_setup.py`. Missing folders are created; every
  new folder and file gets an ID reserved from Drive first, so a retried create cannot make a duplicate; each upload is
  checked against Drive's MD5 of what it received.
- Both share `DriveSession`: one fresh sign-in on a 401, growing waits on 429, 5xx and dropped connections.
- While the owner's Google Cloud app is in "Testing", the refresh token expires after 7 days. The librarian then stops
  with `DriveSignInRefused` and alerts #fno-desk with the fix (rerun the setup tool, or publish the app).

## The librarian

`python -m fno data-librarian <participant-oi|index-close> [--from YYYY-MM-DD] [--to YYYY-MM-DD]` fills the dataset's
gaps in Drive from NSE (`librarian.py`): for each session (NSE's calendar) it keeps a verified file already there, else
fetches the file through the paced NSE session, verifies it (schema, and SHA-256 where the manifest has it) and uploads
it. A damaged file in Drive is reported and never replaced. Run it again after a stop: only missing files are fetched.
Each new dataset needs its own story before it is added to `wiring.LIBRARIAN_DATASETS` (A9: participant OI; A10: index
closes).

## Manifests: a SHA-256 for every archived file

`research/data/manifests/<dataset>.csv` (`date,url,status,sha256,size_bytes`, one row per archived file) is the only
manifest the code reads (`manifest_folder.py`), produced by one code path:
- **at save time**: the Drive upload store is wrapped in `FingerprintingStore`, so every file saved (by the librarian
  or by a `RawFileLibrary` archiving what it fetched) gets its row in the same operation, after Drive accepted it; a
  different SHA-256 for a day that already has a row is refused;
- **whole, from Drive**: `python -m fno data-fingerprints <dataset>` reads every file (read-only) and writes the
  manifest when the dataset has none (an existing manifest is never overwritten); `--spot-check N` compares N files
  with NSE's live bytes.

`python -m fno data-coverage` checks every file's SHA-256 against its row; a file without a row is counted under
"no sha" and listed, and the result is not "complete" until it has one. Rows written at save time are only evidence
once committed: every `data-librarian` run, finished or stopped, commits and pushes `research/data/manifests/`
(`manifest_commit.py`: `git pull --no-rebase` first, the record-scan hook on, never `--no-verify`; a refused commit is
printed, not bypassed), and `data-coverage` lists any manifest file still uncommitted and exits 1. The laptop tool's manifests in
`tools/nse_raw_download/` serve that tool only; the code no longer reads them (the regenerated ones agree with them on
every file both have).

Adding a store (S3, Dropbox) or a source (another exchange) means one new class behind `RawFileStore` or
`RawFileSource`, and one line in `wiring.py`.
