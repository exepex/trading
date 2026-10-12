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

Rules:
- Nothing is written loose in the project folder: every store is wrapped in an `AreaStore` for its area.
- Each source declares its own `dataset` folder and builds paths with `RawFileSource.dated_path` (one place).
- Lower-case folder names, words joined by hyphens; publisher first (`nse`, `bse`, `groww`, ...), then the
  market (`derivatives`, `equities`, `indices`, ...), then the dataset.
- Raw files never change. Saving the same bytes again does nothing; different bytes at an existing path raise
  `RawFileConflict` and nothing is overwritten. Two Drive items with the same name in one folder also raise it.
- Paths are relative, with no empty, `.` or `..` parts.
- Derived files (extracts, results) live with the research that made them, not in the raw archive.

Adding a store (S3, Dropbox) or a source (another exchange) means one new class behind `RawFileStore` or
`RawFileSource`, and one line in `wiring.py`.
