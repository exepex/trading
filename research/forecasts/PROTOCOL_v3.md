# Forecast protocol, version 3 (story G1 v3): the panel extends daily, and live Q5 uses the 15:00 pack

**Status: version 3, draft, NOT frozen.**
- Written by Claude (G1 builder) on 14 Oct 2026, from the owner's decision (`docs/DESK_DECISIONS.md`, 14 Oct 2026,
  "A13 now, through G1 protocol version 3"), the proposal `reviews/claude/response_68_g1-v3-panel-extension.md`,
  ChatGPT review 30 ("AGREED WITH CHANGES") and the orchestrator's decisions in
  `reviews/claude/response_69_2026-10-14-on-review-30.md`.
- It is frozen only after the judge passes it and the orchestrator confirms. Until `research/forecasts/FREEZE_v3.md`
  exists, the daily panel job appends nothing (section 2).

**Relation to versions 1 and 2:**
- Version 1 (`PROTOCOL.md`, protocol commit cf489e4) and version 2 (`PROTOCOL_v2.md`, protocol commit ab2e811) stay
  frozen and byte-identical, together with every file their freeze records list. Every v1 and v2 record, golden value
  and live record already written stays as written.
- Version 3 changes exactly two things:
  1. the NIFTY panel extends daily (section 1);
  2. the threshold used to resolve **live** question 5 (section 4).

  Everything else is version 2 unchanged: the questions, the targets of v1 section 2, the IV30 estimator, the
  baselines, Book 1, the live pack, the per-field 15:00:00 cutoff, the record schema, scoring and the comparisons.

## 1. The panel extends daily (story A13)

Each NSE session's NIFTY option and future rows are appended to the existing panel folder `research/data/nifty-panel/`
after the evening's files, so past IV30 (question 5's base rate, v2's `iv30_history_stale`) stays fresh. Code:
- `fno/research_data/panel_append.py` (`PanelAppender`);
- `fno/pipeline/panel_days.py` (`PanelDayJob`), wired in `fno/pipeline/wiring.py` (`build_panel_day_job`);
- the command `python -m fno pipeline panel-days`;
- the workflow `.github/workflows/panel-days.yml`.

Rules:
1. **A3's builder, unchanged.** Each session is built by `NiftyPanelBuilder`: calendar days, format precedence, the
   NIFTY 50 and India VIX closes from that day's index-close file, values copied and never rounded. A missing file is
   excused only by a sourced exception.
2. **First archived version.** Both inputs, the F&O daily file and the index-close file, are read as first archived in
   Drive's raw area. A11's later versions are recorded in the day's provenance and never used. The panel therefore does
   not depend on when the job ran. If a first version is invalid, the job stops at that day; a correction needs a
   separately named A11 panel revision, which this version does not include.
3. **Named input check.** Before a session is built:
   - `fo_file_missing`: no F&O file archived;
   - `index_close_missing`: no index-close file archived, or story O6 has not yet appended that day's official close
     to `warmup_closes.csv`;
   - `index_close_differs`: O6's row came from another index-close version. One day never has two closes.
4. **All or nothing, append only.**
   - A run appends every pending session or none.
   - The first failure appends nothing, posts one #fno-desk line, and the next run (the morning retry) starts again
     from the same day. A missing day is never jumped over.
   - A day is added only after the manifest's `end`, and never rebuilt or rewritten.
   - A touched year file gets one more gzip member (no header, no file name, zero time), so its old bytes stay an
     exact prefix.
   - The manifest keeps every existing entry key for key. It gains the new days, a later `end`, and new hashes and row
     counts for the touched files only.
5. **Consistency.**
   - Before anything else, the job checks every file the manifest lists: its SHA-256, its content SHA-256 and its row
     count. A mismatch, as an interrupted append leaves, is refused and named, with the fix
     `git checkout research/data/nifty-panel/`.
   - The workflow commits the panel only when the job exits 0, so a crash or a stop publishes nothing.
   - A per-generation pointer was rejected: `panel_reader.py` is v2's recorded code (response 69, item 4).
