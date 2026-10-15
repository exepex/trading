# Response 185: review request to ChatGPT for E8 (owner-timing fills), quality rule 9

**What:** E8 changes the price at which every counted paper trade fills.
- **The rule:** each entry and exit fills at the first 15-minute quote snapshot at or after the time the order reached
  the owner (T) plus a reaction time R. The price is the bid for sells and the ask for buys, and only if the entry
  rule admits it. Otherwise the trade is recorded as missed, never filled at another price.
- **R:** R = 5, 30 and 60 minutes are all reported, with E4's 15:15 fill as the common yardstick. The verdict uses
  R = 60 (owner, 15 Oct 2026, `docs/DESK_DECISIONS.md:181`).
- **The card's time:** O1 posts the card after the 15:15 snapshot, so all three owner-timing views fill the next
  session, at 09:30, 09:45 and 10:15.
- **Why:** the paper record must show what the owner could really get, and the cost of human delay must be measured,
  not assumed.

It decides fill prices, so quality rule 9 (`docs/JUDGE.md`) asks for a ChatGPT review after the judge's PASS and before
any code. This is a **story-text** review. Code may start only when this review comes back with nothing that changes
the design.

**Exact version:** branch `story/e8-owner-timing-fills` at `df7a1d65b0fa887bb8d5538a3ac58544881a99b3`.

**Read:**
- the story: `docs/stories/E8-owner-timing-fills.md` (on the branch);
- the judge: `reviews/judge/judge_193_e8_owner_timing_fills_story.md` on main (FAIL; addenda 1 and 2 FAIL; addendum 3
  PASS);
- the design: `docs/design_v2/03_layers_factory_desk.md:88-102`, `REPLAN.md` section 5 decisions 5 and 12;
- the study behind it: `research/2026-10-16-fill-timing/results.md` (E8a, ledger trial 54, exploratory);
- related: O1's run order (`docs/stories/O1-daily-run.md` on `story/o1-daily-run`), E4c (all legs checked first),
  E2c (fills to Drive).

**What the judge already settled (attack instead of repeating):**
- **The card time:** the card posts at 15:15 or later, so R = 5 moves to the next session's 09:30, because 15:30 is
  after 15:25.
- **Until A16's routine runs,** every owner-timing fill is "missed, no quote".
- **A 14:00 decision helps only with an earlier card too.** That costs either a card posted before the 15:15 checks
  are final, or a second run.
- **The fill step and its failure:** the fill step runs right after `quotes`. If it fails, new entries fail closed and
  exits still run.
- **The ±0.5% NIFTY band** would drop about 32% of overnight entries (204 of 645 days for SF, 210 of 660 for LC).
- **The entry rule is held open** for the owner: price cap only (recommended, wired as the pending default), cap plus
  band, or any price. S1's freeze needs the answer.

**Questions where your view is most useful:**
1. **The adverse selection of the price cap.** With a cap, bought options fill mostly on mornings that moved against
   the idea. Is reporting the split (fills and misses by NIFTY's move) enough, or should the verdict for bought options
   be shown both with and without the misses?
2. **The availability calendar.** A dates-only file in the public repository, and an `away` row counts only if it was
   committed before T. Is a dates-only public file acceptable for privacy, or should it live in Drive with a committed
   hash as the time witness?
3. **Entry validity.** An entry is valid only until its first available session; an away session gives "missed, owner
   away". Exits never expire. Is one session the right limit?
4. **The four views.** Four paper accounts per book run on the same decisions, each with its own exits. Is anything in
   the design likely to let a view's result leak into the verdict (C2 reads the verdict account only)?
5. **Any price.** Under this option, C2's hard caps are re-checked on the fill's own prices (Rs 10,000 per trade and the
   buckets), but the decision's approved cash no longer limits the price. Is that a sound reading of "maximum loss
   fixed at entry"?

**Answer in** `reviews/chatgpt/review_<n>_e8-owner-timing-fills.md`, per point: agree, disagree or change, with the
reason and any numbers.
