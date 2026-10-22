# Freeze record: EDGE1, simple rule-based option trades after real costs

Protocol and analysis code frozen at commit `b4a9a8559a211af249a5b83dea8c7a85c36bf738` (22 Oct 2026, about 13:20 IST), protocol revision 6.

At that point no variant had been run on real data: nothing was priced, no P&L, G1 figure or settlement value was
read. The build read only counts and dates: the lot series and its circular check (`LOT_CHECK.md`), and the input
probe (cycles, missing lots, settlements, entry and exit chains per run; revision 6). Every result is exploratory
(protocol section 2).

Tested on synthetic data only: `tests/research_edge1/`, 61 tests. `mutation_proof.py` catches 32 of 32 planted bugs,
among them the seal (option prices, the sessions filter loosened about 30 days, rows at load), the triggers' edges,
an exit pad at settlement, the bootstrap block and re-centring, the floors, Holm, the nomination's conditions, run 2
testing G1 failures, the STT dates, the lot schedule and the derived lot used as the lot, the moved-expiry relabel,
the SPAN file's point-in-time checks and a deleted final.json allowing a second look.

`study.py` refuses `--select` and `--final` unless every file below matches its hash and `research/edge1` is clean,
and refuses `--final` unless `selection.json` is committed and no `final.json` exists now or in any earlier commit
(protocol section 13). Merging this branch into `main` must keep this commit in history (a merge, never a squash or
rebase): the ledger rows name it.

Check before reading results: `sha256sum` of each file below at the run commit.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `70d8e2451e5bc0d5e5fd8157f7f4f1f962b27cf66d2172fd93ad5d036776f077` |
| `LOT_CHECK.md` | `6df30e9bdd17994af0e56b8c0e09aa09b89306a073e977c77b52c41701309699` |

## Shared code the study changed (checked by `sha256sum` at the run commit, outside the guard)

| File | SHA-256 | Change |
|---|---|---|
| `fno/research_engine/structures.py` | `e4e9c13adb2d3d84210c19763f126a81c9d8430dc2302e96b870b0ca9e2cfac7` | `ShortCondor(offset)`, default unchanged (SC3) |
| `fno/forecast_scoring/block_bootstrap.py` | `28d0ef82d93792bea98e44d4a88e13654c504eba6eaea7fdbed3dfd3044cb91b` | `resampled_means(..., block=)`, default G4's 20 |

## Revision 7 (owner, 22 Oct 2026, after run 1: "fix and re-run, report both"), frozen at `f43006c03157d4d08f81ee89f4dd9ec1ae7c5277`

Run 1 at 3152ed44 had been read (its `selection.json` is now `selection_rev6.json`, sha256
`edc4fd83c2c3dbfbcb8db16b4ea4a7ad4b6e4c8c15a3b827eea2da65acac705c`, committed d4ea08d6). Run 2 had not been run: no row after 14 Feb 2023 had
been priced. The change is protocol section 7's impossible-price rule and its section 14 entry, in `trade.py` and
`report.py` only; tests 68, `mutation_proof.py` 34 of 34. Shared engine files unchanged (hashes above).

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `f7d4842b6d237e09b0147d6d533078f2224354251fad27eca37a225b2bfa3a1d` |
| `selection_rev6.json` | `edc4fd83c2c3dbfbcb8db16b4ea4a7ad4b6e4c8c15a3b827eea2da65acac705c` |

## Code frozen at 3152ed44 (revision 6; superseded by revision 7, run 1 of `selection_rev6.json`)

