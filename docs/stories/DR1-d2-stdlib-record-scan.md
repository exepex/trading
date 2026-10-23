# DR1-d2. The commit hook's record scan needs no installed package (lane 1)

**Builder:** session_01SPR8hz6AY8S99wE6ypFRik (story DR1, audit item 6; orchestrator's go, 23 Oct 2026). The record
scan (story O5) has no active register row; its code is unchanged, only its composition root moves.

**Why (strong evidence, DR1 audit item 6 and the 23 Oct health check):** Book 2's sealed answer was late on 22 Oct
(pushed 15:15:34) and 23 Oct (15:15:28), due 15:15:00; Book 3 left no commit on 22 Oct. The seal's commit runs the
pre-commit hook, `tools/check_records.py`, which imported `fno.composition` (the whole app: numpy, requests, yaml and
more) while the routine's `pip install -r requirements.txt` was still running in the background
(`docs/stories/F1-G5-owner-checklist.md` step 1), so the commit failed until the install ended and the seal was
retried after 15:15. The scan itself (`fno/record_scan/`) and the seal command (`fno.ai`) import only the standard
library.

**Change:**
- `fno/record_scan/wiring.py` (new composition root, standard library only): `build_record_scanner()` moved here
  unchanged; `fno.composition` re-exports it, so every caller is unchanged.
- `send_alert(text)`: the #fno-desk sender is loaded only when a refusal is alerted; if it cannot be loaded (a package
  missing), the line "alert NOT sent: the #fno-desk sender could not be loaded (<error>) | <text>" is printed, so the
  routine can post it. The refusal itself (exit 1) never depends on the sender.
- `tools/check_records.py` imports from `fno.record_scan` only.

**Not changed:** the Book 2/3 prompt's background install and its "wait, then seal again" step (F1/G5 owner's text,
`docs/stories/F1-G5-owner-checklist.md`); with this change the wait is no longer needed for the seal's commit. Told
to the F1/G5 owner.

## Claims

1. Run with `python -S` (no site-packages), `tools/check_records.py` passes a clean file (exit 0) and refuses a planted
   credential (exit 1), printing the alert text it could not send and never the value.
2. Importing the scan and its composition root loads no third-party module (numpy, requests, yaml, pandas, google).
3. The plant "the hook imports `fno.composition` again" fails 2 of the 3 new tests.
4. Every existing scan test is unchanged and passes (the re-export keeps `fno.composition.build_record_scanner`).
5. Gates: ruff, `tools/check_imports.py`, full suite 14,646 passed.

### Plants (one per claim, each reverted after the run)

| Claim | Plant | Caught by |
|---|---|---|
| 1, refusal | `check_records.main` returns 0 on findings | `test_a_planted_credential_is_refused...` fails |
| 1, alert text | the unloadable sender's line drops the text (`"alert NOT sent"` only) | the same test fails |
| 2 | `import requests` at the top of `fno/record_scan/wiring.py` | all 3 tests in `test_stdlib_only.py` fail |
| 3 | `tools/check_records.py` imports `build_record_scanner` from `fno.composition` again | 2 of 3 fail |
| 4 | the scanner built without its record and credential patterns | 35 tests in `test_stdlib_only.py` and `test_patterns.py` fail |

## DR1-d2b: any failure loading the sender (judge 549's minor; lane 1, judge K's delta)

`send_alert` catches every `Exception` while loading or building the #fno-desk sender (a half-installed package can
fail with AttributeError or OSError, not only ImportError), printing "alert NOT sent: the #fno-desk sender could not
be loaded (<class>: <missing module, else "load failed">) | <text>"; the message of a non-import error is withheld (it
may hold a path). Limit, stated: a Rust extension's panic (pyo3's `PanicException`, as `cryptography` 41 raised on 23
Oct) derives from BaseException and is not caught; the hook then exits non-zero, so the commit is still refused, only
without the text.

Claim 6: a sender that raises AttributeError while built still prints the full alert line. Plant: `except ImportError`
again; the new test fails. Gates: ruff, `tools/check_imports.py`, full suite 14,647 passed.
