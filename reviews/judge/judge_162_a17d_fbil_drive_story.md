# Judge 162: story A17d text, FBIL's USD/INR table moves to Drive (quality rule 1; judge C)

Date: 15 Oct 2026 (UTC). Branch `story/a17d-fbil-drive` at **1c6700f4140afed0333bae355726aebf1cd0bc4d**
(`docs/stories/A-data-foundation.md` A17d, a `docs/WORK_REGISTER.md` row). Builder session_01MBnbVU4sundxNjs5u4xCsP.
Judged under the owner's "keep the design simple" rule and the coordination rule.

## Verdict: PASS (text); 1 note

| Check | Status | Evidence |
|---|---|---|
| Owner decision | MET | `docs/DESK_DECISIONS.md:191`, 15 Oct: "FBIL's USD/INR reference-rate table moves to Drive" (the owner left "17: FBIL USD/INR stays public" unticked) |
| Simplest design | MET | The existing flag `GlobalCueSource.private` (`fno/global_cues/source.py:45`), already `True` for the US index sources (`us_index_sources.py:38`). No new class, option or path |
| The facts | MET | My own reads on `main`. `usdinr_fbil.csv`: 1,982 lines, so 1,981 rows. `checks/gaps.csv`: 171 `fbil` rows. `checks/overlap_usdinr.csv`: header `date,kind,rbi,fbil` only. No reader of `usdinr_fbil`/`FbilUsdInrSource` exists outside `fno/global_cues/` (grep over `fno/` and `tools/`) |
| Overlap check names dates, not rates | MET | A difference against the public RBI value would reveal FBIL's rate, so `date,kind` only is the right cut |
| Migration path exists | MET | `ArchivedCopies.adopt` (`archived_copies.py:34`) reads a copy already in the raw archive with its path's fetch time and Drive's creation-time check. It logs a copy only if it is not already logged, so FBIL's two logged copies can be adopted without duplicating log rows |
| Duplicates and contradictions | none | One register row (A17d). It moves a cue to A17's own mechanism and does not touch E2c, E4c or E5b. It reverses response 113's decision 17 by the owner's own decision, which is stated |

### Ruling on the proposed order: code → PASS → merge → adopt and comparison → removal commit. AGREED.

- It never leaves a moment with FBIL's table in neither place. The repository file stays until the Drive table is
  proven equal (counts plus one SHA-256 over sorted rows, no value printed).
- Nothing new becomes public in the window: the repository file is already public until its removal.

### Ruling on the known limits. ACCEPTED, as the owner's call.

- **Git history keeps the old copies.** A rewrite would break every clone and session, and the owner chose "repos stay
  public" the same day.
- **RBI's public table has the same rate on 1,086 shared dates.** So "private" protects mainly FBIL's 2018-2022 fill.
  That is a fact the owner should see once, not a defect. The decision is about FBIL's terms of use, not secrecy of
  the number.

## Note (does not change a trade)

**Run adopt and the comparison before any FBIL fill after the merge.** Once `private = True` is on `main`, a
`global-cues fill` that runs before the adopt would start an empty Drive table with `first_seen_at` = that run. The
adopt would then add older copies behind it. Make the post-merge step explicit: adopt, then compare, then the next fill.
If a routine runs `global-cues fill`, hold it until the comparison passes.

**Verdict: PASS for 1c6700f4140afed0333bae355726aebf1cd0bc4d** (story text). Code may start. Rule 9 does not apply:
there is no money path.

## Addendum 1 (15 Oct 2026): the changed migration order (orchestrator)

**New order:** adopt FBIL's Drive copies and run the comparison from the branch before the merge, and put the removal
commit on the branch. The orchestrator agreed it, because two A17 tests would fail on `main` between the merge and the
removal.

**Accepted.** The adopt writes only to `derived/global-cues/usdinr_fbil/`, which nothing on `main` reads. The merge then
carries the flag, the removal and the real adopt and comparison output together, and CI stays green.

**One condition for my code review and the merge:** the comparison must be against the repository file as it is on
`main` at merge time, not only at adopt time.
- Any FBIL row that a run on `main` adds between the adopt and the merge would be in neither place after the removal.
- So before merging, show that `research/data/global-cues/usdinr_fbil.csv` on `origin/main` is unchanged since the
  commit the comparison read (`git log` on that path). If it changed, adopt the newer copy and compare again.

**The earlier note still holds:** no FBIL fill between the adopt and the merge.
