# Response 86: story S1, the evaluation protocol (builder's claims for the judge)

Story: `docs/stories/S-scoreboards.md` S1. Builder: Claude, 14 Oct 2026. Branch `story/s1-protocol` (nothing on `main`
until the judge passes it). Research and paper only: nothing here computes a result or places an order.

## 0. The verdict in two lines

The tools are built:
- the completeness check, which rejects "to be decided" and its kin;
- the decided check;
- the freeze, which writes a record and registers it in the B4 ledger;
- the freeze-order check;
- the per-version lookup.

The protocol is a **DRAFT, not frozen** (the orchestrator's instruction). All 18 items carry a concrete proposed
value, labelled "proposal, owner decides", with a reason and an evidence label. The freeze refuses it until the owner
decides every item.

## 1. Design

| Part | File | Job |
|---|---|---|
| The document | `research/evaluation/PROTOCOL.md` | version line; one block per item: Value, Status, Reason, Evidence |
| Parser and required items | `fno/evaluation/protocol.py` | the 18 items S1 lists (story, design 12.6, 12.8, 13.5, 13.6) |
| Completeness | `fno/evaluation/completeness.py` | **complete**: every item once, all four fields, a known status and evidence label, no open words anywhere ("to be decided", "to be determined", "TBD", "TBC", "undecided"). **decided**: every status "decided by the owner on YYYY-MM-DD" |
| Freeze | `fno/evaluation/freeze.py` | refuses unless committed unchanged, complete and decided; refuses a missing listed file or a version already frozen. Writes `FREEZE_v<n>.md` with the commit that last changed the protocol and the SHA-256 of every listed file and **config section** (canonical JSON, so layout and comments do not matter, values do); registers a prospective row in `research/ledger.csv` with `protocol_commit` |
| Order and versions | `fno/evaluation/order.py` | a book's first counted decision is its earliest committed D3 run on or after the common start. The freeze record's commit must be a **strict** ancestor of it. A decision is counted under the latest version frozen strictly before its commit |
| Wiring, CLI | `fno/evaluation/wiring.py` (new composition root, added to CLAUDE.md), `cli.py` | `python -m fno evaluation check [--decided]`, `freeze`, `order [--version] [--common-start]` |

`python -m fno evaluation check` on the real draft prints "complete". With `--decided` it exits 2 and lists all 18
items as not decided by the owner.

## 2. Claims per acceptance criterion

| # | Criterion | Tests (`tests/evaluation/`, 32) |
|---|---|---|
| 1 | Freeze commit precedes every book's first counted decision | `test_decisions_after_the_freeze_are_in_order`, `test_a_counted_decision_before_the_freeze_is_out_of_order`, `test_a_decision_committed_with_the_freeze_is_not_after_it`, `test_pilot_decisions_before_the_common_start_do_not_count`, `test_counted_decisions_without_a_committed_freeze_are_refused`, `test_an_uncommitted_run_is_not_a_counted_decision` |
| 2 | Every item has a value or an exact rule; "to be decided" rejected | `test_the_committed_draft_is_complete_and_every_item_awaits_the_owner`, `test_a_value_left_open_is_rejected` (4 spellings), `test_open_words_anywhere_in_the_document_are_rejected`, `test_a_missing_item_is_named`, `test_an_item_without_a_value_is_rejected`, labels, version line, duplicates, unknown items, a wrongly dated decision, the CLI |
| 3 | A change after the freeze is a new version; results reported per version | `test_a_frozen_version_is_never_frozen_again`, `test_a_change_to_any_hashed_target_shows_and_an_unrelated_setting_does_not`, `test_each_decision_is_counted_under_the_latest_version_frozen_before_it` (v1 then v2: before both, under v1, under v2) |
| Freeze record and ledger | | `test_the_freeze_records_the_protocol_commit_and_every_hash_and_registers_the_protocol`, `test_the_freeze_names_the_last_commit_that_changed_the_protocol`, `test_a_draft_is_never_frozen`, `test_an_incomplete_protocol_is_never_frozen`, `test_an_uncommitted_protocol_is_never_frozen`, `test_a_listed_file_that_does_not_exist_refuses_the_freeze`, `test_a_config_section_hash_ignores_layout_but_not_values` |

**Mutations: 28 of 28 caught** (python -B, caches cleared). The mutations covered:
- each completeness rule;
- the decided-date pattern;
- continuation lines;
- a required item removed;
- each freeze refusal;
- the protocol commit taken as the first instead of the last;
- the ledger commit not set;
- the config hash taken over the whole file;
- changed targets ignored;
- the strict ancestor reduced to "ancestor or equal";
- pilot counted;
- uncommitted runs counted;
- the earliest version winning.

The first run missed two: the protocol commit (every fixture changed the protocol once) and the strict ancestor
(no test committed the freeze and a decision together). One more had a bad pattern. I added the two tests, fixed the
pattern, and re-ran: all 28 are caught.

## 3. The draft's proposals, in short (all "proposal, owner decides")

| Item | Proposal | Evidence |
|---|---|---|
| Common start | a rule read from the records: the first session with an on-time decision from all three books under registered versions | reasoning only |
| Pilot | everything before the common start, every book, reported apart | reasoning only |
| Timetable | today's E3 times (cutoff 15:00, pack 14:58 to 15:10, deadline 15:12, snapshot 15:15, fills 15:20, lease 60 s), then calibrated: at least 10 measured sessions, each slot at least the 95th-percentile duration + 60 s | reasoning only |
| Segments | D6's rule as built | some evidence |
| Primary measure | net after every cost within C2's budget; net per unit of risk = mean daily net change ÷ mean daily risk at stake | reasoning only |
| Scoreboard A | one lot, E4 fills, C1 charges, the decision's own exit rule, no account limits | reasoning only |
| Uncertainty | one-sided 95% lower bound > 0 by a moving-block bootstrap of days (block 20 trading days, 10,000 resamples, seed 20261014), plus the minimum sample and positive whole net; Holm across a review's claims | reasoning only |
| Paper gate | keep 3 months and 20 positions | reasoning only |
| Strategy review | keep E6's rule and terms unchanged | some evidence |
| Catastrophic loss, strategy | E6's per-trade rule, plus a new cumulative rule: minus 3 × `catastrophic_loss_rs` | reasoning only |
| Catastrophic loss, book | C2's Rs 30,000 brake unchanged | reasoning only |
| Immediate pauses | brake, strategy rules, C3, C4, D3/D6 integrity, an owner's safety instruction; nothing statistical | reasoning only |
| Review dates | the last session of the 6th full month after the common start, then quarterly; strategy dates from each plan | reasoning only |
| AI cost | usage share of the month's plan cost by session minutes, development included in the denominator, residue to the largest share, unknown month shown as unknown | reasoning only |
| Role value | one ablation a day in a fixed rotation; control roles never ablated; paired net difference per applicable opportunity | reasoning only |
| Role value sample | at least 30 differing applicable opportunities at a review; drop proposed if the upper bound < 0 | reasoning only |
| Per version | the latest version frozen strictly before a decision; never pooled | reasoning only |
| Frozen files | the protocol, its check code, E6's review and statistics, E3's timetable code; config `desk.timetable`, `scorecard_review`, `risk`, `charges`. S2, S3, F8 and F9 code is added before the freeze if it exists, else hashed by a version 2 that changes no rule | reasoning only |

The E6 and E3 provisional terms are mapped one by one in the protocol's table. The proposal keeps every one, except
that the promotion bar for books and pairs becomes the block-bootstrap criterion.

## 4. Said plainly, for the owner's decisions

1. **Trade frequency makes early answers impossible.** One position per strategy per monthly expiry means about 20
   months to reach 20 positions for one strategy. Six months of common start will very likely be inconclusive. That is
   the honest outcome, not a failure of the method (reasoning only, from the playbook format's 30-45 day entry and
   21-day exit).
2. **AI cost: the owner's choice matters.** Including development sessions in the denominator makes the AI books'
   allocated cost small while development dominates usage. The stricter alternative charges the books the whole plan.
   I propose usage share and say why. It is a real choice.
3. **The timetable has no measured run times yet.** The proposal keeps today's times until at least 10 sessions are
   measured. The 2 minutes from deadline to snapshot look tight for an AI book (reasoning only).
4. **The freeze cannot hash code that does not exist.** S2, S3, F8 and F9 are not built, so either the freeze waits
   for them or a version 2 adds their hashes. The draft proposes the second, which changes no rule.
5. **No freeze, no counted decision.** Without a freeze before the common start, criterion 1 fails for every book
   (the order check says so). So the owner's decisions are on the critical path for Book 1's counted trading.
6. **Config status lines** (`scorecard_review.status`, `desk.timetable.status`) are unchanged. They change to "frozen
   in evaluation protocol v1" in the commit that freezes, which hashes those sections.

## 5. Gates

On the tree merged with `main`:
- full suite;
- `ruff check fno tests tools`, `ruff format --check`;
- `python tools/check_imports.py`.

Every new file is under 350 lines (the largest is `fno/evaluation/freeze.py`, 145).

## Addendum 1 (14 Oct 2026): judge 85, one must-fix, one should-fix, two owner questions

**Must-fix (accepted after checking).** Criterion 3 was not enforced. `changed_targets` was called only by a test.
The judge's probe passed unnoticed:
1. freeze v1;
2. change "one-sided 95%" to "80%" in the protocol and edit a frozen code file under the same version;
3. decide.

`version_of` said 1 and nothing failed. I confirmed it in the code.

**Fix:**
- `python -m fno evaluation verify` reports every target of the latest freeze that differs in the working tree.
- `test_the_repository_holds_no_edit_to_a_frozen_target` runs it on the repository. Once a version is frozen, any
  edit to its files or settings fails the suite, and so CI.
- `version_of` reads that version's targets **as the decision's own commit holds them** (`AtCommit`). If any
  differs, it raises `ChangedAfterFreeze`, and nothing is counted under that version.
- Tests: `test_judge_85s_edit_under_the_same_version_is_never_counted` (the judge's exact sequence fails: verify
  names both targets, and `version_of` raises). `test_the_same_edit_as_a_new_version_with_its_own_freeze_is_counted`
  shows the same edit as v2 with its own freeze passes, and the earlier decision stays under v1.

**Should-fix (accepted).** The freeze hashed the working tree.
- Every target must now be committed and unchanged since HEAD; for config sections, `config.yaml` itself.
- The freeze hashes the target as HEAD holds it.
- That made the older protocol-only "commit it first" check redundant, so I removed it rather than keep duplicate
  code.
- Tests: `test_a_listed_file_or_config_edited_since_head_refuses_the_freeze` (a code file, and config).
  `test_the_protocol_is_always_a_target_even_when_not_listed` covers the judge's surviving plant.
- `PlaybookGit.committed_bytes` reads exact bytes at a commit.

**Owner questions added to `PROTOCOL.md`** (section "Open questions for the owner"), with options and my
recommendation (reasoning only):
1. **A hashes-only v2 against per-version reporting.**
   - Option A: freeze only once the S2, S3, F8 and F9 code exists.
   - Option B: a hashes-only v2 that covers every v1 decision, frozen before any result is computed or seen.
   - I recommend A.
2. **About 6 blocks in 120 days under-covers.**
   - Option A: at least 12 blocks (240 trading days).
   - Option B: a t-based lower bound above zero as well.
   - I recommend both.

**Mutations: 32 of 32 caught** (python -B, caches cleared). That is the first round's 28, minus the redundant check's
mutation, plus five:
- `version_of` ignores changes;
- `verify` never reports;
- `verify` checks the oldest version;
- the freeze accepts edited targets;
- the protocol is not always a target.

Said plainly: "the freeze hashes the working tree instead of HEAD" is an **equivalent mutant**. The freeze refuses
unless the two are equal, so the result cannot differ. I hash at HEAD because that is what git holds.

## Addendum 2 (14 Oct 2026): judge 85 addendum 1 should-fix, a deleted or renamed frozen target (branch `story/s1-missing-target-test`)

S1 passed at `b1a6092`. This small follow-up is on its own branch, from that commit.

**Checked.** The code already treats a target it cannot read as changed:
- `changed_targets` catches the "does not exist" refusal;
- `AtCommit` returns nothing for a path a commit does not hold.

But no test held it. A mutation that ignores a missing target passed all 38 S1 tests.

**Tests** (`tests/evaluation/test_missing_target.py`):
- a frozen code file deleted, and one renamed (`git mv`), after the freeze;
- a frozen config section removed.

In each case `verify` names the target, and `version_of` raises `ChangedAfterFreeze` for a decision made after it.

**Mutation.** "A missing target is not a change" is now caught by exactly these 3 tests.
