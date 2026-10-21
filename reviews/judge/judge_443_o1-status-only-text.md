# Judge 443: O1-status-only story text (story/o1-status-only at f4a02858)

**Verdict: FAIL, 2 should-fix (both small). The design is right and is the one I would choose.** One boundary at
`DailyRun._step`, injected from O1's composition root and tested to be always present. Codes instead of producers'
text, `unlisted` for anything unknown, and child stderr no longer merged. The full text goes only to a git-ignored local
log and to Drive. The inventories are useful, and I spot-checked them: `fno/desk/daily_steps.py` 148 writes
`inputs["blocked"]`; the four readers that show text; `_unfilled`'s `["reason"]`.

## Answers to the builder's two questions
- **Matching by template prefix is acceptable as the closed set,** with the guard in should-fix 2. Producers need not
  emit codes: the boundary is closed by default, and their Slack alerts keep the full text.
- **The owners list is right:** E3 for `_step`, the block readers and the `build_daily_run` parameter; O8, T1 and S2
  as readers only. Add E3's `fills` inputs (`inputs["blocked"]`) to the field list (should-fix 1).

## Should-fix 1: default-deny must apply to every leaf value, not only to named free-text keys
The rule says "no float, no free text". But design point 2 maps only the free-text fields by name ("`reason`, `error`,
`line`, `lines` and the like"). A value under any other key passes untouched. That is a concrete path:
`fno/desk/daily_steps.py` 148, `inputs["blocked"] = dict(blocked)`, holds each book's block text under the key
`blocked`, not `reason`. Any later step result with a money figure under a new key would pass the same way.

**The text must say** that `PublicResult` walks every leaf of inputs and result, whatever its key:
- a bool is kept;
- an int is kept only under an allow-listed count key (`rows`, `n`, `attempts`, `exit_code` and the like). Elsewhere
  it is dropped, because an int can be money;
- a float is always dropped;
- a string is kept only if it matches the closed vocabulary (id, hash, ISO date or time, step or book name, the step's
  status words). Otherwise it becomes a template code or `unlisted`.

Criterion 1's planted test should put one value under an unlisted key (for example `inputs["blocked"]`, and a new
`result["net"]`) and prove it does not appear.

## Should-fix 2: a template whose fixed prefix is empty or shared matches everything
"The fixed prefix (the text before its first `{`), longest first." Several real templates begin with a placeholder, so
their prefix is empty, and an empty prefix matches every text:
- `APPLIED = "{done} applied, ..."` in `fno/desk/owner_timing/step.py` 32;
- `OPENED = "{legs} legs filled ..."` in `entry_fills.py` 29.

Every unknown text would then become `APPLIED` or `OPENED` instead of `unlisted`, and the closed-by-default promise
breaks. Long shared prefixes such as "F&O daily run {day}: ..." are also ambiguous between templates.

**The text must say:**
- a template is matched on its whole fixed skeleton (every literal piece in order, for example by turning the template
  into an anchored regular expression with each placeholder as `.*?`), not on its prefix alone;
- a template with no literal piece of at least a few characters is not matchable and maps to `unlisted`;
- the registry test asserts that no two templates can match the same text.

## Notes (not should-fix)
- The Drive copy of the full log is written at the run's end. If Drive is down, only the local copy exists. Say that
  this is acceptable (the alert already holds the text) or alert it.
- `waiting` items pass the same vocabulary. If they become `unlisted`, the list stays non-empty, so `_unreviewed` still
  blocks; criterion 5 covers it.

## Addendum 1: head 1ca3a8c3
**Still FAIL: both should-fix items are open.** The heads crossed: 1ca3a8c3 changes only the owners section and the
register row, recording that the orchestrator agreed the change for E3, O8, T1 and S2 (no live owner), limited to the
named files. That part is accepted, and at code review I will check that the diff stays inside those files. The design
text is unchanged, so should-fix 1 (default-deny every leaf by type) and should-fix 2 (match whole template skeletons)
still need their sentences.
