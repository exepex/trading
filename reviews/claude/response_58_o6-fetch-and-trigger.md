# Response 58: story O6, fetch in GitHub Actions and reason in triggered routines (design note and claims)

Story: `docs/stories/O-operations.md` O6, issue exepex/trading#88. Builder: Claude, 13 Oct 2026.
Research data only; nothing here places, modifies or cancels orders.

## 1. Design

### 1.1 The shared pipeline layer (`fno/pipeline/`)

One small layer that every download job calls **after** its own download step. It never downloads anything itself,
so A12's job (and every later one) keeps its code; joining the pipeline is one extra workflow step.

| Unit | Kind | Job |
|---|---|---|
| `BatchPointer` (`pointer.py`) | value | what a routine is told: `dataset`, Drive `path`, `batch` (the day), `version` (SHA-256 of the bytes). Never data. Parsed back strictly (allow-listed dataset, archive path in `raw/` or `revisions/`, 64-hex version), because the routine receives it as untrusted text |
| `BatchFinder` (`batches.py`) | interface | which batches a job has. Adapter `ManifestBatches`: the committed manifest rows (A10) of one dataset since a day, plus its A11 revision rows (a republished file = a new version = a new pointer) |
| `RoutineTrigger` (`trigger.py`) | interface | `fire(pointer)`. Adapter `RoutineFireTrigger`: `POST https://api.anthropic.com/v1/claude_code/routines/<trigger id>/fire`, bearer token, `anthropic-beta: experimental-cc-routine-2026-04-01`, `anthropic-version: 2023-06-01`, body `{"text": <pointer JSON>}`. `UnconfiguredTrigger` when the routine's two settings are missing (fails loudly, never silently) |
| `PipelineRecords` (`records.py`) | class over `RawFileStore` | "fired" and "processed" records in Drive, one small JSON file per routine, batch and version; written once, never changed or deleted |
| `BatchDispatcher` (`dispatcher.py`) | class | for each pointer: already fired for this version → skip; else fire, then write the fired record |
| `RunSummary` (`run_summary.py`) | value + store | the run's summary and progress (every batch with its outcome) as one JSON file in Drive, and the one-line run report |
| `PipelineRun` (`run.py`) | class | find → dispatch → save the summary → post one line to #fno-desk, plus one alert line per failure |
| `DryRunRoutine` (`dry_run.py`) | class | the example reasoning step the routine runs: pointer → processed already? → read the file from Drive → check its SHA-256 → write a derived summary and the processed record |
| `fno/pipeline/wiring.py` | composition root | the only place that picks the concrete trigger, Drive store, alert sender and dataset → routine routes |

Swapping Drive for another store, or the `/fire` endpoint for something else (it is a research preview), is one new
class behind `RawFileStore` or `RoutineTrigger` plus one line in `fno/pipeline/wiring.py`.

**Exactly once per batch and version.** The Actions side fires a pointer only when Drive has no "fired" record for
that routine, batch and version, and writes the record after `/fire` accepted it. The routine side processes a pointer
only when Drive has no "processed" record. So: no new data fires nothing; the same version fires once; a republished
file (new SHA-256) fires again, and its old result stays beside the new one (paths carry the version). The one gap:
`/fire` accepted but the fired record could not be written (Drive refused). The run then alerts, and the next run
fires again; the routine's processed record turns that second fire into a no-op. I chose "at least once, made
idempotent" over "write the record first", because a record written before a failed fire would lose the batch
silently.

**Failures are loud.** A refused or failed fire (HTTP 401/403 = token expired or revoked, 429 = more than 30 fires an
hour, any other status or network error), a missing routine setting, or a refused Drive write each give one line in
#fno-desk naming the job, dataset, batch and the fix; the step exits 1 so the Actions run shows red. The token is never
printed: lines name the setting, not its value.

**How it plugs into A12 without rewriting it.** A12's job (`filings-archive.yml`, `fno/filings/`) is not changed in
this story. Its day lists (`announcements`, `board-meetings`) are ordinary dated datasets with manifest rows, so they
join by adding one step to its workflow (`python -m fno pipeline fire filings --dataset announcements --dataset
board-meetings`) once a routine reasons on filings; until then there is nothing to fire, and adding the step only adds
a Slack line every 6 hours. The XBRL files use A12's own per-company manifests; they need one more `BatchFinder`
adapter (`FilingManifestBatches`) when a routine needs them. Both are left out on purpose (no second use yet, KISS);
the A12 schedule is also paused by its builder.

