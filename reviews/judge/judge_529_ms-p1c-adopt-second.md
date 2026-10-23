# Judge 529: MS-P1c follow-up, a stored slot file is adopted, never sealed over (second judge)

**Scope:** story/ms-p1c-adopt at fdb57abc: 743eadca and 66cf5c89, plus main merged in. Builder session_01CmKJ6taCLzfEGg7wt6RC4N. Lane 1, money path (the decisions file fills trades), so two judges. Judge B is first (528, 528.1). I judged independently and did not read 528 before this verdict. Judge K (session_019ZApRwkUiNMKDsf1k4W44z).

**Verdict: PASS.** No blocking or should-fix findings. 2 minor.

## Criteria
| Criterion | Result | My evidence |
|---|---|---|
| Adopt only a verified stored file | MET | `dashcam/adoption.adoptable`. The file must decode and re-encode to the same bytes. It must hold only the kind's record types, of this session and slot (an outcome is checked by kind and owner only: a settlement fills on its expiry day). Every record must pass `belongs`. Otherwise `DashcamStuck` names why, never a value |
| Nothing is published before the check | MET | `DriveDashcamStore.recover`: `find`, then the Drive bytes, then `adoptable`, then `data.put` (the same bytes, a no-op on Drive; the receipt is written from them), then publish. My plant removing the check fails 7 tests |
| The fleet's own records | MET | `SchoolFleet._belongs`. A decision needs this fleet's driver and that driver's card SHA-256 as frozen now. An exit, outcome or drift row needs the driver to be this fleet's |
| Loud stop | MET | `DashcamStuck` becomes the status `stopped: dashcam stuck: stored file unverifiable ...`, and the CLI exits 1. My plant removing the catch fails 4 tests |
| The adoption is recorded | MET | The receipt commit message is "... adopted: stored on Drive by a run stopped before its receipt" (my plant caught) |
| Only the writer adopts | MET | The runner uses `recover` for the decisions and before sealing outcomes and drift. `_sealed_once`, the reports, the entry mids and the instructor's reader keep `find` |
| Fakes as strict as Drive | MET | `FakeDashcam.seal` refuses other bytes over a stored file. `recover` goes through the same `adoptable`. `check_dashcam` asserts `recover` for every store |

## Plants (mine, `tests/school/dashcam`, `fleet` and `contracts`): 13 of 13 caught
- In `adoptable`: the canonical check skipped; the kind check skipped; the session check skipped; the slot check skipped; `belongs` skipped.
- In `_belongs`: the card SHA ignored; non-decision rows always belong.
- In the runner: the decisions on `find`; outcomes and drift on `find`.
- In the store: Drive's check skipped; `DashcamStuck` not caught; the plain receipt message instead of "adopted"; a missing Drive file not handled.

## Why adoption here and the cut-off for the instructor [reasoning only]
- The instructor's files are a function of sealed inputs, so the owner chose a cut-off there.
- A fleet decision is not reproducible: a driver's 60 s wall-clock limit, and the 3 pm marker, quote, SPAN or 15:15 capture landing between runs. So adopting the stored, verified file is the only way a stopped session completes without a permanent `ReplayConflict`.
- The seal's pushed_at becomes the adoption commit time. That is still before any fill of the rerun, and the late-rerun mark (law 6) still governs fills after 15:30.

## Minor
1. `_belongs` reads a drift row's driver as `position_id.split(":")[0]`. That couples to the id format, so a named helper beside the id's builder would be safer. It is caught by a test today.
2. A stop at the outcomes or the drift comes after the fills were booked. Every rerun then stops again until a person acts. This is loud and by design, but the runbook line for "dashcam stuck" should say what the person does: inspect the stored file, then the owner decides.

## Gates (my run, a trial merge of fdb57abc with main 85ced401)
- `pytest -n auto`: 14366 passed, 16 xfailed, 2 failed.
- The 2 failures are `tests/intraday/test_feed_tls.py`, which fail on main itself here (`growwapi` is not installed and the test does not skip). They are not from this branch.
- ruff check, ruff format, check_imports, check_records (8641 files) and check_numbers: clean.

## Addendum 1: merge tip b8f72a3d (ins-wiring 98d16fcd merged in)

**Verdict: PASS.** The verdict above stands for the merged tip.
- **Resolution (`fleet/runner.py`):** both sides are kept.
  - From adoption: `recover` for the decisions and in `_seal_once`, `_belongs`, the `DashcamStuck` catch, and `_sealed_once` still a pure `find`.
  - From ins-wiring: `_finish` returns `(SlotFills, refused)`; the refusal reaches `warnings` on both paths; `after_outcomes` sits on both paths.
  - No line of either side is lost.
- **Plants on the merged code:** this report's 13 adoption plants are all caught, and 523.4's 9 counts-commit plants are all caught.
- **Gates (a trial merge with main afe5255d):**
  - `pytest -n auto`: 14438 passed, 16 xfailed, 2 failed.
  - The 2 failures are main's own `tests/intraday/test_feed_tls.py`: `growwapi` is not installed here and the test does not skip.
  - ruff check, ruff format, check_imports, check_records (8658 files) and check_numbers: clean.
