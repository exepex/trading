# Response 29: design section 13 (end product, dashboard, AI runtime) for review

- **Author:** Claude
- **Date:** 2026-10-12
- **For review:** [docs/DESK_DESIGN.md section 13](../../docs/DESK_DESIGN.md) (v2.3, proposed)

## Why this section

The owner asked to regenerate the implementation plan with **every story needed to finish the end product**, but only
once the design is complete and approved. Checking the approved design (sections 1-12) against that request found two
gaps:

1. **No definition of the finished product.** The design says what the desk does, not what "done" is or how the owner
   sees it. The owner had asked for a "new dashboard"; no section defines one.
2. **D4 (where the AI runs) was open.** The AI stories for books 2 and 3 cannot be specified without it.

The owner decided both on 12 Oct 2026: **web dashboard plus Slack**, and **cloud routines** for the AI roles.
Section 13 turns those decisions into design: 13.1 definition of done, 13.2 dashboard, 13.3 Slack, 13.4 monthly
report, 13.5 AI runtime (context pack, isolated sub-sessions per book, commit before fill, fresh quote snapshot for
fills, model identity per decision, attributed cost, failure handling), 13.6 honest limits.

## Questions for you

1. Is the definition of done (13.1) complete: does any story-worthy part of sections 1-12 fall outside it?
2. Cloud routines (13.5): does the context pack plus isolated sub-sessions give a fair, firewalled comparison
   (12.5, 12.6)? Is filling all books from one fresh snapshot after all decisions are committed sound?
3. AI cost under a flat plan (13.5) is attributed, not billed. Is the labelling enough for the "each AI role must earn
   more than it costs" rule (8.1), or should the design require something stronger?
4. Dashboard (13.2): anything missing for "all three books on both scoreboards with every detail" (12.5)?

## What happens after approval

The implementation plan and **all** stories are regenerated for the finished product (three books, both scoreboards,
AI layer, dashboard). Each story will have: **title**, **description** (user story), **context and why** (everything an
agent needs to implement it without asking: background, the design sections it implements, decisions, current code
it builds on), **scope**, **expected design**, **acceptance criteria**, **test plan**, **how the judge verifies**,
**depends, size, status**. Built and judged stories (A2, A4, B4 passed; A5, A6, C1 built) are carried over with their
status. You review the full plan and stories; only after your approval and the owner's are GitHub issues #3-#21
closed and a clean issue set created from the approved plan.
