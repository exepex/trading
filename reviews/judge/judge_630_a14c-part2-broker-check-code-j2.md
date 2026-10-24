# Judge 630: A14c part 2, the daily read-only Groww margin check, code round 1 (judge 2 of 2)

Branch `story/a14c-part2-broker-check` at `5f7dc5d7c`; claims: response 291, "Round 2". **FAIL**, lane 1 (money and
risk, Groww): 1 blocking, 2 should-fix, 2 minor. Trial merge with main `378dbe30f` (register conflict only).

## Criteria

| Criterion (A14c part 2 text, criterion 10) | Verdict | Evidence |
|---|---|---|
| From 09:30 on a session day; outside: "outside market hours", exit 0 | MET | `broker_check.py:66`; plant 09:00 caught |
| No request at or after 14:50; the rest `error` "deadline", exit 1 | MET | `_ask` :136 checks before every request; plants `>` and the index's deadline branch caught |
| One request every 2 s, the NIFTY quote first; no retry storm | MET | `_ask` :134; no retry anywhere; a sign-in failure stops at the first request (quote), `providers/groww.py:143` caches the client; pacing plants (check, wiring) caught |
| Basket rebuilt from the row's own SPAN file: source and SHA-256, three figures to the paisa, legs and sides | MET | `broker_basket.py:240-254`; plants source, figures, sides, 2 lots caught |
| SPAN vs `max(0, scan - NOV)` within Rs 1; exposure at this caller's quote within 0.1% | PARTLY | rule as written (`broker_compare.py:295-301`, 6 plants caught); the level is wrong in a moving market (finding 2) |
| Mismatch: own line, exit 0, never moves the factor | MET | `_finish` :148; no reference to the factor in `broker_*.py`; plants exit 1 and no alert caught |
| Errors: exit 1, reason last, no own alert, class name only | MET | `_one` :121, `_named` :171; text-leak and errors-exit-0 plants caught |
| Read-only allow-list; order calls refused | MET | SDK 1.5 signatures read: both calls take `timeout`; its 6 order names all refused; widened-list plant caught |
| O9 write-once record and receipt; idempotent; first run of the day | MET | `broker_record.py:164-190`; plants error-as-done, done ignored, shortcut off caught |
| O1 step: `DAILY_RUN_STEPS[2]`, own receipts only, behind `live_from` (null) | MET | `fno/daily/wiring.py:144-151`, `config.yaml:210`; receipts-all plant caught |
| Gates: full suite | NOT MET | finding 1 |

## Findings

1. **Blocking: the suite fails without the Groww SDK, which is CI's environment.** `test_before_09_30_the_check_needs_no_drive_or_groww_settings`
   fails on the branch and on the trial merge: `RuntimeError: Install the Groww SDK first` (`broker_wiring.py:30` builds
   `GrowwProvider`, whose `__init__` imports `growwapi`, `providers/groww.py:132`). `checks.yml:35` installs only
   `requirements.txt`; `growwapi` is in `requirements-groww.txt`. Passes after `routine_setup.sh --groww`. So the claim
   "needs no Groww settings" is false for the SDK too. Fix: build the provider on first use (as Drive already is), then the test passes without the SDK.
2. **Should-fix: exposure is compared at a level read once, but Groww charges each basket at the live level when it is asked.**
   The quote is the run's first request; baskets follow 2-3 s apart (60.7 s for 15 on 25 Oct; about 2 min for 40).
   Exposure is linear in the level, so a move above 0.1% in that time flags a correct row. Reproduced with the
   branch's fakes: NIFTY +0.12% after the quote gives 6 of 6 `mismatch`, one "review the stress factor" alert, exit 0,
   and those baskets are `done` (never asked again that day). +0.10% passes. The 21 Oct evidence was after the close,
   when the level does not move, so it cannot show this. How often a 15-basket run sees it is reasoning only: about 1%
   of normal days, more on volatile ones and on 40-basket runs. Fix (text and code): read the level before and after
   each basket, or once more at the end, and call a basket a mismatch only when it is outside tolerance at every level in that range. Test it with a level moving under the check.
3. **Should-fix: the basket's lot is read twice, and the check's copy is untested (plant survived).** The row builder
   uses `cfg["lot_sizes"]["NIFTY"]` (`nse_margins/wiring.py:46`) and the check reads it again (`broker_wiring.py:35`). Plant: the
   check's lot set to BANKNIFTY's: 573 tests passed. Neither copy is dated: A20a's archived `fo_mktlots.csv` (read by
   `fno/school/roads/lots.py`) gives the lot by expiry month. A config left behind an NSE lot revision then sends the
   wrong quantity, and the row's figures still prove themselves. Fix: one source (the row builder's calculator), a
   wiring test, and an `error` when A20a's dated lot for the basket's expiry differs.
4. **Minor: stale story text.** `A-data-foundation.md:2040` says the step runs "about 14:35 IST, after the weather and the v4
   forecasts". The code runs it third (`constants_operations.py:62`), right after the 14:05 start and before weather;
   at 14:35 it would overlap the 14:30-14:40 v4 capture. "About 35 seconds" was measured at 44.7 s and 60.7 s.
5. **Minor (rule 3):** round 2's change (the first-run shortcut, the REH1j test edits) has no self-review entry.

## Plants

27 planted one at a time on `5f7dc5d7c`, each restored with `git checkout`. 25 caught. Survivors: finding 3's lot, and
`level <= 0` loosened to `is None`, which is equivalent except for a negative level (`quote_reading` already maps 0 to
None).

## Notes

- Trial merge without the SDK: 16,624 passed, 1 failed (finding 1), 1 skipped, 14 xfailed. With the SDK: 244 of 244 in
  `tests/nse_margins` and `tests/daily/test_steps.py`. ruff, format, imports and the record scan are clean. Slack token kept.
- Open item, not a finding: the market-hours sample owed Mon 26 Oct about 10:00 IST. It is also the first real test of finding 2.
