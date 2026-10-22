# Response 320: A9c code, a second NSE archive host for the librarian's dated files (builder's claims, for Judge F)

Builder session 01MKtUHByHsR9cNwaP5KhFYH, branch `story/oss1-second-host`:
- code at c1a80c0a;
- the text amendment and its test at d761d3c9 (judge 471 note: provenance rows, the canonical URL).

The story text passed in judge 471 addendum 1. This is lane 1 and is not merged: nothing merges before 26 Oct, and only
after your PASS. The A20 builder, who owns `raw_source.py`, reviews the `raw_source.py` and wiring diff first.

## What changed

| File | Change |
|---|---|
| `fno/storage/raw_source.py` | `PRIMARY_HOST` and `SECOND_HOST`. `NseArchiveSource(..., host=PRIMARY_HOST, retry_waits=RETRY_WAITS)`. `requested_url(path)` is the class's `url_for` with the instance's host (the class method is unchanged). `_response` uses `self.retry_waits` and `requested_url` |
| `fno/storage/fallback_source.py` (new, 99 lines) | `FallbackSource(RawFileSource)`: the primary first; the secondary only on `RawSourceUnavailable` that is neither `RawFileRefused` nor `RawSourceCoolingOff`; `None` stays `None`; `last_written` is the primary's only; `fetch_published` from the secondary carries no write time. Also `ProvenanceLog` with `CsvProvenanceLog` |
| `fno/storage/wiring.py` (312 lines) | `build_fallback_source` (secondary on `SECOND_HOST`, `retry_waits=()`, provenance in `research/data/manifests/second-host/`). Used by `build_librarian` and `build_nse_library` only. `build_nse_source` accepts the host keywords |
| `fno/storage/librarian.py` (1 line), `fno/storage/coverage.py` (type) | `archive_range(self.source, ...)` instead of `type(self.source)`: it reads only `first_day` and `last_day`, which the wrapper copies |
| `fno/http_pacing.py` | `archives.nseindia.com` at 1.0 s in `HOST_SPACING_SECONDS` |
| `fno/storage/host_check.py` (new), `fno/storage/hosts_cli.py` (new), `fno/cli.py` | `python -m fno data-hosts --day D`, read-only |
| `tests/test_second_host.py` (new, 26 tests); `tests/test_storage.py` (the two library assertions extended to `.primary` and `.secondary`) | |

## Criteria

| # | Evidence |
|---|---|
| 1 | Unreachable primary (4 connection errors): the secondary answers with one request and the same bytes, and a provenance row is written. A 403 (`RawFileRefused`) and a `SourceCoolingOff` never reach the secondary (it raises if called). `None` (404) stays `None`. Both failing gives one error naming both hosts, with tries 4 + 1 |
| 2 | `last_written` with the primary down raises the primary's error and never asks the secondary. `fetch_published` from the secondary is `PublishedFile(data, None)` |
| 3 | All 8 librarian classes plus `NseLegacyFoSource`: `requested_url` equals `url_for` on `nsearchives` by default, and differs only in the host on `archives`. `tests/test_fingerprints.py`'s `nsearchives` assertion still holds (the manifest URL is canonical, criterion 10) |
| 4 | `build_librarian` and `build_nse_fo_library` return a `FallbackSource` whose secondary has `retry_waits == ()`. `build_nse_source` and `build_revision_capturing_source(...).source` stay single on the primary. `archive_range` through the wrapper equals the class's |
| 5 | A second-host file is stored once through `FingerprintingStore`; the same bytes again change nothing; one manifest row under the canonical URL, with the SHA-256 equal to the provenance row's |
| 6 | `data-hosts` test: same, neither, different, one unreachable, one 404 give exit 0, 0, 1, 1, 1. Live run below |
| 7 | Gates below; no file over 350 lines |
| 8 | Fake clock: a primary at its slowest (4 x 60 s requests, 3 x 120 s Retry-After waits) plus the secondary's one 60 s request ends at **660 s exactly**. The request counts are 4 and 1. `HOST_SPACING_SECONDS[archives] == 1.0`, and the requested URL's hostname, the pacer's key, is `archives.nseindia.com` |
| 9 | A second-host file stored, then A11's `RevisionCapturingSource` on the primary serving a different copy: one revision, the raw store still holds the first copy, and the provenance row names `archives.nseindia.com` |
| 10 | With `second-host/index-close.csv` inside the manifests folder, `ManifestFolder.read(NseIndexCloseSource)` returns its one row (canonical URL) and nothing from the subfolder |

