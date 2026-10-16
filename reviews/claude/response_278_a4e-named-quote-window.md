# Response 278: story A4e, a named 3 pm quote window for protocol v4's pack (builder's claims)

Branch `story/a4e-named-quote-window` (lane 1). Story text: `docs/stories/A-data-foundation.md`, section A4e, passed by
judge 278 addendum 1 at c350d375 (08c6f465 adds only judge 278's own note to criterion 4b; confirmation asked).
Interface agreed with G10's builder (01VK88LxJvV1Gi7Wbr3D4fzp), 16 Oct. Builder session 01MKtUHByHsR9cNwaP5KhFYH.

## Verdict in two lines

`python -m fno quotes record --window v4` records NIFTY in 14:30-14:40 IST into its own dataset
(`quote-snapshots-v4`), quotes in Drive only, every pack field with its own times and A16's clock check in the sidecar;
plain `quotes record` is unchanged. **Strong evidence** (tests, 14 of 14 planted bugs caught, v2 golden cases
unchanged). Not run live: nothing schedules it until O1 and the owner decide (Known limits).

## What changed

| File | Change |
|---|---|
| `fno/quotes/window.py` (new) | `QuoteWindow` and `named_window(cfg, name)`: `quotes.windows.<name>` read and refused (ConfigError naming the key) before anything is built |
| `fno/quotes/capture_log.py` (new) | `CaptureLog` (two clock readings, chains, levels), `TimedProvider` and `TimedLevels` (decorators: the real provider and level source, unchanged, timed) |
| `fno/quotes/window_wiring.py` (new composition root) | the v4 recorder: same sources as A4's, own dataset, Drive-only store for that dataset, `stop_requests_at` = window end, timed provider and levels, A16's clock check |
| `fno/quotes/recorder.py` | takes `window` (default: A4's constants, `DEFAULT_WINDOW`) and an optional `log`; `begin` before the first request, `finish` into the sidecar (348 lines) |
| `fno/quotes/cli.py` | `--window NAME` (refused with `--source nse`; a bad name or entry stops with "nothing asked", exit 1) |
| `fno/storage/quote_wiring.py` | `build_drive_only_quote_store(..., dataset=)`: the Groww dataset whose quote files go to Drive (default unchanged) |
| `fno/intraday/wiring.py` | A16's clock check moved, unchanged, into `build_clock_check()`, used by A16 and A4e (one rule, no copy) |
| `config.yaml` | `quotes.windows.v4: {start: "14:30", end: "14:40", max_early_wait_minutes: 30}` |
| `CLAUDE.md` | the new composition root in the Code list |
| tests | `tests/quotes/test_named_window.py`, `test_named_window_config.py`, `window_fakes.py` |

**Found while building (fixed, not in the story text):** A4b's Drive-only store sends to Drive only quote files under
the exact dataset `groww/derivatives/quote-snapshots/`. A v4 quote file would have stayed in the repository folder (kept
out of git by `.gitignore` and the record scan, but never saved to Drive: a lost day). The v4 store is now built for
its own dataset; a planted bug that drops this is caught.

## Criteria, tests and broken-code proof

Each mutation planted in place, the two new test files run, the file restored (14 of 14 caught).

| # | Criterion | Tests | Mutation → result |
|---|---|---|---|
| 1 | Default unchanged | every existing quotes test, A4's byte-for-byte baseline, the default sidecar has no A4e key, `tools/forecast_live_golden.py` "unchanged" | (default constants untouched) |
| 2 | Window | 14:05 run waits, nothing asked before 14:30 (chains, levels, quotes); 13:59 "too early", provider never asked; retry; no request after 14:40:00, a 6 s answer to a 14:39:5x request kept at its real later time; retries never start after 14:40, day ends "none" | start ignored, end ignored, 20-minute wait, no stop → all CAUGHT |
| 3 | Own dataset | sidecar and marker under `quote-snapshots-v4`, quote file in fake Drive only, A4's report sees nothing; the composition root's store prefix | shared dataset, store not routed to Drive → CAUGHT |
| 4 | Clock | both ok; skew before; skew after; no server answering (unchecked, no skew); a check that raises (one reading, never clock_ok) | status = last reading, missing reading ignored, log never begun, log not written → all CAUGHT |
| 4b | Own times | chains per expiry with spot and both times; levels requested after the last chain answer and received before the first quote request; a level answered after 14:40 keeps that time; NSE futures carry no bid or ask | chain time not logged, level receive = request → CAUGHT |
| 5 | Refusals | unknown name, missing or extra key, bad time, unquoted YAML 14:30 (the number 870), start not before end, negative or boolean wait; the command stops before building anything, also with `--source nse` | start<end check removed, nse allowed → CAUGHT |
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

On ac55bc60: `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q -n auto`: 7,704 passed, 1 error in
`tests/factory/test_freeze_and_verdict.py` (a setup error under parallel runs only: the file passes alone, 13 of 13,
with and without this change; not touched by A4e). `ruff check fno tests tools`: clean; `ruff format --check`: 1,391
files formatted; `python tools/check_imports.py`: clean (1,481 files); `python tools/check_records.py`: clean;
`python tools/forecast_live_golden.py`: "live golden cases unchanged: case_a, case_b". No file over 350 lines
(`recorder.py` 348).

## Known limits (from the story; nothing built for them)

- Not in the routine: O1 adds the step and the owner moves the start to 14:05; whether 14:30 is an extra capture
  (about 190 more Groww calls at A16's 14:30 mark, one key) or replaces 14:55 is the orchestrator's and owner's call.
- The default capture's clock stays unchecked (v2's frozen behaviour).
- `recorder.py` is at 348 lines: the next change to it must split it first.
