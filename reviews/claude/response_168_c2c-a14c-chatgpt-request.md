# Response 168: review request to ChatGPT for C2c and A14c, the crash buffer on the whole margin and its recompute (quality rule 9)

**Why you:** both stories change money and risk. C2c changes how C2 (the risk manager) and C4 (the hard-validity
checks) stress every paper trade's margin. A14c recomputes the stress factor k = 1.45, which lapses after 13 Nov 2026;
from 14 Nov every paper trade is refused. Quality rule 9 asks for your review after the judge and before the code.
One request covers both, because C2c applies what A14c measures.

**Exact versions (story text only, no code yet):**
- C2c and C2d: branch `story/c2c-whole-margin-stress` (C2c at `8a9a23e9`, C2d at `fff6b646`), section "C2c" of `docs/stories/C-code-roles.md`. Judge 174
  (judge G) FAILed `3b4342c` on one should-fix: credit spreads with the STR1 cap. `8a9a23e9` fixes it and is waiting for
  judge G's addendum.
- A14c: branch `story/a14c-stress-recompute` at `f2192b2f`, section "A14c" of `docs/stories/A-data-foundation.md`.
  Judge 173 PASS, with addenda 1-3 (the owner's Q3 and Q4 included). `f2192b2f` adds judge 176's full-run rule and
  the broker check's timing, and is waiting for judge D.

**Read:** both sections; judges 173 and 174 (`reviews/judge/`); response 77, section "Stressed-margin factor" (how 1.45
was measured); judge 75 (the formula); `docs/DESK_DECISIONS.md` rows of 15 Oct at `d68b1a9c`: "Crash buffer applies to
the whole margin" and "Stressed-factor recompute uses everything since 1 Jan 2020".

**The problem found (strong evidence):**
- 1.45 was measured as the largest rise of a held position's whole margin (scan plus exposure).
- C2 and C4 multiply only the scan: `max(0, k x scan - NOV) + min(0, NOV) + exposure`.
- On the real 14 Oct rows the scan is 1-14% of the margin; exposure is 59,077.07 a lot on every four-leg row.
- So k = 1.45 adds +0.6% to SF 100, +5.7% to SC 300 (the largest) and 0% to every BF row. The owner's crash buffer
  is almost inert.

**C2c (one term):**
- **Formula:** `max(0, k x scan - NOV) + min(0, NOV) + k x exposure`; at entry `max(0, k x scan - NOV) + k x exposure`.
- **Uncapped credit rows (SF, SC):** exactly `k x` what C2 counts.
- **Debit rows (BF):** never below `k x` what C2 counts. The premium is still never multiplied (judge 75).
- **Capped credit spreads (CCS, PCS):**
  - The STR1 cap still bounds the SPAN part, so the figure lies between what C2 counts and `k x` that.
  - Known answer, CCS 300: 52,260.42 against `k x initial` 56,503.72.
- **Effect at 1.45, per lot:** SF 100 60,269 → 86,854; BF 300 59,077 → 85,662. About 31% fewer lots fit the same
  capital (1 − 1/1.45). The owner has been told.
- **Scope:** C4's independent copy of the formula changes too, and a test makes C2 and C4 agree.

**A14c:**
- **What it builds:** a read-only command. For every entry day since 1 Jan 2020 and every structure and width, it
  rebuilds the entry's legs and recomputes the margin on each later day's first-archived NSE `i1` file up to exit.
- **What it reports:** the largest held rise of the whole margin, rounded up to the next 0.05, with an evidence table.
- **What it never does:** write `config.yaml`. The owner enters the value.
- **2020 files:** their short-option minimum is modelled behind A14's calculator; any other method difference is
  refused by name.
- **Reproduction check:** response 77's three hand figures, 1.127 (2026), 1.265 (2020) and 1.407 (2024), within 0.001
  or explained, after the full back-fill (about 1,700 files, 16 GB in Drive).
- **Owner, 15 Oct, Q3: automatic, with an alert.** A weekly Actions job appends the factor to
  `research/data/margins/stress_factor.csv`. A rise applies at once. **Any** fall is held: the old factor stays and the
  owner is asked. The orchestrator proposed holding only a fall above 0.05; I hold every fall, because a maximum over a
  window that only grows cannot fall unless the data or the method is wrong.
- **Owner, 15 Oct, Q4: accept the circular limit, plus one Groww comparison per recompute.** It runs in the Claude
  routine, because GitHub holds no broker key. Tolerance: SPAN within Rs 1, exposure within 1% after index rescaling.
  A mismatch alerts but does not hold the factor.
- **Story C2d** (same branch as C2c, at `fff6b646`, after judge 176): C2 and C4 read k from the latest row of that file
  dated strictly before the decision day (point in time; a row written on the day itself is never used). `config.yaml`
  keeps only the method, the file and `max_age_days`. A seed row carries the owner's 1.45 of 14 Oct with no measured
  value, and A14c's first run after it is a full run, so the hand value never becomes a floor.
- **Groww check:** it runs in each session's daily run (story O1), once per applied factor, and records its result in
  `research/data/margins/stress_broker_check.csv`.
- **Timeline:** build by about 3 Nov; first run about 6 Nov; judge by 11 Nov. Then weekly.

**Questions (accept / partial / reject, with evidence; real cases only, per the owner's 15 Oct "keep the design
simple" rule):**
1. Is stressing the exposure by k right? Exposure is charged on the short legs' notional and rises with the index and
   by NSE circular. Or should k stress only what can actually rise in a crash? Give a real case either way.
2. For CCS and PCS the cap keeps the SPAN part at the broker's own figure and stresses only the exposure. Is that the
   right bound for a defined-risk spread, or should the exposure also be capped?
3. Is "largest held rise of the whole margin, entry to 21 days before expiry, since 2020, up to the next 0.05" a sound
   rule for k? Or is a quantile, or a per-structure k, more honest? Remember the 2020 minimum made 2020's margins
   track the index.
4. Review the automatic design itself (owner Q3; the orchestrator accepted holding every fall, 15 Oct):
   - the factor is applied through an append-only data file, never `config.yaml`;
   - a rise applies at once, and every fall is held for the owner;
   - a result below 1.0 is refused, and so is an archive with fewer sessions than the last run's.
   Is anything missing that could quietly loosen the buffer? Are the weekly cadence and the Groww tolerance right?
5. Anything that would change a trade, a fill or a stop decision and must change before the code is built?

**Answer file:** `reviews/chatgpt/review_117_c2c-a14c-stress.md` plus its line in `reviews/chatgpt/README.md`. Check
that 117 is still free. Never overwrite an existing file. If your write is blocked, paste the text in chat and the
owner relays it.
