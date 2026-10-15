# Response 194: the 92 Drive trial files (list only, nothing deleted)

Builder session 01MKtUHByHsR9cNwaP5KhFYH, 15 Oct 2026, for the orchestrator's clean-up task (owner decision of 16 Oct
2026, `docs/DESK_DECISIONS.md`: "the Drive trial files are listed by name first"). Read-only: Drive was listed through
the repository's own owner sign-in (`build_owner_drive`); nothing was written, moved or deleted.

## Verdict in three lines

- **The 92 are A12's filings trial files, not A4b quote uploads.** The task called them "old A4b test uploads"; that
  is a mix-up. They are the 13 Oct filings trial run (response 56 part 5, judge 51), already listed in
  `research/data/manifests/filings/outside-layout.csv`. A4b left only 4 small probe files in Drive (below, separate).
- **All 92 are safe to delete (strong evidence):** each one has a copy with the same MD5 in the year layout that the
  archive reads, and no sidecar, marker or reader points at the trial copy.
- **One thing changes with the deletion:** `outside-layout.csv` then describes files that no longer exist (its note
  says "kept and never deleted"). The deletion's commit should remove it or mark each row deleted, with the date.

## How the 92 were found and checked

1. Listed every folder and file under the owner's Drive root (about 43,800 files, nothing in the trash). The only
   files that sit directly in a `raw/nse/equities/filings/<category>/<SYMBOL>/` folder, outside a `<YYYY>/` folder,
   are these **92**: IRCTC 37, POLYCAB 37, 360ONE 18; 16,633,282 bytes in all; all created 13 Oct 2026 between 14:15
   and 14:26 UTC (19:45-19:56 IST), the trial run's time.
2. **Each is a trial, not a recorded file:** all 92 match a row of `outside-layout.csv` (path and MD5), the file the
   A12 builder committed on 13 Oct ("trial upload of 13 Oct 2026 before the year folders; ... read by nothing"), and
   the CSV has exactly 92 rows, so nothing is missing or extra. None of them is a quote file: no Groww quote snapshot
   is among them (the two real NIFTY quote files in `raw/groww/derivatives/quote-snapshots/2026/10` are not touched).
3. **Each has its real copy in the year layout:** for every file, the filings manifest (`results-xbrl.csv` or
   `shareholding-xbrl.csv`) has a row for the same filing with the same MD5, and Drive holds that file at
   `<category>/<SYMBOL>/<year of period_end>/<name>` with the same MD5 (92 of 92). That includes 360ONE's 18, which
   judge 51 found without a copy on 13 Oct; the archive queue has since reached 360ONE.
4. **Nothing points at the trial copies:**
   - Committed `.meta.json` sidecars and `.canonical` markers on `main` (20 files): none names any of the 92 files.
   - On all of `main`, the 92 file names appear in only three files: `outside-layout.csv` (the list itself) and the
     two filings manifests, whose rows describe the year-layout copy (`fno/filings/filing.py`, `filing_path(kind,
     symbol, year, filename)`, always puts a year folder in the path).
   - Code: only `fno/filings/coverage.py` looks at files outside the year layout, to count them on a separate line
     ("files outside the year layout (trial run of 13 Oct 2026 ...)"). After the deletion it prints nothing for them.
5. Two of the 92 share an MD5 (360ONE, `INTEGRATED_FILING_NBFC_INDAS_1656845_...` and `..._1656851_...`): two NSE
   filings with identical bytes. Both have their own year-layout copy, so deleting both trial copies loses nothing.

## Not in the 92, for the owner's choice

- **A4b's Drive probes (mine):** 4 files in `_probe/a4b/`, `write-read-20261015T131912.txt`, `...T131925.txt`,
  `...T131937.txt`, `...T132759.txt`, 61 bytes each, created 15 Oct 13:19-13:28 UTC: the write-then-read checks of
  Drive sign-in before A4b's merge. Nothing in the repository names them. Safe to delete with the 92 if the owner
  wants; harmless if kept.
