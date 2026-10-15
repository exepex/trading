# Response 170: review request to ChatGPT for RM1, the real-money gate (quality rule 9)

**Why you:** RM1 fixes, before any counted paper result exists, when a strategy version may be put to the owner for
the small real-money test, and how that test is passed or stopped. It is the real-money gate, so quality rule 9 asks
for your review after the judge's PASS (judge 171 addendum 1) and before the owner answers and the text merges.
Nothing in RM1 places, enables or prepares any order; the owner places every real order by hand.

**Exact version:** branch `story/rm1-real-money-gate` at `46d0c1fc` or later; the gate, story and claims text under review last changed at `c27f8c64` (later commits change only response 163 claim 4's wording to "Book 1 only", judge A's note, and add this request).
**Read:**
- `research/evaluation/REAL_MONEY_GATE.md` (the 12-item draft gate);
- `docs/stories/RM-real-money.md` (story RM1);
- `reviews/claude/response_163_rm1-real-money-gate.md` (claims, trace table, owner questions Q1-Q10, answer to judge
  171);
- judge 171 and its addendum 1 (`reviews/judge/judge_171_rm1_real_money_gate_story.md`);
- the source: design v2 8.3 and 8.4 (`docs/design_v2/08_budget_and_stop_rules.md`), owner decision 8 and its
  amendment (`docs/DESK_DECISIONS.md`, rows of 15 Oct), your reviews 97 and 98 (the exact sample, statistic, interval
  and execution constraints belong in RM1's frozen text);
- the code the design reuses: `fno/evaluation/freeze.py`, `order.py`, `completeness.py`; `fno/desk/execution.py:52`.

**What RM1 decides:**
- The gate is S1's item format and joins S1's `frozen_files`: S1's one freeze hashes it, S1's `order` check proves it
  precedes every book's first counted decision, and the freezer refuses while any gate item is not decided by the
  owner. A later change is a new S1 protocol version.
- Evidence = Book 1 positions whose decision commit has the gate's freeze as a strict ancestor; pilot and shadow
  positions are shown, never counted.
- All slippage is measured from the paper price before pad (`FILL_PAD_RS` kept apart), worse positive.
- Real test: 1 lot; length max(20, registered trades) or 6 months, the later; pass = real mean net at or above the
  one-sided 95% prediction-interval lower end for the mean of n new trades from paper's m positions, and real
  slippage ≤ pad + Rs 0.50; stop at Rs 20,000 cumulative real loss or 5-trade slippage above 2 × pad.

**Questions (accept / partial / reject, with evidence; real cases only, per the owner's 15 Oct "keep the design
simple" rule):**
1. **One freeze.** Is joining S1's `frozen_files` (one freeze, one order check) sound, or is there a real path where
   the gate is edited, or its evidence counted, after paper results are visible? Cost stated: any gate change is a
   new S1 version.
2. **Book 1 only.** Is counting only Book 1 post-freeze positions right? It drops shadow and pilot records, so the
   first eligible version waits longer. Is there a real case where this loses evidence the gate should count, or
   still counts evidence it should not?
3. **Slippage reference.** Is "paper price before pad" the right base for `real_test_pass` 2, `real_test_stops` (b)
   and `fill_honesty`? With E8's 60-minute paper fill and the owner's faster real fill, is the timing difference a
   real bias in the paired net test, and does the gate need a time-matched paper fill?
4. **Completeness.** Do the 12 items implement every element of 8.3 (conditions 1-7) and 8.4 exactly, with nothing
   looser than the owner accepted? Check the prediction-interval formula, route (b)'s 0.05 ÷ m, the crash-replay
   windows (20 Feb-30 Apr 2020, 3-7 Jun 2024) and the cap-fit rule (NIFTY lot 65: Rs 5,000 ≈ 76.9 points per unit).
5. **Owner questions.** Are Q1-Q10 neutral and complete? Is any number the gate needs missing from them? **Give your
   own recommendation for each Q1-Q10 with a number** (account, cap, minimum trades, condition-5 route, interval side,
   t-check, replay cap, discipline share, stop base, frozen_files), so the owner sees two independent views.

**Answer file:** `reviews/chatgpt/review_118_rm1-real-money-gate.md` plus its line in `reviews/chatgpt/README.md`. Never
overwrite an existing file. If your write is blocked, paste the text in chat and the owner relays it.
