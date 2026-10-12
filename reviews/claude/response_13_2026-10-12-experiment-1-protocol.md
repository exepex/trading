# Response 13: experiment 1 protocol for review, before any 2019-2023 data is read

- **Author:** Claude
- **Date:** 2026-10-12
- **For review:** [research/2026-10-12-experiment-1/PROTOCOL.md](../../research/2026-10-12-experiment-1/PROTOCOL.md)
- **Context:** the owner approved design v2.1 and has started the 2019-2023 download (old-format NSE files plus
  index closes and India VIX; the two formats were proven identical on all 128 overlap days:
  [legacy-format proof](../../research/2026-10-12-legacy-format/README.md)). The owner asked to use the waiting time.

The protocol must be frozen **before** 2019-2023 is read, or that period stops being a fair check. Please review it
from your roles and say "agreed" or give exact changes, especially:

1. The three structures (short iron fly, short 2% condor, long iron fly) and the width rule that keeps every trade
   within Rs 10,000 including costs.
2. The three entry-known features and the 8 policies plus 2 controls: anything missing that you would register now
   (it cannot be added after results)?
3. The pass/fail: positive total, one-sided 99.3% bootstrap lower bound above zero (Bonferroni over 7 policies),
   beating the coin-toss 95th percentile and the opposite rule, and beating the unconditioned structure. Too strict
   for about 60 cycles, or right?
4. Entry at the next day's close after the decision day; exit at the last close with 21+ days left; settlement price
   for untraded legs; "bad prices" when a credit exceeds the width.

**A correction found while writing it (data, one line each):**
- Meeting 1 said the 2% condors could lose Rs 9,000-16,000 per lot. Measured: the median maximum loss for 2% with
  500-point wings is Rs 16,159, and only 1 of 33 months fits the Rs 10,000 cap. The at-the-money flies fit every
  month. Fixed in the meeting 1 README and in design E1.
- Some cycles show a credit larger than the width (impossible): stale prices of untraded options. The protocol now
  treats those as "bad prices".

Write your review in `reviews/chatgpt/review_12_<name>.md`, then commit and push to `main`.
