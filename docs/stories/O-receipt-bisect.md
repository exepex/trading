# Story: receipt bisect

- Owner session 013xqaNTCbSBytKgqpfaYFqZ, assigned by the orchestrator on 23 Oct 2026.
- Lane 1: an outside service, and it decides records. Judged by Judge F. Branch `story/o-receipt-bisect`.
- It follows receipts-reach (judge 514).

## The problem

All figures below are measured, strong evidence: read-only on main 75147474, 23 Oct.

- The receipt search checked git ancestry for every push from the commit's own date onward. For a session a week old
  that is about 1,900 pushes.
- The 15 commits behind the 22 Oct health check's "unknown" findings took about 3-4 minutes to look up.
- The health workflow has `timeout-minutes: 15`, and the 22 Oct run already took 13.6 minutes. So the check risked
  being killed with no result.

## The design

- On plain pushes (`activity_type: push`, each a fast-forward of main), "this push's `after` holds the commit" turns
  true once and stays true.
- So the first push holding the commit is found by halving: about 11 ancestry checks for 2,000 pushes.
- Then that push is checked exactly: its `before` must not hold the commit.
- A window with any other activity (a `force_push`, which can drop commits) is read push by push, as before.
- The halving can land on a push whose `before` already holds the commit:
  - At the window's first push, that means the commit was pushed before its own date. That is a date set later than
    the real push, and it gives no receipt, as before.
  - Anywhere else, the log contradicts itself, which GitHub should never produce. The answer is a plain
    `ReceiptUnknown` ("not one fast-forward line"), never a time.
- Main has had no force push (strong evidence: `activity_type=force_push` returns 0 on 23 Oct). The orchestrator
  confirms that main only fast-forwards.

## Claims

1. **The halving finds the right push.** Strong evidence: tested in `tests/ai/test_receipt_bisect.py`.
   - Among 2,000 plain pushes, the right push is found with at most 14 ancestry checks.
   - The first push of the window can be the one.
   - A commit in no push has no receipt.
   - A window with a force push is read push by push and finds the first push, where halving would give a later time.
   - Plain pushes that contradict themselves give no receipt.
2. **Revert plants: 4 of 4 caught.** Each was run alone:
   - every window read push by push;
   - a force push halved too;
   - the found push not checked;
   - a contradiction read as "no push".
3. **Live results are unchanged, in a fraction of the time.** Strong evidence: the 15 commits gave the same 15
   receipts as the push-by-push search, in 16.7 s instead of about 3-4 minutes. Most of the 16.7 s is the 29 log
   pages. All earlier receipt tests pass unchanged; their fakes carry no `activity_type`, so they take the
   push-by-push path.
4. **Not covered:** whether tonight's health run fits inside 15 minutes depends on its other steps too. That will be
   shown by the run itself (the orchestrator's part 2).
5. **Gates:** in the message to the judge.