### 1.2 Drive layout (new areas beside `raw/` and `revisions/`)

```
fno-research/
  pipeline/                                     the pipeline's own bookkeeping
    runs/<job>/<YYYY>/<MM>/<run id>.json        run summary + progress: every batch and what happened to it
    fired/<routine>/<dataset>/<batch>/<version>.json      Actions fired this version (written once)
    processed/<routine>/<dataset>/<batch>/<version>.json  the routine finished this version (written once)
  derived/                                      what routines produce, for every role to reuse
    <routine>/<dataset>/<batch>/<version>.json  one result per version: old and new results both kept
```

`<run id>` is GitHub's run ID and attempt (`<run_id>-<attempt>`), so a re-run never overwrites. Nothing is ever
deleted or changed: every write goes through the raw stores' rule (same bytes = no-op, different bytes refused).

### 1.3 The trigger pointer

The `text` the routine receives (about 200 bytes, no data):

```json
{"batch": "2026-10-13", "dataset": "nse/derivatives/participant-oi",
 "path": "raw/nse/derivatives/participant-oi/2026/10/fao_participant_oi_13102026.csv",
 "version": "8ceb5e8a293785580ff181a2bc1e96f720c4597711c45326f2297cecde483897"}
```

A republished file's pointer has the same `batch` and a `revisions/...` path with the new `version`.

### 1.4 Plan per routine

| Routine today | Actions workflow | Side by side without collisions | Status |
|---|---|---|---|
| participant-OI release times, 17:11 IST daily (`trig_01Gb78…`) | `participant-oi-release.yml`: 17:11 IST and 22:45 IST (a GitHub job stops at 6 h, the watch runs 17:11 to 23:30, so the second run covers the tail), same `participant-oi watch --until 23:30 --every 5` command; then `data-librarian participant-oi` for the day (the file into Drive with its manifest row) and `pipeline fire` (dry-run routine) | Actions writes its check log to `research/data/participant_oi/actions/` (new `--evidence-folder` option), so both never append to the same file; the rule reads only the routine's log until the owner switches | built |
| participant-OI monthly sweep, 07:07 IST on the 1st (`trig_01XiPY…`) | `participant-oi-sweep.yml`: 05:37 IST on the 1st, same `participant-oi sweep`; then `pipeline fire` for republished files found | sweep log to the Actions folder; Drive revisions and the A11 index are idempotent (the same version again changes nothing). Runs first, so the routine's run is the second look | built |
| 3 pm quote recorder, 14:48 IST daily (`trig_01M5iC…`) | `quote-recorder-nse.yml`: 14:20 IST, waits to 14:40, then `quotes record --source nse` (A4's command, NSE's public chain) | own dataset `nse/derivatives/quote-snapshots` beside `groww/...`; `quotes report` reads Groww's only | built after the owner chose (a); see section 5 |

The routines are not edited or disabled (out of scope; owner decides after 5 clean sessions).

### 1.5 Can NSE's public data replace Groww for the 3 pm recorder? (checked 13 Oct 2026)

- **Evidence (strong, measured today from a cloud container):** NSE's `option-chain-v3` answers with, per contract,
  the best bid and ask **with sizes** (`buyPrice1`, `buyQuantity1`, `sellPrice1`, `sellQuantity1`), the day's traded
  volume, and one page timestamp (`13-Oct-2026 15:40:00`). A12's probe already showed NSE's JSON API answers from
  GitHub's runners (same host); the option-chain endpoint itself from a runner is not yet tested.
- **But the recorder cannot use it as is.** `NSEProvider` has no `quote_book`, so today every contract would be
  recorded "unquoted" and every day incomplete. Making NSE work needs a new `NseQuoteBook` adapter **and a change to
  A4's freshness rule**: Groww gives a per-contract last-trade time (used to prove "traded today"); NSE gives day volume
  (traded today: yes) and one page timestamp (how old the snapshot is: better than Groww, which gives none). That is a
  change to what the recorded history means, so it is the owner's call, not mine.
- **Two consequences either way:** NSE and Groww quotes are different feeds, so an NSE recorder cannot "give the same
  outputs" as the Groww routine (criterion 1 would become "agrees within a measured tolerance"); and the two must be
  separate datasets (`nse/derivatives/quote-snapshots` beside `groww/...`), never mixed.

