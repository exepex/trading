# Response 310: story FL1-1d, the design part: the signed-off report design as production code

- **Author:** Claude (the designer session, session_014fc2LA2Q7TbwiJ4yACmi9R)
- **Date:** 2026-10-22
- **Branch:** `story/fl1-1d-design` (lane 1, new code under `fno/`)
- **Decision:** the owner signed off the report design at d8f0440 on `story/fl1-report-design` (DESK_DECISIONS
  11ef1b23); the orchestrator asked for it as production code, with no visual change, for Judge E.
- **Builds on:** the FL1 builder's `PageView` (`fno/forecast_lab/page/model.py`) and `PageRenderer` port
  (`fno/forecast_lab/page/render.py`); the builder switches `page_wiring.py` to the new renderer with one line.

## What was built

`fno/forecast_lab/design/`, one package, every file under 350 lines, standard library only:

| File | What it does |
|---|---|
| `renderer.py` | `DesignRenderer(PageRenderer)`: `picture(view)` draws the morning page when `view.edition == "morning"`, else the evening page; `details(view)` is the same page (the owner asked for one single page per edition) |
| `morning.py` | Edition A, 08:50 IST: the key, the cues strip, per index the three big numbers (most likely, almost certainly, the forecast middle with the 3-day range), chart 1 over the last 10 sessions with today's forecast as a labelled point and a labelled range line, "why this forecast", the reliability chip |
| `evening.py` | Edition B, 20:05 IST: the key, per index the result card, chart 1 (30 sessions), chart 2, the day-by-day table (10 rows), the counts with percentages for the last 30 and for the month, the back-fill note, the calendar, the reliability trend, the misses, the levels |
| `blocks.py` | The result card (forecast middle, actual close, gap in points and percent, the result chip, the plain "closed … pts above/below …" line), the day table, the counts, the misses table |
| `lines_chart.py` | Chart 1: forecast middle (dashed) vs actual close (solid), dot per day in the result colour, last values written, a title per day; the morning variant with the forecast column |
| `gap_chart.py` | Chart 2: the gap per day, zero line, dashed step lines for both range edges, every miss and the last day written with its signed gap |
| `trend_chart.py` | The reliability trend from the builder's `rolling_90`, target 90%, warning zone under 80%, the state word |
| `calendar.py` | The month calendar of results |
| `page.py` | The frame (head, header, footer), the key, the cues strip, the reasons block, the levels table, the chip |
| `values.py` | The plain values read once from the `PageView` (`Day`, `Range`); the only arithmetic is the gap and its percentage, until FL1-1d-2 carries them |
| `formats.py` | Outward rounding to 10 through `plain.outward` (one rule for the text lines and the pages), the middle to 10, signed gaps, the three-colour result read from the builder's `inside_50` / `inside_90` flags |
| `design.css` | The signed-off stylesheet, unchanged, plus three lines for the confirmation line, the back-fill note and the levels' "as of" |

## Rules kept

- **No visual change** from d8f0440: the HTML structure, classes and stylesheet are the preview's; the preview's
  generator read a JSON dump of the same `PageView`, the package reads the dataclasses.
- **The page computes nothing it should not.** The result colour comes from the builder's inside flags; the ranges
  round through `plain.outward`; the gap (close minus middle) and its percentage are the one exception, named in
  `values.py`, until the model carries `gap_points` and `gap_pct` (FL1-1d-2, agreed with the builder).
- **No guess as a fact.** The cues strip, the "why" lines and the levels table read the builder's `cues`, `why` and
  `levels` when the model has them (FL1-1d-2) and print "not available yet" in plain words until then; a section's
  status `not_out_yet` / `not_available` / `failed` prints as plain words. The preview's example values are not in
  production.
- **Fields the model may not have yet** (`edition`, `provisional`, `confirmation`, `backtested`, `cues`, `why`,
  `levels`) are read with defaults, so the renderer works on `main`'s model today and on the builder's branch.
- Strings from the model (provenance, reasons, cue names and values) are HTML-escaped.

## Tests

`tests/forecast_lab/test_design_pages.py` (7 tests) pins the key once per page, the three big numbers, chart 1 and
chart 2 as desktop and phone drawings for both indices, the day table's nine columns, the counts with percentages,
the calendar, the trend, the forecast point on the morning chart, "not available yet" for unwired cues, no shaded
band or bar (no `polygon`, no `rect` but the trend's warning zone), no request, one definition of "right", the
edition dispatch, and an index with no scored session. `tests/forecast_lab/test_design_camera.py` draws both
editions with the real Chromium at 1100 and 390 px (skipped where Chromium is absent). `design_builders.py` makes
the page from made-up levels (30 sessions, three misses, a method record with its rolling trend).

## Gates (on the branch at 65f87bc6, merged tree = main df5c66af plus this)

- `python -m pytest -q -n auto`: 1,822 passed (the design tests and the code-size test included).
- `ruff check fno tests tools`: clean; `ruff format` applied.
- `python tools/check_imports.py`: clean (1,810 files).
- `tools/check_numbers.py` runs on `main` after the merge (this response's row is claimed, 310).

## For the FL1 builder (agreed by message, 22 Oct)

- Switch `page_wiring.py`: `from .design.renderer import DesignRenderer` and `ReportMaker(pages, DesignRenderer(), ...)`;
  the camera width is already 1100.
- FL1-1d-2 fields the pages will read as soon as they exist: `Outcome.gap_points` / `gap_pct`, misses over 30
  sessions, `PageView.cues`, `IndexView.why` and `levels` (as `Cue`), `confirmation`, `provisional`; `rolling_90`
  stays as it is.

## Honest limits

- The levels table and the cues strip are empty ("not available yet") until FL1-1d-2; the preview showed example
  values, the production page shows none.
- The miss reasons cover the sessions the builder keeps (7 today); the misses table prints "reason not kept for this
  day" for the others until the builder keeps 30.
- `details(view)` returns the same page as `picture(view)`: the attached file and the picture are one page by the
  owner's decision; the earlier details file (method grids, scores, checks) is not part of the signed-off design.