| `PROTOCOL.md` | `70d8e2451e5bc0d5e5fd8157f7f4f1f962b27cf66d2172fd93ad5d036776f077` |
| `cards.py` | `0279d2016e7c2d3e71572ec42e2b046ff6be7cd1fb221edc4bd937bb4a75c387` |
| `edge1study/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `edge1study/day_files.py` | `f8235abeac26cdf95788be02de8b1d43cb23a7b518cb38b9a37cd5d0e292879a` |
| `edge1study/expiries.py` | `66c52bf023042fe62747688f1703279f8969b08e9d26ac36aea4ac7dd9825308` |
| `edge1study/guard.py` | `9798196576f4c39bd24c0d6d1f5f9420f69c994de5248e5fad2633633bd1e32b` |
| `edge1study/inputs.py` | `c5344deb85416cb9cab1e6f91060437c4e515b840871349a0a548fcbe96aa5d1` |
| `edge1study/lots.py` | `7498d835b9cb74fd9b78b5792a93d5cb956fb91d0e535b44d0d4da39b1c6764b` |
| `edge1study/margin.py` | `b6623e54cd4c835ef5927ef667822f0803c6d85417a28e475bf823861cdc0b7e` |
| `edge1study/panels.py` | `56173d687553a41ad677af0e4d60d5ed700b755e821419e3d4024fa6c46082a2` |
| `edge1study/report.py` | `64c5846aece6b35762082acd5ff552c4e81f2654f522adcdd2d7874514ded14d` |
| `edge1study/runner.py` | `fca02d4c28948f6a739d4e685f5fbaa4e81c0613ce3e9c6b22def60d6b170730` |
| `edge1study/runs.py` | `e61893739ed01d3df08d6425814d12753bf02b9aa72761efe63ac48803ed0deb` |
| `edge1study/stats.py` | `20e943f227c2d21cc3a4ebc416f74d16bc67e563b56834be89785ff522e358e1` |
| `edge1study/structures.py` | `48700a304ef259549b0bce3c207940375cf9853dbf2d03a5f1fd2223e886790a` |
| `edge1study/stt_history.py` | `28189c216b74bf0119418e5a894401729c1fe2650cfb28c72ea091bd3f200c6e` |
| `edge1study/trade.py` | `b8507c52452bc5e28c0aae531771dbf703412d95a304c5f52c58856a10363968` |
| `lot_changes.py` | `0703373177439e3c4d124e8a380d2c8f33d75c0db8f5b8f1495a4299c089d0b8` |
| `mutation_proof.py` | `e1872dfd76bbcfa94f82bf950d118780387b886069c898c4206fac383bbbd93a` |
| `study.py` | `7d3718ab4f59ecec0f4d76b8f0775775ab7bce89ecd2296f2e03924e049ce3a5` |

## Analysis code

| `PROTOCOL.md` | `f7d4842b6d237e09b0147d6d533078f2224354251fad27eca37a225b2bfa3a1d` |
| `cards.py` | `0279d2016e7c2d3e71572ec42e2b046ff6be7cd1fb221edc4bd937bb4a75c387` |
| `edge1study/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `edge1study/day_files.py` | `f8235abeac26cdf95788be02de8b1d43cb23a7b518cb38b9a37cd5d0e292879a` |
| `edge1study/expiries.py` | `66c52bf023042fe62747688f1703279f8969b08e9d26ac36aea4ac7dd9825308` |
| `edge1study/guard.py` | `9798196576f4c39bd24c0d6d1f5f9420f69c994de5248e5fad2633633bd1e32b` |
| `edge1study/inputs.py` | `c5344deb85416cb9cab1e6f91060437c4e515b840871349a0a548fcbe96aa5d1` |
| `edge1study/lots.py` | `7498d835b9cb74fd9b78b5792a93d5cb956fb91d0e535b44d0d4da39b1c6764b` |
| `edge1study/margin.py` | `b6623e54cd4c835ef5927ef667822f0803c6d85417a28e475bf823861cdc0b7e` |
| `edge1study/panels.py` | `56173d687553a41ad677af0e4d60d5ed700b755e821419e3d4024fa6c46082a2` |
| `edge1study/report.py` | `27a3a37dda4ba8a2d4435407c69b3100c62bec4687fc1f9364518ddf07c59bff` |
| `edge1study/runner.py` | `fca02d4c28948f6a739d4e685f5fbaa4e81c0613ce3e9c6b22def60d6b170730` |
| `edge1study/runs.py` | `e61893739ed01d3df08d6425814d12753bf02b9aa72761efe63ac48803ed0deb` |
| `edge1study/stats.py` | `20e943f227c2d21cc3a4ebc416f74d16bc67e563b56834be89785ff522e358e1` |
| `edge1study/structures.py` | `48700a304ef259549b0bce3c207940375cf9853dbf2d03a5f1fd2223e886790a` |
| `edge1study/stt_history.py` | `28189c216b74bf0119418e5a894401729c1fe2650cfb28c72ea091bd3f200c6e` |
| `edge1study/trade.py` | `f54b6630d5935f95267421b6cce37fc82c8e8967b60a00ec536bb3b99b75626c` |
| `lot_changes.py` | `0703373177439e3c4d124e8a380d2c8f33d75c0db8f5b8f1495a4299c089d0b8` |
| `mutation_proof.py` | `39b79ec8b9f1d98e49448f3161328a82a9ea19e9063e636ab2cbb227d7f1ea87` |
| `study.py` | `7d3718ab4f59ecec0f4d76b8f0775775ab7bce89ecd2296f2e03924e049ce3a5` |
