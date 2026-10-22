# Judge 478: O9b step 1b, the global cues to Drive (story/o9b-cues @ 44ef74ad)

Judge F. Round 1 of 2. Lane 1 (outside-service data, a workflow, FL1's report input). Labels: **strong**, **some**,
**reasoning only**.

## Verdict: FAIL (1 should fix, 1 minor). The data move itself is sound.

Gates on 44ef74ad: **9860 passed**, 16 xfailed; ruff, ruff format (1866) and `check_imports.py` are clean.

What is right:
- The public tables, the shared revisions log, `us_trading_dates` and the public checks are receipt-backed series,
  through A17's `RowLog` and the `Report` port.
- `global-cues.yml` commits the receipts, manifests and `behind_alerted.txt` only.
- `catch_up` adds only the rows after a whole-line start held in Drive; anything else is refused.
- `PartOutOfOrder` stops a part that would sort before a held one.
- The merge-day race step (no global-cues run queued; `move` before and after the merge) is in the plan.

## Should fix

**SF1. A Drive network failure ends FL1's whole report instead of giving the promised failed "Reasons' facts" view
[strong: a probe].**
- `CueRows` (`fno/forecast_lab/page/facts.py`) catches only `RuntimeError`. That covers missing settings,
  `DriveDataUnavailable` and `DriveSignInRefused`.
- A Drive read that fails at the network level raises `requests` errors (`ConnectionError`, `HTTPError`;
  `fno/storage/drive_session.py` re-raises them after its retries). These are `OSError`, not `RuntimeError`.
- My probe: `CueRows` over a table whose `rows()` raises `requests.ConnectionError` → the error **escapes**.
- The page builder calls `self.facts.facts(day)` unguarded (`builder.py` line 59), so the 08:50 or 20:05 edition
  is lost for a Drive outage, where the story says "a failed view, shown and alerted once".
- Before O9b these tables were repository files and could not fail this way, so this is new behaviour.

Fix expected:
- catch `(RuntimeError, OSError)`, or `requests.RequestException` too, in `CueRows`, naming the class only;
- a test: a table raising `requests.ConnectionError` gives the failed view, the rest of the page, and one alert.

## Minor

**The private cues stay on `DrivePartsRowLog`.** The step text states this and the A17 owner agreed, but the umbrella
text (line 84) still says the global cues move to the receipt-backed classes "one way, not two". Update that line,
and add the private cues' move as a named later step in section 3, so it is tracked.

Plants: the probe above. Mutations: the builder's 12 of 12 (read, not rerun, given SF1).
