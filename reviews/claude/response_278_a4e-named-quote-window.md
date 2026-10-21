# Response 278: story A4e, a named 3 pm quote window for protocol v4's pack (builder's claims)

Branch `story/a4e-named-quote-window` (lane 1). Story text: `docs/stories/A-data-foundation.md`, section A4e, passed by
judge 278 addendum 2 at 08c6f465 (merged to main, ac35f980).
Interface agreed with G10's builder (01VK88LxJvV1Gi7Wbr3D4fzp), 16 Oct. Builder session 01MKtUHByHsR9cNwaP5KhFYH.

## Verdict in two lines

`python -m fno quotes record --window v4` records NIFTY in 14:30-14:40 IST into its own dataset
(`quote-snapshots-v4`), quotes in Drive only, every pack field with its own times and A16's clock check in the sidecar;
plain `quotes record` is unchanged. **Strong evidence** (tests, 19 of 19 planted bugs caught, v2 golden cases
unchanged). Not run live: nothing schedules it until O1 and the owner decide (Known limits).

## What changed

| File | Change |
|---|---|
| `fno/quotes/window.py` (new) | `QuoteWindow` and `named_window(cfg, name)`: `quotes.windows.<name>` read and refused (ConfigError naming the key) before anything is built |
| `fno/quotes/capture_log.py` (new) | `CaptureLog` (two clock readings in order, chains, levels; `request_allowed` refuses any market request after the window's end), `TimedProvider` and `TimedLevels` (decorators: the real provider and level source, unchanged, timed and stopped at the end) |
| `fno/quotes/window_wiring.py` (new composition root) | the v4 recorder: same sources as A4's, own dataset, Drive-only store for that dataset, `stop_requests_at` = window end, timed provider and levels, A16's clock check |
| `fno/quotes/recorder.py` | takes `window` (default: A4's constants, `DEFAULT_WINDOW`) and an optional `log`; `begin` before the first request, `finish` into the sidecar (348 lines) |
| `fno/quotes/cli.py` | `--window NAME` (refused with `--source nse`; a bad name or entry stops with "nothing asked", exit 1) |
| `fno/storage/quote_wiring.py` | `build_drive_only_quote_store(..., dataset=)`: the Groww dataset whose quote files go to Drive (default unchanged) |
| `fno/intraday/clock_wiring.py` (new, small composition root) | A16's clock check moved there unchanged as `build_clock_check()`, used by A16's `wiring.py` and A4e (one rule, no copy; apart so the 3 pm recorder does not import A16's Groww intraday graph, G10's builder's point); `CLAUDE.md`'s list, A16's composition-root test and A16c's one-clock test name it |
| `config.yaml` | `quotes.windows.v4: {start: "14:30", end: "14:40", max_early_wait_minutes: 30}` |
| `fno/desk/commit_guard.py` | the desk's raw-quote guard covers every Groww quote dataset (`<quotes>/groww/**/*.csv`, as `.gitignore` and the record scan already do), so a v4 quote file is refused too (E2b's file: one line, its owner told) |
| `CLAUDE.md` | the new composition root in the Code list |
| tests | `tests/quotes/test_named_window.py`, `test_named_window_config.py`, `window_fakes.py` |

**Found while building (fixed, not in the story text):** A4b's Drive-only store sends to Drive only quote files under
the exact dataset `groww/derivatives/quote-snapshots/`. A v4 quote file would have stayed in the repository folder (kept
out of git by `.gitignore` and the record scan, but never saved to Drive: a lost day). The v4 store is now built for
its own dataset; a planted bug that drops this is caught.

## Criteria, tests and broken-code proof

Each mutation planted in place, the new test files and the desk guard's tests run, the file restored (19 of 19 caught).

| # | Criterion | Tests | Mutation → result |
|---|---|---|---|
| 1 | Default unchanged | every existing quotes test, A4's byte-for-byte baseline, the default sidecar has no A4e key, `tools/forecast_live_golden.py` "unchanged" | (default constants untouched) |
| 2 | Window | 14:05 run waits, nothing asked before 14:30 (chains, levels, quotes); 13:59 "too early", provider never asked; retry; a request at 14:40:00 allowed, at 14:40:01 refused; no quote, chain, levels or expiry-list request after 14:40 (a slow expiry list, a clock check running past 14:40); a 6 s answer to a 14:39:5x request kept at its real later time; retries never start after 14:40, day ends "none" | start ignored, end ignored, 20-minute wait, no quote stop, no stop before expiries, chain or levels, stop off by one → all CAUGHT |
| 3 | Own dataset | sidecar and marker under `quote-snapshots-v4`, quote file in fake Drive only, A4's report sees nothing; the composition root's store prefix; the desk's guard refuses a v4 quote file | shared dataset, store not routed to Drive, desk guard on the default dataset only → CAUGHT |
| 4 | Clock | both ok; skew before; skew after; no server answering (unchecked, no skew); a check that raises, before or after, keeps its place as `clock_unchecked` (never clock_ok) | status = last reading, failed reading dropped, log never begun, log not written → all CAUGHT |
| 4b | Own times | chains per expiry with spot and both times; levels requested after the last chain answer and received before the first quote request; a level answered after 14:40 keeps that time; NSE futures carry no bid or ask | chain time not logged, level receive = request → CAUGHT |
| 5 | Refusals | unknown name, `quotes` empty or `windows` not a mapping, missing or extra key, bad time, unquoted YAML 14:30 (the number 870), start not before end, negative or boolean wait; the command stops before building anything, also with `--source nse` | start<end check removed, nse allowed → CAUGHT |
| 6 | Gates | below | |

## Output sample (fake quotes, fake Drive, fake clock; nothing sent)

```
== v4 window, started 14:05:00 (fake quotes, fake Drive, fake clock; nothing sent)
recorded: nifty_20261013_143146 (12 contracts, complete=True)
repository: ['groww/derivatives/quote-snapshots-v4/2026/10/nifty_20261013.canonical', 'groww/derivatives/quote-snapshots-v4/2026/10/nifty_20261013_143002.meta.json', 'groww/derivatives/quote-snapshots-v4/2026/10/nifty_20261013_143146.meta.json']
fake Drive: ['groww/derivatives/quote-snapshots-v4/2026/10/nifty_20261013_143002.csv', 'groww/derivatives/quote-snapshots-v4/2026/10/nifty_20261013_143146.csv']
{
 "chains": [
  {
   "expiry": "2026-10-27",
   "request_sent_at": "2026-10-13T14:31:53+05:30",
   "response_received_at": "2026-10-13T14:31:54+05:30",
   "spot": 22000.0
  },
  {
   "expiry": "2026-11-24",
   "request_sent_at": "2026-10-13T14:31:55+05:30",
   "response_received_at": "2026-10-13T14:31:56+05:30",
   "spot": 22000.0
  }
 ],
 "levels_requested_at": "2026-10-13T14:31:57+05:30",
 "levels_received_at": "2026-10-13T14:31:58+05:30",
 "india_vix": 13.95,
 "india_vix_time": "13-Oct-2026 14:29",
 "futures": [
  {
   "expiry": "2026-10-27",
   "last": 22010.0,
   "volume": 1200
  }
 ],
 "clock_checks": [
  "clock_ok",
  "clock_ok"
 ],
 "clock_status": "clock_ok",
 "clock_worst_skew_seconds": 0.0,
 "started_at": "2026-10-13T14:31:46+05:30",
 "finished_at": "2026-10-13T14:32:23+05:30"
}
```

## Gates

On the final code: `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -n auto`: 7,714 passed, 0 failed (an earlier run
on ac55bc60 had one setup error in `tests/factory/test_freeze_and_verdict.py` under parallel runs only; it passes
alone, with and without this change, and did not recur). `ruff check fno tests tools`: clean; `ruff format --check`: 1,391
files formatted; `python tools/check_imports.py`: clean (1,481 files); `python tools/check_records.py`: clean;
`python tools/forecast_live_golden.py`: "live golden cases unchanged: case_a, case_b". No file over 350 lines
(`recorder.py` 348).

## Self-review

One independent review agent (correctness and silent failures) read the diff at ac55bc60:
- **Accepted, fixed (blocking):** the window's end stopped only the quote-book requests. An attempt started just before
  14:40 could still ask for the expiry list, the chains and the levels after it (the clock check alone can take up to
  2 x 15 s). Now every market request goes through `CaptureLog.request_allowed`; after the end, expiries and chain
  raise WindowEnded (recorded, incomplete) and levels record the failure (never raised). Tests: a slow expiry list; a
  clock check running past 14:40; the 14:40:00 / 14:40:01 boundary. Broken-code proof: each guard removed fails.
- **Accepted, fixed:** a failed clock reading was dropped, so `clock_checks` lost its before/after order. It now keeps
  its place as `clock_unchecked`.
- **Accepted, fixed:** the desk's raw-quote guard (E2b) covered only the default dataset; it now covers
  `<quotes>/groww/`, like `.gitignore` and the record scan.
- **Accepted, fixed:** `quotes` empty or `windows` not a mapping raised a traceback; now a ConfigError naming the key.
- **Notes, no change:** the story's "run stopped before its last request" case cannot write a sidecar (no `finish`), so
  it is tested as a failing check instead; `--outside-window --window v4` after 14:40 asks nothing (by design);
  alerts do not name the window (the snapshot time does); with `quotes.provider: auto` and no Groww keys, NSE quotes
  land in the Groww folder, as for the default run today; if a 14:30 run's files are left uncommitted, the 14:55
  part's NIFTY commit glob sweeps them in once (for O1 when it schedules the run).
- Checked by the agent, no finding: the default run (constants, no log, same sidecar keys); no reader of the default
  dataset sees the v4 folder (`report.py`, `compare.py`, the desk, the v2 capture, health, learning, G4's replay).

## Known limits (from the story; nothing built for them)

- Not in the routine: O1 adds the step and the owner moves the start to 14:05; whether 14:30 is an extra capture
  (about 190 more Groww calls at A16's 14:30 mark, one key) or replaces 14:55 is the orchestrator's and owner's call.
- The default capture's clock stays unchecked (v2's frozen behaviour).
- `recorder.py` is at 348 lines: the next change to it must split it first.
