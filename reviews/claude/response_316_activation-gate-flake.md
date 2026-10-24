# Response 316: the activation-gate flake (judge 437): not reproduced in 10 full runs, no code change

From the A4 builder (session 01MKtUHByHsR9cNwaP5KhFYH), for the orchestrator, 22 Oct 2026. The task was to make
`tests/playbook/test_activation_gate.py::test_an_str1_version_is_refused_for_shadow_and_paper_and_nothing_is_written[research-STR1b-2]`
robust after it failed once under `-n auto` in judge 437.

## Result

- The test did not fail in any of my runs.
- I changed no code and no test: without the failure's own message, any change would be a guess (CLAUDE.md, "No
  patches").
- The failure's evidence is lost. Judge F's gate command piped pytest through `tail -4`, which kept only the
  `FAILED ...` line (judge F, 22 Oct).

## What I ran (main 9a0f8bcc and later)

| Run | Result for the test |
|---|---|
| 8 full `-n auto` runs, one after another | passed in all 8 |
| 2 full `-n auto` runs at the same time in one container, while 25 short pytest sessions rotated the shared `/tmp/pytest-of-root` folders (judge F's setup on 21 Oct) | passed in both |
| 6 runs of `tests/playbook` and `tests/daily` at `-n 16` | passed in all 6 |

That makes 10 full parallel runs. Over the same runs, one other test failed once:
`tests/daily/test_git_limit.py::test_a_commit_hung_in_its_hook_is_stopped_with_the_hook_and_leaves_no_lock` (see below).

## Causes ruled out, with the check behind each

1. **Slowness.** The judge's "34.9 s for the file" is normal: the file takes 34.4 s even run alone. Each test's call
   takes about 0.25 s; the rest is the first run's one-time start-up, and repeat runs take about 10 s. Nothing in the
   code under test has a timeout: no `timeout=` and no clock read in `fno/playbook/` or in B4's `Git` adapter.
2. **State shared within a worker.** `STR1_ACTIVATION_PENDING` is changed only by `monkeypatch.setattr` in the same
   file, which is undone after its test. No test leaves `os.environ` changed in a way that reaches git.
3. **A git hook in the temporary repositories.** `core.hooksPath` is local to the checkout, with nothing global or
   system-wide. A fresh `git init` repository has no hook path, so the record scan never runs on the test's commits.
4. **Checks that run before the activation gate.** `EvidenceCommitted` and `ExpectedNetSet` apply only to `paper`
   and `paused`. The failing case is `research`, so only the transition check and the activation check run before the
   expected refusal.
5. **Temporary folders deleted by an overlapping session.** Judge F confirmed their full run overlapped short pytest
   sessions in the same container. But pytest keeps a lock in each running session's `pytest-N` folder. In my
   reproduction, 25 short sessions rotated old folders out while both running sessions' folders (405 and 406)
   survived, and both full runs passed. So this explains nothing, as far as I can show.

## What would make the next occurrence diagnosable

The real gap is that the evidence was thrown away. My proposal, for the orchestrator to put to the judges and
builders: a gate run keeps the failure text. Use `-rf`, and never pipe the whole run through `tail`; for example, save
the full output to a file and print its summary. A mismatched `pytest.raises(match=...)` already prints the message
that actually came, so one kept failure would name the cause.

## The other flake found on the way

- **Where:** `tests/daily/test_git_limit.py` line 69 (`assert not _alive(pid)`) failed once in 5 runs.
- **Why (reasoning only, from the code):** `fno/desk/git_limit.py` kills the process group, then waits only for git,
  the group leader. The hook, a grandchild, could still be alive for a moment.
- **Fix:** reported to the O1/O2 builder, who took fix (a). The call now waits until no live, non-zombie process of
  the group is left (at most 5 s). They also fixed judge E's separate cause in the same test.
- **Status:** on `story/o2-git-limit-test` (a708fbc0), going to judge D.
