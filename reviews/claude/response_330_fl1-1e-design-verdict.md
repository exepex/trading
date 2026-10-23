# Response 330: FL1-1e, the design part: the evening page says whether today's forecast was right, first

- **Author:** Claude (the designer session, session_014fc2LA2Q7TbwiJ4yACmi9R)
- **Date:** 2026-10-23
- **Branch:** `story/fl1-1e-design-verdict` (lane 1: it changes what the posted report says; Judge E, with the FL1
  builder's `story/fl1-1e-today-verdict`)
- **Decision:** the owner, 23 Oct (conversations/2026-10-23.md, "Owner on the evening forecast report"): the evening
  edition's top block per index, readable in 30 seconds, in this order: (1) the verdict (the close against both
  ranges, glyph plus word); (2) when there is no verdict, a red line first saying what is missing and why; (3) why,
  from measured facts only, labelled, never an invented cause; (4) the record with live and back-test apart; (5) then
  tomorrow's forecast. "Lane 1 (FL1 builder, the designer for the page, judge E)."

## The page's own fault on 23 Oct (strong evidence: the code)

With today unchecked, the FL1 builder's `IndexView.result` is `None`. The design's `values.result_of` then fell back
to the newest scored session, so the page showed 21 Oct's result card under "Was today's forecast right?" with no
word that today was not checked. The text lines said "close not read"; the picture did not. Fixed: `result_of` reads
only the edition's own check and returns `None` otherwise; the page then prints the red line first.

## What changed (`fno/forecast_lab/design/`, standard library only, every file under 350 lines)

| File | Change |
|---|---|
| `verdict.py` (new, 80 lines) | The four verdict lines in the FL1 builder's approved words (FL1-1e): "today: closed X (NSE's close; the official file confirms it in Monday's morning report)", "inside “most likely”: yes/no", "inside “almost certainly”: yes/no", "verdict: ✓ right / ✗ wrong" (green/red; right = inside "almost certainly", the one definition). No check: `<p class="nocheck">⚠ {IndexView.unchecked}</p>` first ("today: not checked (no verdict)" when the model carries no reason), then "last checked: Thu 22 Oct, ✓ Correct". `morning_report(day, next_session)`: "tomorrow morning's report" only when the next session is the next calendar day, else "Monday's morning report"; "the next morning report" when the model has no `next_session`. The morning's "Last session's check" in the same words with the day as prefix ("Fri 23 Oct: closed …") |
| `evening.py` | `top_block`: the verdict (or the red line), the three numbers and the three-colour chip as the explanation, why, the reliability chip and the method line (back-tested apart), then "Next session's forecast · close Mon 26 Oct" (the three big numbers, from `index.today`, which the evening view already carries). The charts, tables, calendar, trend, misses and levels follow unchanged |
| `morning.py` | The big numbers moved to `blocks.big_numbers(index, label, missing)` (shared with the evening); the previous session's check shown when `IndexView.result` is there (the morning's own check on the official close) |
| `blocks.py` | `big_numbers` (moved); `result_card(d, report)`: the provisional note names the same morning report as the verdict line, never "next morning" on a Friday |
| `values.py` | `result_of(index)`: the edition's own check or `None`; the fallback to an older day removed |
| `design.css` | 6 lines: `.check` (the four lines) and `.nocheck` (the red line) |

Fields of the builder's branch (`IndexView.unchecked`, `PageView.next_session`) are read with `getattr` defaults, so
this branch runs on `main`'s model today and on the builder's after its merge, in either order. The words (`YES_NO`,
`VERDICTS`) are the design's copies until `plain.py` exposes them; then one import replaces them (asked of the
builder, 23 Oct).

## Design choice (option A, for the owner to confirm or change)

The signed-off key has three words (✓ correct / ⚠ close call / ✗ missed); the approved text line has two (✓ right /
✗ wrong). The page now says both, in one order: the verdict line "✓ right" first, as the text does, and the
three-colour chip beneath it as the explanation ("⚠ Close call · Closed 80 pts above the most-likely range, inside
“almost certainly”"). A close call therefore reads "verdict: ✓ right" over an amber chip. Options sent to the
orchestrator: B, the chip only (one vocabulary, but the picture and the text would differ); C, right/wrong only on the
card, the three colours kept for the charts and tables. A switch is a few lines.

## Tests (`tests/forecast_lab/test_design_pages.py`, 14 tests; `test_design_camera.py`, 4)

New: the verdict's four lines in the exact words and their order before the numbers, why, the record and the next
forecast; a close outside "almost certainly" reads "✗ wrong" in red with "no" on both ranges; no check: the red line
first, "last checked" named, no verdict and no "why", the plain words when the model carries no reason; the morning
report's name (Friday → "Monday's morning report"; Thursday → "tomorrow morning's report"; none → "the next morning
report") on the verdict line and on the note under the close; the morning's "Last session's check"; `result_of`
returns `None` instead of an older day. The honesty test's provisional wording updated. `design_builders.py`: every
fake index now carries its own check (`result`), and `unchecked(index, why)` drops it and the timeline's last point.

## Gates

- `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py`: clean.
- `python -m pytest -q -n auto`: the full suite on the branch (result in the commit message's addendum below).
- `python tools/check_numbers.py` runs on `main` at the merge (this row is claimed: 330).

## Honest limits

- The phone-width pictures in the camera test (390 px) are clipped on the right by headless Chromium's minimum window
  width, before and after this change; the posted picture is 1100 px wide and is not affected. Not fixed here.
- "Why" still comes from the builder's cues and the one measured line (gap against the range's width); when the
  builder's `why` is empty the page prints "not available yet", never a cause.
