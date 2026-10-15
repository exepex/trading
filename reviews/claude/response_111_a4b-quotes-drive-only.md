# Response 111: story A4b, raw Groww quotes in Google Drive only (builder's claims)

Branch `story/a4b-quotes-drive-only` (lane 1). Story text: `docs/stories/A-data-foundation.md`, section A4b (first
pushed alone at ec4ace4; updated in the code commit with the readers the self-review found). Owner decision: 15 Oct
2026, "6 A" (`docs/DESK_DECISIONS.md`). Builder session 01MKtUHByHsR9cNwaP5KhFYH.

## Verdict in two lines

Groww's quote rows now go to the owner's Drive only; the repository keeps sidecars, markers and hashes. Every reader
I found keeps working through one hash-checked store, and no frozen file is edited. **Strong evidence** (tests,
mutations, one real Drive round trip). Open points that are not mine to decide are at the end.

## What changed

| File | Change |
|---|---|
| `fno/quotes/drive_only_store.py` (new) | `DriveOnlyQuoteStore`: a Groww-dataset `.csv` goes to the private store only and is returned only if it hashes to the committed sidecar's `csv_sha256`; missing → `RawQuoteMissing`, changed → `RawQuoteHashMismatch`, no settings → `RawQuoteStoreUnavailable`; `None` only without a sidecar or with `raw_file_saved: false`. Drive is built on first use |
| `fno/storage/quote_wiring.py` (new composition root) | wires it to `AreaStore(build_owner_drive(), "raw")` and the repository folder; apart because `wiring.py` would pass 350 lines |
| `fno/storage/wiring.py` | `build_quote_store(folder)` calls it (so G1 v2's frozen `baseline_wiring.py` and `cli.py` get it unchanged) |
| `fno/quotes/recorder.py` | the quote file is saved inside a guard; on failure the attempt is incomplete, the sidecar gets `raw_file_saved: false` and `raw quote file not saved: <type>` (type only: Drive error texts can hold the folder ID); a complete attempt's sidecar is byte-identical to A4's |
| `fno/quotes/cli.py` | result line ends with the reason; one alert "raw quote file NOT saved to Drive" with the full error text (private Slack only); exit 1 |
| `fno/quotes/report.py`, `compare.py` | read through the store (they read the folder directly before) |
| `fno/desk/execution_capture.py` | commits the record and the sidecar only; an unsaved or unreadable quote file gives no record (sidecar still committed) |
| `fno/desk/snapshot.py` | a failed Drive read becomes `SnapshotError`, so C3's gate refuses and alerts, and exits still run |
| `fno/forecast_scoring/wiring.py` | `replay_quote_store`: G4's replay reads a pre-A4b commit's own quote files and a later commit's from Drive, hash-checked |
| `.gitignore` | `research/data/quotes/groww/**/*.csv` |
| `research/data/quotes/groww/.../nifty_20261014_145500.csv` | removed from the tree (stays in history at 5c22bcc); its Drive copy verified first (below) |
| `CLAUDE.md` | routine steps 2 and 4 (where the rows go, the third alert); the new composition root |
| `docs/stories/A-data-foundation.md`, `fno/storage/README.md`, `docs/IMPLEMENTATION_PLAN.md` | story, A4's storage line, layout note, plan row |
| tests | `tests/quotes/test_drive_only_{store,recording,readers}.py`, `tests/quotes/drive_fakes.py`, `tests/forecast_scoring/test_replay_quote_store.py`; signature updates in `test_quote_recorder.py` and `test_nse_quote_book.py` (no assertion changed); `tests/desk/test_safety.py` gets a fake Drive (its assertions unchanged) |

## Criteria, code, tests and broken-code proof

Each mutation was planted in a scratch worktree, the named tests run, then the file was restored (script and full
output: 20 of 20 caught, plus the freeze plant).

| # | Criterion | Code | Tests (positive / negative / boundary / empty) | Mutation → result |
|---|---|---|---|---|
| 1 | Raw rows to Drive only | `drive_only_store.py` `put`, `is_raw`; `quote_wiring.py` | goes to Drive only; NSE file and sidecars stay in repo; `is_raw` boundaries (other dataset, nested prefix, `.csv.part`); app store writes `raw/<path>` | put everything in the repo → CAUGHT |
| 2 | No raw quote in the repository | `.gitignore`; recorder sidecar; tree | sidecar keys ⊆ the story's table (both kinds of sidecar, and the real 14 Oct one); `git check-ignore` (Groww csv yes, NSE csv no, sidecar no); no tracked Groww csv; a planted folder ID in a Drive error never reaches the sidecar or the result line | remove ignore rule → CAUGHT; error text into sidecar → CAUGHT |
| 3 | Hash-checked reads, loud failures | `drive_only_store.py` `get` | one-byte change refused; missing → error; no settings → error naming settings, not values; no sidecar / unsaved → None; empty file with its hash → `b""`; Drive signed in to once, on the first raw file | drop hash check, missing→None, ignore `raw_file_saved`, eager sign-in → all CAUGHT |
| 4 | Every reader keeps working | readers table in the story | capture `load_snapshot`, B7 `RecordedSnapshots`, E2 `SnapshotInput`, E4 `RecordedExecutionSnapshots`, C4 `EvidenceReader`, Book 1 inputs, report, compare: equal results from A4's folder and the split store; E3 commits repo files only, no record when unsaved or unreadable; E4 Drive failure is `SnapshotError`; G4 replay: post-A4b layout equals pre-A4b layout, changed or missing Drive copy stops it | report/compare read folder, E3 commits csv, E3 unsaved/unreadable crash, E4 error type, replay always local → all CAUGHT |
| 5 | Drive down | `recorder.py` `_save_quote_file`, `_attempt`; `cli.py` | one failed save then canonical; down all window → "none", no csv anywhere, one alert, exit 1; no Drive settings at all → same; complete day → no alert; outside-window failed save → exit 1 | swallow error, still complete, no flag, no alert, exit 0, fallback to repo → all CAUGHT |
| 6 | Frozen files untouched; point in time | none edited | no file in any G1 FREEZE table's byte-checked rows changes (script over all `FREEZE*.md`; `recorder.py` and `forecast_scoring/wiring.py` are in "recorded, not byte-checked" tables and already differed from their recorded hashes on main); `python tools/forecast_live_golden.py` → "live golden cases unchanged: case_a, case_b"; live pack from Drive == pack from folder | one byte planted in `fno/forecast/capture.py` → `tests/forecast/test_freeze_v2.py` 2 failed |
| 7 | Routine stays correct | `CLAUDE.md` steps 2-4 | gitignore test (step 3's `git add` cannot stage a Groww csv) | (rule text) |
| 8 | Gates | | see below | |

## Real output sample (dry run, fake quotes, fake Drive; no real quote, no Drive, no Slack)

Made by `record_today` of the committed code with A4's test `FakeProvider` and `FakeDrive`; the "alert sent" line is
the test fake's return value, nothing was posted.

```
== Drive up
recorded: nifty_20261013_145503 (12 contracts, complete=True)
exit code: 0
repository folder: ['.../2026/10/nifty_20261013.canonical', '.../2026/10/nifty_20261013_145503.meta.json']
fake Drive: ['groww/derivatives/quote-snapshots/2026/10/nifty_20261013_145503.csv']
== Drive down all window
recorded: nifty_20261013_150930 (12 contracts, complete=False) - raw quote file not saved: DriveDown
exit code: 1
alert: "3 pm quote recorder: raw quote file NOT saved to Drive (DriveDown: drive unreachable (HTTP 503);
  nifty_20261013_150930). The sidecar is kept, no raw quote went to the repository; an attempt in the 14:55-15:10
  window is retried each minute. Fix: check the four FNO_GDRIVE_* settings (A9: run tools/gdrive_oauth_setup.py if
  the owner's consent expired)."
repository folder: ['.../nifty_20261013.canonical' (says "none"), '.../nifty_20261013_150803.meta.json',
  '.../nifty_20261013_150930.meta.json']
fake Drive: []
last sidecar: {"complete": false, "failures": ["raw quote file not saved: DriveDown"], "raw_file_saved": false, ...}
```

## Real Drive check (the 14 Oct file)

Through the committed store, from this session (owner's Drive, `raw` area): local SHA-256 `9d9de08b2e1b70c3...`
equals the sidecar's `csv_sha256`; 67,154 bytes; put 6.35 s; three reads, each a fresh store with a new sign-in:
2.24 s, 2.38 s, 2.29 s, bytes identical. Then the file was `git rm`'d. **Strong evidence** that the 15:15 lock has room:
the forecast job adds about 2.3 s per snapshot read (measured here, not in GitHub Actions: a guess that Actions is
similar).

## Self-review (Quality rule 3): two independent review agents

- **Correctness agent:** one blocking finding, accepted and fixed: G4's live replay (`fno/forecast_scoring/wiring.py`)
  read the exported commit with a plain folder store, so from 15 Oct the frozen `load_snapshot` would find the Groww
  marker without its quote file and quietly use NSE's snapshot; every replay would say DIFFERS. Fixed with
  `replay_quote_store` and two tests. One minor (E3 read-back error after a good save) fixed as part of the next item.
- **Silent-failure agent:** (1) the same replay finding; (2) accepted, fixed: a Drive read error at the desk's 15:15
  step was not a `SnapshotError`, so the daily run would stop before exits; now `SnapshotError` (gate alerts, exits
  run) and E3's capture gives no record; (3) accepted, fixed: Drive error texts (request URL with the private folder
  ID) went into the public sidecar; now the type only, full text only in the private alert; (4) desk capture has no
  Drive alert of its own: not fixed, E3 is not live, noted in the story; edge `.CSV` name: no code writes one, not
  fixed.

## Gates

`git config core.hooksPath .githooks` (record scan ran on each commit); `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`:
see the push message for the count; `ruff check fno tests tools`: clean; `ruff format`: clean;
`python tools/check_imports.py`: clean; `tests/test_code_size.py`: passes (`wiring.py` 348 lines).
`pip install -r requirements-groww.txt` fails in this container (clint and args do not build; the file's own comment
says so); no test needs `growwapi`.

## Not mine to decide (for the orchestrator and the owner)

1. **E2's common pack would republish raw quotes** once E3's daily run commits packs (`SnapshotInput` copies each
   option's bid, ask and quantities into `journal/packs/<day>/common.json`). Needs a decision before E3 goes live.
2. **Today's routine (15 Oct, ~14:50 IST) commits another raw csv** unless A4b is merged first; if it lands, move it the
   same way (upload, verify, `git rm`).
3. **The routine's environment must hold the four `FNO_GDRIVE_*` settings**, or every attempt fails loudly and the day is
   "none". Not checked from here.
4. **Behaviour change:** an unreadable Groww Drive copy now fails the forecast day loudly instead of falling back to
   NSE's snapshot.
5. History is unchanged: the 14 Oct file is still public in commit 5c22bcc, as the owner decided.
