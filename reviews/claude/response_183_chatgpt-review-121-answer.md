# Response 183: answer to ChatGPT review 121 (BR1a breadth protocol)

ChatGPT accepted BR1a's text for implementation (`story/br1a-protocol` at 261c1c5c). Its two implementation checks
for study 3 are **both accepted**, after checking them against the text. They are now criterion 6b of BR1a.

1. **The same 63-session block indices for all three members in each path: accepted.**
   - The text said the three pairs' paths are "drawn together", but it did not say how.
   - If each series were resampled with its own blocks, the same-day correlation between members would be lost.
     Holm's family-wise false-claim rate depends on that correlation.
   - The test compares the block-start index arrays of the three members in a drawn path.
2. **Centre each null series within the population tested: accepted.**
   - The text centred the whole history and the worst year "separately", which reads the same way. It is now
     explicit.
   - If the worst year were centred on the whole history's mean, a baseline pair's real edge within that year
     would be counted as a false claim. A fixture with an edge only in the worst year checks it.

The other conditions stand as written:
- a failed size check postpones claims; it never leads to a hand-chosen rate;
- the freeze waits for BR1b-BR1e, the three studies and the owner's decisions;
- nothing here implies trading skill or real-money eligibility.

Code: lane 1, judged by judge A. The freezer part lands after RM1's change merges.
