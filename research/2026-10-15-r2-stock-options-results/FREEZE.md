# Freeze record: R2 stock options around results (feasibility)

Frozen at commit `93a19c318003994c6cedd070d038ee89d45dd74e` (15 Oct 2026 IST), before any data of this study was
read: no stock-option volume, open interest, lot value, strike step, price, spread or event move. Nothing ran before
it. Ledger trial 53 names this commit.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `89947b4cacbdf4ad87ee956dfb6dca6e5e2b4cc1241b6556a8e1515be6e40a6b` |

The analysis script's hash is added here in its own commit before the first full run (`PROTOCOL.md` section 11).
Merging this branch into `main` must keep the freeze commit in history (a merge, never a squash or rebase), or B4's
ledger guard refuses the trial.

Check before reading results: `sha256sum -c` on the files above at the run commit.

## Pre-run amendment 1 (15 Oct 2026)

`AMENDMENT_1.md` (judge 97's follow-ups 1-3 and 5, and data details the protocol leaves open) is committed before
`study.py` and before any data of this study is read. It changes no threshold and no rule chosen with an outcome in
view; `PROTOCOL.md` keeps its hash above and governs.

| File | SHA-256 |
|---|---|
| `AMENDMENT_1.md` (revision 1, judge 109; the first version was `8b36416b...1da47d`) | `3b84ecae577fd3d8ab2426d788646e19fcbb338e3d40551fe41cf27e6435d1e6` |

## Analysis script, frozen before the run (PROTOCOL.md section 11; judge 97 follow-up 2)

`study.py --run` refuses to run unless each file below hashes to its row here and the folder has no uncommitted
change. Tested on synthetic data only (`tests/research/test_r2_*.py`, 100 tests with `tests/research`; mutation proof
`mutation_proof.py`: 57 of 57 planted bugs caught). Criterion 3's annualisation is `r2study/rules.py`
`clusters_a_year` (clusters counted in the decision window / (window days / 365.25)).

| File | SHA-256 |
|---|---|
| `AMENDMENT_2.md` | `7be4e595ebe5c64cf652a52f7a40e7ba03187fc7c42e2978215001b4c05d0c19` |
| `study.py` | `c13cd672f7da7304378859f59fd22f903b66713c365b433f988ac8c8f6c11261` |
| `snapshot.py` | `03a0d20a269bc96c0f8f90d136dcd651b30482c43bcc40472b386d4896f070a7` |
| `r2study/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `r2study/analysis.py` | `55bd4d9d00c8507a09eb8656715ebc03db7c5274ae0e559a8c6dc740b252efb0` |
| `r2study/bhav.py` | `7df230ccdda77f91ac97d9879a1e870f3967f3b0e2bcb8419dfd0a7a67349451` |
| `r2study/clusters.py` | `5136a920f86f60553b69e0e86b02878bad4bc7f65a924108aa99d9b236ebd3a9` |
| `r2study/descriptive.py` | `fbfcc0e8712064a143b608da4b9290c6697e9ea04c86f960264d9737049ba0e5` |
| `r2study/evaluate.py` | `5752f06b3f54297047b59a2599f32d3ce65eb5fef181c5905faec61b365faf75` |
| `r2study/events.py` | `8984c902e026bb3680ea34650faf0b01d2278c59925736a73e216f58d515fc86` |
| `r2study/inputs.py` | `743efb58e6e1464fbaf80897f995da7d8a39be899c3c880524a3a29a5053e007` |
| `r2study/lots.py` | `b5cdd4d1fb25ab018e6af810d5469c27c88c5f1248628e71e6fd1406a5681b40` |
| `r2study/markets.py` | `56c3dcc4535f8cf957a956b63406f0d8b4355bf3bb78259f186dc3c87919dfdf` |
| `r2study/moves.py` | `d0049da9dcc0273065e807c76f25ae0b402996257cb5d61d142e1c42c2bb025f` |
| `r2study/reading.py` | `3cf610090260b46df39237aaa79709d58596e3d270cd786aef4f3a196e019cc2` |
| `r2study/report.py` | `8c806f85a3bc0011d10cd8c5d121299dfc31d3ddde3ead4484350ab75919b69c` |
| `r2study/rules.py` | `82ddceebf88ba4f801044bcb09bbe7a7e4fb69be403499dea4165761d94839e8` |
| `r2study/sessions.py` | `b43fd2d64c3164f12d5d6f88e98052b0845d0fdae736b5192f10371bd10c811a` |
| `r2study/snapshot_capture.py` | `00514a8d8f828bcb2cd5d0c47f72c0c0bb100478a39d1a00e95fad2ef32d2453` |
| `r2study/sources.py` | `c6e86a04a45fe56cb4671720150462b34a8eaa36e0982cad63cbc07306f7b400` |
| `r2study/spreads.py` | `c9785181911453ed07eca29c465b7e71825014116cfae7b2f3d7fd2f4ecc458e` |
| `r2study/stages.py` | `f23084576a599f1caf30063cfc59c53f0c3a1c1d8ff3e0b2160490e7c308f1e1` |
| `r2study/steps.py` | `9ea92cd0581d135160e8cf05c44af43cf847365c8ca85b1a17e300c2f137a792` |
| `r2study/structures.py` | `f14473ea3c2d83164005fa89caf1ad21d3c4364b7e9b2c138b1badc94ad010da` |
| `r2study/wiring.py` | `273417312c343ec683bf8a9606ea41158e4f65e2fade2aa4dfbd4fb5d753fab9` |

## Analysis script, revision 1 (judge 109 addendum 2), frozen before the run

Judge 109 addendum 2 failed adccf53 on three should-fixes, all taken: tests for its eight surviving mutations
(`mutations.json` now 68 plants, 68 caught); the run rebuilds the snapshot's legs from the raw Drive file and the
previous session's F&O file and applies amendment 2 item 10's 20% rule itself (`r2study/snapshot_legs.py`); the
results name the snapshot by its Drive path and SHA-256, checked against the hash `snapshot.py` printed. Minors:
`check_frozen` also hashes `PROTOCOL.md` and both amendments; a market-hours filing on a non-regular session (muhurat)
is after-hours for R; the default cache is outside the checkout (`~/.cache/r2-study`). `snapshot.py` and
`r2study/snapshot_capture.py` are unchanged from adccf53 (the snapshot is taken with exactly those files).

**Disclosure (judge 109 addendum 2, minor 4):** before this freeze, `snapshot.py --ready` parsed the 14 Oct 2026 F&O
file and NSE's event calendar in memory and printed only "72 F&O stocks with results in the next 10 sessions". Judge
109 addendum 2 ruled it harmless. No other study data was parsed before this freeze.

`study.py --run` refuses to run unless every file below hashes to its row and the folder is clean.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `89947b4cacbdf4ad87ee956dfb6dca6e5e2b4cc1241b6556a8e1515be6e40a6b` |
| `AMENDMENT_1.md` | `3b84ecae577fd3d8ab2426d788646e19fcbb338e3d40551fe41cf27e6435d1e6` |
| `AMENDMENT_2.md` | `7be4e595ebe5c64cf652a52f7a40e7ba03187fc7c42e2978215001b4c05d0c19` |
| `study.py` | `9600da29a1d7352ab20a336acee3940621e1d328d628713a2b18746d1fb952ea` |
| `snapshot.py` | `03a0d20a269bc96c0f8f90d136dcd651b30482c43bcc40472b386d4896f070a7` |
| `r2study/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `r2study/analysis.py` | `2a9f0c1ea7942b0516a0ed18e2dd656b69e57f0da47f3a0749e004d3a83cc9f8` |
| `r2study/bhav.py` | `7df230ccdda77f91ac97d9879a1e870f3967f3b0e2bcb8419dfd0a7a67349451` |
| `r2study/clusters.py` | `5136a920f86f60553b69e0e86b02878bad4bc7f65a924108aa99d9b236ebd3a9` |
| `r2study/descriptive.py` | `fbfcc0e8712064a143b608da4b9290c6697e9ea04c86f960264d9737049ba0e5` |
| `r2study/evaluate.py` | `5752f06b3f54297047b59a2599f32d3ce65eb5fef181c5905faec61b365faf75` |
| `r2study/events.py` | `8984c902e026bb3680ea34650faf0b01d2278c59925736a73e216f58d515fc86` |
| `r2study/inputs.py` | `743efb58e6e1464fbaf80897f995da7d8a39be899c3c880524a3a29a5053e007` |
| `r2study/lots.py` | `b5cdd4d1fb25ab018e6af810d5469c27c88c5f1248628e71e6fd1406a5681b40` |
| `r2study/markets.py` | `56c3dcc4535f8cf957a956b63406f0d8b4355bf3bb78259f186dc3c87919dfdf` |
| `r2study/moves.py` | `d0049da9dcc0273065e807c76f25ae0b402996257cb5d61d142e1c42c2bb025f` |
| `r2study/reading.py` | `3cf610090260b46df39237aaa79709d58596e3d270cd786aef4f3a196e019cc2` |
| `r2study/report.py` | `8c806f85a3bc0011d10cd8c5d121299dfc31d3ddde3ead4484350ab75919b69c` |
| `r2study/rules.py` | `82ddceebf88ba4f801044bcb09bbe7a7e4fb69be403499dea4165761d94839e8` |
| `r2study/sessions.py` | `1f1a2cba1fd59717366710082dda723caa7135f6d0a4a78dbb4836ee231c53c6` |
| `r2study/snapshot_capture.py` | `00514a8d8f828bcb2cd5d0c47f72c0c0bb100478a39d1a00e95fad2ef32d2453` |
| `r2study/snapshot_legs.py` | `82987f705ca9c28a1dfdaef48245d71408ac9f7314c67c1f5e256b1fb1d435ee` |
| `r2study/sources.py` | `c6e86a04a45fe56cb4671720150462b34a8eaa36e0982cad63cbc07306f7b400` |
| `r2study/spreads.py` | `c9785181911453ed07eca29c465b7e71825014116cfae7b2f3d7fd2f4ecc458e` |
| `r2study/stages.py` | `f23084576a599f1caf30063cfc59c53f0c3a1c1d8ff3e0b2160490e7c308f1e1` |
| `r2study/steps.py` | `9ea92cd0581d135160e8cf05c44af43cf847365c8ca85b1a17e300c2f137a792` |
| `r2study/structures.py` | `f14473ea3c2d83164005fa89caf1ad21d3c4364b7e9b2c138b1badc94ad010da` |
| `r2study/wiring.py` | `3f0117f285a4ea2ee6d3f368ef67101b5ab4ea93d7f60c63cbc73015bb58d6e3` |
