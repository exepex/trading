# Number registry (story O12)

One file per numbered series; each series has its own numbers, so series never clash with each other.

| File | Numbers | Name column |
|---|---|---|
| `claude-response.csv` | `reviews/claude/response_<n>_<slug>.md` | the file name |
| `chatgpt-review.csv` | `reviews/chatgpt/review_<n>_<slug>.md` | the file name |
| `judge-report.csv` | `reviews/judge/judge_<n>_<slug>.md` | the file name |
| `judge-addendum.csv` | `## Addendum <k>` in `judge_<n>_*.md`, numbered `<n>.<k>` | a short label |

Columns: `number,name,session,claimed_at_utc`. Rows with session `existing` are the files that were on `main` when
O12 merged (history, kept as it is, duplicates included); every later row is a claim.

**Claim before you write.** `python tools/claim_number.py <category> <slug> --session <id>` pushes your row to `main`
from a temporary worktree (your branch is untouched) and prints the number; a refused push is retried on the new
`main`. Without the tool: pull `main`, append one row with the next number and the UTC time
(`YYYY-MM-DDTHH:MM:SSZ`), commit only this file and push to `main`; if the push is refused, pull and take the next
free number. The number is yours only once the push is accepted. Claims are lane 3 (status rows).

`python tools/check_numbers.py` (CI, every push) fails when a numbered file or heading has no row, a number is used
twice outside the history, or a row is malformed. Never edit or delete someone else's row.
