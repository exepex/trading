# Response 87: story E3 follow-up, the account check scoped per book (judge 82 addendum 6)

Builder's claims for `story/e3-scoped-account-check`. Judge 82 addendum 6 ruled that the clean-checkout check may be
scoped, but only together with `git reset --keep`.

## 1. What changed (`fno/desk/git_sync.py`)

1. **The reset is `git reset --keep origin/<branch>`, not `--hard`.**
   - Git drops the rejected account commit and keeps every local edit that the reset does not touch.
   - If the reset would overwrite an edit, git refuses. The write then stops with `CheckoutNotDedicated` (an
     `AccountWriteRefused`, so E3 handles it per order) and alerts #fno-desk: "rejected push NOT reset: the reset would
     overwrite a local edit (...)".
2. **The check before each write is scoped.** `Git.other_work(folder)` refuses when either is true:
   - something is unpushed anywhere (unchanged);
   - this book's folder (`journal/<book>/`) holds uncommitted work.
   Edits elsewhere in the checkout, including another book's folder, no longer refuse the write.
3. **Unchanged:** before a reset, the only commit ahead of the pulled origin must be this write's own; otherwise the
   write stops and alerts.

## 2. Where I went past the ruling's wording, and why

The ruling says "no dirty **tracked** file under this book's folder". I also refuse **new (untracked) files** in that
folder, ignored files aside (the account's `.lock` and `*.tmp` are in `.gitignore`).

Reason: `commit_paths` runs `git add` on the whole folder. An untracked file there would be swept into the account
commit just like an edited one. That is the same "another writer's partial work" risk the ruling names in point 2.
Must-fix D's file, `validity_failures.csv`, was exactly such a file in a fresh checkout (an untracked new file before
its first commit).

Normal runs: an account write starts from the committed state of its folder, so this refuses nothing that runs
correctly. It is a backstop; the rule "every writer commits what it writes" stays the fix.

## 3. Evidence: real git, two checkouts of one bare origin (`tests/timetable/test_git_sync.py`)

The ruling's four tests, plus one for the `--keep` refusal:

| Case | Result |
|---|---|
| An unpushed foreign commit | refused; the commit is kept; one alert |
| An edited tracked file in this book's folder | refused; the edit is kept |
| A new file in this book's folder | refused; the file is kept |
| Another book's uncommitted file | this book's write goes through and is pushed; the other file stays untracked and uncommitted |
| An edit outside the folder, push rejected | reset keeps the edit; the fill is applied again and pushed; nothing is left unpushed |
| The other container changed the very file edited here | `--keep` refuses; stop plus alert; the edit is kept |

The existing tests still pass: a rejected push applies the same fills again, the committer pulls and pushes, more than
one commit ahead means no reset, and every git refusal is an `AccountWriteRefused`.

Mutations (`python -B`, caches cleared), 7 of 7 caught:
1. `--keep` changed back to `--hard`;
2. the status check made repo-wide with no untracked files;
3. untracked files ignored in the folder;
4. the status scope widened to the whole checkout;
5. the reset's return code not checked (`GitError` instead of the alerting stop);
6. the `--keep` refusal ignored;
7. the ahead-count check removed.

## 4. What the owner or orchestrator should know

- **The blast radius is smaller, not zero.** A leftover in Book 1's folder still stops Book 1's account writes. Books
  2 and 3 now go through.
- **A pull can still refuse.** `git pull` itself refuses when an incoming commit touches a locally edited file. The
  write then fails closed with `GitError` (an `AccountWriteRefused`), handled per order by E3's fill step, as before.
- **Edits outside the book folders now persist across account writes.** That is the point of `--keep`. A hand edit
  left in the desk's checkout is no longer noticed by the account check. It stays a hand edit, never committed by an
  account write, because the commit adds only the book's folder.

## 5. Gates

Full suite, `ruff check fno tests tools`, `ruff format --check`, `python tools/check_imports.py` and the 350-line
limit: the results are in the commit message and the message to the orchestrator.
