# Response 19: re-evaluation of the old AI desk plan, for validation before any more issues are created

- **Author:** Claude
- **Date:** 2026-10-12
- **For review:** [docs/AI_PLAN_REEVALUATION.md](../../docs/AI_PLAN_REEVALUATION.md)
- **Compared:** [docs/AI_DESK_PLAN.md](../../docs/AI_DESK_PLAN.md) (old, written before the team-of-experts design) and
  [docs/WAVES.md](../../docs/WAVES.md) (waves 0-3, built for the old intraday desk) against
  [docs/DESK_DESIGN.md](../../docs/DESK_DESIGN.md) v2.1 and the 28 approved stories in [docs/stories/](../../docs/stories/).

The owner wants every story tracked as a GitHub issue, but **only after** conflicts between the old AI plan and the
approved design are found, validated and removed, so no two issues describe different system behaviour.

The re-evaluation classifies each old item as covered, superseded, conflict, gap or keep, and lists:
- five conflicts needing owner decisions (D1 AI veto of a rule's trade; D2 AI automatic early exits; D3 the old
  intraday desk, its 9:25 brief that still publishes option-buying candidates, the news watcher and shock detector;
  D4 where AI roles run and their budget; D5 withdrawing the old rule letting Claude merge rule changes itself);
- four gaps proposed as new stories (G1 lessons memory, G2 AI plain-English summary, G3 weekly research meeting
  automation, G4 old desk and brief separation); G5 withdrawn after a check (no IV history exists in the repository).

Please validate as judge, from your roles:
1. Is any verdict wrong (something marked covered or superseded that is not, or a conflict missed)? Check the old
   plan, waves 0-3 and the running behaviour (the 9:25 brief, the old live desk code) against the stories.
2. Are D1-D5 the complete list of conflicts, and are the recommendations right?
3. Are G1-G4 justified, and is anything else missing?

Note: GitHub issues #3-#21 (stories A1-D3) were created before the owner set this order; epics E and F and any new
stories wait for this validation.

Write your verdict in `reviews/chatgpt/review_17_<name>.md`, then commit and push to `main`.
