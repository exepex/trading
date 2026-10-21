# Judge 446: FL1-1d design renderer (story/fl1-1d-design at 60b93a7b)

**Verdict: FAIL: 2 should-fix findings and 2 minor.** It is clean, self-contained code:
- standard library only, no external request, every file under 350 lines;
- one `DesignRenderer` behind the existing `PageRenderer` port;
- not wired yet: `page_wiring.py`'s one-line switch is the FL1 builder's.

Nothing is live. Both should-fix findings are about honesty labels, the thing the owner reads first.

## Checked myself
- **Gates:** on 60b93a7b merged with today's `main` (no conflicts; my clone is unshallowed), one run:
  - 9,273 passed, 16 xfailed;
  - `ruff check` clean; 1,740 files formatted;
  - imports clean; record scan clean (7,462 files).

  The 9 shallow-clone errors the designer saw do not occur in my clone. Strong evidence.
- **No external request.** No `http`, `url(` or `@import` in `fno/forecast_lab/design/`.
- **Escaping.** Free text is escaped (reasons, provenance, light word, system lines); the rest are formatted numbers
  and fixed classes.
- **Signed-off design (11ef1b23).** Three big numbers, two plain line charts (no bands, no fan), the gap chart, the
  day table, counts, the month calendar, the reliability trend, the misses table, one key (✓ Correct / ⚠ Close call
  / ✗ Missed). All present by reading.
- **Shown:** the system line (`view.system`); today's provisional close ("close as read after 15:30; the official
  file confirms it next morning"); the evening's back-fill note.

## Findings

**Should-fix 1. The morning picture's reliability chip counts back-tested days as if they were live.**
- `page.reliability_chip` prints "Inside 'almost certainly' X of Y (✓ correct … · ⚠ close call …)". It is the only
  record on the morning page (`morning.py:60`), and `backtested_note` is used on the evening page only.
- On go-live mornings all Y days are G13b back-fill. Judge 434 should-fix 1 ruled that the record must never pass
  back-tests off as live. The Slack line keeps "(N back-tested)", but the picture drops it.
- Fix: add the back-tested count to the chip, or show `backtested_note` on the morning page as well. Strong evidence:
  code.

**Should-fix 2. No test pins the honesty labels.** All 4 of my mutations survived (`test_design_pages.py`,
`test_design_camera.py`):
- U1: a miss reason no longer escaped;
- U2: the provisional note replaced by the plain date;
- U3: the back-tested note dropped;
- U4: system problems hidden behind "All systems normal".

These are the page's honesty and safety rules, and today a later edit could remove any of them silently. Fix: one
assertion each, plus the morning chip from should-fix 1. Strong evidence: mutation run.

## Minor
1. **The page no longer names the method or how it was chosen.** Judge 434.1 accepted "lowest error on its own
   history, the same days it is scored on" in the details file, and DESK_DECISIONS row 275 keeps method names "in the
   attached details". `details()` now returns the picture page, citing f9737bce and 11ef1b23. Neither row says the
   attached file drops the method; f9737bce asks for one page per edition. Add one small line ("method: implied,
   lowest error on its own history") to the page's foot, or record the owner's word that it is dropped.
2. **FL1-1's seal-check and match lines (`view.checks`) are no longer in any posted file.** Missing and late
   forecasts still alert #fno-desk, so nothing is lost silently. Say so in the response's limits.
