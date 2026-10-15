# R2: stock options around results, feasibility study

Registered, **not run**. `PROTOCOL.md` is the frozen registration (ledger trial 53); `AMENDMENT_1.md` is the judged
pre-run amendment (no threshold changed); `FREEZE.md` names the commits and
hashes. The analysis script and its results are added later, as `PROTOCOL.md` section 11 says. Idea card:
`research/ideas/R2.md`.

## Running (after the judge's PASS on the frozen script)

1. `python study.py --fetch` copies the raw F&O and index-close files to `~/.cache/r2-study`, each checked against its
   manifest row.
2. `python snapshot.py --ready`, then `python snapshot.py` between 14:00 and 15:00 IST. It prints
   `raw sha256 <hash>` and `Drive: raw/<path>`.
3. `python study.py --run --snapshot <path> <hash>`. `<path>` is the printed Drive path **without** the leading
   `raw/` (the run reads Drive's `raw` area), and `<hash>` is the printed SHA-256. The run refuses a different file.
