# Response 221: answer to ChatGPT review 131 (E6b missed executions in scorecards, story text)

Reviewed: `story/e6-s2-missed-execution` at `65e29fcf` (judge 212 PASS). ChatGPT: PARTIAL, suitable for implementation;
pin the denominators and cohort labels before any promotion comparison. All points accepted; reporting only.

1. **Gate refusals beside execution: ACCEPT.** An execution opportunity is an order that reaches the fill step;
   C2, C3, timing and blocked-book refusals are not execution misses. Both counts are shown per strategy and book with
   reasons: e.g. 100 decisions, 80 refused by C2, 20 reach the fill, 20 open shows "fills 20 of 20" and "opened 20 of
   100 decisions", never "100% of signals traded". A test plants a strategy with 80 C2 refusals.
2. **Partial fills: ACCEPT.** An unwound partial entry is an execution miss and its real net (spreads, C1 charges,
   legging loss) enters net per opportunity: nine closes at +Rs 900 and one unwind at -Rs 250 give a filled-only
   average of Rs 900 and a net per opportunity of Rs 785.
3. **Open trades: ACCEPT.** Show open_count and the oldest open age in sessions; label both averages "closed only,
   provisional while trades are open"; recompute from the same immutable events when they close, never backdated.
4. **Cohort: ACCEPT.** Before any figure is used for a version or promotion comparison, the block shows the
   opportunities and misses on that claim's own eligible dates and version, or is labelled "all dates, not the claim
   cohort" (a filter in the existing counter, no new engine). E6b still changes no S1 verdict.
5. **The owner-facing chain: ACCEPT.** Per strategy and book: chosen decisions, gate refused, reached the fill,
   opened / missed / pending, closed / still open; E4d's fixed priority and size_shared_in_book; E8's owner away,
   price moved and no quote apart; closed-only net prints its denominator (opportunities minus open, pending excluded);
   unknown reasons go to "other", never vanish.

Next: the E6b builder adds these to the story text; judge B confirms; the text merges; code after E8 and S6.
