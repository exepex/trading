# Response 308: A22b, GIFT Nifty in its own file for the 08:50 morning edition

Builder session_013u1Ac2N9eRQ8XCYPjwpaat, for Judge F. Branch `story/a22b-gift-early` from main 37203a6a. Owner's
choice (c), "Both" (DESK_DECISIONS e70525ee4): GIFT at 08:50 as context, N0 in FL1's 09:12 post.

## What changed

- `fno/preopen/day_row.py`: `EARLY_FILES = {"gift": "preopen/gift/YYYY/MM/<date>.csv"}`, `early_file(part, day)`,
  `early_row(day, result)` (the day row's cells for that part, with the date; a value only when `ok`/`late`, as in the
  day row), and `receipt_path(day, file=None)` (the day row by default, unchanged for O8).
- `fno/preopen/record.py`: when a part in `EARLY_FILES` ends, its file is saved write-once and the receipts are pushed
  at once through `early_commit`. A taken file, a failed save or a failed push becomes a problem line (in the run's one
  alert and an O10 row). The day row is unchanged and still carries GIFT.
- `fno/preopen/wiring.py`: `early_commit` is O9's receipt committer, with A22's `run_paths`.
- A22 story amendment 1, one sentence in the CLAUDE.md section, and a register row.

## Evidence (`tests/preopen/test_record.py`, 4 new tests; 55 in `tests/preopen/`)

- A good morning: the GIFT file has date, `ok`, seen 08:40:00 and the values. It is pushed once, at 08:40:00 on the
  injected clock, before the pre-open window, and its receipt is written.
- A GIFT that never freshens: written `incomplete` with the reason and no value, pushed at 08:44:59.
- A failed early push is named in the alert, which carries no value.
- A second run finds the file taken and pushes nothing; the on-time file stands.
- Real timing [reasoning]: the push is one `git pull --no-rebase` plus a push, a few seconds, so the receipt is on
  GitHub by about 08:41 (fresh at 08:40) or 08:45-08:46 (stale until the window ends), before the 08:50 edition.

For FL1: `early_file("gift", day)` (Drive, under `data/`) and `receipt_path(day, early_file("gift", day))`.

## Gates

Full suite with `growwapi` blocked, as in CI: 9,118 passed, 16 xfailed. ruff, format, imports and record scan are
clean.

## Addendum 1: judge 445 (PASS) minors

1. A failed early push is alerted only at about 09:11. The amendment now says the same-morning signal is FL1's morning
   edition printing "GIFT Nifty: missing" when no GIFT receipt is there (sent to FL1's builder to record in FL1-1d).
2. The amendment's two rows are in A22's gap list.
The first live morning's GIFT push time goes here after it.
