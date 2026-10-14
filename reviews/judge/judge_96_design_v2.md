# Judge 96: design v2 and re-plan: `story/x-design-v2` d48bdfc87f0e85c62be7dbed109a5c2710f4157e (PR #100, response 95)

**What I did.**
- Read all 15 files in full: `docs/design_v2/` and response 95.
- Checked each claim against `docs/DESK_DECISIONS.md`, `research/evaluation/PROTOCOL.md`, response 92, judges 93-95 and
  my own merge records.
- Re-derived every formula the design uses.
- **Scope:** documents only. Every file is under 350 lines; the longest, `REPLAN.md`, has 159.

## Claims

| # | Claim | Result | Evidence |
|---|---|---|---|
| 1 | Forecasts settle skill in months; trade P&L takes years | **PARTLY (must-fix 1)** | "Trades take decades" is right: 1,200-2,000 trades for +153 (response 92, judge 93). The 5.5 power formula is right: n = (2.49 × r)², with 1.645 + 0.842 = 2.487; r 5 gives 155 and r 10 gives 620. But it uses an unadjusted one-sided 5%, while 5.5 tests with Holm across the family. See must-fix 1. |
| 2 | Protocol v4: QLIKE and Brier scores, implied vol as the primary baseline, Holm, minimum effects, power check after 60 outcomes; G1 v3 stays frozen | MET as a design | QLIKE = RV/f − ln(RV/f) − 1, as in Patton 2011. Brier and log scores, reliability table, block bootstrap with the block length at least the horizon. Implied vol is the primary baseline for V2, V3 and V5. v4 is a new version; no frozen file is edited. Open question for ChatGPT (response 95 asks it): HAC t-test against block bootstrap at small n. |
| 3 | Weather becomes a scored large-move forecaster, with response 94 as v0 baseline | MET | p_big_1d and p_big_5d, v0 checklist as the baseline, thresholds registered before use, "price of calm" reported. The owner's "red means no new trade" (decision row of 14 Oct, trading principles) is kept. |
| 4 | Cost wall at 2× full cost; B6 history scan replaced | MET | The cost figures match judges 93 and 95: four-leg 810-940; weekly 100-384 including pads; two-leg about 410. 2 × 820 = 1,640 stops the condor's best gross of 978. Replacing B6 is right: a scan of spent 2019-26 history would be one more trial on spent data. |
| 5 | Desk: Rs 20 lakh, bucket cap Rs 30k, account cap Rs 1.5L, brake Rs 1.2L, consistent with the Rs 10,000 per trade | MET | Owner row "Paper account Rs 20 lakh, Rs 10,000 maximum loss per trade" (=> YES). The bucket cap is 3 × 10,000. The brake is 6% of 20 lakh, the same 6% as Rs 30,000 on Rs 5 lakh. All caps are labelled proposals, for the owner to decide. |
| 6 | T1 card replaces P4; the advocate's code checks can block, its AI objections cannot | MET | Matches the owner's "devil's advocate attacks every call" (row of 14 Oct). Not letting it veto keeps the paper record a test of the registered rule. Its objections are scored. |
| 7 | REPLAN keeps built work; slice A 15 Oct - 4 Nov; stop review about 31 May 2027 | PARTLY (should-fix 1, 3) | Nothing built is dropped. Only B6's scan and F4's owner overrides are dropped, both by owner rows ("never override on paper"). "The last session of the 6th full month after an early-November freeze" is 31 May 2027. Statuses and dates: see below. |
| 8 | S1: 8 open items change; decided items are not reopened | **PARTLY (must-fix 3)** | `PROTOCOL.md` has 18 items: 5 decided, 13 open, matching REPLAN section 4's list. Seven open items change, plus the open t-check. But REPLAN section 4's note adds G8 and E8 to the decided `frozen_files` list. |
| 9 | 11 owner decisions in REPLAN section 5 | MET as a list, but incomplete (must-fix 3) | The 11 lines are there. The `frozen_files` extension is missing from them. |

