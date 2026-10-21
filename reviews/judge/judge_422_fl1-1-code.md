# Judge 422: FL1-1 code, the 15:45 forecast lab report (story/fl1-forecast-lab at ad13de4e)

**Verdict: FAIL: 4 should-fix findings and 4 minor.** The gates are green and most of the design is sound. The
problem is in production: the match report and the late-seal alerts sit behind a check on today's official close,
which is almost never archived by 15:45. So in production they would almost never appear, and nothing tells anyone.

## What I ran and checked myself
- **Gates:** I ran them on ad13de4e merged with today's `main` (892b16b8, no conflicts; G13b is on `main` now).
  - 8,855 passed, 18 xfailed;
  - `ruff check` clean; 1,639 files formatted;
  - imports clean; record scan clean (7,276 files).
  - The builder reported 8,854 and 19 on its own tree; `main` has moved since. Strong evidence.
- **Channel IDs:** I checked them in Slack with a read-only channel search. #fno-forecast and #fno-intraday were
  created on 21 Oct, and their IDs match `fno/constants_channels.py` and DESK_DECISIONS row 263. #fno-desk's matches
  CLAUDE.md. The IDs are not quoted here, because `main`'s scan allows only #fno-desk's until FL1 merges. Strong.
- **Record scan:** it allows exactly these three IDs, and a fourth ID is caught (`test_patterns.py`). Strong.
- **O1 step:** `lab_close` is last, after `candles`. It is wrapped as `Alerted(LiveFrom(NotBefore(15:45)))`, with
  `live_from` null, and its receipts are limited to the lab's own Drive folder. I read the code; the wrapper order
  means a day before go-live does not wait. Strong.
- **18 planted mutations:** 14 caught, 4 survived (M3, M5, M13, M17). One more mutation survived on a path
  should-fix 4 needs (M16). Details are at the end.

## Findings

**Should-fix 1. The match report and the late-seal alerts almost never happen at 15:45.** Strong evidence: probe test
plus reading the code.
- `MatchSection.lines` (`match.py`) returns at once when `outcomes.close(underlying, day)` is None. It prints
  "today's official close is not archived yet; today's match comes in the next report" and returns **no alerts**.
- The builder's own open point 2 says the close is almost never archived at 15:45; judge 406.2 found the same: NSE's
  official close lands in the evening.
- The next report does not do what that line promises. `CloseReport.build` matches only the targets of its own `day`.
  So day d's targets are never matched, and their missing or late seals are never alerted.

My probe ran day d and the next session with closes archived only from the following day, as in production. The
setup had a late N1 seal for day d. Result:
- zero alerts on either run;
- neither report mentions the late forecast's issue day;
- both reports say "today's match comes in the next report".

That breaks criterion 2 (a late seal is recorded and alerted) and the owner's "matching report" (row 262), silently.

Fix:
- Check seals and send the missing or late alerts whatever the archive state; the seal check needs no close.
- Have each report match the latest target day whose close is archived and that has not been matched yet. In practice
  that is the previous session's targets, labelled with their date.
- Or put the evening-report option to the owner. Either way, the report must never promise a match it will not
  deliver.
- Add a two-day test like my probe.
- Open point 3 belongs here too: with no daily `pricerange score` step, G13b's scores are not refreshed, so even an
  archived close shows "no scored row yet". Name the step's owner and its place in `DAILY_RUN_STEPS` before go-live.

**Should-fix 2. Desk alerts that fail to send are reported as sent.** Strong evidence: probe.
- `LabClose.run` collects `self.desk.send(...)` but throws the outcome lines away. `POSTED` prints
  "{len(sent)} alert(s) to #fno-desk" whatever the outcomes said.
- With `NoAlertSender` (no token) and a late seal, the run printed `#fno-forecast: alert sent; 2 alert(s) to
  #fno-desk`, exit 0. No "alert NOT sent" line appeared.
- CLAUDE.md's routine step 3 depends on that line to post by hand with the connector. So a missing or late forecast
  alert is lost silently.
- Second, a rerun after a "not posted" failure posts the stored report and **sends every alert again** (the stored
  alerts are re-sent on each run). That breaks "alerted once".

