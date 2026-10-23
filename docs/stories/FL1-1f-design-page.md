# FL1-1f, the design part: the page's top block from the builder's words

Lane 1. Builder: the designer session (session_014fc2LA2Q7TbwiJ4yACmi9R). Branch `story/fl1-1f-design-page`, from
`main` f2e7a4c3 (the FL1 builder's FL1-1f merged), for Judge E's delta check (orchestrator, 23 Oct 2026). The owner's
decision of 23 Oct (the evening's top block, readable in 30 seconds) and the builder's story
`docs/stories/FL1-1f-evening-top-block.md` set the words; the page mirrors them with no copies.

## What the page shows (per index, the evening)

1. **The verdict rows**, from `page/verdict_words.py`: "today: closed 22,459.00 (NSE's close; the official file
   confirms it in Monday's morning report)", then "most likely 22,099–22,379 → ❌ outside by 80.00 points (above)",
   "almost certainly 21,849–22,529 → ✅ inside", then "verdict: ✓ right" (green) or "✗ wrong" (red). The ranges are
   the forecast's own edges to the point (`range_words`), inside or outside by how many points (`edge_words`); right
   is the builder's `inside_90` flag (`plain.VERDICTS`).
2. **No verdict: the red line first**, `no_verdict_words(index, view.day, view.next_session)`: "⚠️ today: no verdict.
   Today's close could not be read (<the reader's reason>). The result comes in Monday's morning report." or "❌ today:
   no verdict. No forecast was issued for today (<the issue's reason>), so there is nothing to check."; then "last
   checked: Thu 22 Oct, ✓ Correct". An index with no code prints "⚠ today: not checked (no verdict)".
3. **Why**, each row the builder's sentence: `day_line` ("Day (measured): opened …, ranged …, closed …; the
   forecast's centre was … and its “most likely” width … points."), `size_line` ("Size (measured): swing … = 0.8× the
   “most likely” width; close 70 points inside the nearest “almost certainly” edge, narrow (narrow = within ¼ of the
   half-width; reasoning).") and `cause_lines` ("Missed because (measured): …" or the no-cause line; "Context
   (measured, not a cause): …", "Context: not available (…)" or "Context (measured): no notable moves in our data.").
   The missing context sources are read as the text line reads them (`page/message.py`'s rule: every `SectionView`
   whose status is `not_out_yet` or `failed`, its `why`). The evening's why block lists no cue of its own any more
   (the Context row carries them); the morning's keeps its cue list.
4. **The record pill**: `plain.record_words(index)` ("Live so far: 1 day, inside “almost certainly” 1 of 1 | Back-test
   (29 of the last 30 days): 26 of 29"), coloured by `plain.light` (live checks only); "Too few live days to rate ·"
   in front until it can rate. The morning's pill is the same. The page's own chip counts are gone.
5. The three numbers, the three-colour chip and its plain line, the method line and the next session's forecast
   stay (FL1-1e, option A). The result card's small range and the day table's two range columns now show the
   forecast's own edges to the point, like the verdict rows, so a close a few points outside is never shown inside a
   rounded range; the big forecast numbers (the morning's and the evening's next session) stay rounded outward, as
   the morning text rounds them.

The morning's "Last session's check" uses the same rows.

## Claims (for Judge E)

- Every word on the block is the builder's: `verdict.py` and `page.py` import from `plain.py` and `verdict_words.py`;
  the design keeps three strings with no text-line twin ("today: not checked (no verdict)", "last checked: …", the
  provisional morning label) and no other.
- `tests/forecast_lab/test_design_pages.py` (17 tests) pins: the verdict rows with the edges to the point and the
  "outside by N points (side)" words, for a hit, a close call (right, green, over the amber chip) and a miss (wrong,
  red); the red line's sentence with the reason and the report's name for both codes, placed before "last checked"
  and the method line; the morning's rows; a past day never called "today"; the record pill equal to
  `plain.record_words` with the light's words in front, and green once the live checks rate; the back-test count on
  both pages; a cue's unit on the change only; the honesty labels; the renderer dispatch; no band, bar or request.
- `tests/forecast_lab/test_design_camera.py` draws both editions at 1100 and 390 px with the real Chromium.
- Checked by eye at 1100 px (the posted width) on made-up levels: a close call with the why rows and the pill, and an
  unchecked index with the red line first.
- Gates: `ruff check`, `ruff format`, `python tools/check_imports.py`; the full suite's count is in the branch's
  last commit message addendum below.

## Gates on the branch (55ef15fd, from main f2e7a4c3)

- `python -m pytest -q -n auto`: 14,762 passed, 0 failed, 1 skipped, 16 xfailed.
- `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py`: clean.
- The first run had 19 failures in the school's golden-text test: the fakes carried a track record by default, which
  changed the builder's text line; fixed at 55ef15fd (a track only when asked, as with the check).