Also verified:
- CUSUM: k 0.5 gives one-sided ARL0 of about 930 at h 5 and about 340 at h 4. The text says "about 900" and "about 340".
- Straddle: 0.8 × S × σ × √T gives Rs 790 a unit and Rs 51k a lot (30 days), Rs 21k a lot (5 days), at NIFTY 25,000.
- Expected false passes: 52 trials × 1% = 0.52.
- Every decision quoted (eight layers, volatility focus, 20 lakh, the ten differentiators and eight missing pieces,
  trading principles, judge plus ChatGPT, future slices follow v2) matches a 14 Oct owner row.

## Must-fix

1. **The "months" claim uses the wrong significance level.**
   - Section 5.5 tests with Holm at 5% family-wise, but its power arithmetic uses one-sided 5% per comparison.
   - With k registered comparisons, Holm's first step is at 5%/k. Say k is 15: judgeable questions V1, V2, V6 (two
     parts) and V7, times 3 forecasters. Then z = 2.71, and n = ((2.71 + 0.84) × r)² = (3.55 r)².
   - That gives 315 outcomes at r 5 (V1: about 15 months) and 1,260 at r 10 (about 5 years). The text says 8 months to
     2.5 years.
   - V1 also starts only after A16 has run 20 sessions, and A16 waits on the owner's host decision. Its primary
     baseline, HAR on intraday data, needs about 250 sessions.
   - Fix: redo the arithmetic at the family's actual level. Restate "months" as "about a year or more for the daily
     questions, at favourable r", in `01_` 1.3, `OWNER_SUMMARY.md` and response 95. "Faster than trades" still holds,
     with strong evidence; "months" is not shown.
2. **The stop rule's Test A treats "not shown" as "no skill".**
   - On 31 May 2027, about 6 months after v4's freeze, most comparisons will be underpowered by must-fix 1's
     arithmetic.
   - As written, "no" on Test A plus "no" on Test B leads to stop or pivot. So the owner could stop for lack of data, not
     lack of skill.
   - Fix: use the 60-outcome power report section 5.5 already defines. A comparison whose projected date is past the
     review is "undecided". Test A then has three answers: yes, no (adequately powered and not shown), or undecided.
     State the owner's choice for "undecided" in 8.2 (for example, continue at reduced AI cost to the projected date,
     or stop).
3. **A decided S1 item is changed without an owner decision.**
   - REPLAN section 4 says "the new scoring code (S2's change, G8, E8) joins the hashed list before the freeze".
   - The owner decided `frozen_files` on 14 Oct (option A): the S2, S3, F8 and F9 code joins the list, and version 1
     waits for it.
   - Adding G8 (forecast scoring) and E8 (fills) changes that decided value. It also lengthens the wait before
     counting.
   - It may well be right, but it is a change to a decided item. Fix: put it to the owner as decision 12 in section 5,
     with the delay it adds, or drop it.

## Should-fix

1. **REPLAN section 1 statuses are stale.** They were read from `docs/stories/*`, not from the judge record. Already
   PASSed and merged: A12 (judge 51, merges 09e51a7 and 510b5c6), C4 (83, dafbebe and b03c4ef), E3 (82, 85c570a and
   e6484cc), E5 (84, 58f5781), S1 (85, bdd46ff and 35f6f46; owner batch 1 e46e3d8) and A14 (77, 6568315). Slice A week
   1's "judge rounds of the built queue" is smaller than the table implies. Take statuses from
   `reviews/judge/README.md`.
2. **Decisions are cited by row number** ("decision 94", "60", "56", "55", "52"). Those are line positions in
   `DESK_DECISIONS.md`; they change when rows are inserted, and two already point one row off (55 and 56). Cite each by
   date and bold title.
3. **Slice A dates.** About 10 M-sized and 5 S-sized stories, for two builders, in 15 working days, plus judge rounds,
   is at the edge of possible (reasoning only). The critical path depends on others:
   - G6 needs ChatGPT agreement before G7, G8 and M1;
   - the host decision gates A16, E8's real fills and LM1;
   - C5 waits for the owner's numbers.

   Mark the dates as targets and name these dependencies. Otherwise a slip will look like a broken promise.
