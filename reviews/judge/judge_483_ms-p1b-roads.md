# Judge 483: MS-P1b, roads and the quality gate

**Scope:** story/ms-p1-roads at 183783bd (code 2ed9bbbf, on contracts 756e6545; builder session_01F1RVMF8MNngi97JVNs99L5),
diff 756e6545..183783bd. Judge I (session_01MvZneCLZqBuiGyNxawdVee). Lane 1. Round 1 of 2.

**Verdict: FAIL.** 3 should-fixes, 2 minors. Judge H claimed 482 for this story too; this file is judged on its own.

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | 5 roads on a trading day, none on a holiday | MET | `catalogue.py:27`; plant (trading-day check) caught |
| 2 | Each closure reason from a planted fixture | PARTLY | all 7 reasons tested; 6 capture checks have no failing test (finding 3) |
| 3 | Exactly one reason per closed road | MET | `RoadStatus` holds one; all-pairs test; my plants 26, 28 caught |
| 4 | Gate at 10/10 vs 9/10, 95.0% vs 95.1% | MET | `capture_gate.py:47-52`; plants 19, 30 caught |
| 5 | Conformance | MET | a's checks pass; also on b merged with contracts tip 32fdbdde (368 school tests) |
| 6 | Read-only `capture-gate` run | MET | my run reproduces all 5 lines; only 113 Drive GETs + 3 token calls; no file written; exit 0 |
| - | Leg denominator defined before counting | NOT MET | finding 1 |
| - | Gates | MET | pytest -n auto 10,449 passed, 16 xfailed; ruff check/format, check_imports, check_records, code size clean; largest file 190 lines |

## Accepted decisions (checked)
1. **Ranges, not mids: ACCEPTED** [strong for the count, reasoning for the rule]. I count 0 of 716 band legs impossible on ranges (9 road-days, 21-22 Oct). A mid outside a vertical's bounds while the spreads overlap is not an impossible price. The mids numbers are wrong (minor a).
2. **Any impossible band leg closes the road-day: ACCEPTED as reasoning only.** It is stricter than 3.5, and on ranges it closed nothing. Part h's card must freeze it.
3. **Unreadable listing → `expiry_mismatch`: ACCEPTED** (it fails closed; a separate code would be a's change). **"A Drive outage raises": NOT MET** for one realistic case (finding 2).
4. **Lots from the session's own A20a copy: ACCEPTED.** `lots.py:27`; plant 9 caught. A20a copies at 07:45 IST with an 11:15 retry, before the slot.

## Findings
1. **Should-fix: the leg denominator is read off the capture, so a missing leg leaves it.** `band_keys` (`band.py:13-17`) takes only the keys the capture holds. The sidecar's `expected_contracts` is Groww's own chain (`recorder.py:223`), so a strike Groww drops passes "complete". My plant drops strike 1100 from a good capture: the road opens with 28 of 28 legs (100%). Under 3.5 it is 28 of 32. Today it has no effect: the captured band equals NSE's listed band on all 9 road-days (FINNIFTY's 64 legs are its November strikes, 100 apart).
   - Fix expected: the scheduled legs come from the archived NSE listing already read for the expiry check (no new read), or from a fixed grid of the step. A scheduled leg missing from the capture counts as observed, not passed.
   - Test expected: a dropped band strike lowers the share.
2. **Should-fix: a Drive reply that is not JSON becomes a closure.** `expiries.py:23` catches `ValueError`, and `requests.JSONDecodeError` is one, e.g. a proxy's HTML page from Drive. My plant: `ExpiryUnavailable`, so all 5 roads close `expiry_mismatch` and the 10-session gate is spoiled without a word.
   - Fix expected: let `requests.RequestException` through before the parse catch.
   - Test expected: one that shows it propagates.
3. **Should-fix: 6 capture checks have no test that fails when the check is removed (quality rule 4).** The claim of "25 of 25 caught, incomplete check removed" does not cover them. The survivors:
   - `not meta["failures"]` and `recorded == expected > 0` (`capture.py:131-132`);
   - spot finite and positive;
   - `finished < started` (removing it crashes later in `SlotSnapshot` instead of closing the road);
   - the session-date tests for start and finish (`rules.py:36`).
   - Fix expected: one failing test each.

**Minor:** (a) `prices.py:7-9` and decision 1 say "8-72 legs a day, up to a third of MIDCPNIFTY". My counts on mids over the whole chain: 9-87 per road-day with all pairs (MIDCPNIFTY 87 of 212, 41%), 8-61 with neighbours only. Inside the band only MIDCPNIFTY flags (15 and 6). Correct the text. (b) Reading `valid` as `!= "false"` survives. The recorder writes only true/false, so this is near-equivalent; a reader test with a `valid=false` row would close it.

## Other checks asked
- **No new NSE or Groww read: MET.** I logged every URL: only Drive. `StoredFilesOnly` fetches nothing; the plant is caught.
- **Failing road stays closed, others run: MET.** `test_one_faulty_road_never_closes_another`; each road gets its own verdict. An outage raises for all, by decision 3.
- **FINNIFTY 70%: reproduced, not loosened.** 90 of 128. On each day the 27 Oct legs are 42 of 42; the 23 Nov legs are 3 of 22, with all 19 failures invalid (no trade that day, A4).
  - [reasoning only] After the 27 Oct roll, December becomes the second expiry, so FINNIFTY will likely keep failing.
- **Contracts round 2:** no effect on b. The code merges cleanly; only the story text conflicts. b's `fno.quotes` dataset imports pass a's new import test, and a's `test_shared_values` pins them equal.

## Plants
32 planted (30 mutations, 2 probes), 23 caught. The survivors are findings 1-3 and minor b.
