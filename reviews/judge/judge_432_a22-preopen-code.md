# Judge 432: A22 pre-open capture, code (story/a22-preopen @ a2b2ad8c), for response 300

Judge F (independent). Story `docs/stories/A22-preopen-data.md` (text PASS, judge 407 add. 1-2), claims
`reviews/claude/response_300_a22-code.md`. Lane 1 (NSE, Groww, Drive, Slack, a Claude routine). Labels: **strong**,
**some**, **reasoning only**.

## Verdict: FAIL (1 should fix). The rest is MET apart from the live-only criterion 7.

## Gates (mine, at a2b2ad8c, an environment with `requirements.txt` only, as CI has)

| Gate | Result |
|---|---|
| pytest `-n auto` | **1 failed, 9023 passed, 17 xfailed**: `tests/preopen/test_parts.py::test_the_capture_reads_gift_the_fo_list_then_nifty_and_banknifty_from_groww` (SF1) |
| ruff, ruff format (1676), `check_imports.py`, record scan (7361) | clean |
| Size | `fno/preopen/` files 21-98 lines |

## Planted mutations (mine, in a separate copy; `tests/preopen` plus `tests/health/test_preopen_check.py`)

| # | Plant | Caught |
|---|---|---|
| 1 | a read seen after the window's close is still `ok` (never `late`) | yes (4 failed) |
| 2 | retry every 300 s instead of 30 s | yes (5) |
| 3 | parts' problems dropped from the alert and O10 rows | yes (5) |
| 4 | no trading-day check | yes (3) |
| 5 | a second run's "day row taken" not caught | yes (2) |

The builder's own 11 mutations are listed in the claims.

## Should fix

**SF1. One test needs the Groww SDK, which CI does not install, so the merge would turn main red [strong:
reproduced].** `test_the_capture_reads_gift_the_fo_list_then_nifty_and_banknifty_from_groww` calls
`fno.preopen.wiring._parts(...)`. That builds `GrowwProvider(cfg)`, whose `__init__` imports `growwapi` and raises
`RuntimeError("Install the Groww SDK first ...")` when it is absent (`fno/providers/groww.py`:130-134).
`.github/workflows/checks.yml`:35 installs `requirements.txt` only; `growwapi` is in `requirements-groww.txt`, which
only the routine installs. The test's comment ("builds only: Groww signs in on the first read") is right about the
sign-in but not the import.

Fix expected, either:
- the test injects a provider (or monkeypatches `GrowwProvider`) so it checks the part names and symbols without the
  SDK; or
- `_parts` builds the provider lazily, inside the `ReadOnlyGroww` lambda, so wiring needs no SDK until the first read.
  This is better: a routine without the SDK then fails at the read, as a named part failure.
Then run the full suite in a CI-like environment, without `requirements-groww.txt`, and cite it.

## Criteria (code read, tests and my plants)

| # | Status |
|---|---|
| 1 GIFT Nifty: fresh within 15 min, yesterday or before-midnight stale, HTML or missing block refused | MET |
| 2 F&O list: complete only from NSE's 09:08:00 (choice 3, stricter than the text: accepted), empty `data` incomplete | MET |
| 3 Index: 09:09 candle close; step 0b re-run through the production reader, 21 of 21 equal for both indices (output in the claims, as add. 2 asked) | MET as reported (no Groww key here) |
| 4 Windows: exact boundaries on an injected clock; `late` when seen after close | MET (plant 1) |
| 5 Storage and records: write-once via O9, the day row taken once, one O10 row per problem, one alert; lines name parts, statuses and exception kinds only (I checked every `BadAnswer` and `PartFailed` message: times and kinds, no level; `CandleParse` names the exception type only) | MET (plants 3, 5) |
| 6 Routine section in CLAUDE.md; end-to-end with fakes | MET |
| 7 Real output: first live mornings | pending, live only |
| 8 Witness: O8 row by 09:20 (09:20:00 ok, 09:20:01 late; regular and special expected; holiday and muhurat not) | MET; O8's owner reviews the `fno/health` diff, as agreed |

The builder's eight choices beyond the text are each reasonable and stated:
- keep only the final raw answer per part, with read counts in the row;
- do not read `key=NIFTY`/`key=BANKNIFTY`;
- the 09:08:00 finality rule;
- one read for a late run;
- values only for `ok` or `late` parts;
- the clock checked once;
- commit order;
- `symbol=` on A16b's source, default unchanged. A16b's owner is told.

The text's open question 2 (terms of NSE's pages) is settled by the owner's row 281 (judge 431 add. 1). This is NSE's
public JSON, read without a login, paced, and stored privately.