**Question for the owner (also in the checklist):** for the 3 pm recorder in GitHub Actions, choose one:
- **(a) NSE public data (my recommendation; reasoning plus some evidence):** no broker key in GitHub. I build
  `NseQuoteBook` and a separate NSE dataset, run it beside the Groww routine for at least 3 sessions, and report how
  far the two disagree (spread, mid) before anything switches. Risk: NSE may refuse GitHub's runners or lag at 15:00.
- **(b) Groww in GitHub secrets:** same outputs as today, but the broker's API key and TOTP secret would sit in
  GitHub (encrypted, but a repository with Actions write access could read them in a workflow). Needs your explicit
  approval (O6 criterion 4).
- **(c) keep the routine** for the recorder only (costs AI credits each day).

No broker key was put in GitHub.

**Owner's answer (relayed by the orchestrator, 13 Oct 2026): (a) NSE public data; no broker key in GitHub, ever.**
Built the same day: section 5.

## 2. What was built

- `fno/pipeline/` (9 modules, each under 110 lines): `pointer.py`, `trigger.py`, `records.py`, `batches.py`,
  `dispatcher.py`, `run_summary.py`, `run.py`, `dry_run.py`, `cli.py`; composition root `fno/pipeline/wiring.py`.
  Commands: `python -m fno pipeline fire <job> --download ... --run-id ... [--note ...]` and
  `python -m fno pipeline dry-run '<pointer>'`.
- A8 commands gained `--evidence-folder` (watch, sweep) and `participant-oi compare`
  (`fno/research_data/release_compare.py`); the builders in `fno/composition.py` take the log path (default unchanged).
- Workflows `.github/workflows/participant-oi-release.yml` and `participant-oi-sweep.yml`.
- Owner checklist `docs/stories/O6-owner-checklist.md` (the dry-run routine's prompt, tokens, secrets, switch-off).
- Drive layout in `fno/storage/README.md`; constants `ENV_ROUTINE_DRY_RUN_*`, `PIPELINE_AREA`, `DERIVED_AREA`.

## 3. Claims per criterion (with evidence)

1. **Migrated jobs run on schedule and give the same outputs (3 sessions side by side).** NOT MET YET (needs time and
   the owner's secrets). Built: the release check (17:11 and 22:45 IST) and the monthly sweep (05:37 IST on the 1st)
   run the routines' own commands; `participant-oi compare` gives the day-by-day verdict
   (`tests/research_data/test_release_compare.py`). The first scheduled run is 14 Oct 2026, 17:11 IST. The 3 pm
   recorder now runs on NSE's public chain in Actions (owner's choice (a), section 5); its criterion is the
   disagreement report over at least 3 sessions, since NSE and Groww are different feeds.
   Known difference: the Actions copy re-checks the last 5 files from its own log, so its `REWRITTEN` re-checks
   start empty and match the routine's after 5 sessions.
2. **Exactly once per batch and version; nothing new fires nothing; a republished file fires again.** MET in tests
   (`tests/pipeline/test_pipeline_run.py`: `test_new_data_fires_once_and_a_second_run_fires_nothing`,
   `test_no_new_data_fires_nothing_and_still_reports_one_line`,
   `test_a_republished_file_fires_again_once_and_the_first_version_is_kept`; routine side
   `tests/pipeline/test_dry_run_routine.py`: a version is processed once, a wrong version writes nothing). The one real
   fire of the dry-run routine waits on checklist steps 2-5 (the token can only be made by the owner).
3. **A failed fire, an expired token or a refused Drive upload posts one clear line and never fails silently.** MET
   in tests: `test_a_failed_fire_alerts_leaves_no_record_and_the_next_run_fires`,
   `test_a_refused_drive_record_is_alerted`, `test_drive_refusing_the_sign_in_alerts_and_fails`,
   `test_a_failed_download_fails_the_run_even_with_nothing_to_fire`, and the five failure kinds of `/fire` in
   `test_every_failed_fire_says_why_without_the_token` (401, 403, 429, 500, unreachable). Missing secrets give
   `routine dry-run not configured: add the secrets ...` (`test_missing_settings_give_a_trigger_that_names_them`).
   Each failure makes the step exit 1, so the Actions run is red as well.
4. **No secret value in any file or log; no broker key in GitHub.** MET in tests:
   `test_a_refused_token_never_reaches_any_output_or_file` (a token-shaped value through a refused fire: not in any
   alert, printed line or Drive file) and `test_the_command_refuses_a_bad_pointer_and_prints_no_secret`. Lines name
   settings, never values; the workflows pass secrets only as environment variables (GitHub masks them in logs). The
   record scan (O5) covers the two new secret names (`ENV_` constants) and `check_records.py` passes. No Groww value
   in GitHub. The judge should still read the first real Actions log.
5. **Behind interfaces, concrete classes only in composition roots, nothing over 350 lines.** MET: `BatchFinder`,
   `RoutineTrigger` and the existing `RawFileStore`/`AlertSender`; concrete classes are chosen only in
   `fno/pipeline/wiring.py` (and the A8 builders in `fno/composition.py`); largest new file `fno/pipeline/wiring.py`
   (about 90 lines); `tests/test_code_size.py` passes.

Gates (13 Oct 2026, after section 5): `python -m pytest -q` 1406 passed; `ruff check` and `ruff format --check` clean; `check_imports` and `check_records` clean.

## 4. Doubts and limits

- **The `/fire` API is a research preview** (some evidence: docs read by the story writer on 13 Oct; I could not
  call it without a token). If the response has no session link, the fired record still works; if the shape of the
  request changes, every fire fails loudly and the fix is one class.
- **At least once, not exactly once, in one corner:** `/fire` accepted, then Drive refused the fired record. The run
  alerts and the next run fires again; the routine's processed record makes it a no-op (only the AI session start
  is spent twice).
