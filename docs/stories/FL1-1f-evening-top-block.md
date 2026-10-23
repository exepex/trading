# FL1-1f: the evening's top block, readable in 30 seconds

Lane 1. Builder: session_01FWkBH4zNAEFSEpjUzVEgnd. Branch `story/fl1-1f-evening-top-block`, built on FL1-1e
(`story/fl1-1e-today-verdict`), for Judge E. Approved by the orchestrator on 23 Oct 2026 after the owner's message
about the 20:05 edition: the evening "did not indicate ... whether the forecast was correct or not, and if it was not
correct, why? And if it was correct, then why? ... in under 30 seconds".

## What the owner gets (the Slack text; the designer mirrors it on the page as their own story)

Per index, in this order:

1. **The verdict line.** It reads: "*NIFTY* today: closed 22,600.00 (NSE's close; the official file confirms it in
   Monday's morning report) | most likely 22,533–22,797 → ✅ inside | almost certainly 22,283–23,018 → ✅ inside →
   ✓ right".
   - An edge that is missed reads "❌ outside by 214.65 points (below)": a glyph and a word, never colour alone.
   - The ranges are the forecast's own edges to the point. The morning's words round them outward to 10, which could
     show a close a few points outside the range as inside it.
2. **No verdict: a red line first, never only in the footer.** It says what is missing, why, and when the answer
   comes:
   - "⚠️ *NIFTY* today: no verdict. Today's close could not be read (<the reader's own reason>). The result comes in
     Monday's morning report."
   - "❌ *NIFTY* today: no verdict. No forecast was issued for today (the Thu 22 Oct 15:45 issue holds no
     next-session forecast for Fri 23 Oct), so there is nothing to check."
3. **Why**, up to three lines, each labelled:
   - "Day (measured)": the open and its gap on the previous official close, the day's low to high, and the close,
     against the forecast's centre and its "most likely" width. A level not recorded is left out, never made up.
   - "Size (measured)": the day's swing as a multiple of the "most likely" width. For a hit, how many points inside
     the nearest "almost certainly" edge, and whether that is narrow or comfortable. Narrow means within a quarter of
     the half-width; that threshold is reasoning only and is labelled so.
   - "Missed because (measured)": only reasons that FL1-1c's direction-aware facts measured. Otherwise "Missed
     (reasoning): no measured cause in our data, so likely noise". A cause is never guessed.
   - "Context (measured, not a cause)": the page's evening cues (US closes, VIX, Brent, USD/INR, flows) by size.
4. **The record, live and back-tested apart**: "🟢 Live so far: 1 day, inside “almost certainly” 1 of 1 |
   Back-test (last 30 days): 25 of 30".
   - "Live" counts every live sealed check so far, today's own included.
   - "Back-test" counts the back-filled sessions among the last 30.
   - The morning line uses the same words.
5. **Next**: tomorrow's and the 3-session forecast, as before.

The footer (the status line) stays, but nothing that changes a verdict lives only there.

## Data

- **The day's open, high and low** come from A4h's same 15:40 read: `TodayCloses.levels`, from A4h's parsed record.
  - The record has had `open` since 22 Oct. `high` and `low` are in NSE's raw answer, which A4h already keeps
    (checked on 23 Oct: NIFTY 50 high 22,787.25, low 22,372.00).
  - The A4h builder has been asked to add them to the parsed record, so there is one source. Until they do, the Day
    line shows the open and the close only, and the Size line has no swing. Nothing is invented.
  - The DR1 builder is informed, because A4h's closes are DR1's first dataset.
- **The previous close** is the previous session's official close (`Outcomes`, as the morning uses it).
- **The record** comes from the page's own next-session points (G13b's scores plus today's own check). Live means
  sealed and on time; everything else is back-test.

## Design

- `page/today_view.py`: values only. The day's shape, the record (`TrackRecord`) and the cause of no verdict.
- `page/verdict_words.py`: the top block's words, built from `plain.py`'s shared words (`VERDICTS`, `PROVISIONAL`,
  `OFFICIAL`, `morning_report`, `record_words`).
- `page/message.py`: the message's text. It moved out of `plain.py`, so that `plain.py` (shared words) and
  `verdict_words.py` (the evening block) do not import each other.
- The model gains `DayShape`, `TrackRecord`, `IndexView.shape`, `IndexView.track` and `IndexView.unchecked_why`,
  each with a default.
- `TodayCloses.levels` is a port method with an empty default.

## Tests

- Edges are the forecast's own, so a close 0.40 points outside is shown outside.
- A hit is called narrow or comfortable.
- A miss shows its measured reasons, or "no measured cause".
- Context is never a cause, and the quiet marker is never a cue.
- The Day line shows only the levels that were recorded.
- The record keeps live and back-tested days apart, including when there is no live day and no back-test day.
- The builder carries the day's path and the record. The morning, and an evening without a check, carry no path.
- A4h's levels come from the same record, only when recorded, and only after 15:30.
- The no-verdict lines are given for both causes.
- The replay's evening shows its real gap first.
- MS-P1g's evening golden text is regenerated from the unwrapped maker. Its picture hashes, alerts and verdict count
  are asserted unchanged.
- Mutations: 9 of 9 caught, after three survivors got tests (the live window, the morning's path, an empty level).

## Real data (read-only dry run of the 23 Oct evening, nothing posted or written)

- NIFTY closed 22,600.00: inside 22,538–22,795 and 22,286–23,018, right. Its close was 314 points inside the nearest
  edge, comfortable.
- BANKNIFTY closed 54,287.35: outside "most likely" (54,509–55,189) by 221.43 points below, inside "almost certainly"
  (53,868–55,753), right.
  - The hand verdict sent earlier said 212.65 points. That was measured against the morning's outward-rounded range
    (54,500); the forecast's own edge is 54,509.4. The edges-to-the-point rule exists for exactly this reason.
- Record: NIFTY "Live so far: 1 day, 1 of 1 | Back-test (last 30 days): 25 of 30"; BANKNIFTY 1 of 1 and 28 of 30.
- The Day lines carry the open and its gap on the previous close (NIFTY +55, BANKNIFTY +40). There is no swing until
  A4h records high and low.
- Context: the evening cues as read from A17 (shown in Slack only, never in repository files).
