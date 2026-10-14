# Response 70: story D1, the playbook format (builder's claims for the judge, and three questions)

Story: `docs/stories/D-playbook-decisions.md` D1. Builder: Claude, 14 Oct 2026 (slice 3, owner decision of 14 Oct:
start slice 3 now). Research and paper only: nothing here places, modifies or cancels orders, and nothing is approved.

## 0. The verdict in two lines

The playbook format, loader, registry and status changes are built and tested (criteria 1-6). **The playbook today is
empty of approved strategies** (experiment 1: no policy passed), which is a valid, tested state: `python -m fno playbook
check` prints `approved for paper: none (Book 1 trades nothing)`.

## 1. Design (what the judge will find where)

| Part | File | Job |
|---|---|---|
| Format | `fno/playbook/schema.py`, `fields.py`, `vocabulary.py` | every field required, exact keys, field-named refusals; known features (B1 F1-F3, each with its B7 live version) and structure codes (B2 SF/SC/BF) |
| Fingerprint | `schema.parameters_sha256` | SHA-256 of the parsed rule: every field except `status` and `evidence` (comments and spacing are not changes) |
| Lifecycle | `transitions.py` | the story's allowed changes and who may make each (table below) |
| Registry | `registry.py`, `playbook/registry.csv` | append-only rows `name, version, sha256, status, changed_on, approved_by, evidence_commit` (the story's columns); each version's rows must form an allowed history with one fingerprint |
| Approval checks | `approval_checks.py`, `live_reports.py` | one interface (`ApprovalCheck`), three rules: evidence filled; evidence committed before the approval and unchanged since; live features pass B7's gate |
| Loader | `loader.py` | reads every `playbook/*.yaml`, refuses duplicates, wrong file names, rule changes, status mismatches, missing files, failed checks |
| Status change | `lifecycle.py` | checks the change with the same checks, appends one row, sets the file's `status:` line |
| Wiring, CLI | `wiring.py` (new composition root, added to CLAUDE.md), `cli.py` | `python -m fno playbook check`, `python -m fno playbook set-status` |

Status names follow the story: `research` = candidate, `paper` = approved, `paused`, `retired`.

Allowed changes (`transitions.ALLOWED`, test `test_the_table_has_no_change_beyond_the_story`):

| From | To | Who |
|---|---|---|
| unregistered | research (register a candidate, freezing its rule) | owner or `desk` (addendum 1) |
| unregistered or research | paper | owner, plus the evidence and gate checks |
| paper | paused | owner or `hard_loss_rule` (E6's automatic pause) |
| paused | paper | owner only (checks run again) |
| any except retired | retired | owner |

**Neutral to how a rule is approved.** The format records an approval reference, not a method: `evidence` holds the
test results' path and commit, the red-team note, the judge's verdict, the frozen protocol's freeze record and the
owner's approval date. A historical experiment and a forward test fill the same fields. No approval rule was invented
beyond the story; the only addition is `freeze_record` (asked for by the orchestrator as provenance) — see question 2.

**Why `status` and `evidence` sit outside the fingerprint.** Both change through the lifecycle; everything else is the
tested rule. To stop evidence being swapped after approval, `EvidenceCommitted` requires the file's evidence to equal
the evidence in the file as committed at the approval row's `evidence_commit` (default: HEAD when the change is made),
every evidence file to exist in that commit, and the test results' commit to be in its history.

**B7 follow-up closed (judge 44: "hand-edited per-day values pass today").** The production gate
(`RecomputedLiveReports`, wired in `fno/playbook/wiring.py`) uses a committed report only if every per-day row equals
a fresh recomputation by B7's own `run_live_validation` (later days may exist; the committed days must match exactly).
B7's frozen files (`live_gate.py`, `live_validation.py`, `ledger.py`, all in experiment 1's FREEZE.md) are imported,
not changed.

## 2. Claims per acceptance criterion

| # | Criterion | Code | Tests (`tests/playbook/`) |
|---|---|---|---|
| 1 | Missing field, unknown feature or structure code refused, field named | `fields.Fields` (exact keys), `schema._condition`, `_structure` | `test_schema.py`: every one of the 42 fields deleted in turn (`test_every_missing_field_is_refused_by_name`), unknown field, feature, live-feature name, structure code, operator/threshold kinds, looser use rule, bad values; `test_loader.py::test_a_bad_file_is_refused_with_its_name_and_field` |
| 2 | Same name and version refused; changed parameter in a registered version refused; append-only registry checked against git history | `loader._read_files`, `loader.check_against_history`, `registry._check_histories`, `registry.rewritten_history`, `history.PlaybookGit.file_versions` | `test_two_files_with_the_same_name_and_version_are_refused`, `test_a_changed_parameter_in_a_registered_version_is_refused`, `test_a_comment_or_spacing_edit_is_not_a_parameter_change`, `test_registry.py::test_the_history_check_reads_git` (temp repo, edited row caught), `test_the_repository_registry_was_only_ever_appended_to` (real history) |
| 3 | Only the allowed changes; each a new row | `transitions.check_transition`, `Registry.append`, `StatusChanger.change` | table-driven over 5 x 4 statuses x 3 approvers; `test_lifecycle.py::test_research_to_paper_to_paused_to_paper_to_retired`, `test_the_owner_alone_may_resume_a_paused_strategy` (nothing written on refusal) |
| 4 | No `paper` without all evidence and the owner approval date | `approval_checks.EvidenceFilled`, `EvidenceCommitted` | `test_paper_needs_every_evidence_field`, `test_evidence_changed_after_approval_is_refused`, `test_uncommitted_evidence_cannot_be_approved`, lifecycle refusal writes nothing |
| 5 | Worked example loads, clearly `research`, claims no pass | `playbook/example-sc-iv-rich-no-event-v1.yaml` (experiment 1's failed P6) | `test_the_repository_playbook_loads_and_approves_nothing` |
| 6 | No `paper` unless every live feature passed B7 (loader gate) | `approval_checks.LiveFeaturesValidated`, `live_reports.RecomputedLiveReports` | `test_a_live_feature_without_a_passing_report_blocks_paper`, `test_the_gate_uses_the_strategys_own_stricter_rule`, `test_live_reports.py::test_a_hand_edited_value_fails` |

Empty playbook: `test_an_empty_playbook_is_valid_and_approves_nothing`.

**Judge verifies ("edits a parameter in a committed version and confirms the loader refuses it").** No version is
registered in the repository (nothing is approved and the example is not registered: registering needs the owner),
so do it in a scratch copy:

```
cp -r . /tmp/d1 && cd /tmp/d1
python -m fno playbook set-status example-sc-iv-rich-no-event 1 research --by owner --on 2026-10-14
python -m fno playbook check                      # loads: research
sed -i 's/    threshold: 0$/    threshold: 0.5/' playbook/example-sc-iv-rich-no-event-v1.yaml
python -m fno playbook check                      # refused: ...: rule: differs from the registered version
```

## 3. Mutation checks (each mutation made in a scratch copy, `tests/playbook` run, then reverted)

All 9 killed:

| Mutation | First failing test |
|---|---|
| loader: fingerprint comparison off | `test_a_changed_parameter_in_a_registered_version_is_refused` |
| `paused -> paper` also allowed for `hard_loss_rule` | `test_the_owner_alone_may_resume_a_paused_strategy` |
| evidence-filled check removed | `test_paper_is_refused_without_evidence_or_validated_features_and_nothing_is_written[False-...]` |
| evidence-equality comparison removed | `test_evidence_changed_after_approval_is_refused` |
| recomputation comparison removed | `test_a_hand_edited_value_fails` |
| unknown-key refusal off | `test_an_unknown_field_is_refused_by_name` |
| duplicate name+version check off | `test_two_files_with_the_same_name_and_version_are_refused` |
| registry: one fingerprint per version off | `test_a_bad_history_is_refused_with_its_place[rows2-...]` |
| loader: status-vs-registry check off | `test_the_file_status_must_match_the_registry` |

**Checks run on the merged tree (after `git pull --no-rebase`):** `python -m pytest -q` 2056 passed (158 of them in
`tests/playbook/`), `ruff check fno tests tools` clean, `ruff format --check` clean, `python tools/check_imports.py`
clean. Note: the first full run on the container's shallow clone failed `test_freeze_v2` (freeze commit not in a
shallow history, unrelated to D1); after `git fetch --unshallow` it passes.

## 4. What is not done, and doubts (said plainly)

- **The example's funding (Rs 20,000 margin per lot) and expected range are illustrative, not measured**, and say so
  in the file. `research/data/margins/margins.csv` has no SC row yet; a real candidate needs a measured margin.
- **`strikes_rule` and `width_rule` are required text, not machine-readable.** D2 builds structures on live quotes and
  will need them in a fixed form; D1 cannot pick that form without D2's design. Some evidence: the B2 structures
  already fix the strike rule by code (SF, SC, BF), so D2 may only need the width list.
- **Exits, size rule and pause rules are text too.** E6 must turn pause rules into code; D1 only records them.
- `EvidenceCommitted` and the git-history test need full git history; CI already fetches it (`fetch-depth: 0`).
- The live-feature gate recomputes from the recorded A4 days, so `playbook check` needs the same data B7's validation
  needs whenever a `paper` version exists. With none today, nothing is recomputed.

## 5. Questions for the owner (they change what is built next, not D1's criteria)

1. **Forward testing as the approval (ChatGPT review 30: the 2019-23 holdout is used).** Criterion 4 forbids `paper`
   without full evidence, so a rule whose test *is* forward paper trading cannot be Book 1's paper trade while it is
   being tested. Should a forward test run (a) outside Book 1, as recorded but untraded decisions for a `research`
   version frozen in the registry (works with D1 as built), or (b) as a new status such as `forward_test` that Book 1
   trades with its own limits (needs a story change)? Recommendation: (a), reasoning only: it keeps "Book 1 trades
   only what was tested" true and needs no new state.
2. **`freeze_record` as a required evidence field** (not in the story's list; added as the provenance the orchestrator
   asked for). Keep it required for `paper`?
3. **Who may register a candidate (`research` row)?** Built: owner only, like every other change. Registering only
   freezes a rule before its test; it approves nothing. Should the desk (a builder or the research loop) be allowed to
   register candidates without the owner?

## Addendum 1 (14 Oct 2026): the orchestrator's answers to questions 2 and 3

- **Q2:** `freeze_record` stays a required evidence field for `paper`. No change.
- **Q3:** registering a `research` candidate is open to the desk; only the owner moves a version to `paper`.
  Built: new approver `desk` (`fno/constants.py` `APPROVER_DESK`, CLI `--by desk`), allowed only for
  unregistered -> research (`transitions.ALLOWED`). Tests for both paths: `test_lifecycle.py::
  test_the_desk_may_register_a_candidate_but_only_the_owner_approves_it` (desk registers; desk to paper refused,
  nothing written; owner then approves) and `test_the_desk_cannot_approve_an_unregistered_candidate_either`; the
  table test now covers 4 approvers (`owner`, `desk`, `hard_loss_rule`, an unknown one).
- **Q1** (forward test as the approval) is with the owner.

## Addendum 2 (14 Oct 2026): judge 67's must-fix, accepted and fixed

**Accepted, with evidence.** Judge 67 is right: `RecomputedLiveReports` checked only the rows a committed report
contained, and B7's gate then counted those rows, so removing disagreeing days (or the latest stretch) raised the
agreement. Reproduced before the fix: `test_removing_bad_days_from_the_committed_report_does_not_pass_the_gate` fails
on the old code (mutation back to `return report`: 3 tests fail).

**Fix (the judge's first option):** the gate now decides on the fresh recomputation over every recorded day
(`fno/playbook/live_reports.py`). The committed report must still exist and match the recomputation on each day it
holds, because it is the red team's record. Tests: 25 recorded days with 5 disagreeing (80%), the committed report
without those 5 rows (100%, passes the old gate), for both cherry-picked middle days and a truncated end. The gate
fails in both cases and reads the full 25 days.

**Consequence, said plainly:** an approved strategy whose live feature stops agreeing on later days fails the gate at
the next load. A failed check refuses the whole playbook, so Book 1 trades nothing until the owner pauses or retires
that version. That is fail-safe: the strategy would no longer trade what was tested. But it stops every strategy, not
only the one affected. E6's pause rules are the place to turn this into an automatic pause of that version alone
(reasoning only).

**Minor point taken too:** `python -m fno playbook check` now runs the append-only check itself, on git history plus
the working file (`wiring.registry_history_problems`), so an edited row is caught before CI.
`test_the_history_check_includes_the_working_file` covers an uncommitted edit.
