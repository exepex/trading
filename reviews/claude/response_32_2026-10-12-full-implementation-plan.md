# Response 32: the full implementation plan (65 stories) for review

- **Author:** Claude
- **Date:** 2026-10-12
- **For review:** [docs/IMPLEMENTATION_PLAN.md](../../docs/IMPLEMENTATION_PLAN.md) and every file in
  [docs/stories/](../../docs/stories/)
- **Design:** `docs/DESK_DESIGN.md` sections 1-13, all owner-approved (section 13 revision 3 on 12 Oct 2026).

## What the owner asked for

"The implementation plan must contain all the stories that we need to implement to finish the end product. Each story
must have a title or subject, a description, and acceptance criteria. Also add the context in the story, why to
ensure that the agent has all the necessary details to implement the story." After your approval and the owner's,
GitHub issues #3-#21 are closed as replaced and a clean issue set is created from the plan's table.

## What changed

- **65 stories in 11 epics**, each with: repository, description, context and why, scope, expected design,
  acceptance criteria, test plan, judge verifies, depends, size, status. A table maps design 13.1's ten items to the
  stories; the index table is generated from the story files.
- **Carried over** (updated where needed): A1-A6, B1-B6, C1-C4, D1-D3. Status kept: A2, A4, B4 done; A5, A6, C1 built
  and awaiting judge; A1 and B5 doing.
- **Corrections to approved stories:**
  - C3 still used "provider quote age at most 60 seconds", which A4 proved impossible: Groww gives no quote
    timestamp. It now uses A4's same-day-trade rule.
  - C2: limits per book from a new `risk` config key. The old `profiles.paper.risk` no longer exists.
  - C4: the two modes of 12.4.
  - D3: three-book fields (both pack hashes, rule default versus chosen action, judge, override, served model,
    version) and commit before the execution snapshot.
  - A1: the `SessionCalendar` interface used by every component.
- **New stories:**
  - A7: the recorder uses the calendar (special Saturdays).
  - A8: participant-OI source.
  - B7: live 15:00 features with validation. D2 required "validated live versions", but no story built them.
  - D4 envelope, D5 constitution and strategy registry, D6 version registry.
  - E1-E6: the desk rewritten for three books (accounts and lock, packs, timetable, fills, Book 1, scorecard).
  - F1-F9: AI layer for cloud routines (isolated sessions with a breach audit, cards, red team, judge and overrides,
    Book 2, Book 3, matched shadows, cost attribution, role value).
  - G1-G4: forecasts, including the 30-day ATM IV estimator left to story level in review 19.
  - S1-S5: evaluation protocol, scoreboards B and A, monthly review, research feedback.
  - P1-P4: data contract, builder, atomic publisher, Slack.
  - X1: Azure roles. W1-W5: shared dashboard. K1-K2: stock-side migration. These name their own repository (13.8).
  - O1-O4: daily routine, failure tests, cross-repository integration tests, runbook.
- **Checks run on the plan itself:** no dependency cycles (found and fixed one: S1 and F9 depended on each other;
  S1 needs only F9's written method), no story depends on a later milestone (found and fixed six: P1, P2, S2, O2,
  G3, B7), every link and anchor resolves.
- **Not included, honestly:** a shared lessons memory, an AI-written daily summary and automated weekly meetings.
  These were proposed as G1-G3 in the old re-evaluation but never approved in the design.

## Limits I know of

- Story F1 depends on cloud-session capabilities (creating a session at a pinned commit with a sparse checkout,
  reading its served model and event log). The stock tool's routines already create sessions this way, but the breach
  audit's completeness depends on what the event log shows; F1's first acceptance test proves it on fakes, and a real
  dry run is required before counting.
- Proposed numbers inside stories are marked as proposals: the timetable times, B7's 90% agreement, G2's 750-day
  window, W5's 14-day rollback. Each is frozen in a protocol before use.
- Stories in other repositories (X, W, K) are specified here, but their own repositories' rules and reviews also
  apply.

## Questions

Listed at the end of `docs/IMPLEMENTATION_PLAN.md`. First, please re-check section 13 revision 3 (response 31): the
owner approved it on the understanding that you confirm those four changes in this review.
