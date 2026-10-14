# Response 81: story D3, the decision record (builder's claims for the judge)

Story: `docs/stories/D-playbook-decisions.md` D3. Builder: Claude, 14 Oct 2026. Branch `story/d3-decision-record`
(nothing on `main` until the judge passes it). Research and paper only. No 2019-2023 golden or back-fill row is opened.

## 0. The verdict in two lines

Every evaluated opportunity and the day's "no trade" get a record. A run is written atomically, once, and refused
when the same inputs come again. A replay through D2's real evaluator reproduces every record exactly. A run
committed at or after the execution snapshot is late and never filled. One record schema with every three-book
field, validated by version.

## 1. Design (files under `fno/playbook/`)

| Part | File | Job |
|---|---|---|
| Replay inputs | `decision_inputs.py`, `decision_codec.py` | `Recording*` adapters capture, while D2 reads them: the live feature values per context, the trade counts and each shadow account. With the playbook snapshot, the market (C2 quotes and futures) and the book they form `DayInputs`, stored as `inputs.json`. `Replayed*` adapters feed them back |
| Record | `decision_record.py` | one record per opportunity plus `no_trade.json` for the day. Body: header hashes, features, rule result, structure, expected, risk (C2 verdicts with numbers), validity, decision, alternatives, `corrects`. Three-book fields, `served`, `validate_record`, `decision_facts` (for D6) |
| Store | `decision_store.py` | `journal/<book>/decisions/<date>/<run_id>/` (`run_id` = date + `-r<n>`): `inputs.json`, the records, `records.sha256` |
| Run and replay | `decision_run.py` | `DecisionRun.decide` evaluates with D2 through the recording adapters and writes; `replay` re-runs D2 on the stored inputs and lists every differing field |
| Timing | `decision_timing.py`, `PlaybookGit.added_at` | on time or late from the commit that added `records.sha256`; `require_on_time` for E4/E5 |
| Wiring | `wiring.py`: `build_decision_run`, `snapshot_playbook` | the app's evaluator (all six C2 rules) and the playbook as it stands, with HEAD |

What the store guarantees:
- **Atomic:** the run is written into a hidden temporary folder and then renamed into place.
- **Write-once:** an existing run is never rewritten.
- **Idempotent:** a run whose `inputs.json` equals an earlier run's of the day is refused.
- **Edits are found:** `edited()` checks every file against `records.sha256`.
- **Corrections:** a correction is a new run whose record carries `corrects: {run_id, opportunity_id}`.

**Today's rulings applied:**
- **`served` carries every component.** Book 1 serves `playbook` (a digest of the rule fingerprints it may trade
  that day) and `config` (the config hash). It is computed by the run, never passed in. D6 scores a record only when
  every registered component is present and equal.
- **The record is the truth for the day (judge 74).** `inputs.json` holds every playbook file's text, the registry
  text and the commit read (`header.registry_commit`). A stop written after 15:00 cannot change what the record says
  was used.
- **One format for all three books.** Fields a book does not have are present and null: Book 1 has no authority
  check, Book 3 strategy, model or session; Book 2 has no Book 3 strategy; Book 3 has no rule default or authority
  check. Links not built yet (`version_id` without a registered version, `judge` C4/F4, `owner_override`,
  `forecasts`) may be null for every book.

## 2. Claims per acceptance criterion (`tests/decisions/`, 27 tests)

| # | Criterion | Tests |
|---|---|---|
| 1 | Every evaluated opportunity has a record, no-trade outcomes included | `test_every_opportunity_and_the_day_have_a_record`, `test_nothing_approved_still_records_the_days_no_trade` |
| 2 | Replay through D2 reproduces the decision, the rejected alternatives and every risk and validity reason | `test_a_replay_through_d2_reproduces_every_record` with 5 cases: chosen and "not chosen: slot"; rule did not fire; bad prices on every width; unproven; shadow. Each asserts the case produced its reason, then that the replay gives no difference. `test_a_replay_finds_an_edited_reason_and_edited_inputs` |
| 3 | A crash leaves the complete record or none (killing the writer) | `test_a_writer_killed_mid_way_leaves_no_run_and_the_next_run_is_whole`: a subprocess dies (`os._exit`) on the third file write; no run exists, only the hidden temporary folder; the next run is whole and replays |
| 4 | Never edited; a correction is a new linked record | `test_a_run_is_never_rewritten_and_an_edit_is_found`, `test_a_correction_is_a_new_run_linked_to_the_record_it_corrects`; plus `test_the_same_inputs_twice_are_refused_new_inputs_make_a_new_run` |
| 5 | A record committed after the day's execution snapshot is late and never filled | `test_a_run_is_on_time_only_if_committed_before_the_execution_snapshot` (15:12 on time; 15:15 and 15:20 late; `require_on_time` raises), `test_an_uncommitted_run_is_late` |
| 6 | Versioned schema; every three-book field present and validated | `test_every_record_matches_its_schema_and_feeds_d6`, `test_a_record_off_its_schema_is_refused` (6 cases), `test_book_3_may_leave_the_rule_default_empty` |

