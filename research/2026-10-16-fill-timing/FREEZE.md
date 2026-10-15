# Freeze record: FT1, the fill-timing study (story E8a)

Frozen at commit `47d15989a4045a1804b235fcb5fad13ec7e2a7ea` (15 Oct 2026 IST), before any option or future price of this study was read. Only the
coverage probe ran before it, and it recorded symbols and candle counts, never a price (`probe.csv`). Ledger trial
54 names this commit.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `0dea9e11a01066ac811eba944ffb64973574a75de0c26b4640bf19399fe1e238` |
| `probe.csv` | `6cefa0cac8b585c2e220129f32e33bef19ec191954bb370b12a27ae91a167d58` |

The analysis code's hashes are added here in their own commit before the full fetch (`PROTOCOL.md` section 19).
Merging this branch into `main` must keep the freeze commit in history (a merge, never a squash or rebase), or B4's
ledger guard refuses the trial.

Check before reading results: `sha256sum -c` on the files above at the run commit.