Fix:
- Print each alert's outcome line.
- Count only alerts that were sent.
- Send the alerts once: mark them sent in the posted marker, or in a second marker written when they are sent.
- Test both cases.

**Should-fix 3. Criterion 7's membership check is not built.** Strong evidence: grep. Criterion 7 says "The bot's
membership in both new channels is checked with one read-only `conversations.info` call in setup". No code in `fno/`
or `tools/` calls `conversations.info`. Response 294 mentions it as needed, but not under "Open".

Fix: build it (a few lines in the routine setup, read-only, never a test post). Or record it as a named go-live check
with an owner in the story and the register. The step is off today, so this does not block safety. It does block a
claim that criterion 7 is met.

**Should-fix 4. Criterion 2 is not tested through G13b's real adapter.**
- My mutation M16 changes `G13bRanges.sealed` to pass `late=False` instead of G13b's `found.late`. All tests pass.
- `test_g13b_integration.py` uses only an on-time record.
- FL1's own seal rule (`sealed_at < 09:15 of the target day`) is weaker than the story's rule ("before the next
  session's 09:15"). For an N3 issue sealed two sessions late, G13b's `late` flag is the **only** guard against
  look-ahead. So that is exactly the path that must be tested. Strong evidence: mutation run plus reading
  `sealing.py`.

Fix:
- Add an integration case where G13b's `SealCheck` marks a record late (pushed after the next session's 09:15, but
  before the N3 target's open) and FL1 refuses and alerts it.
- Better still, make FL1's own rule the story's rule too.

**Minor.**
1. **Survived mutations M3 and M13:**
   - M3: today's issue is shown even if `sealed_at > now`. The test covers only `sealed_at=None`.
   - M13: a non-`ok` row is matched.

   Add one assertion each. M5 (the trust line counts only the first underlying) and M17 (no issue-day filter in the
   match) also survive. M17 is harmless today, because back-fill stops before `live_from`. Add a BANKNIFTY-only day
   to the trust test.
2. **Slack wording:**
   - T1's `UNKNOWN` says "(check #fno-desk)", so a lost post to #fno-forecast would point the owner at the wrong
     channel.
   - The POSTED line reads "#fno-forecast: alert sent" for a report.

   Pass the channel name to the wording.
3. **Where the channel constants live:** `fno/constants_channels.py`, not `fno/forecast_lab/constants.py` as the story
   says (row 263 said `fno/constants.py`). The choice is fine, since constants.py is at its size limit; update the
   story line.
4. **O11 (criterion 8):** the strict xfail with its reason is accepted for now (reasoning only). With no G13b issue in
   the replay, `lab close` there could only alert "no forecast was sealed". G13b's replay step plus `lab close` is a
   condition before `live_from` is set, not a later nicety. Record that in the story.

## What is good
- The port and adapter split matches the agreed design: FL1 never builds a Drive path, and G13b's shapes are pinned
  by a real-object integration test.
- The report is written once with an O9 receipt and read back with its SHA-256 checked. M8 caught.
- A rerun posts the stored text, never a rebuilt one (M12 caught).
- A "may have posted" outcome is never retried (M7 caught).
- Method versions are never pooled (M4 caught).
- Only live scores are counted (M10 caught).
- Exit codes follow O1's contract (M15 caught).
- No over-engineering: one `Sections` port waits for FL1-1b, and nothing more.

## Mutation table (each restored; run on `tests/forecast_lab`, `tests/record_scan`, `tests/daily`)

| Result | Mutations |
|---|---|
| Caught (14) | M1 FL1 ignores G13b's late; M2 seal `<` to `<=`; M4 pool methods; M6 no posted check; M7 may-have-posted not marked; M8 no SHA check; M9 direction flipped; M10 history not live-only; M11 closed day runs; M12 always rebuild; M14 a missing issue not alerted; M15 failure exits 0; M18 no target-day filter |
| Survived (4) | M3, M5, M13, M17 (minor 1) |
| Survived, on the criterion-2 path | M16 adapter drops G13b's late (should-fix 4) |
