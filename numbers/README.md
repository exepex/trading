# Number registry (story O12)

One file per numbered series; each series has its own numbers, so series never clash with each other.

| File | Numbers | Name column |
|---|---|---|
| `claude-response.csv` | `reviews/claude/response_<n>_<slug>.md` | the file name |
| `chatgpt-review.csv` | `reviews/chatgpt/review_<n>_<slug>.md` | the file name |
| `judge-report.csv` | `reviews/judge/judge_<n>_<slug>.md` | the file name |
| `judge-addendum.csv` | `## Addendum <k>` in `judge_<n>_*.md`, numbered `<n>.<k>` | a short label |
| `ledger-trial.csv` | blocks of trial ids in `research/ledger.csv`, numbered `<a>-<b>` (or `<n>`) | the experiment prefix |

**Ledger trials (story O12e).** Claim a block before registering trials:
`python tools/claim_number.py ledger-trial <experiment-prefix> --session <id> --count <k>`, then merge `main` into
your branch (`git pull --no-rebase origin main`) and register the trials with an experiment that is the prefix or
starts with it and `-`. `Ledger.register`, the factory and the evaluation freeze refuse an id outside such a block;
the check fails on a trial in no block, a trial in another experiment's block, and overlapping blocks. Ids that are
not whole numbers (`book3:<strategy_id>`) are names, not counted ids, and stay outside. Trials 1-108 were on `main`
when this merged and are seeded history (pinned), one block per run of one experiment.

Columns: `number,name,session,claimed_at_utc`. Rows with session `existing` are the files that were on `main` when
O12 merged (history, kept as it is, duplicates included); their SHA-256 is pinned in `fno/numbering/seed_pins.json`,
so none can be added later. Every later row is a claim. An addendum heading must carry its number (`## Addendum 3`);
the 14 old unnumbered `## Addendum` headings are outside the series. Write only the addendum's own number in the heading (`## Addendum 5` for claim 307.5, never
`## Addendum 307.5`): the tool prints the exact heading.

**Claim before you write.** `python tools/claim_number.py <category> <slug> --session <id>` pushes your row to `main`
from a temporary worktree (your branch is untouched) and prints the number; a refused push is retried on the new
`main`. Without the tool, claim from a separate copy of `main`, never your own working checkout (a reset there would
wipe uncommitted work and unpushed commits):

1. `git fetch origin main && git worktree add --detach ../claim origin/main` (or a fresh clone), then work in
   `../claim`;
2. append one row: the next number after every row and every numbered file of the series, the file name, who you
   are, the UTC time (`YYYY-MM-DDTHH:MM:SSZ`);
3. commit only this file and `git push origin HEAD:main`;
4. refused? Someone claimed first. Never `git pull` (a merge can keep both rows with one number): in `../claim` only,
   `git fetch origin main && git reset --hard origin/main`, then step 2 again;
5. accepted: the number is yours; `git worktree remove ../claim`, then write the file in your own checkout.

In GitHub's web editor (or its contents API) the same holds: edit the file on `main`, commit straight to `main`; a
refused save (the file changed meanwhile) means someone claimed first, so reload and take the next number.
Claims are lane 3 (status rows).

`python tools/check_numbers.py` (CI, every push; `number-alert.yml` posts new problems to #fno-desk on each push, story O12b) fails when a numbered file or heading has no row, a number is used
twice outside the history, or a row is malformed. Never edit or delete someone else's row: the check protects the
seeded history (pinned) and catches a reused number, but it cannot see a claimed row edited or deleted before its file
exists (git history and the judge's lane-3 audit can).
