# Builder's response to wave 2, round 1

| # | Fix | Evidence |
|---|---|---|
| 1 | Tests for `archive_text_or_none` (404 -> None, 200 -> text, 500 -> HTTPError) and for `ReferenceData.load` with a failing FII load (lot sizes and ban list still loaded, `fii` None); `FakeNseFeed` gains `archive_text_or_none` | tests/live/test_wave2_rules.py `test_participant_files_missing_or_failing` |
| 2 | FII signal abstains when the latest file is more than `max_age_days` (5) old; the data date is in the reason | `test_fii_signal_votes_on_change_for_indices_only` (stale and fresh cases) |
| 3 | `MoveCheck.detail` returns "move check: not measurable ... not applied" when it cannot measure, so the idea carries it; tests for zero spot | `test_move_check_refuses_unrealistic_targets_and_notes_the_ratio` |
| 4 | Reason: "FII index futures long share +x% pts vs its recent average; options tilt change +y (data of DD Mon)" | fno/live/signals/participant_signals.py |
| 5 | Hold converted to calendar days (max_days x 7/5 = 2.8) in services; default 2.8; documented | fno/live/services.py, fno/live/move_check.py, docs/WAVES.md |
| 6 | README: guard list, signal count and list, contract choice, module map | README.md |
| 7 | `python -m fno calibrate` (fno/backtest/calibration.py) re-measures path efficiency and move ratios | run output in the session log |
