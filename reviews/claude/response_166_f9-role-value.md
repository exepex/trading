# Response 166: story F9a, role-value scoring code (so S1 v1 can freeze); story text for the judge

Builder: Claude, 15 Oct 2026, branch `story/f9-role-value` (issue #61). Lane 1 (a new story; scoring). Orchestrator:
session_01VG1RqxLFUVdvvPuMRYZtDH. **Text only: no code until a judge PASSes this text.**

## What and why

- REPLAN slice B and S1's `frozen_files` (owner's option A, 14 Oct 2026): S1 v1 is frozen only once F9's code exists, so
  every scoring rule is hashed before the first counted decision. **Strong evidence** (the two texts say so).
- So F9 is split: **F9a** builds only the scoring code on records (rotation, record checks, score, interval, review
  gate, control counts, report). **F9b** (slice E) makes the shadow decisions and writes the records. F9a reports
  nothing real until books 2-3 trade. **Reasoning only** (the split is my proposal).
- Story text: `docs/stories/F-ai-layer.md`, section F9.

## Claims (to check against the text)

1. F9a values both actions of a pair by importing S3's `fno/scoreboard/standard_unit.py` (orchestrator, 15 Oct 2026;
   S3's text on `story/s3-scoreboard-a`, item 2), never a copy. **Revised:** my first text read pre-valued nets from
   the rows. That is worse: the standard unit values through the time exit and E7 settlement on later snapshots, so a
   net stored on the day would be incomplete, and the valuation path would sit outside the hashed scoring code.
   Open actions are cut and listed, as in S3. **Strong evidence** (S3's text); F9a's code round waits for S3's merge.
2. F9a reuses F8's `allocate` for cost (shares are already keyed `(purpose, book, role_or_bundle)`,
   `fno/budget/allocation.py:21`). **Strong evidence** (read the code).
3. **Withdrawn after judge 172 (S3 revision 2 is reused).** F9a cannot reuse an existing bootstrap: `fno/scoreboard/uncertainty.py` is a ratio of net to risk (and not mine to
   change), and `fno/forecast_scoring/block_bootstrap.py` is pinned to protocol v2's frozen constants (seed 20261013,
   linear percentiles). A third small bootstrap is the honest cost of three frozen protocols. **Strong evidence**
   (read the code); whether to unify them later is a judgement call (reasoning only).
