# Judge 637: GW1 Groww rate guard, `story/gw1-groww-rate-guard` at 5d5d054ae (round 1 of 2, judge K, judge 2 of 2)

**FAIL, lane 1** (an outside service; fills read its captures). 3 should-fix, 3 minor. I did not read judge I's verdict.

**Gates.** A trial merge of 5d5d054ae840306ebb82b87a78b9fe044892b8e6 into origin/main ade79b9d7 is clean (284c1fbfe). On it,
with the Slack token set: `pytest -n auto` 16,615 passed, 1 skipped, 13 xfailed, exit 0. ruff check and format are clean.
`check_imports` (2,767 files), `check_records` (9,297 files) and `check_numbers` are clean. **No test posted to Slack**
(23:36:01-23:46:00 UTC): #fno-intraday is empty. #fno-desk and #fno-forecast hold only "DRY RUN, <day> replay" lines,
which the orchestrator's rehearsals were already posting before my run began (00:51 CEST onwards).

## Checks

| Asked | Verdict | Own evidence |
|---|---|---|
| No frozen v4 file changed | MET | none of the 17 changed files is in `FREEZE_v4.md` on main (I grepped each path in the 484-line table and the list). `slots.py`, `recorder.py` (quotes), `book_fetch.py`, `pacing.py`, `composition.py` and the intraday `wiring.py` are untouched |
| No recorded value falsified | MET for A4's rows | the quiet window waits only in `expiries()`, before the attempt's first call. Every other call is refused unsent, so `request_sent_at` stays true (plant "no refusal check": caught). For E8, see SF3 |
| Read-only, 429 named, pause, sign-in back-off | MET | SDK 1.5 source: `GrowwAPIRateLimitException` sets `code "429"` and `GrowwAPIException` keeps `.code`, so `is_rate_limit` catches both. The sign-in tries come at +0, 5, 15, 35, 65 and 95 min, then none (code read) |
| Does any situation exceed the limits; does (a) break the owner's rule | **YES** | SF1 and SF2 |

## Findings

1. **Should fix: limit (a) breaks the owner's rule, and the 429 stop counts only after a breach.**
   - A16 alone at 5/s is the whole 300 a minute. With one run `won` at 5/s and one run `unclaimed` at 2.5/s, a 48-83 s mark gets about 360-620 calls, over 300 a minute.
   - This is realistic. A16's fires overlap by design ("runs one hour past `--until`", A16-owner-checklist section 7), so two runs meet at every mark of that hour. On 16 Oct, two takers lost 74-87 quotes each to 429s (`claims.py:1-3`).
   - "Until the first 429" is the breach itself. The owner said "in any situation", so the builder's limit (a) is not acceptable unless the owner rules otherwise.
   - **Fix, one of two (the owner picks; my reasoning only):**
     - (i) an `unclaimed` run does not take the mark and records it missed. Cost: the mark is lost when every run's claim fails.
     - (ii) A16 asks at 2.5/s always, and the quiet window grows to about 180 s. A4c then starts about 15:03, E3 about 15:18, and E3 ends past `fills_by` 15:20.
2. **Should fix: a mark taken late runs outside the 90 s quiet window.**
   - A16 may take a mark up to 120 s after it (`takeable_marks`, `ON_TIME_SECONDS = 120`), then asks for 50-83 s more, so until about mark + 203 s.
   - A4c (15:01:30, 2.5/s) or E3 (15:16:30) would then share the second with A16's 5/s: 7.5/s, about 450 a minute.
   - It has not happened yet: all 124 taken slot rows sent within 0.0013 s of the mark. But reruns happen: 23 Oct "restarted at 15:05".
   - **Fix:** A16's recorder (not frozen) takes no mark later than a few seconds after it, so its read always ends inside the window. Or the window covers 120 + 90 s.
3. **Should fix (text): E8's stand-in fill snapshot moves later.**
   - When A16's mark is missing, E8 uses an A4 capture whose `started_at` is in the mark's 2-minute window, for example E3's 15:15 capture (`mark_snapshots.py:90-96`). It drops only quotes asked before the mark.
   - Under GW1, E3's `started_at` stays 15:15, but every quote is asked from 15:16:30 to about 15:19. A "15:15" exit fill is then priced 90-240 s after the mark; before GW1 it was 0-154 s.
   - This is not stated, and the orchestrator's Q1 covered timing "never a recorded value". E8 is not live yet.
   - **Fix:** state it under Known limits and tell E8's owner. Either E8 drops stand-in quotes asked after mark + 120 s, or the owner accepts it.

## Minor