D6 link: `test_a_record_with_every_component_is_scored_and_one_missing_is_not`,
`test_the_record_keeps_the_registry_state_and_commit_it_read`. Wiring: `test_the_app_snapshot_reads_the_repository_playbook`.

## 3. Mutation checks: 12 of 12 caught (`python -B`, caches cleared before each)

| Mutation | Caught by |
|---|---|
| no temporary folder | the crash test |
| duplicate check off | the idempotency test |
| rewrite allowed | the never-rewritten test |
| edits not found | the never-rewritten test |
| late at `>` | the 15:15 case |
| uncommitted counted on time | the uncommitted test |
| null check off | 3 schema cases |
| `served` check off | the schema test |
| replay compares nothing | the edited-reason test |
| config not served | the D6 link test |
| features not recorded | 7 replay tests |
| alternatives dropped | criterion 1's test |

## 4. Limits and doubts, said plainly

- **Expected P&L summary.** The playbook holds the expected net, its range and its source, but no 10th/90th
  percentile. `p10_rs` and `p90_rs` are null until the playbook format carries them. `worst_rs` is the trade's
  modelled maximum loss. A story change (D1 format) is needed to fill the percentiles honestly.
- **Validity (C4) is not built.** `validity.c4` is null; `validity.candidate` says "built" or why not (for example bad
  prices).
- **Availability times.** Each value's source and availability time are in the common pack (E2), named by
  `common_pack_sha256`. The record does not repeat them. The market here is C2's form (mid, IV); converting the common
  pack's quotes into it is E5's job.
- **Shadow outcomes** are recorded in Book 1's run with `mode: "shadow"`, as the forward test's record. They never
  count as Book 1's decisions. A separate shadow journal could hold them if the owner prefers.
- **Replay uses the current code and `config.yaml`.** The record names `code_commit` and `config_sha256`; a replay at
  a different commit or config may differ, and the record says which commit and config it was made with.
- **Committing and the order against the execution snapshot are E3's**; D3 provides `require_on_time` and its test.

## Addendum 1 (14 Oct 2026): judge 80's two must-fixes, accepted and fixed

1. **Every part of criterion 2 is held by a test.** The judge's plants ("replay skips risk", "replay skips
   alternatives", "alternatives drop shadow outcomes") passed all 27 tests: the replays were right, but nothing
   pinned each part. New tests in `tests/decisions/test_replay_guard.py`:
   - `test_an_edit_to_any_part_of_a_record_is_found_by_the_replay`: on a contested day (a slot refusal with C2
     verdicts, plus a shadow candidate), editing `risk`, `validity`, `alternatives` or `decision` in the losing record
     makes the replay report exactly that field.
   - `test_alternatives_are_all_the_other_outcomes_shadow_included`: every record's alternatives are all the other
     outcomes, book and shadow; the day record lists all of them.
2. **A replay under different code is refused.**
   - `replay(run, evaluator, code)` first checks that the running `fno/` and `config.yaml` equal the record's
     `code_commit`, uncommitted and untracked files included (`GitCodeTree`, `PlaybookGit.tree_matches`; wired as
     `build_code_tree`).
   - If they differ, it raises `ReplayRefused`, naming the commit and the worktree command
     (`git worktree add <dir> <commit>`).
   - `todays_code=True` runs anyway, and its output starts with "NOTE: compared with today's code, not the recorded
     commit ...: not a reproduction".
   - Tests: `test_the_code_tree_matches_only_the_same_committed_code` (same commit; an uncommitted edit; an untracked
     file; a file outside `fno/`) and `test_a_replay_under_other_code_is_refused_and_a_todays_code_comparison_says_so`.
3. **Mutations** (`python -B`, caches cleared): the judge's three plants, plus "replay skips validity", "code check
   off", "today's-code note dropped" and "untracked files ignored": 7 of 7 caught. The earlier 12 still caught. So 19
   of 19.

Follow-ups recorded by the orchestrator, not on this branch:
- (a) every approval, pause or retirement changes Book 1's served digest, so E3/D6 must register a new D6 version
  with each, or Book 1 goes unscored;
- (b) D1 must add frozen p10/p90 from the test results before the first approval.
