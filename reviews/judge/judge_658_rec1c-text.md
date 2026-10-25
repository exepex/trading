# Judge 658: REC1c text amendment (the evening check), story/rec1c-evening-check at adaf0cb62 (judge J, round 1 of 2)

**FAIL** (text), lane 1: 3 should-fix, 2 minor. The amendment commit changes only `docs/stories/REC1-recommender.md`
(+51). Its diff from d82e459d also carries main's merge. Doc-reading tests on the head: 932 passed, 13 xfailed.

## The orchestrator's questions
| Question | Answer | My evidence |
|---|---|---|
| Can the check count a candidate outside the fixed set? | No, by the text, but S2 | Item 3 reads only the record's listed candidates. A school outcome must name the same `decision_sha256`, `driver_id` and `road`. `OutcomeRecord.decision_sha256` is "the sealed decision file the entry rests on" (`fno/school/contracts/records.py:65`), and that is the candidate's own seal hash. The open gap is more than one outcome per candidate (S2) |
| Can a ticket count as a trade? | No | Item 3: `is_ticket` is reported apart as a ticket, and criterion (b) tests it |
| Can "abstaining saved/cost" appear before every candidate closes? | No, by the text; m1 | "once complete" only; `incomplete` and `not known yet` give no total line. The file still holds a partial total (m1) |
| Is the CLAUDE.md line consistent with the evening routine? | Not yet | S1 |
| Is it acceptable that 20:05 never shows the same day's check? | Yes (reasoning only) | A school position closes at an exit or at expiry, mostly after the day, so a same-evening check would nearly always say `not known yet`. The 08:50 edition shows the latest checks (REC1d), and the text states the gap |
| The brake rule | Agreed | It matches judge 654.1's open point, with a test and a plant |

## Findings
**S1 (should fix) The step's place and its commit contradict each other.**
- Item 2 says "right after `lab close` (and `release-check`)", and also "the edition's receipts are committed before
  it, as today".
- Today the edition's receipts and the release logs are committed in the evening's step 3, after `release-check`.
- A check placed between `release-check` and step 3 runs while the edition's receipts are still uncommitted, and its
  own push (pull, then push) races them.
- Fix: put the step after step 3's commit and push, as a step "3b", and name its commit: only
  `receipts/data/recommend/`, by its own command. Also say that step 4's notes cover its alert and exit 1.

**S2 (should fix) The outcome match is not one-to-one.**
- `OutcomeRecord` carries `corrects` (the SHA-256 of a record it replaces), and the text never says how a correction
  is counted. Both records could be added, or the stale one used.
- Fix: per listed candidate, resolve corrections first, so the replaced record drops out. Exactly one live record means
  closed. None means open. Two or more live records, or a record that names the candidate's seal under another driver
  or road, means `data_check_failed` and an alert.
- Add a plant: a correction counted twice.

**S3 (should fix) The 60-session limit ends silently.**
- A candidate that never closes is re-checked for 60 sessions. The text does not say what the last check writes.
- A missing outcome cannot be told apart from an open position, so a day can drop out of the series with no verdict.
  That is a silent skip, and criterion 12 forbids it ("missing record ... `data_check_failed`").
- Fix: the 60th check writes a final file with `data_check_failed` ("never closed in 60 sessions") and alerts it.
- Also say whether `incomplete` is final once its listed candidates have closed. Otherwise it is re-checked, and
  rewritten as a new file, every evening for 60 sessions.

**m1 (minor)** Item 4's "the total over the closed trades" is also in a `not known yet` file. Name it "closed so far"
and keep it out of every line, so no reader takes it for the day's total.
**m2 (minor)** Say that "never fails the evening edition" includes the week's LR1 section, and REC1d's 08:50 read of
a check file that is missing or `data_check_failed`.

## Plants
None (a text round). For the code round: a correction counted twice (S2); the 60th check silent (S3); a ticket counted
as a trade; a candidate not listed but matched; the abstention line before complete.

## Notes
- I did not coordinate with any other judge.