6. **Per-day provenance.** Each appended day's manifest entry holds:
   - A3's entry: the F&O and index-close file names and SHA-256;
   - `inputs_version` ("first archived (A11 original)");
   - `inputs_read_at`: when the run read them, an upper bound for their archive time;
   - `later_versions`: the A11 versions known at the run, with SHA-256 and availability time;
   - `appended_at`;
   - the calendar SHA-256 it used.

   The append commit is the commit that adds the day to `manifest.json`.
7. **Writes only under this freeze.** The job runs `require_version_frozen(ROOT, HEAD, PROTOCOL_v3.md, FREEZE_v3.md)`
   (v2's check, unchanged) before it reads anything.

## 2. No look-ahead, and replay

- **No look-ahead.** A day's rows exist only from its evening, or the next morning's retry. The live capture reads past
  IV30 only for days before the forecast day (`LiveForecastHistory`: `panel.options` with `d < day`).
- **Replay.** A live day is replayed from the inputs at the **parent of the commit that added its records**, never from
  today's grown panel. Those inputs are the panel and its official closes, the quote snapshots, the session calendar
  and `config.yaml`. The replay recomputes the day with the recorded generation time and compares the pack and the
  records byte for byte (`fno/forecast_scoring/replay.py`, `python -m fno forecast-scores replay --day YYYY-MM-DD`).
- **The history back-fill** is checked against the panel it was built from: its own days, and its `pack_sha256` equal to
  the manifest's SHA-256 at the commit that wrote it (`tests/forecast/test_backfill.py`).
- **Golden values.** The v1 golden test compares the golden file's own days, all of which must still be present and
  equal. A day the panel gained later is not part of the golden contract.

## 3. Experiment 1

Experiment 1 is finished. Its panel files on `main` now grow append-only (owner, 14 Oct 2026). Its result is
reproduced only from its frozen worktree at `0c1c957`, never from `main`. The steps are in
`research/2026-10-12-experiment-1/README.md`. `tests/research/test_experiment_1_frozen.py` checks the 45 frozen hashes
at that commit and the published result's SHA-256.

## 4. Question 5's threshold: live 15:00, history close proxy

Question 5 asks whether the next 20 trading days' realised volatility is below the 30-day ATM implied volatility known
at the forecast's cutoff.
- **Live forecasts (`live_1500_proxy`):** the threshold is the 15:00 IV30 locked in that day's hashed pack, with its
  status. A flagged or missing pack IV30 makes primary question 5 void, as in v1 and v2. The scorer reads it from the
  forecast's own pack, verified against the capture receipt, and never recomputes it from a later panel.
- **History back-fill (`close_proxy`):** the threshold is that day's close-proxy IV30, as v1 section 2 defines.
- **Realised volatility** uses the official closes over the next 20 trading sessions, as before.
- **Separate series.** Live and back-fill question 5 scores are never pooled or compared as one number. All books on
  a day share one pack, so the contest stays fair.
- **Code and test:**
  - `fno/forecast_scoring/resolution.py`: `resolve(question, day, mode)`;
  - `score_sources.py`: `LiveForecasts.iv30` from each verified pack;
  - `tests/forecast_scoring/test_scoring_live_q5.py` plants a disagreement. The next RV is 4.62 points; the 15:00 pack
    says 5.0, so the outcome is yes; the 15:30 panel says 4.0, so it would be no. Live uses the pack and history uses
    the panel.

## 5. The freeze (after the judge and the orchestrator only)

`research/forecasts/FREEZE_v3.md` will name the commit that adds this text in its final form, and the SHA-256 of:
- this file;
- the A13 code: `fno/research_data/panel_append.py`, `fno/pipeline/panel_days.py`, `fno/pipeline/wiring.py`;
- the live Q5 and replay code: `fno/forecast_scoring/resolution.py`, `score_sources.py`, `replay.py`;
- `.github/workflows/panel-days.yml`.

The daily panel job checks it before every run.

At the freeze, `panel-days.yml` gains its schedule: after `index-closes.yml`, about 21:41 IST, plus one morning retry
before 14:00 IST. v1's and v2's freeze records stay as they are and keep being checked by their own users.

## 6. Holdout

No 2019-2023 row of `golden_iv30_rv20.csv` or the G2 back-fill was opened, printed or analysed for this version. The
A13 tests use real NSE file subsets from 2020 and 2024 (A3's fixtures), which are raw files, not golden or back-fill
rows.