- **A Slack line every run** (two a day plus one a month) is what the story asks ("one-line run report"); if it is
  too noisy, the owner can ask for failures only.
- **A routine reads a pointer as untrusted text.** The command refuses anything that is not one of our pointers; the
  prompt also refuses text with a quote or several lines before it reaches the shell. Reasoning only; no test can
  cover a model's handling of a hostile payload.
- **The participant-OI file now goes into Drive daily** (A9 librarian in the release workflow). The routine never
  did that, so this is a new output, not a difference to compare.

## 5. The 3 pm recorder on NSE's public data (owner's choice (a))

Built after the owner chose (a). No broker key in GitHub; the workflow installs only `requirements.txt`.

- `NseQuoteProvider` (`fno/providers/nse_quotes.py`): an `NSEProvider` that also answers `quote_book` from the
  chain it fetched (one request per expiry, no per-contract calls). Best bid and ask with sizes (`buyPrice1`,
  `buyQuantity1`, `sellPrice1`, `sellQuantity1`; NSE's 0 is "no quote"), last price, the page timestamp as
  `quote_time`, and `traded_today` from the day's volume. `QuoteBook` gained the two optional fields (Groww's books
  are unchanged).
- A4's rule, extended (not replaced): "a trade in the contract today" is proven by the last trade time when the
  provider gives one (Groww) and by day volume above zero when it does not (NSE). A quote whose page time is not today
  is invalid. Each row says which proof it used (`freshness_proxy`) and the quote's time basis (`age_basis`).
