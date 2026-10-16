# Response 151: story A4c, the other traded index options at 3 pm (builder's claims)

Branch `story/a4c-all-indices` (lane 1). Story text: `docs/stories/A-data-foundation.md`, section A4c, passed by judge
151 addendum 2 at e10c811 (with the `CLAUDE.md` 3 pm section on the same branch). Owner decisions: 15 Oct 2026 (time
slots; "drop NIFTYFPI and NIFTYNXT50, record only the traded indices"). Builder session 01MKtUHByHsR9cNwaP5KhFYH.

## Verdict in two lines

`python -m fno quotes record-indices` records BANKNIFTY, FINNIFTY and MIDCPNIFTY after NIFTY's push, inside 15:01-15:13
IST, paced; raw quote files in Drive only; NIFTY's own recording is unchanged byte for byte. **Strong evidence** (tests,
14 of 14 planted bugs caught, step 0 on real Groww). Not yet run live: the first real day is for rule 8, after the merge.

## Step 0: Groww accepts the three names (read-only, real, 15 Oct 2026 about 21:35 IST)

Run from this session with the committed provider (`GrowwProvider.expiries` and `.chain`; counts only):

```
BANKNIFTY ok: 3 expiries listed, 740 option legs in the nearest chain
FINNIFTY ok: 2 expiries listed, 504 option legs in the nearest chain
MIDCPNIFTY ok: 3 expiries listed, 590 option legs in the nearest chain
```