4. **"88-93% of F&O traders lost money FY22-FY26 (SEBI)".** SEBI's published studies cover FY22-FY24 (and FY25 in a
   2025 update). Cite the exact studies, or drop FY26.
5. **Prices at NIFTY 25,000 are illustrative.** NIFTY was 22,722 on 14 Oct; the straddle is then about Rs 46k a lot.
   The conclusion is the same, but say "illustrative".

## What is right and worth keeping

Throughout, the design separates what is decided, what is a proposal and what is reasoning. Its limits file is candid.
It also keeps every frozen protocol untouched by making v4 a new version.

## Verdict: FAIL for d48bdfc

Three must-fixes, all in the text, no code:
1. redo the power arithmetic at Holm's level;
2. a third "undecided" answer for the stop rule;
3. the `frozen_files` extension put to the owner.

After a PASS on the fixed SHA, ChatGPT reviews via response 95, and the owner approves.

## Addendum 1 (15 Oct 2026): revision 1, tip 13e256061bd8d73106c56623e5548d53d8b1d52b

7789288 carries the content. 13e2560 only rewraps lines: a word-level diff of 7789288 against 13e2560 shows no changed
word. Only `docs/design_v2/` and response 95 change.

| Item | Result | Evidence |
|---|---|---|
| Must-fix 1: power at Holm's level | MET | Section 5.5 now plans at α/m (0.05/15 = 0.0033, z 2.71) and 80% power: n = (3.55 r)². I recomputed every cell of the new horizon table: r 3 → 114 (5.5 months, 2.3 years, 9.5 years); r 5 → 316 (15 months, 6.3 years, 26 years); r 10 → 1,264 (5 years, 25 years, 105 years). "Skill in months" is gone from 01 §1.3 and §1.7, `OWNER_SUMMARY.md` and response 95. They now say "no question is known to settle in months; r is measured after 60 outcomes". V1's dependence on A16 and on intraday HAR is stated. |
| Must-fix 2: stop rule | MET | Tests A and B each have yes, no and undecided. "No" for Test A needs a projected settle date on or before the review, or an interval that already rules out the minimum effect. Underpowered never counts as "no". The owner chooses in advance among three options for "undecided": (1) continue to the projected date, at most 2 years, with AI cut to the forecasters at half budget, after which undecided counts as no; (2) code only; (3) stop. The text gives a recommendation, and states plainly that "undecided" is the most likely result on 31 May 2027. |
| Must-fix 3: `frozen_files` | MET | The note adding G8 and E8 is dropped. G8 is left to v4's own freeze, which is correct: it is G-protocol code. Adding E8 is now owner decision 12, with its reason and its cost in delay. |
| Should-fixes | MET | REPLAN §1 statuses now come from the judge record; I checked every cited merge commit and each is an ancestor of `main` (e3506ec, f314254, c12137e, b4f1e1b, 374ad67, 58f5781). Decisions are cited by date and title. Slice A dates are marked "targets, not commitments", with the ChatGPT, host and C5 dependencies named. SEBI loss figures are cited by study and year and labelled as secondary summaries, matching `reports/Retail FnO losses and safeguards.md`. |
| Size | MET | The longest file is now `REPLAN.md` at 168 lines; every file is under 350. |

**Two corrections to my own judge 96.**
1. **The NIFTY level.** The orchestrator is right that my "22,722 on 14 Oct" was wrong: 22,721.95 is the 13 Oct close.
   14 Oct closed at 22,622.70 (`warmup_closes.csv`; index-close manifest). The design now uses about 22,620. I
   recomputed the straddle: 0.8 × 22,620 × 0.138 × √(30/365) = Rs 716 a unit, about Rs 46,500 a lot; the 5-day straddle
   is about Rs 19,000 a lot. Both are correct.
2. **The SEBI figures.** My should-fix doubted any FY26 figure. The repository's own report cites an August 2026 SEBI
   study (87.7% of individuals lost in FY26), through secondary sources. The revision labels it that way, which is right.

**Verdict: PASS for 13e256061bd8d73106c56623e5548d53d8b1d52b.** Next, ChatGPT reviews it via response 95 and the
owner approves. Nothing merges before that.