- Seen while listing, other builders' and not trial uploads, so not proposed: the participant-OI `dry-run` folders
  under `derived/` and `pipeline/` (18 small JSON files, written by the O6 pipeline's dry runs) and
  `cards/2026/10/2026-10-15_..._test.json`. Their owners should say whether they are wanted.

## About the Drive IDs

The repository is public, so the table gives the last 8 characters of each Drive ID only (enough to match, not a full
handle). The full IDs are not secrets, but the A4b rule keeps Drive identifiers out of public text. Whoever deletes
should go by **path and MD5** anyway, re-listing just before the deletion, and delete only a file whose path and MD5
match this table and whose year-layout copy still has the same MD5. I can produce the full IDs privately, or run that
checked deletion, on the owner's word.

## The 92 files

| # | Folder (under the owner's Drive root) | File | Bytes | Created (UTC) | Drive ID (last 8) | MD5 | Year-layout copy, same MD5 |
|---|---|---|---|---|---|---|---|
| 1 | `raw/nse/equities/filings/results-xbrl/360ONE` | `INDAS_117829_1362824_28012025022512.xml` | 19970 | 2026-10-13 14:24:47 | …DVVw3BYL | `3202989a736065ec03718523c71e43a7` | `2024/` yes |
| 2 | `raw/nse/equities/filings/results-xbrl/360ONE` | `INDAS_117830_1362830_28012025022703.xml` | 43154 | 2026-10-13 14:24:41 | …2UQSZsg6 | `9f2305f8aed0a44904d8821dbd59e750` | `2024/` yes |
| 3 | `raw/nse/equities/filings/results-xbrl/360ONE` | `INTEGRATED_FILING_NBFC_INDAS_1656841_21042026090738_WEB.xml` | 2084023 | 2026-10-13 14:25:37 | …WEr0TUd1 | `616f23fb49e86aeade4dd196a189f214` | `2026/` yes |
| 4 | `raw/nse/equities/filings/results-xbrl/360ONE` | `INTEGRATED_FILING_NBFC_INDAS_1656845_21042026091311_WEB.xml` | 74545 | 2026-10-13 14:25:34 | …zBAIqaNm | `5556792f651ea2208884c6e1df6bc422` | `2026/` yes |
| 5 | `raw/nse/equities/filings/results-xbrl/360ONE` | `INTEGRATED_FILING_NBFC_INDAS_1656851_21042026091700_WEB.xml` | 74545 | 2026-10-13 14:25:40 | …iE6IN4vN | `5556792f651ea2208884c6e1df6bc422` | `2026/` yes |
| 6 | `raw/nse/equities/filings/results-xbrl/360ONE` | `INTEGRATED_FILING_NBFC_INDAS_1694152_16072026034644_WEB.xml` | 21981 | 2026-10-13 14:25:32 | …dWZy2UJD | `35d17f937e38bea37c9719c92f1db2ca` | `2026/` yes |
| 7 | `raw/nse/equities/filings/results-xbrl/360ONE` | `INTEGRATED_FILING_NBFC_INDAS_1694178_16072026035938_WEB.xml` | 29623 | 2026-10-13 14:25:29 | …lllQhTsS | `0ffe36b02cfb25a0c1e62e9d9e425565` | `2026/` yes |
| 8 | `raw/nse/equities/filings/results-xbrl/360ONE` | `INTEGRATED_FILING_NBFC_INDAS_1694653_16072026075305_WEB.xml` | 2085489 | 2026-10-13 14:25:27 | …X1ScqMx8 | `e24cdf3b2f1c85d50824c0cf5e2675ff` | `2026/` yes |
| 9 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_101179_1029211_19012024033338.xml` | 28404 | 2026-10-13 14:25:17 | …-zBdhEy8 | `f5c38394fa2df3f6ae9c17bc666235be` | `2023/` yes |
| 10 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_101180_1029220_19012024033541.xml` | 48221 | 2026-10-13 14:25:15 | …p3gnMQ2h | `b78de2a96e2b559f5e87d1732f6ab011` | `2023/` yes |
| 11 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_104663_1107165_24042024033751.xml` | 49195 | 2026-10-13 14:25:13 | …zPx3e67p | `13e9736d41e8302689cf6a504adf4da7` | `2024/` yes |
| 12 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_104665_1107187_24042024035513.xml` | 70479 | 2026-10-13 14:25:11 | …fY-G5ZWd | `0bb8fe03b645b5484d2df7ad87edf7ca` | `2024/` yes |
| 13 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_109901_1207581_31072024022301.xml` | 15736 | 2026-10-13 14:25:02 | …zHQDTq3E | `39ac52b8db82c2f8b66da75e2cee1932` | `2024/` yes |
| 14 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_109902_1207587_31072024022530.xml` | 30763 | 2026-10-13 14:24:58 | …aiAlRwE_ | `3515700c12589db7054466233ca21d91` | `2024/` yes |
| 15 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_112987_1284577_22102024013123.xml` | 49974 | 2026-10-13 14:24:55 | …P7JEmf6o | `ac4161a90987260dba537046783bd5c4` | `2024/` yes |
| 16 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_112988_1284581_22102024013326.xml` | 72901 | 2026-10-13 14:24:53 | …9gtmURu5 | `4671ad3008784a488a7e6c34a61c1471` | `2024/` yes |
| 17 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_98666_975565_03112023032214.xml` | 51145 | 2026-10-13 14:25:22 | …blD9r36t | `b5e1296d5224f93b237fb484d74376d0` | `2023/` yes |
| 18 | `raw/nse/equities/filings/results-xbrl/360ONE` | `NBFC_INDAS_98667_975571_03112023032502.xml` | 71658 | 2026-10-13 14:25:20 | …ZSSBYHNG | `361bca1fe084b8314064209779cbacdf` | `2023/` yes |
| 19 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_104096_1055100_14022024041946.xml` | 57495 | 2026-10-13 14:15:23 | …lYjKieaR | `87f525f4f8505a0f43c5b9e11d6b766c` | `2023/` yes |
| 20 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_107950_1145391_29052024064236.xml` | 82588 | 2026-10-13 14:15:21 | …ipQmjc2q | `8f35128651d48a6d1c571346368509a3` | `2024/` yes |
| 21 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_107958_1145462_29052024065559.xml` | 83469 | 2026-10-13 14:15:20 | …Gy6E2xR3 | `6ae26632231e7e9a377ccb92b98d9e03` | `2024/` yes |
| 22 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_112060_1225112_14082024014402.xml` | 36370 | 2026-10-13 14:15:18 | …qHvm0leB | `d4a60de8adb8f759c34dbd037aa3d46c` | `2024/` yes |
| 23 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_112061_1225120_14082024014723.xml` | 36625 | 2026-10-13 14:15:17 | …lSmV9Czv | `cbe51bc3ddd12931b50bc12f142a816d` | `2024/` yes |
| 24 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_114147_1297198_05112024041739.xml` | 76170 | 2026-10-13 14:15:16 | …SlBIcemF | `063f8e197e507381fd631550471491b8` | `2024/` yes |
| 25 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_114148_1297203_05112024041839.xml` | 77191 | 2026-10-13 14:15:14 | …Ja_bNBVx | `7231c3fe5d97744ae771516edae2e3ce` | `2024/` yes |
| 26 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_119822_1379361_12022025015204.xml` | 51507 | 2026-10-13 14:15:13 | …d9o7cFp9 | `7ed5b800bf60241ca21c568bace11d97` | `2024/` yes |
| 27 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_119824_1379368_12022025015330.xml` | 52385 | 2026-10-13 14:15:11 | …8vDQ9kUm | `144aef1391d50e8694905803d749e088` | `2024/` yes |
| 28 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INDAS_99401_980311_08112023025257.xml` | 82431 | 2026-10-13 14:15:24 | …JrPXrfDI | `6fb4a835339490838508c3dfcc7d4c59` | `2023/` yes |
| 29 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1455633_28052025092632_WEB.xml` | 192374 | 2026-10-13 14:15:45 | …3pcxzPVx | `67803a869d5c66ea8757aa62a9951765` | `2025/` yes |
| 30 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1455646_28052025092833_WEB.xml` | 82531 | 2026-10-13 14:15:44 | …shN6C8mh | `a4ba201282f083b85bc1d0f87fc35ced` | `2025/` yes |
| 31 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1512033_13082025073317_WEB.xml` | 35117 | 2026-10-13 14:15:43 | …cOAQ_z5s | `7c27542d0accca35a2adcb7d1f014d59` | `2025/` yes |
| 32 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1512045_13082025073741_WEB.xml` | 35325 | 2026-10-13 14:15:41 | …FTtBFk2z | `9b472c2ffd8e448c5e37e99ede042b97` | `2025/` yes |
| 33 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1568189_07112025055350_WEB.xml` | 191710 | 2026-10-13 14:15:40 | …iP9J7YcD | `a047aff7ecc4aa82eebae85b3ce4fd7e` | `2025/` yes |
| 34 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1568193_07112025055416_WEB.xml` | 81966 | 2026-10-13 14:15:38 | …I6B-rRX9 | `e4da472b71c6b04462c2f2ec11a7b3d3` | `2025/` yes |
| 35 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1572955_12112025085939_WEB.xml` | 177264 | 2026-10-13 14:15:37 | …3-qeCfz4 | `cde7bb5c730ad471d3aa0be49f6511ac` | `2025/` yes |
| 36 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1572958_12112025090010_WEB.xml` | 77395 | 2026-10-13 14:15:35 | …YFNjM_i6 | `3aabd44247aef6a7c88c00ec49473a06` | `2025/` yes |
| 37 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1624447_12022026065316_WEB.xml` | 50124 | 2026-10-13 14:15:34 | …xv27B0qM | `5a0e16eb9ebf95cae0667e9451d79ba7` | `2025/` yes |
| 38 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1624448_12022026065323_WEB.xml` | 49725 | 2026-10-13 14:15:33 | …9v5JWeMy | `f113661d0bc14482cda1e5576066698d` | `2025/` yes |
| 39 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1673643_26052026103824_WEB.xml` | 184975 | 2026-10-13 14:15:31 | …mUaVuk22 | `f6ba1bfc2d60c68d724e383ff89b80d3` | `2026/` yes |
| 40 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1673644_26052026103831_WEB.xml` | 84628 | 2026-10-13 14:15:30 | …LjobaFrW | `badeadeaf3950fce9e0cb2e9f369148f` | `2026/` yes |
| 41 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1713129_12082026084314_WEB.xml` | 30863 | 2026-10-13 14:15:28 | …H1RD3xU0 | `87bb231ba344841c0f59abce8e8b09db` | `2026/` yes |
| 42 | `raw/nse/equities/filings/results-xbrl/IRCTC` | `INTEGRATED_FILING_INDAS_1713130_12082026084321_WEB.xml` | 30838 | 2026-10-13 14:15:27 | …Uiv2K_3G | `4e077598130ee3d4eaad4392259e2e4e` | `2026/` yes |
| 43 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_101140_1026990_18012024041516.xml` | 46983 | 2026-10-13 14:16:25 | …WjAv8ZEE | `e7df1c1ba7063c9a974cb00f04f1dd0d` | `2023/` yes |
| 44 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_101141_1027038_18012024042726.xml` | 63675 | 2026-10-13 14:16:23 | …0xyHkbUg | `c3955b95f5d56b7319e070073f5039d9` | `2023/` yes |
| 45 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_105605_1120043_10052024042154.xml` | 77720 | 2026-10-13 14:16:22 | …VYV0rKkG | `1062f01199445e28fbb5bf8e6a5ba86c` | `2024/` yes |
| 46 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_105607_1120051_10052024042433.xml` | 89381 | 2026-10-13 14:16:21 | …Y4fVUl9C | `819a88d05112285374a510a1a7c5ff48` | `2024/` yes |
| 47 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_109091_1192212_18072024053453.xml` | 30943 | 2026-10-13 14:16:20 | …_dvMAlTe | `78c4513cc2853ceed3872876c8a2aca5` | `2024/` yes |
| 48 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_109092_1192234_18072024053614.xml` | 39996 | 2026-10-13 14:16:18 | …OiUOzlCq | `edfd58f8152e388005774236ed4e81f2` | `2024/` yes |
| 49 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_112847_1275832_17102024064954.xml` | 72198 | 2026-10-13 14:16:17 | …_Qy7-QyP | `8311d2969e4ed9c2af1d1e2c676a4559` | `2024/` yes |
| 50 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_112849_1275859_17102024065630.xml` | 88725 | 2026-10-13 14:16:12 | …aU0o12Qy | `7a378259edc564f0dee3efa9574d30aa` | `2024/` yes |
| 51 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_117487_1357150_22012025051222.xml` | 47372 | 2026-10-13 14:16:11 | …_SEMbf_U | `4ecd2d9d8b4339a7f638be51775c4a7b` | `2024/` yes |
| 52 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_117488_1357164_22012025051528.xml` | 53019 | 2026-10-13 14:16:10 | …id2JI3Ri | `a3e0a7a3567c4909ae742a0a9cb04919` | `2024/` yes |
| 53 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_97668_958607_18102023055032.xml` | 76624 | 2026-10-13 14:16:27 | …2mSJm8TV | `6b617c78168697c563ec2ae5756177d2` | `2023/` yes |
| 54 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INDAS_97669_958659_18102023055636.xml` | 88337 | 2026-10-13 14:16:26 | …BQcNVVG5 | `4440b3d907cfa3776085fd52a3835690` | `2023/` yes |
| 55 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1432542_06052025071425_WEB.xml` | 90012 | 2026-10-13 14:16:44 | …N2An9--Q | `4b57c07160aef21b91e80384de6a7b1f` | `2025/` yes |
| 56 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1432577_06052025072509_WEB.xml` | 357017 | 2026-10-13 14:16:43 | …tZKzF3cY | `e3eaa25d4339af8986aa22a2e418ece9` | `2025/` yes |
| 57 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1485403_17072025035738_WEB.xml` | 34211 | 2026-10-13 14:16:41 | …EGZFk9gX | `f22a85ddd74ce98724ca84af9e069567` | `2025/` yes |
| 58 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1485404_17072025035800_WEB.xml` | 34081 | 2026-10-13 14:16:40 | …OZ_wKMVo | `8319e75af3790da313e88bb9eed5f2b7` | `2025/` yes |
| 59 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1552462_17102025061529_WEB.xml` | 290969 | 2026-10-13 14:16:38 | …pRvoxHjV | `e881fcb558b6c7944e1b8e8fbc394159` | `2025/` yes |
| 60 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1552465_17102025061553_WEB.xml` | 79249 | 2026-10-13 14:16:37 | …xPTXZvwR | `1d8f209d0385806316ef6ef341d0bf0c` | `2025/` yes |
| 61 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1602514_16012026051409_WEB.xml` | 52829 | 2026-10-13 14:16:36 | …N2GoPSR9 | `54c75657231cdbe7207d591c435d71fd` | `2025/` yes |
| 62 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1602515_16012026051416_WEB.xml` | 53617 | 2026-10-13 14:16:35 | …ilMs3RlA | `40257a92376dc0a5d0df16c16d95c23f` | `2025/` yes |
| 63 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1664065_06052026044742_WEB.xml` | 291660 | 2026-10-13 14:16:33 | …GmNRFIB7 | `52b33e1181248e6c535cea4516f42a2b` | `2026/` yes |
| 64 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1664066_06052026044749_WEB.xml` | 88258 | 2026-10-13 14:16:32 | …SkzXzUxs | `d2a8c4707bdf1623338be8787c4cd20d` | `2026/` yes |
| 65 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1694175_16072026035908_WEB.xml` | 34128 | 2026-10-13 14:16:31 | …pINiBovF | `b8babff123462d4a778380b0bfc533ba` | `2026/` yes |
| 66 | `raw/nse/equities/filings/results-xbrl/POLYCAB` | `INTEGRATED_FILING_INDAS_1694176_16072026035916_WEB.xml` | 34151 | 2026-10-13 14:16:30 | …r5KzKjpo | `295307a476b61934b5694ae38133ade9` | `2026/` yes |
| 67 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_1481166_11072025060933_WEB.xml` | 109998 | 2026-10-13 14:15:57 | …XKfAxphC | `d9f24a28d59623f739467790785572a5` | `2025/` yes |
| 68 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_1547941_14102025062416_WEB.xml` | 113737 | 2026-10-13 14:15:56 | …e4W1WWhn | `455340f5700a8a5f740e4fe7f13a2044` | `2025/` yes |
| 69 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_1601699_15012026054553_WEB.xml` | 167787 | 2026-10-13 14:15:54 | …kwLIrC4K | `2c2caaa7b9a96bacbd3f013255bad86e` | `2025/` yes |
| 70 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_1650182_13042026071657_WEB.xml` | 173929 | 2026-10-13 14:15:53 | …XAGXm6kG | `e40c1ae08829f4ed31d5adbaa2f97201` | `2026/` yes |
| 71 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_1694538_16072026063705_WEB.xml` | 167621 | 2026-10-13 14:15:51 | …cVU6a2IS | `356e0ebb18fbf898213b3b70443cc6a6` | `2026/` yes |
| 72 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_1734943_09102026042705_WEB.xml` | 173910 | 2026-10-13 14:15:49 | …WnSkN4-o | `b3e8592aa18a473c42f59ff7da70ae2a` | `2026/` yes |
| 73 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_181701_953709_16102023042925_WEB.xml` | 262788 | 2026-10-13 14:16:07 | …f29RZ5NX | `435121ef2b370ab876efd895622f7a5f` | `2023/` yes |
| 74 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_183818_1016320_11012024035546_WEB.xml` | 262785 | 2026-10-13 14:16:05 | …38ktS0Nu | `9ac03e04821432db31ee240e164e3faf` | `2023/` yes |
| 75 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_187487_1097975_18042024030516_WEB.xml` | 262807 | 2026-10-13 14:16:04 | …ljmUhvqd | `8c1c777f986a5932157752e20d7c86a9` | `2024/` yes |
| 76 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_189538_1186446_16072024111722_WEB.xml` | 257760 | 2026-10-13 14:16:03 | …DdoVd8GB | `c98b37a478c62addbea3797a733e3ea3` | `2024/` yes |
| 77 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_192300_1272578_16102024042831_WEB.xml` | 272847 | 2026-10-13 14:16:01 | …Na6jQl8A | `3d679a4e174c288006113e9417e21efe` | `2024/` yes |
| 78 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_194275_1341944_10012025035746_WEB.xml` | 267815 | 2026-10-13 14:16:00 | …8Ib9rHll | `eab2b1fdcf44cd81fa6242dad2d7a0fd` | `2024/` yes |
| 79 | `raw/nse/equities/filings/shareholding-xbrl/IRCTC` | `SHP_197261_1414872_15042025045145_WEB.xml` | 262793 | 2026-10-13 14:15:58 | …UxNiufYf | `9b099f1b16b6485c03dbed8bc44ecdc7` | `2025/` yes |
| 80 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_1556152_24102025023357_WEB.xml` | 234339 | 2026-10-13 14:16:51 | …O9wS3D8l | `09de3c810b2956c773fcbc28da166e55` | `2025/` yes |
| 81 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_1594856_05012026122600_WEB.xml` | 231399 | 2026-10-13 14:16:53 | …QsFMc4Xv | `f61c9d8b2644dfb2fdba967886e44aa5` | `2025/` yes |
| 82 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_1606875_21012026025304_WEB.xml` | 302624 | 2026-10-13 14:16:50 | …wZZX0Y14 | `96979aa8f0e443842be68049d4e93cef` | `2025/` yes |
| 83 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_1654385_18042026071959_WEB.xml` | 305555 | 2026-10-13 14:16:48 | …aQrcH3dg | `110715df64b6274cc2d46242984d7262` | `2026/` yes |
| 84 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_1697354_20072026063756_WEB.xml` | 305827 | 2026-10-13 14:16:47 | …fsCaghnF | `2e5c009dd3992a29a5dcb4627ef37057` | `2026/` yes |
| 85 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_179974_895259_20072023051011_WEB.xml` | 421737 | 2026-10-13 14:17:04 | …a3hjWpK6 | `5837c83f3549f3dfe4a6e0f86c5b93c9` | `2023/` yes |
| 86 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_182815_964391_20102023091614_WEB.xml` | 432536 | 2026-10-13 14:17:02 | …TbLKiUCJ | `19da4ef9c2330cb1feb47fc2f87566f3` | `2023/` yes |
| 87 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_185238_1031505_20012024022331_WEB.xml` | 414533 | 2026-10-13 14:17:01 | …GOfLkgCB | `d11e3398606d3e62dbbc503389ff39f0` | `2023/` yes |
| 88 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_186756_1092136_15042024034956_WEB.xml` | 424856 | 2026-10-13 14:16:59 | …rJBNqLLC | `acd264d4aa399ac1214689ad6affd737` | `2024/` yes |
| 89 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_190610_1197110_20072024021333_WEB.xml` | 424865 | 2026-10-13 14:16:58 | …lOKzMrWs | `84afe801457a72adde3c211f18fedb63` | `2024/` yes |
| 90 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_191467_1264112_10102024113836_WEB.xml` | 435532 | 2026-10-13 14:16:57 | …F7gyi5Hr | `6a537dcfe000f66419f659872b69974e` | `2024/` yes |
| 91 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_195683_1438344_14052025024914_WEB.xml` | 429865 | 2026-10-13 14:16:55 | …muzVfGBO | `c423517240ad104d9e45706fd3f67010` | `2024/` yes |
| 92 | `raw/nse/equities/filings/shareholding-xbrl/POLYCAB` | `SHP_197005_1413408_12042025063545_WEB.xml` | 435010 | 2026-10-13 14:16:54 | …3oVTiAyu | `84c8bf107077752fefbe2697f723891e` | `2025/` yes |
