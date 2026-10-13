# Raw archive manifests (stories A9, A10)

One file per raw dataset in Drive (`fno-research/raw/...`): `<dataset>.csv` with columns
`date,url,status,sha256,size_bytes`, one row per archived file (status 200), sorted by date. They prove later that no
archived file changed: `python -m fno data-coverage` compares every file's SHA-256 with its row, and a file without a
row keeps the result from being "complete".

| File | Dataset | How it was made |
|---|---|---|
| `fo-bhavcopy.csv` | current F&O format (2024 on) | read from Drive, 13 Oct 2026 (`data-fingerprints`); agrees with the laptop tool's `manifest.csv` on all 689 files both have |
| `fo-bhavcopy-legacy.csv` | old F&O format (2019 to 5 Jul 2024) | read from Drive, 13 Oct 2026 |
| `index-close.csv` | index closes | read from Drive for 2019 on (13 Oct 2026); 2017-18 rows written as each file was saved (A10) |
| `participant-oi.csv` | participant OI | read from Drive, 13 Oct 2026; agrees with `manifest_participant_oi.csv` on all 1,929 files |

New files get their row when they are saved (`FingerprintingStore`, `fno/storage/manifest_folder.py`). A row is never
edited or deleted by hand; a different SHA-256 for a day that has a row is refused by the code.
