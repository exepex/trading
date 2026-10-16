# Number registry (story O12)

One file per numbered series; each series has its own numbers, so series never clash with each other.

| File | Numbers | Name column |
|---|---|---|
| `claude-response.csv` | `reviews/claude/response_<n>_<slug>.md` | the file name |
| `chatgpt-review.csv` | `reviews/chatgpt/review_<n>_<slug>.md` | the file name |
| `judge-report.csv` | `reviews/judge/judge_<n>_<slug>.md` | the file name |
| `judge-addendum.csv` | `## Addendum <k>` in `judge_<n>_*.md`, numbered `<n>.<k>` | a short label |

Columns: `number,name,session,claimed_at_utc`. Rows with session `existing` are the files that were on `main` when
O12 merged (history, kept as it is, duplicates included); their SHA-256 is pinned in `fno/numbering/seed_pins.json`,
so none can be added later. Every later row is a claim. An addendum heading must carry its number (`## Addendum 3`);
the 14 old unnumbered `## Addendum` headings are outside the series.

**Claim before you write.** `python tools/claim_number.py <category> <slug> --session <id>` pushes your row to `main`
from a temporary worktree (your branch is untouched) and prints the number; a refused push is retried on the new
`main`. Without the tool, commit nothing else first, then:

1. `git fetch origin main && git reset --hard origin/main` (your claim must sit on the newest `main`);
2. append one row: the next number after every row and every numbered file of the series, the file name, who you
   are, the UTC time (`YYYY-MM-DDTHH:MM:SSZ`);
3. commit only this file and `git push origin HEAD:main`;
4. refused? Someone claimed first. Never `git pull` (a merge can keep both rows with one number): go back to step 1.

The number is yours only once the push is accepted; then write the file. Claims are lane 3 (status rows).

`python tools/check_numbers.py` (CI, every push) fails when a numbered file or heading has no row, a number is used
twice outside the history, or a row is malformed. Never edit or delete someone else's row.
