# Raw data archive (fno/storage)

Large static files are kept in one tree, identical on disk and in Google Drive:

```
<root>/                              local: the --keep-raw folder; Drive: the shared root folder (FNO_GDRIVE_FOLDER_ID)
  <publisher>/<market>/<dataset>/    what the files are, readable from the path
    <YYYY>/<MM>/                     one folder per month of the file's date
      <original file name>           the publisher's own name, unchanged
```

Example: `nse/derivatives/fo-bhavcopy/2024/01/BhavCopy_NSE_FO_0_0_0_20240102_F_0000.csv.zip`.

Rules:
- Each source declares its own `dataset` folder and builds paths with `RawFileSource.dated_path` (one place).
- Lower-case folder names, words joined by hyphens; publisher first (`nse`, `bse`, `groww`, ...), then the
  market (`derivatives`, `equities`, `indices`, ...), then the dataset.
- Raw files never change. Saving the same bytes again does nothing; different bytes at an existing path raise
  `RawFileConflict` and nothing is overwritten. Two Drive items with the same name in one folder also raise it.
- Paths are relative, with no empty, `.` or `..` parts.
- Derived files (extracts, results) live with the research that made them, not in the raw archive.

Adding a store (S3, Dropbox) or a source (another exchange) means one new class behind `RawFileStore` or
`RawFileSource`, and one line in `wiring.py`.
