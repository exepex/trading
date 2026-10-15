# Response 152: story G10, protocol v4 timeline (story text)

Branch `story/g10-v4-timeline` from main 29d1fcef. Text only: `docs/stories/G-forecasts.md` section G10. For judge A,
then ChatGPT (rule 9). Written from the owner's rows of 15 Oct 2026 (last rows at 29d1fcef).

## Checked before writing (evidence labels as the project uses them)
- **Every v4 time today is 15:00** (strong evidence: `PROTOCOL_v4.md` lines 38, 60-65, 84-85, 113-142;
  `fno/forecast_v4_rules/capture.py:28`; `fno/weather/capture.py:39`). The v2 times (15:10 wait, 15:13 pull, 15:15
  deadline) live in the frozen v2 workflow and `fno/ai/timing.py`; G10 leaves them alone until v4 is live.
- **The cutoff change does not touch today's forecasters' content:** G7's and M1's inputs end at `d-1` (their module
  docstrings), so their back-fill is unchanged; the criterion proves it byte for byte.
- **A16's fallback has a gap for IV30** (strong evidence: A16 records the nearest weekly and nearest monthly; IV30
  interpolates two monthlies around 30 days). So `A2` days carry a flagged IV30. Stated; no extra chain proposed.
- **No 14:30 IV history exists** (panel: end-of-day chains; A16b: index candles only).
- **Name collision:** REPLAN's "G10" is the AI books' v4 prompt; proposed: that becomes G11.

## Choices for the judge and ChatGPT
1. X = the 95th percentile of `abs(ln(S_15:15 / S_14:30))` over A16b's 2020-26 regular sessions (reasoning only;
   99th is the alternative). Flag only, as the owner decided.
2. `system_late` is decided by the pack (none by 14:40), not by the files, so a day without the common input is out for
   everyone even when a baseline that needs no pack (V6) could be computed.
3. A4c's slot moves to 14:41-14:44 and 14:47-14:58 (revision 1); stocks are the owner's decision.
4. The 15:10 deadline is GitHub's push time, as v2's 15:15 is today.

## Revision 1: answer to judge 161 (FAIL, 3 should-fix): all accepted

1. Stock chains taken out of the table: one line, "the stock-chain slot is decided by the owner separately".
2. Correct (strong evidence: A16 marks every 15 minutes, so 14:45 sat inside 14:41-14:58). A4c is now 14:41-14:44 and
   14:47-14:58. The same check found a fourth overlap the judge did not list: A16's 14:30 mark and the new 14:30 NIFTY
   capture run in the same minute on the same key (they never overlap today). Stated in the story; criterion 6's dry
   run measures both together, and the capture starts after A16's mark if they clash.
3. The AI books' v4 prompt story is renamed G11 in `REPLAN.md` (lines 27 and 130) and `REPLAN_new_stories.md` (line 51).
Judge note (c), accepted: X uses A16b's checked closes of the candles ending at 14:30 and 15:15, not candle opens.

## Revision 2: ChatGPT review 113 (PARTIAL, one blocker) and the owner's decision (response 159)

- **Cutoff integrity (blocker), fixed by the owner's choice "Honest times, window to 14:40":** every live field keeps its
  real `observed_at`; the pack's cutoff is "observed by 14:40:00"; a day's label carries its pack's latest observation
  time; after 14:40 the day is `system_late`; nothing is ever labelled earlier than observed. ChatGPT's fixture is
  criterion 1a (14:29:59 in, 14:41:00 out, the real A16 fallback with its own times).
- `A` and `A2` only for packs complete within the window. X frozen with its sample count, source revision and the
  nearest-rank 95th percentile convention. One pack hash bound to every family (criterion 1b). GitHub receipt time,
  never commit time. Counts of `A`, `A2`, `system_late` and flagged days on every report. Live and close-proxy cohorts
  apart. G1 v2's 15:00 records never merged into v4.
- Judge 161 addendum 1 notes: the table row reads "(G11)"; the two-sign-in line says "some evidence, once, outside
  market hours".

## Revision 3: judge 161 addendum 2 (FAIL, 1 should-fix) and notes a-d

- **`observed_at` defined (should-fix, accepted; strong evidence):** Groww returns no quote timestamp
  (`fno/quotes/recorder.py:65-69`; `fno/providers/groww.py:94-103` has only `last_trade_time`). `observed_at` is our
  request's answer receipt time, the honest upper bound; `last_trade_time` stays its own field for the "traded today"
  check only; a provider's own stamp only where one exists (NSE's page time).
- The window lines agree: the capture starts at 14:30:00; a quote is in if received by 14:40:00.
- Fixture 1a rewritten: received 14:40:00 in, 14:40:01 out; a quote received 14:31:05 with its last trade at 14:29:59
  carries 14:31:05.
- Notes a-c: the flag's S is A16's checked 14:30 and 15:15 levels (the same rule X is calibrated on; the pack's spot
  would measure a different interval each day); "14:30" -> "the pack's" in changes 3 and 6, the heading and the owner
  paragraph; criterion 2 names `terms.V4_CAPTURE_START`.
- Note d: two lines added to the S1 protocol draft (`research/evaluation/PROTOCOL.md`, `timetable`, a draft, not frozen):
  the 15:15 skill score is a diagnostic only, nothing is promoted on it; an instrument missing at the 60-minute fill is
  a no-fill.