(`growwapi` was installed here with `pip install --no-deps growwapi` plus `pynacl`, `nkeys`, `nats-py` and `pyotp`, since
`requirements-groww.txt` does not build in this container. Groww lists only this year's FINNIFTY expiries, as for NIFTY;
in late December A4's NSE-file fallback already covers it.)

## What changed

| File | Change |
|---|---|
| `fno/quotes/slot.py` (new) | `Slot`: underlying, NIFTY-only cross-check, request stop time, workers, pace, listing check; `NIFTY_SLOT` is A4's |
| `fno/quotes/book_fetch.py` (new) | `BookFetcher`: one book per contract in order, each with its own send and receive time; workers under A16's `RatePacer`; no request starts after the slot's stop |
| `fno/quotes/recorder.py` | takes a `Slot` (file stems `<underlying lower-case>_...`, `nifty_` for NIFTY); the previous session's NSE file in the sidecar as `universe`, a name it does not list is `NOT_LISTED`; `attempt_now`, `close_day`, `is_session` for the index runner |
| `fno/quotes/quote_validity.py` (new) | A4's `traded_today` and `quote_validity`, moved unchanged (size limit) |
| `fno/quotes/indices.py`, `indices_cli.py` (new) | the 15:01-15:13 runner (one attempt per index in turn, retries while the window lasts, "none" at its end, no wait on a closed day) and the command (one line per index, one alert, exit 1 if any index is not recorded) |
| `fno/quotes/expiry_listing.py` | a day's NSE file read and parsed once per run |
| `fno/quotes/cli.py`, `fno/composition.py`, `fno/constants.py` | the `record-indices` command, `build_index_quote_recorders`, `RECORDED_INDEX_OPTIONS` |
| `CLAUDE.md` (earlier commit, passed with the text) | 3 pm steps 2, 3 and 3b |
| tests | `tests/quotes/test_index_recording.py`, `index_fakes.py`, `test_routine_commit_paths.py` |

## Criteria, tests and broken-code proof

Each mutation planted in a scratch worktree, `tests/quotes` run, file restored (14 of 14 caught).

| # | Criterion | Tests | Mutation → result |
|---|---|---|---|
| 1 | Each index recorded; Drive-only quotes; universe in the sidecar; refused or unlisted index → "none", others complete | each-index, refused-index, unlisted-index (one attempt, provider never asked), unreadable NSE file | universe dropped, unlisted skipped silently, unlisted retried, day not closed, rows out of order → all CAUGHT |
| 2 | NIFTY unchanged | A4's byte-for-byte baseline (4 scenarios), every existing quotes test, `tools/forecast_live_golden.py` "unchanged" | NIFTY stem changed → CAUGHT |
| 3 | Window and pace | waits for 15:01; an index whose turn comes after 15:13 asked nothing; nothing starts after 15:13 (started 15:12:50); started at 15:13 asks nothing, "none"; a request at exactly 15:13:00 allowed, 15:13:01 refused; pacer waited before every request; slot 3 workers, 2.5 a second | stop removed, no wait, pacer skipped, pace changed → all CAUGHT |
| 4 | Quiet index: complete, invalid rows, no alert | quiet-index test | cross-check applied to indices → CAUGHT |
| 5 | Closed day; no NSE file | closed day at the routine's 14:35 start: nothing asked, nothing written, no wait, exit 0; no NSE file: one sidecar per index with the reason, one alert, exit 1 | session check removed → CAUGHT (with the 14:35 start) |
| 6 | Each part stages only its own files; `CLAUDE.md` gives those paths | `git add --dry-run` in a temp repo with all parts' files (NIFTY, NSE, indices; Groww CSVs ignored); `CLAUDE.md` holds the same pathspecs | (path test) |
| 7 | Gates | below | |
| 8 | First live day | after the merge (rule 8): the orchestrator records NIFTY's, NSE's and the indices' commits | not yet |
| — | NSE file parsed once | three indices, `listed` and `listed_on`: one read, one parse | cache removed → CAUGHT |

**One wording point for the judge (criterion 5):** with no NSE file the run "records nothing" in quotes, but it does
write one sidecar per index saying why (the attempt is the record of the failure, as A4 does for every incomplete
attempt) and closes the day "none". It asks Groww nothing.

## Real output sample (dry run: fake quotes, fake Drive, fake clock; nothing sent)

```
== normal day (started 15:00:30)
BANKNIFTY recorded: banknifty_20261013_150103 (12 contracts, complete=True)
FINNIFTY recorded: finnifty_20261013_150130 (12 contracts, complete=True)
MIDCPNIFTY recorded: midcpnifty_20261013_150157 (12 contracts, complete=True)
exit code: 0 | alerts: []
repository: 6 files (3 markers, 3 sidecars) | fake Drive: 3 quote files
== FINNIFTY refused, MIDCPNIFTY not listed (started 15:00:30)
BANKNIFTY recorded: banknifty_20261013_150103 (12 contracts, complete=True)
FINNIFTY recorded: finnifty_20261013_151213 (0 contracts, complete=False)
MIDCPNIFTY recorded: midcpnifty_20261013_150133 (0 contracts, complete=False) - not listed as an index option in the previous session's NSE file
exit code: 1 | alert: "3 pm index recorder: not recorded today (canonical none): FINNIFTY (incomplete);
  MIDCPNIFTY (not listed as an index option in the previous session's NSE file). Data only; NIFTY is separate; the
  sidecars in research/data/quotes/groww/ say why."
```

## Gates

On f9ea121e (code final): `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`: 5891 passed, 0 failed (554 s);
`ruff check fno tests tools`: clean; `ruff format --check`: 1080 files already formatted; `python tools/check_imports.py`:
clean (1121 files); `python tools/check_records.py`: clean (5957 files); `python tools/forecast_live_golden.py`: "live
golden cases unchanged: case_a, case_b"; no file over 350 lines (`recorder.py` 340, `composition.py` 340).

## Self-review

One independent review agent (correctness and silent failures) read the diff at a11f21fc:
- **Accepted, fixed:** a rerun after 15:13 on a day already recorded reported all three indices "window closed",
  alerted and exited 1 (NIFTY's `record` checks its marker first). Now each index with a marker is "already recorded"
  before the window check. Test: a rerun at 15:20 asks Groww nothing, alerts nothing, exits 0. Broken-code proof:
  putting back the old start fails it.
- **Accepted, fixed:** the end time was checked once per retry round, so a later index's expiry and chain calls could
  start just after 15:13 (criterion 3). Now it is checked before each index's attempt. Test: an index whose turn comes
  after 15:13 is asked nothing. Broken-code proof: removing the check fails it.
- **Already a known limit:** a bad NIFTY day (retries to 15:10) leaves the indices little time; they may end "none".
- Checked by the agent, no finding: NIFTY's clock calls, names and keys unchanged; `pool.map` keeps row order and
  per-row times; the pacer's lock; Groww's client made in the main thread before the workers; round-robin retries;
  one alert; no test weakened.

## For the owner and the orchestrator

1. After the merge, the routine's prompt needs steps 2, 3 and 3b as in `CLAUDE.md` (exact text in the section).
2. Known limits (story): NIFTY retries to 15:10 can squeeze the indices; the pace figures come from one morning; a
   new index needs an owner decision.
