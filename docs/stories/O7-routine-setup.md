# Story O7: one setup for every scheduled routine

**Why (15 Oct 2026).** The 3 pm recorder fired on time (14:48:26 IST) but its session found `python` and `python3`
at /usr/local/bin (3.11) while bare `pip` was /usr/bin/pip (3.13). The packages went into the wrong Python; the
session spent 14 minutes recovering, the capture began at 15:02:25, after the 15:00 forecast cutoff, and forecast
v2 lost every same-day input (10 of 20 probabilities, no IV30). A dry run in another session of the same
environment the same day found a different layout (everything 3.13): the machine is not the same from run to run,
so the fix cannot assume one layout.

**Change.**
- `tools/routine_setup.sh [--groww]`: finds every distinct interpreter behind `python3` and `python` (real path),
  installs the requirements into each with `<interpreter> -m pip install -q --use-pep517`, proves both names import
  the packages, turns on the record scan hook, and prints `routine setup ok: <interpreters> (<s>s, <time> IST)`.
  Any failure stops at once with one `routine setup FAILED: ...` line, instead of an AI session guessing.
- CLAUDE.md (3 pm recorder step 1), README.md and `requirements-groww.txt` name the script; bare `pip` is not
  used by any routine.
- `tests/test_routine_setup.py`: the script installs only through the interpreter it checks, covers both names,
  keeps the flag and the hook; CLAUDE.md, AGENTS.md and README.md name no bare `pip install`.
  `tests/test_groww_install_command.py` (A16c) no longer requires CLAUDE.md and README.md to hold the install line
  (they now name the script; the new test checks the script's flag).
- After merge, every scheduled routine's prompt (3 pm recorder, A8 release recorder, A8 monthly sweep, O6 dry run,
  Book 2 and Book 3, the judge's lane-2 audit) calls `sh tools/routine_setup.sh` instead of its own install line.

**Not changed.** GitHub Actions jobs keep `pip install`: `actions/setup-python` puts the matching `pip` first on
PATH. The commit hook already picks `python3` first, and the script covers `python3`.

**Checked.** The script on this machine (one interpreter: 5 s); with a planted `python` that cannot see the
packages, it stops with "routine setup FAILED: 'python' (...) cannot import numpy, requests, yaml".
