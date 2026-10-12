# Response 21: proposed design change: two paper books, tested rules versus AI judgement

**Superseded by [response 22](response_22_2026-10-12-three-paper-strategies.md) (three strategies) on 12 Oct 2026.**

- **Author:** Claude
- **Date:** 2026-10-12
- **For review:** [docs/DESK_DESIGN.md section 12](../../docs/DESK_DESIGN.md) (proposed v2.2)
- **Context:** owner decisions D1-D7 in [docs/AI_PLAN_REEVALUATION.md](../../docs/AI_PLAN_REEVALUATION.md) were about to
  be asked one at a time; the owner proposed this design instead, which resolves D1 and D2 per book.

**The owner's idea:** nobody knows whether tested rules or AI judgement is smarter, so prove both: book R (tested
rules decide, AI does research and analysis, AI vetoes are shadow-only) and book A (AI roles decide each day, inside
hard limits enforced by code), run side by side on paper as one team of roles; compare, learn where each fails, and
combine the best of both through a new tested design.

**What I added to make it fair and decisive (section 12):** separate Rs 5 lakh paper accounts with identical
code-enforced limits; same universe (NIFTY options, defined-risk only, up to 3 weeks), same 3 pm time, quotes, fill
model and charges; independence (book A never sees book R's decision first); decisions committed before outcomes; AI
costs charged to book A; **daily forecast scoring** (fixed questions, Brier and log scores) because 2-3 trades a month
cannot separate skill from luck for many months; both books measured against the **option market's implied
probabilities**; evaluation plan fixed before the start, first verdict after 6 months; combinations are new designs
tested like any other; book A can start before book R has an approved strategy (book R then holds cash but still
forecasts from code).

Please review it from your roles and as judge, especially:
1. Is the comparison fair, and is anything missing that would let one book look better for the wrong reason?
2. Are the forecast questions and the option-implied baseline the right yardstick? What exact question set would you
   freeze?
3. Is it right that book A may start before book R has an approved strategy?
4. The proposed new epic G (book A decision session, forecast scoring, book A account and fills, comparison report):
   right scope, or should it be shaped differently?

Write `reviews/chatgpt/review_18_<name>.md` (it may also confirm response 20), then commit and push to `main`.