- Own dataset: `research/data/quotes/nse/derivatives/quote-snapshots/` (the recorder's new `dataset` argument;
  Groww's default path and bytes unchanged, the A4 baseline tests pass). Found and fixed on the way: `quotes report`
  scanned the whole quotes folder, so it would have mixed NSE into Groww's spread report; it now reads Groww's
  dataset only (`test_the_spread_report_reads_groww_only`).
- `python -m fno quotes record --source nse` (`build_nse_quote_recorder` in the composition root) and
  `python -m fno quotes compare`: per day, capture times (and NSE's page time), contracts each side has, strikes only
  one side has, and over contracts both quote validly the median |mid gap| and each side's median spread.
- Workflow `.github/workflows/quote-recorder-nse.yml`: 14:20 IST daily, waits to 14:40, records 14:55-15:10, commits
  its snapshot, posts one line to #fno-desk when the result is not good.
- **Evidence:** tests `tests/quotes/test_nse_quote_book.py` (book fields, own dataset, volume proof, exact comparison
  numbers, report separation). Live run from this cloud container, 13 Oct 2026 21:35 IST (outside the window, into a
  scratch folder, not committed): 184 contracts near the money, 172 valid, 6 one-sided, 6 with no trade today, page
  time 15:40:00 (NSE's post-close snapshot), complete=True.
- **Not yet known (reported when the 3 sessions are in):** whether NSE answers the option-chain endpoint from
  GitHub's runners (A12's probe proved other NSE JSON endpoints do), and how stale NSE's page time is at 15:00 (it
  showed 15:40:00 after the close, so it does update during the day; its refresh interval during the session is not
  measured yet). Nothing switches until the owner has seen `quotes compare` for at least 3 sessions.

## 6. Criterion 2's real fire, end to end (13 Oct 2026)

The owner created the dry-run routine (`trig_01Tb8CYfG4DKnC4ARaUn1dqD`), added the two secrets and ran
`participant-oi-release` by hand.

**First run, Actions run 38429626109 (success, 21:50:28 to 21:51:00 IST).** The run summary in Drive
(`pipeline/runs/participant-oi-release/2026/10/38429626109-1.json`, download `success`) lists 4 batches in the 5-day
window, all `fired`, each with its routine session:

| Batch | Version (SHA-256, first 12) | Routine session | `pipeline/fired` | `pipeline/processed` | `derived/dry-run` |
|---|---|---|---|---|---|
| 2026-10-08 | 277ff398753f | cse_01HDGovSvsGEptc3t4Tn9A4H | yes | yes | yes |
| 2026-10-09 | d95f403185bb | cse_01Kyd9QHUhW2G2ZLkfbnMrmj | yes | yes | yes |
| 2026-10-12 | 8ceb5e8a2937 | cse_01WzUooPmNGNxdJqtMaCCLWQ | yes | yes | yes |
| 2026-10-13 | de403e686af8 | cse_019Vbzuq2QUCYAhzLgcuKgoD | yes | yes | yes |

(Read from Drive with the owner sign-in; each record file is named by the full SHA-256.) 2026-10-10 and 11 are a
weekend: no file, no batch.

**The routine's printed line** (session cse_019Vbzuq2QUCYAhzLgcuKgoD, fired 16:20:57 UTC): `processed: 7 lines, 976
bytes; summary dry-run/nse/derivatives/participant-oi/2026-10-13/de403e686af87a4a841704616476ea26715fd1f5e2f576643eec65ecfeb6b88c.json`.
The pointer arrived inside `<routine-fire-payload>` marked as data, exactly as sent.

**Finding fixed in the checklist:** in that session plain `pip install` installed into a different Python than
`python` (`ModuleNotFoundError: requests`); the routine recovered with `python -m pip`. The prompt in
`docs/stories/O6-owner-checklist.md` now says `python -m pip install`. **The owner must paste that line into the
routine's prompt** (a routine's prompt is not read from the repository).

**Cost, measured (strong evidence):** that session ran 75 s and reported USD 0.13 at list price on the Sonnet model
(4 turns, about 216,000 input tokens, mostly cached). Four fires on the first run, about USD 0.54; afterwards about
one fire per session day, so roughly USD 3 a month for this dry-run routine on the subscription. Most of the cost is
the routine's fixed start-up context, not the work.

**Second run, Actions run 38430016919 (dispatched by this builder, success, 16:22:51 to 16:23:22 UTC).** Job log:
`Omenix F&O participant-oi-release (GitHub Actions run 38430016919-1): download success; 4 batches in window, 0 fired
to dry-run, 4 already fired, 0 failed` / `alert sent to #fno-desk`. No routine session was started. The watch
returned today's check already in the Actions log (present at 21:50 IST, `de403e686af8`) and committed nothing new;
the librarian found the file "already there and verified". Every secret in the log shows as `***`.

**Criterion 2: MET** (tests, plus one real fire of 4 batches, each processed once, and a second run that fired
nothing).

**Finding on the old routine (strong evidence, from its own transcript):** the 17:11 IST run of "participant-OI
release times" (session cse_01GciwRDoU5NX9U5CWYwig8K) recorded its checks, but every push to `main` failed with HTTP
403 ("`exepex/trading` isn't in this session's authorized repository set"). Its 6 commits stay in a dead container;
the committed log has only the 06:06 checks for 13 Oct. The routine still shows `SUCCEEDED`. So
`participant-oi compare` shows 13 Oct as `DIFFERENT` (routine: absent at 06:06; Actions: present, 21:50 IST): the
difference is the routine's lost push, not the data. Fix for the owner: add `exepex/trading` to that routine's
repositories (claude.ai/code, Routines, the routine, Repositories). The Actions job has no such gap: it pushes with
its own `contents: write` token. This builder did not edit the routine (out of scope).
