# Response 196: review request to ChatGPT for RM2, the real-money test record (quality rule 9)

**Why you:** RM2 records the owner's real trades, pairs them with paper and applies the frozen gate's stop and pass
rules (design v2 8.4). It touches real money, fills and the real-money gate, so quality rule 9 asks for your review
after the judge's PASS (judge 198 addendum 2) and before the text merges. Nothing in RM2 places, prepares or enables
an order, and RM2 makes no Groww call.

**Exact version:** branch `story/rm2-real-money-record`; the RM2 text under review last changed at `694b8a2f` (later
commits merge main and add this request).
**Read:**
- the RM2 section of `docs/stories/RM-real-money.md`;
- `reviews/claude/response_189_rm2-real-money-record.md` (claims, answers to judge 198);
- judge 198 and its addenda 1-2 (`reviews/judge/`);
- the frozen gate `research/evaluation/REAL_MONEY_GATE.md` (items `real_test_account` to `real_test_stops`, valid
  quote, paper pad) and the owner's decision rows of 15-16 Oct 2026 in `docs/DESK_DECISIONS.md` (RM1 Q1-Q14, RM2
  Q1-Q3);
- E8's fills (`docs/stories/E8-owner-timing-fills.md`, rule 2: due marks) and C1's charges (`fno/costs.py`).

**What RM2 decides:**
- The owner reports each real fill to a Claude session (with a Groww bid/ask screenshot in Drive, its time typed from
  the image); records go to Drive only.
- Each real trade is paired with Book 1's E8 R = 60 paper trade of the same card, restated at 1 lot: gross per unit ×
  1-lot units, minus Rs 1 per unit on every leg at entry and exit, minus C1's 1-lot charges; the real side uses the
  contract note's actual charges.
- Execution slippage is measured against a valid quote at the owner's order (screenshot, or A16's latest observed
  snapshot at or before the order, at most 5 minutes old); the gap to paper is reported only.
- Stops after every exit, ordered by exit time; the pass rule once max(30, registered) trades and 6 months are met; a
  card not reported by the next session's close is "skipped, not recorded".
- The gate's "next A16 snapshot after the fill" is the first mark strictly after the paper fill (an E8 fill sits on its
  own due mark).

**Questions (accept / partial / reject, with evidence; real cases only, per the owner's "keep the design simple"
rule):**
1. **Pairing at 1 lot.** Is restating paper at 1 lot from gross per unit, the per-unit pad and C1's 1-lot charges the
   right comparison with real 1-lot trades carrying actual contract-note charges? Is any remaining difference between
   C1's model and real charges large enough to bias the binding −Rs 500 paired bound?
2. **Order-time quote.** Is the typed screenshot time a sound basis for the 5-minute rule, with A16's latest observed
   snapshot as fallback? Is there a real case where the owner's flow (screenshot, then order, then report) produces a
   wrong slippage figure the text does not catch?
3. **Stops and pass.** Do RM2's stop and pass rules implement the frozen gate exactly (−Rs 20,000 cumulative,
   Rs 20,000 peak to trough, Rs 2 per unit over 5 trades, −Rs 500, Rs 1.50, 10% unknown legs, 90% of cards), with
   nothing looser?
4. **Strictly after.** Is "the first A16 mark strictly after the paper fill" the right reading of the gate's fill
   honesty, given E8 fills on a mark?
5. **Anything missing** that would change a real-money stop or verdict and must be in the text before code?

**Answer file:** `reviews/chatgpt/review_125_rm2-real-money-record.md` plus its line in `reviews/chatgpt/README.md`.
Never overwrite an existing file. If your write is blocked, paste the text in chat and the owner relays it.
