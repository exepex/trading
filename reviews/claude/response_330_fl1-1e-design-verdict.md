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

## Design choice: option A (the owner chose it, 23 Oct, via the orchestrator)

The signed-off key has three words (✓ correct / ⚠ close call / ✗ missed); the approved text line has two (✓ right /
✗ wrong). The page now says both, in one order: the verdict line "✓ right" first, as the text does, and the
three-colour chip beneath it as the explanation ("⚠ Close call · Closed 80 pts above the most-likely range, inside
“almost certainly”"). A close call therefore reads "verdict: ✓ right" over an amber chip. The owner chose A over B (the chip only) and
C (right/wrong only on the card).

The orchestrator's rule, pinned by its own test: a past day is never called "today". The verdict line and the card's
heading say "today" only for the page's own day, else the day's name ("Wed 21 Oct: closed …").

## Tests (`tests/forecast_lab/test_design_pages.py`, 15 tests; `test_design_camera.py`, 4)

New: the verdict's four lines in the exact words and their order before the numbers, why, the record and the next
forecast; a close outside "almost certainly" reads "✗ wrong" in red with "no" on both ranges; no check: the red line
first, "last checked" named, no verdict and no "why", the plain words when the model carries no reason; the morning
report's name (Friday → "Monday's morning report"; Thursday → "tomorrow morning's report"; none → "the next morning
report") on the verdict line and on the note under the close; the morning's "Last session's check"; `result_of`
returns `None` instead of an older day; a past day's check is named by its date, never "today". The honesty test's provisional wording updated. `design_builders.py`: every
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

## Addendum: judge 538 (FAIL, round 1; 3 blocking, 1 minor) answered at 6c7495f8 and the next commit

Each point checked against the code before accepting; all four accepted.

| # | Judge 538 | Decision | What changed |
|---|---|---|---|
| F1 | 19 school edition tests fail: `design_builders.page()` gave every index a `result`, so the school's golden text changed | **Accept**, already fixed at 6c7495f8 (the judge read 21e9009f) | The fakes carry a check only when asked (`checked=True`); the golden text is byte-identical again. The 14 page-hash assertions that remain pin the design's bytes, not the school wrapper: the MS-P1g builder's lane-2 branch `story/ms-p1g-editions-test` (c115ff2b) compares the wrapped and unwrapped makers in one run and passes 62 of 62 against this branch; it merges first (orchestrator, 23 Oct) |
| F2 | The red line's place before "last checked" is not pinned | **Accept** | The unchecked test asserts red line < "last checked" < method line |
| F3 | Option A's amber case is not pinned | **Accept** | One close call pinned: "most likely: no", "almost certainly: yes", "✓ right" green, before the amber chip |
| F4 | A provisional morning check would say "tomorrow morning's report" | **Accept** (minor, fixed here: it is this branch's line) | `morning_check` labels a provisional close "NSE's close; the official file has not confirmed it yet", never a report's name; pinned by a test |

## Addendum: the 23 Oct dry run (real records, composed to a scratch folder, never posted)

Both editions composed from today's records on a scratch merge of the FL1 builder's branch and this one, to check
the pictures before the owner's labelled dry run (orchestrator, 23 Oct). Two faults of the page, fixed at ffcec24f
and pinned by `test_the_chip_counts_over_its_own_window_and_a_cues_unit_goes_on_the_change_only`:

| Seen | Cause | Fix |
|---|---|---|
| The morning chip said "25 of 30 (✓ correct 2 · ⚠ close call 5)" | The chip counted over the 10 days the morning chart shows | The chip counts over its own window (`index.scored` sessions) on both pages |
| "S&P 500 7,663.43% −1.21%", "GIFT Nifty 22,836% +0.65%" | A cue's level printed with the change's unit | The unit goes on the change only: "7,663.43 −1.21%" |

The merged tree main + the MS-P1g test fix (c115ff2b) + a8ed3186: 14,587 passed, 0 failed. After the builder's
branch lands, one commit swaps the page's word copies for `plain.py`'s (`YES_NO`, `VERDICTS`, `UNCHECKED` keyed by
`IndexView.unchecked`, `PROVISIONAL`, `OFFICIAL`, `morning_report`), prepared and tested on the scratch merge.
