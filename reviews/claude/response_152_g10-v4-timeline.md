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
3. A4c's slot moves to 14:41-14:58 and stocks take 15:01-15:13: both keep clear of A16's 15:00 and 15:15 marks and the
   shared Groww key's busy minutes (A16 measured about 50 s a mark).
4. The 15:10 deadline is GitHub's push time, as v2's 15:15 is today.
