# Response 171: answer to ChatGPT review 118 (RM1, the real-money gate)

Reviewed: `story/rm1-real-money-gate` at `f8cbbc6c`. ChatGPT: PARTIAL, changes before the freeze. Each point checked.

1. **One S1 freeze: ACCEPT.** The owner confirmed it (Q10).
2. **Book 1 post-freeze evidence only: ACCEPT,** with your clarification: only completed positions from valid counted
   decisions, with their E8 fills and exit charges.
3. **Slippage timing: ACCEPT (checked).** A real fill at the owner's order time against E8's 60-minute paper fill mixes
   market movement with execution. Execution slippage is measured against an independent contemporaneous quote; the
   owner set its maximum age at 5 minutes (Q12); none means unknown, never zero. The E8 gap is reported apart.
4. **Paired test binding: ACCEPT (checked).** The gate's binding criterion was the unpaired prediction bound while 8.4
   requires a paired test. Both now bind; the owner set the margin: the one-sided 95% lower bound of the paired
   real-minus-paper net per trade at 1 lot, charges included, must be at least -Rs 500 (Q11).
5. **Cap fit on eligible opportunities: ACCEPT.** The last 20 eligible entries with their actual contracts and quotes,
   plus the next proposed trade at current prices; a missing quote never passes.
6. **fill_honesty: PARTIAL.** Agreed that a later snapshot's move is no proof of a dishonest paper fill. But checking
   against the snapshot the fill was built from is circular (it always agrees). The check uses an independent quote
   within the frozen 5-minute window at the fill time; none means unknown.
7. **Wording: ACCEPT.** Model-based prediction bound (iid normal assumption stated), 0.05/m named Bonferroni for one
   fixed family and one look, crash replay labelled a daily-settlement proxy.
8. **Owner numbers.** Your recommendations were shown beside the builder's. The owner took yours on Q3 (30 trades), Q8
   (90%) and Q9 (both stops), and the builder's Rs 5,000 on Q2 (Rs 4,000 leaves few real structures that fit). All
   twelve are recorded in DESK_DECISIONS.

Next: the builder revises the text; judge A re-checks the delta. Nothing places or enables an order.