**Planted bugs, 9 of 9 caught** (each made, the tests run, then reverted):

| Planted bug | Tests failing |
|---|---|
| a refusal sent to the second host | 2 |
| write times taken from the second host | 1 |
| the second host given full retries | 1 |
| the host ignored in the URL | 12 |
| no provenance row | 3 |
| the second host's write time kept | 1 |
| the second host unpaced (0.0) | 1 |
| the librarian built without the fallback | 2 |
| the hosts check blind to differences | 3 |

**Real output, quality rule 6** (`python -m fno data-hosts --day 2026-10-21`, live, read-only, 22 Oct):

```
participant-oi 2026-10-21: nsearchives.nseindia.com 676104d5e70b | archives.nseindia.com 676104d5e70b -> same
index-close 2026-10-21: nsearchives.nseindia.com ccaff4c52383 | archives.nseindia.com ccaff4c52383 -> same
cm-bhavcopy 2026-10-21: nsearchives.nseindia.com 7d19ef4c8f7e | archives.nseindia.com 7d19ef4c8f7e -> same
security-delivery 2026-10-21: nsearchives.nseindia.com 1e05e1696d50 | archives.nseindia.com 1e05e1696d50 -> same
fo-bhavcopy 2026-10-21: nsearchives.nseindia.com ae3a26bc4696 | archives.nseindia.com ae3a26bc4696 -> same
span-bod 2026-10-21: nsearchives.nseindia.com d673e476b512 | archives.nseindia.com d673e476b512 -> same
participant-volume 2026-10-21: nsearchives.nseindia.com e82e32daa35f | archives.nseindia.com e82e32daa35f -> same
fii-stats 2026-10-21: nsearchives.nseindia.com 649a5349a42b | archives.nseindia.com 649a5349a42b -> same
hosts 2026-10-21: 8 same, 0 not published on either, 0 different or not checked
```

A legacy F&O file (15 Jun 2023) is also the same on both hosts (`ae6643dcf3cf`).

**Gates** (d761d3c9):
- ruff and ruff format: clean;
- `check_imports`: clean;
- `pytest -n auto`: **9845 passed, 16 xfailed**, a clean run with nothing else on the machine.

## Facts to know (said plainly)

1. **The manifest wording was wrong in the text you passed.** I found it before writing code and told you; the text
   is amended (d761d3c9, your condition 1).
2. **The check's name changed** from `data-librarian hosts` to `data-hosts`: `data-librarian` takes the dataset as
   its first argument.
3. **One line outside the story's file list.** `librarian.py` passes `self.source` to `archive_range` instead of
   `type(self.source)`. Without that line the wrapper's own class would be passed, which has no dataset days.
4. **Library reads also log provenance.** `build_nse_library`, the readers' "from the stores, else NSE", writes
   provenance rows the same way. Those rows are committed with the manifest rows by whoever commits those, as today.
5. **A stale bytecode cache while testing (my mistake, now fixed):**
   - my "unpaced" plant swapped `1.0` for `0.0`, the same length, and the restore came within the same second;
   - Python's bytecode cache then kept the planted value, so one full run failed on the pacing test while the source
     on disk was right;
   - I cleared every `__pycache__` and re-ran. Committed code was never affected.
6. **Failures elsewhere while I tested, none in A9c's files:**
   - an earlier run had one failure I did not capture;
   - a run that overlapped another pytest session of mine gave `git commit` exit 128 in
     `tests/test_ci_scope.py` and one more git-based test;
   - the clean solo run above passed everything. This fits response 316's lead that overlapping sessions disturb the
     git-based tests. (Reasoning only.)

## After the merge (quality rule 8)

The orchestrator runs `python -m fno data-hosts --day <last session>` and `python -m fno data-librarian index-close
--from <a week ago>` on real data, and records both lines.
