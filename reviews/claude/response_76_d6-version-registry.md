# Response 76: story D6, the version registry and evaluation segments (builder's claims for the judge)

Story: `docs/stories/D-playbook-decisions.md` D6. Builder: Claude, 14 Oct 2026. Branch `story/d6-version-registry`
(nothing on `main` until the judge passes it). Research and paper only.

## 0. The verdict in two lines

Every book's versions are registered, append-only, in `journal/versions.csv`. A decision is scored in a version's
segment only if that version's row was committed before the decision (git ancestry). A served model or component
that differs from the active version makes the decision `unscored` and pauses that book's scoring until a new version
is registered.

## 1. Design

| Part | File | Job |
|---|---|---|
| Registry | `fno/books/version_registry.py`, `journal/versions.csv` (header only) | the story's columns; `components` is a JSON object of text values; checks: known book, full 40-character `registered_in_commit`, a version ID once per book, `starts_on` strictly after the book's previous version; append keeps the old bytes |
| Segments | `fno/books/versions.py` | `Versions.active_version(book, day, decision_commit)`, `Segments.segment_of(decision_id)`, `Segments.scoring_paused(book, day)` |
| Decision input | `DecisionFacts` in `versions.py` | book, day, record ID, the commit holding the record, and the components actually served. D3 is not built; this is what its record must give D6 |
| Wiring, CLI | `fno/composition.py` (`build_version_registry`, `build_versions`), `fno/books/versions_cli.py` | `python -m fno versions register <book> <id> --starts-on --components '{...}' --reason` (records HEAD as `registered_in_commit`; commit the file at once), `python -m fno versions check` |

**Why the registry row's own commit is read from git, not from the file.** `registered_in_commit` is written before
the row is committed, so it can only name the commit where the components were frozen (HEAD at registration). The
commit that actually added the row is found with git's search, as B4's ledger does. A version is the decision's
version only when both of these hold:
- the row's commit is an ancestor of the decision's commit;
- `registered_in_commit` is an ancestor of the decision's commit.

So a version cannot be declared after seeing its decisions: a later `starts_on` or back-dated text does not help.

**Pause rule.** If a decision's served components differ from the active version's (any key the decision reports),
that decision is `unscored` and the book is paused on that version. Later decisions of that book stay `unscored` while
the active version is still the paused one. The first decision on a newly registered version is scored again. Only
that book pauses; the others are unaffected. Labels are computed in (book, day, record ID) order, whatever order the
decisions come in.

## 2. Claims per acceptance criterion (`tests/versions/`, on temporary git repositories)

| # | Criterion | Tests |
|---|---|---|
| 1 | A version registered in a commit after a decision is not its version | `test_a_version_registered_after_a_decision_is_not_its_version` (`starts_on` before the decision's day, row committed after it: unscored; a decision committed after the row: scored); `test_components_frozen_outside_the_decisions_history_do_not_count`; `test_a_version_starts_on_its_day_not_before` |
| 2 | Served model differs: `unscored`; later decisions stay `unscored` until a new version | `test_a_served_model_mismatch_is_unscored_and_pauses_scoring_until_a_new_version` (fallback on day 2, unscored; day 3 back on the registered model, still unscored, "paused since"; v2 registered, day 4 scored as v2; `scoring_paused` = False, True, True, False); `test_a_pause_in_one_book_leaves_the_others_scored` |
| 3 | Segments deterministic from the registry | `test_segments_do_not_depend_on_the_order_decisions_are_given`; `test_active_version_is_the_latest_started`. S2 and S3 group by `Segment.label` (`<book>/<version>` or `unscored`) |
| 4 | Registry rows never edited | `test_the_repository_registry_was_only_ever_appended_to` (the file's git history plus the working file); `test_an_edited_past_row_shows_in_git_history`; `test_append_keeps_the_old_bytes_and_refuses_a_bad_row`; `test_bad_rows_are_refused` |

**Judge verifies ("inserts a fallback decision and confirms it is unscored and scoring pauses")** is exactly the
criterion 2 test. It can be repeated on any temporary repository with `tests/versions/builders.py`'s `Repo`.

## 3. Mutation checks: 10 of 10 caught (bytecode caching off)

| Mutation | Caught by |
|---|---|
| row-commit ancestry off | `test_a_version_registered_after_a_decision_is_not_its_version` |
| `registered_in_commit` ancestry off | `test_components_frozen_outside_the_decisions_history_do_not_count` |
| `starts_on` ignored | `test_a_version_starts_on_its_day_not_before` |
| pause not kept | the criterion 2 test |
| mismatch not detected | the criterion 2 test |
| decisions not sorted | the criterion 2 test |
| pause applied before its day | the criterion 2 test |
| `starts_on` order not checked | `test_bad_rows_are_refused` |
| duplicate version not checked | `test_bad_rows_are_refused` |
| unknown book not checked | `test_bad_rows_are_refused` |

## 4. Limits, said plainly

- **D3 does not exist yet.** `DecisionFacts` names what its record must provide: the record's commit and the
  components actually served. For the AI books that is the model the session actually served. For Book 1 it is the
  playbook hashes. Until D3, nothing produces real decisions to label.
- **Which components a decision must report is up to each book's record.** A key the decision does not report is not
  compared. D3 or F1 should fix the required keys per book (Book 1: playbook hashes; Books 2 and 3: model, prompt
  versions, role set, envelope or constitution hash).
- **The append-only check and ancestry need full git history**; CI fetches it (`fetch-depth: 0`).
- `rewritten_history` and `PlaybookGit` are reused from the playbook package (DRY), so `fno/books` now imports
  `fno/playbook` in the tests only. The production code uses B4's `Git` directly.