- **m1:** the sign-in worst case counts "about 10 processes" but leaves out A16's several overlapping fires and their reruns, and the daily rerun's children. It is still well under 150 (about 100 by my count), but say so.
- **m2:** `groww-check` and the feed probe's REST client build `GrowwProvider` directly, so they get no quiet windows. Both run by hand, and A16 leaves no headroom. Two lines, neither file frozen.
- **m3:** the unpaced sequential readers (NIFTY's 3 pm capture, `v4`, E3) stay under 10/s only because Groww is slow: 180 contracts in 158 s on 23 Oct 14:55. Add this to Known limits.

## Plants

**Mine: 18, all caught:**
- 429 detection off; a pause of 1 s; the pause check off by 1 s.
- The mark excluded; the window's end included; a quiet window of 60 s.
- The back-off cap at 60 min; a 7th try; no day reset; the boundary moved by 1 s.
- No wait before an attempt; no refusal check; `api` without the allow-list.
- No halving; always half pace.
- Groww's text in the alert; Groww's text in the 429; the next-year 429 swallowed.

## Addendum 1: round 2 (the last), `story/gw1-groww-rate-guard` at 33f34e571 (judge K)

**Parts 1-4: PASS. Parts 5-6: FAIL, 1 blocking. The branch as a whole cannot merge as it stands.** I did not read
judge I's verdict.

**Gates.** A trial merge of 33f34e57183cf270d85dd4141d3a1b6802cf8b34 into origin/main d6438bafa is clean (00cd71685). On it,
with the Slack token set:
- `pytest -n auto`: 16,795 passed, 1 skipped, 13 xfailed, exit 0.
- ruff check and format are clean. `check_imports` (2,782 files), `check_records` (9,325 files) and `check_numbers` are clean.
- No test posted to Slack: all three channels are empty for 00:41:24-00:51:01 UTC.
- No changed `fno/` file is in `FREEZE_v4.md`.

| Round-1 finding | Verdict | Own evidence |
|---|---|---|
| SF1: a won run plus an unclaimed one | fixed | `ClaimResult.take` is `outcome == WON`. An unclaimed run retries once after 15 s, then records `missed` ("claim not pushed ... not taken here"). A claim committed but not pushed now counts only after `publish()` pushes it, and the old `NOTHING_AS` = published hole is closed. A pull conflict keeps the remote copy (`-X theirs`), so its holder is `lost`. No path gives two takers |
| SF2: a late mark outside the window | fixed | A16 asks at 4/s until `FAST_LEAD` (1 s) before mark + 120 s, then at 1/s, and every call is paced before its send time. A mark taken up to 120 s late is at 1/s from its start. After a window, A16 at 1/s plus A4c at 2.5/s plus NIFTY at about 1.2/s is about 4.7/s, under 5/s and 300 a minute |
| SF3: E8's stand-in | stated | in Known limits, with 120-274 s, and in the register's E8 row |
| m1, m2, m3 | fixed | 3 sign-in tries per process; the worst case is 38 × 3 = 114, under 150. `groww-check` and the feed probe go through `get_provider`. The unpaced readers' limit is stated |

**Blocking B1: E3's capture can now end after `fills_by`, and C3 then refuses the day's prices.**
- The story says "`desk.fills_by` (15:20) limits only a rerun". That is not so. C3's `SnapshotInWindow` (`fno/checks/snapshot_checks.py:30`) needs the capture's `finished_at` ≤ `fills_by`, and fails as `prices_unverified` otherwise.
- E3 now asks from 15:17:00. Its five recorded captures took 2:34-3:15 (sidecars of 19, 21, 22 and 23 Oct), so they would end at 15:19:34-15:20:15. That leaves 3-26 s of margin, and 22 Oct's 3:15 fails.
- Your decision (fills_by about 15:23) is not on the head: `config.yaml` still says `fills_by: "15:20"`.
- **Fix:** move `desk.fills_by` in this change (or merge it first), and correct line 114. Check the knock-ons:
  - the rerun rule (`FILLS_LATE`) and `runner.py`'s wait to `fills_by`;
  - the school's `SCHOOL_STARTS_BY` 15:25. With E3 ending about 15:20 the school starts about 15:21, which is fine; a day with an E3 retry is near the limit.

**Minor:**
- **m4:** two of my plants survive: `FAST_LEAD` = 0 (fast starts can be booked up to 1 s past the window), and the fast pace back to 5/s. Neither breaks a limit while the window refuses the others, but both rules lack a test.

**Plants:** 12 of mine, 10 caught:
- unclaimed taken; no claim retry; `publish` skipped;
- always fast; 1/s made 4/s; calls unpaced; window 90 s;
- 4 sign-in tries; `groww-check` and the feed probe built directly.