4. Control roles are scored from C4's failure log only (`fno/checks/validity_failures.py`: one row per failed check,
   with `opportunity_id`). C3 keeps no per-book refusal log, so C3 is a Known limit. **Some evidence** (I read the
   C3 gate's code, not every caller).
5. No file over 350 lines: about six small modules (role set and rotation, paired-row source and checks, score,
   bootstrap, controls, report and CLI). **Reasoning only** until built.

## Questions for the owner (via the orchestrator), each with my recommendation

S1's text leaves these open; the code must fix one answer before the freeze.

1. **"One-sided 95% interval" with two ends.** `role_value_minimum_sample` drops on "upper end below zero" and keeps on
   "lower end above zero", but a one-sided interval has one end. Options: (A) 5th and 95th percentiles, each a one-sided
   95% bound (a 90% two-sided interval); (B) 2.5th and 97.5th. **Recommend A**: it matches the words "one-sided 95%"
   for each claim, and nothing is dropped automatically. Reasoning only.
2. **Holm across roles.** `uncertainty_criterion` applies Holm when several claims are made at one review. With 6
   units each tested at 5%, the chance of at least one false "drop proposed" is about 26% (1 - 0.95^6). Options:
   (A) no Holm, because every verdict is only a proposal the owner decides; (B) Holm across a book's units at each
   review, using bootstrap one-sided p-values. **Recommend B**: it is what S1 already says for claims, and a false
   "drop" costs a role that may help. Some evidence (the arithmetic), reasoning for the choice. It adds about 20 lines.
3. **Cost per opportunity.** Options: (A) the unit's allocated cost over the period divided by every day its card was
   consulted (it runs every day, ablated only 1 day in n); (B) divided by ablation days only (overstates the cost n
   times). The shadow session's own usage is evaluation cost, recorded under its own purpose and shown apart, not
   charged to the role. **Recommend A** plus the separate evaluation line. Reasoning only.
4. **Blocks.** "Blocks of 20 ablation days of that role": I read it as 20 of the unit's applicable opportunities in
   date order (with n units, about 20n trading days). **Recommend** that reading; say so in S1's text. Reasoning only.
5. **Shared input with S3: settled** by the orchestrator (15 Oct 2026): F9a imports `standard_unit.py`; any
   change to it goes through the orchestrator to S3's builder.
6. **S1's `frozen_files`.** F9a's files (`fno/role_value/*.py`, not `wiring.py`/`cli.py`) must join the list; that is
   S1's text, so I propose it to S1's owner rather than edit it.

## Known limits

In the story text: no rows until books 2-3 trade; 30 changed opportunities may take years; F9a trusts the rows'
hashes (F9b tests the real withholding); C3 not counted; the shadow's own usage shown apart.

## Answers (orchestrator, 15 Oct 2026)

- **Numbering:** first filed as response 162, which was taken twice; renamed to 166.
- **Split F9a / F9b:** agreed.
- **Question 2, Holm:** the owner said yes. Holm's correction runs across a book's units at each review (story text
  updated).
- **Questions 1, 3, 4:** coded as my recommendations, as **provisional constants, to confirm at the S1 freeze**. A test
  pins them against S1's text. The owner signs S1 at the freeze.
- **Question 5:** S3's builder owns `standard_unit.py`. The orchestrator's note says "F9a reads only the nets and
  builds no valuer". I read that as matching the text: F9a gets each net by calling the standard unit, and has no
  valuer of its own. I sent this reading back to the orchestrator to confirm.
- **Question 6:** S1's text owner is session_0185gR5DmoDh2zBAvgRU4CEB. I sent it the `frozen_files` line and the
  wording for questions 1 and 4.

## Answers to judge 172 (FAIL at 642c3f73), each checked before accepting

| Point | Verdict | Evidence and what changed |
|---|---|---|
| B1 a unit's cost has no source | **accepted** | Confirmed: F2 runs roles as sub-agents in one session (`F-ai-layer.md:98`), and F8 writes one row per (session, day) (`fno/budget/usage_ledger.py:25`). Strong evidence. Chose (b), a declared split: the book's daily allocation split equally across the consulted units, with F8's paisa rule. The decider gets no portion, so the cost is labelled an upper bound. A day with no usage row, or no plan cost, makes the cost "unknown", with no verdict and no Holm entry (criterion 5). Why not (a): nothing records per-sub-agent minutes today. F9b may measure them, as a new protocol version. Reasoning only. |
| B2 gap list | **accepted** | Table added. Abstentions are in (criterion 9: a no-trade is 0 and counts as a change). Joint tests are in through bundles only; pairwise ablation is out (twice the extra usage, a sample already years long). Lower risk is out of the verdict (S1's metric is net; question 9). Roles added one at a time is out (a slice E rollout order; each addition is a new D6 version). |
| SF1 Holm | **accepted** | Uses S3 revision 2's reader and step-down (`S-scoreboards.md` on `story/s3-scoreboard-a`, lines 158-165), imported. Claims entering: two per unit ("earns" on the series, "drop" on the negated series), all 2m in one list. The 5th/95th interval is printed only (criteria 7, 11). |
| SF2 constants vs S1's text | **accepted** | S1's text owner recorded them as pending edit 3 (register row "S1 text", main). The text now says they enter S1's text before the code round, provisional until the freeze. |
| SF3 third bootstrap | **accepted** | S3 revision 2's resampler takes any ordered series with a risk column (1 for a mean), and its owner says it stays generic. F9a imports it, so no third bootstrap. My earlier claim 3 is withdrawn. |
| SF4 review_dates source | **accepted** | Confirmed: no code computes S1's rule; `fno/scorecard/review.py` reads playbook dates. F9a adds `review_dates(common_start, calendar, through)` on `SessionCalendar` (`fno/research_data/calendar.py:36`), tested on a holiday month-end. Placement: question 8. |
| m1 snapshot = run log's | **accepted** | Both ids must equal `CommittedRuns.snapshot_ids()` (`fno/scoreboard/committed_runs.py:59`, S3's reader, imported). |
| m2 no-trade advances | **accepted** | Stated in the rotation item and criterion 1. |

Correction to question 3: the shadow decision runs inside the same book session, so its usage cannot be shown apart.
It is a Known limit now, and I am telling S1's text owner.

## New questions (via the orchestrator)

7. **Holm is stricter than S1's words.** With two one-sided claims per unit in Holm, one unit alone needs p < 0.025 on
   its side (about a two-sided 5% test), where S1 says "one-sided 95%". Options: (A) keep 2m claims (valid for any
   direction, stricter); (B) one claim per unit, its direction fixed before counting (for example "drop" only, since
   that is the action). **Recommend A**: the direction is not known in advance, and choosing it after seeing the sign
   doubles the error. Some evidence (standard multiple-testing reasoning).
8. **Where `review_dates` lives.** Recommend `fno/evaluation/review_dates.py` (S1's package, hashed with S1), so S3 and S4
   use one function. That needs S1's text owner's yes, because it is that package. Otherwise it goes in
   `fno/role_value/`, and S4 imports it from there.
9. **Lower risk for lower profit (design 3.1).** Out of F9a's verdict. Recommend: show nothing new now, and add a
   risk-adjusted role rule only as an S1 item the owner decides, if S3's risk measure proves useful. Reasoning only.
10. **`wiring.py` in `frozen_files`** (S1's text owner's pushback). **Accepted**: the composition root picks the
    scorer class, so a one-line edit after the freeze could swap the rule unhashed. Hash `wiring.py`; leave out only
    `cli.py`. Some evidence (that is what wiring does here).

## S1 text owner's answers (15 Oct 2026)

- `wiring.py` is hashed; only `cli.py` is left out. The cost line is the declared split. Holm over 2m claims is fine.
- **Question 8, settled:** `fno/evaluation/review_dates.py`, built by F9a and hashed with S1. It codes only the
  scheduled-review rule of S1's current item: the last session of the sixth full month after the common start, then
  every 3 months on the month's last session. REPLAN section 4's weekly post-mortem and stop-rule review are not
  coded here. RM1 also adds `fno/evaluation/gate.py`. There is no file overlap, and both are in the register.

## Owner and orchestrator answers to questions 7-10 (15 Oct 2026)

- **7:** keep two one-sided claims per unit in Holm. It is only stricter, and the direction is not known in advance.
- **8:** `fno/evaluation/review_dates.py` (above).
- **9 (owner):** "money only, risk shown". The verdict uses profit. Beside it the report prints the worst month of
  paired differences and the mean one-lot maximum-loss difference (scoreboard A's maximum loss, from S3's code); neither
  ever decides. A "drop proposed" is a proposal the owner can overrule. New criterion 12.
- **10:** `wiring.py` is hashed.

## Code round (on S3's branch, orchestrator's go of 15 Oct 2026; text PASS judge 172 add. 1 at 36f6b0fa)

Files: `fno/role_value/` (`role_set.py`, `role_set_file.py`, `rows.py`, `checks.py`, `records.py`, `valuation.py`,
`cost.py`, `score.py`, `verdict.py`, `controls.py`, `report.py`, `render.py`, `wiring.py`, `cli.py`),
`fno/evaluation/review_dates.py`, one parser line in `fno/cli.py`, the composition-root line in `CLAUDE.md`, and
`tests/role_value/` (39 tests). Every file is under 120 lines.

| Criterion | Where | Test | Evidence |
|---|---|---|---|
| 1 hashes, run-log snapshot, rotation | `checks.py` | `test_checks.py` (wrong unit, packs, snapshots, equal but wrong snapshot, a no-trade or unavailable day advances) | strong (tests) |
| 2 bundles | `role_set.py`, `checks.py` | a bundled role refused alone; no unit row for it | strong |
| 3 known answer | `score.py`, `report.py` | `test_score_and_verdict.py` (30 opportunities by hand), `test_report.py` (one pair: 1,460 - 1,000 = 460) | strong |
| 4 review gate, review_dates | `verdict.py`, `review_dates.py` | not a review, the day before, 29 and 30; a June month-end holiday | strong |
| 5 unknown cost, split sums | `cost.py` | `test_cost.py` (by hand), `test_report.py` (no plan cost) | strong |
| 6 control roles | `controls.py` | `test_report.py` (2 caught, 1 prevented, no profit figure) | strong |
| 7 Holm, S3's | `verdict.py` | 6 claims by hand; `verdict.holm is uncertainty.holm` | strong |
| 8 standard unit | `valuation.py` | identity of the imports; a spy shows one `value` call per take; open pair waits | strong |
| 9 no-trade = 0 and a change | `valuation.py` | trade vs no-trade both ways (+1,460 and -1,460) | strong |
| 10 excluded rows | `report.py` | `shadow_unavailable` and an unconsulted card counted apart | strong |
| 11 figures vs S1's text | `test_protocol_figures.py` | 30, 20, 10,000, 20261014 read from S1 today | strong, **partial**: see deviation 5 |
| 12 risk shown, never deciding | `score.py`, `render.py` | changing only the max-loss figures leaves p-values and verdicts equal | strong |

**Deviations from the text, each for the judge to check:**
1. **`consulted_units` (a `;` list) replaces the `consulted` column.** The passed text's own split ("equally across
   the units consulted that day") needs every consulted unit, not only whether the ablated one was consulted.
   `consulted` is now derived (the ablated unit is in the list). The text's column list was the error.
2. **A pair is "not scored" and listed when an opportunity is not observed** (no record, another common pack, a risk
   input not usable, a refused paper account), or when a maximum loss cannot be computed. These are S3's reasons.
   The text did not name them.
3. **Hashes are checked on scored rows only.** A `shadow_unavailable` or `unscored` row has no shadow pack or snapshot.
4. **The real decision must be the day's run collected on time** (S3's `CommittedRuns`, E3's late rule). Otherwise the
   pair is not scored, with "real decision not found".
5. **Criterion 11 is partial until S1's pending edit 3 lands.** S1's text has no wording yet for the percentiles or
   the cost denominator. The percentile test checks 5 and 95 as soon as S1 states "Nth and Mth". Until then it
   checks that the old "one-sided 95%" wording is still there. The cost denominator cannot be checked from the text
   until S1 states it. Reasoning only: there is nothing yet to read.
6. **"First full month"** is read as the month after the common start's month (S1's own example: 2 Dec 2026 gives a
   June 2027 review). Some evidence (the example).
7. **The role units file, `agents/role_units.yaml`**, maps book, then version, then unit id to its roles, with control
   role ids refused (`role_set.py: CONTROL_ROLES`). F2 writes it with each version. It does not exist yet, which is
   harmless while there are no rows.
8. **Fewer than 20 applicable opportunities** give no interval and no p-value (S3's resampler needs one block). That
   is always true below the 30-changed minimum.

Not done here (as the text says): firing shadows (F9b); any change to S3's files; S1's text (pending edits with its
owner). `fno/scoreboard/` is imported only, never edited.

## Judge 194's two minors (code PASS at f04076dd), both accepted

1. **Equal nets, different decisions.** Accepted: "changed" sets the 30 minimum, and unfilled entries happen in normal
   running. Added `test_an_unfilled_take_against_a_skip_is_a_change_worth_zero` (0 against 0, changed). The code
   already compared decisions, not nets (`valuation.py`, `choices`), so this is a test only.
2. **The rotation counted from the version's first row.** Accepted, fixed in code rather than in wording, because F9b
   may write pilot rows. `check_rotation` counts only rows on or after the common start. The report lists earlier
   rows as "pilot, before the common start" and never scores them (S1 `pilot_evidence`). Tests: a pilot row never
   moves the cycle; a pilot row is excluded.

The ChatGPT request is response 186 (first filed as 185, taken on main by E8).
