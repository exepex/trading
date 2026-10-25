# Judge 653: REC1b code, the daily recommendation record, `story/rec1b-daily-record` at 2e039a045 (round 1 of 2, judge K, judge 2 of 2)

**PASS, lane 1.** 2 minor. I did not read judge J's verdict.

**Gates.** A trial merge of 2e039a045bff6377767c4862117207c2296adf64 into origin/main ac43022a0 is clean (361e31e45). On it,
with the Slack token set:
- `pytest -n auto`: 16,927 passed, 1 skipped, 13 xfailed, exit 0.
- ruff check and format are clean. `check_imports` (2,801 files), `check_records` (9,350 files) and `check_numbers` are clean.
- **No test posted to Slack:** all three channels are empty for 01:07:54-01:17:31 UTC.

## Checks (the orchestrator's five, against my amendment 641 and 641.2)

| Asked | Verdict | Own evidence |
|---|---|---|
| `complete` only from the source's own record | MET | `SchoolSource.read`: unavailable unless the step is `ok` and its reason is not `school:OFF` or `school:NOT_A_SESSION`. Even then it is complete only when the session's 15:00 decisions seal is found and read with its SHA-256 checked (`dashcam.read`). A missing or damaged seal is `InputFailed`, so the day is `data_check_failed`. `DeskSource.read`: complete only when the run log names Book 1's `run_id` and every file matches `records.sha256`, both ways. The school CLI (`fno/school/cli.py:55-62`) prints "school off" or "not a trading day" with exit 0, which are exactly the two `ok` reasons excluded |
| An unavailable source is never empty-complete | MET | `gather._unread` makes a failed reading `unavailable (input_failed)`; the post prints "<name>: unavailable (<status>)", never a count. My plants caught: OFF dropped from `NOT_RUN`; the status ignored; a missing seal read as complete; an unread source as complete; unavailable printed as 0 |
| The #fno-desk line leaks nothing | MET | `post.py` puts out answers, reason codes, per-source counts, version IDs, the receipt path and a 12-character hash prefix. Problem lines name record paths, whose file names are `<strategy>-v<n>:<expiry>` (`opportunities.py:25`): no strike or price, and the same paths are already public in `journal/`. `test_run.py` scans the line for a strike or price |
| The card is byte-identical | MET by construction (m1) | `git diff origin/main...2e039a045 -- fno/cards` is empty; the card step runs before `recommend` and reads nothing it writes |
| recommend's timing does not depend on market hours | MET | `"recommend": Alerted(LiveFrom(CommandStep(...)))`: no `NotBefore` or `StartsBy`. The CLI has no clock check beyond `--on`'s default day. A school refused for `TOO_LATE` still leaves `recommend` to run, with the school `unavailable` |

**Also checked:**
- **Write-once and receipt first:** `RecommendRun.run` saves, and posts only after `store.save` returns. `NotSaved` gives one problem line and no post. A receipted day is never posted again.
- **Rung rule:** a changed `RUNG_RULE.md` hash makes no record (`test_a_changed_rung_rule_makes_no_record`).
- **Live key:** `daily.live_from.recommend: null`, so it is not live.

## Minor

- **m1:** criterion 10 promises a golden file showing "the card's output byte-identical with the step on and off", but no such test exists. Today the property holds by construction: the card reads nothing of REC1b. Either add the golden test or change the criterion to the construction argument; the latter is enough.
- **m2:** a survivor. Dropping `"run_id" not in entry` in `DeskSource.read` is caught by no test. A Book 1 entry with no `run_id` (a failed book) would then raise `KeyError`, an alerted crash, never complete. The code is right; add the case.

## Plants

**Mine: 10:**
- **Caught (8):** OFF not excluded; the status ignored; a missing seal as complete; Book 1's hash unchecked; an unread source as complete; unavailable printed as a count; the step removed from `DAILY_RUN_STEPS`; the line never sent.
- **Survived (2):**
  - m2 above;
  - `traded` without `mode == BOOK`. This one is equivalent: a shadow's outcome is `SHADOW_TRADE` ("shadow: would trade", `fno/constants.py:277`), never `CHOSEN`, so the mode check is a belt only.

## Notes

- The builder's stated limit stands: during a GitHub outage the receipts are unknown. A rung-3 version could then read lower, and an unavailable school would not force `data_check_failed`. This cannot happen before rung 3, and it is correctly left to the rung-3 story.
- The timing line still waits on GW1's measured chain (641.2 m3). GW1 parts 5-6 are blocked on `fills_by` (637.1 B1). Once that moves, the school's measured start belongs in the text.
