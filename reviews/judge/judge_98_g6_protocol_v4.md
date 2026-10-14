# Judge 98: G6 forecast protocol v4 (draft, not frozen): `story/g6-protocol-v4` 51334da (lane 1, response 99)

**What I did:**
- read `PROTOCOL_v4.md`, every module of `fno/forecast_v4/`, the G6 story entry and response 99;
- checked them against design v2 sections 5 and 8.2, the owner's 15 Oct decisions and the A7 calendar;
- re-derived the V4 golden example by hand;
- recomputed the disclosed base rates and the special-session list from the committed files;
- rebuilt one bootstrap p-value with my own plain loop;
- planted 13 mutations of my own;
- ran the full gates on a trial merge with `main`.

The holdout was respected: I opened no 2019-2023 row of `golden_iv30_rv20.csv` or the back-fill. I read only
`warmup_closes.csv`, the A7 calendar and panel file names.

## Gates

On a trial merge of 51334da with `origin/main` (8d96afa, full history, Slack token unset): **3282 passed**. `ruff
check`, `ruff format --check` (723 files) and `check_imports` are clean. The largest new file is 155 lines and the
protocol is 286.

## Independent checks

| Check | Result |
|---|---|
| QLIKE ranking loss | `ln f + RV/f` = textbook + `ln RV + 1`, so paired differences are equal when RV > 0. It is defined at RV = 0, and RV is never floored (`loss.py`). The gate denominator is the baseline's **textbook** QLIKE (`pairs.py` passes `textbook_qlike` as the baseline loss), which is always >= 0. If the ranking loss were used there, the sign of the 3% could flip; my mutation of exactly that was caught |
| Two date sets | Scored set: resolved, not void, both values present, zeros kept. Gate set: the same dates with RV > 0, with the excluded count reported. This matches the owner's confirmed unit (DESK_DECISIONS, 15 Oct) |
| Bootstrap p | My own loop, using the same SeedSequence([20261015, 4]), ceil(n/L) starts from 0..n-L and a cut to n, gives p = 0.0046995 on 137 synthetic differences with L = 10. `one_sided_test` gives the same value to every digit. The direction is right: the null-centred values `D* - D` are compared with a negative D |
| Futility bound | Percentile bound of the ratio of means, with pairs kept together and the 9,500th of 10,000. "Every member futile" as an intersection-union test at 5% each is valid (Berger 1982) |
| V4 golden | 0.00037 x 252/5 gives 13.656%. 0.138^2 x 7/365 / (5/252) gives 13.567%, so "no". With 9 days, 15.384%, so "yes". Both reproduced by hand |
| Base rates | From `warmup_closes.csv`, regular sessions only: 2,410 sessions and 2,409 returns. 100 returns have abs >= 2% (4.15%); 331 of 2,405 five-return windows contain one (13.76%). Zero returns on 31 Mar 2017 and 8 May 2024. All match section 8 |
| Special sessions | The calendar has 6 `special` sessions in 2017-26: 1 Feb 2020, 20 Jan 2024, 2 Mar 2024, 18 May 2024, 1 Feb 2025 and 1 Feb 2026, plus 9 muhurat sessions. This matches section 2's "6, of which 2 short DR sessions and 4 with normal timings" |
| V5 | Outcome only from `NseFinalSettlement` of the frozen expiry, from that expiry day's file. The source path, SHA-256 and first-seen time are kept, and a level first seen before 15:30 IST on the expiry is refused. "Inside" is strict |
| Stop rule | Matches design 8.2 as amended. Zero shadows gives `no_economic_test`. A with nothing counted is undecided. A "no" needs every counted member futile |
| Mutations | 13 planted; 12 caught (sign of the p count, the uncentred p, the gate denominator, the Holm step, p = 1, the V5 boundary, the session set, the look rates, the percentile rank, zero shadows, the block range, the one-way switch). **One survived:** dropping near-zero positive RV (<= 1e-12) from the gate set. See follow-up 1 |

## The questions asked

- **Two looks at 0.02 and 0.03.** This is a proper split.
  - By the union bound, P(any false claim) <= 0.02 + 0.03 = 0.05 however the looks correlate, given Holm controls each
    look at its rate. Holm with unjudged members at p = 1 is still valid: they only enlarge m.
  - It is a pre-registered alpha-spending rule (Bonferroni over looks), which is what design 03 §3.1 requires for
    anything judged more than once. That paragraph is written for factory shadows, but the principle is the same.
  - It is needed: design 8.2 already has two looks (the review, and the re-run on the projected date), and running 5%
    at each would allow up to about 10%.
  - But it changes how owner decision 7 operates. See must-fix 2.
- **Fixed 15-member family with p = 1 for unjudged members.** Correct and conservative. Leaving V3, V5 and V4 out is
  reasoned (about 12 independent outcomes a year) and stated. It keeps the design's "m of about 15".
- **V2 and V3 on the close proxy.** Agreed. The target is defined on the proxy itself, and QLIKE ranks correctly
  under a conditionally unbiased proxy (Patton 2011). It costs power, not validity.
- **Strict "inside" for V5.** Immaterial in practice and conservative. Agreed.
- **Special sessions excluded.** It matches the A7 calendar and judge 96 addendum 2's "one set". Excluding them is
  right for v4. G1 v1-v3 stay as frozen.
- **"No power report means option 2".** This is a reasonable default, but it interprets owner decision 7. See must-fix 2.

## Must-fix

**1. The premium-adjusted baseline's history is not specified, and that decides whether V2 can be judged at the
review.**
- What the protocol says: V2's (and V3's) primary baseline needs the median of `RV_h / raw implied_h` over 750 resolved
  sessions (at least 500), with raw implied built from "IV30 from the 15:00 pack".
- Why that is a problem: live 15:00 IV30 exists only from 13 Oct 2026. On that source alone, the primary is not
  eligible until about late 2028. Every V2 pair is then missing, and V2's three members cannot be judged at the
  review of about 31 May 2027, which design 8.2 lists as judgeable.
- The alternative is not settled either. Using the panel's end-of-day IV30 as history is a different estimator. A
  750-session window from late 2026 also reaches into 2023, near the forecast holdout years, and the protocol says
  nothing about either.
- Fix: name the history source.
  - If it is a labelled point-in-time proxy, for example the panel's end-of-day IV30, say why it is acceptable and keep
    the window inside 2024 onwards. 2024 to Oct 2026 is about 690 sessions, so the 500 minimum holds without touching
    2019-2023.
  - If no proxy is used, say plainly that V2 has no primary pairs before about 2028, and put that consequence to the
    owner.

**2. Two choices that change how owner-decided rules work are put to the judge and ChatGPT, not to the owner.**
- **(a)** Test A's "yes" at the review now needs Holm at family-wise **0.02**. Design 5.5, approved by the owner,
  says 5%. At r = 3 that is 134 outcomes instead of 114, so a "yes" at the review is harder to reach.
- **(b)** "No power report, so option 2" decides what owner decision 7's rule (option 1 within 2 years, else
  option 2) does when there is no projected date.
- Both are sound, and I would recommend them. But they belong in an owner flag, as I required for decisions 4, 7 and 8
  in judge 96.
- Fix: in protocol section 11 and response 99, mark (a) and (b) "for the owner's confirmation before the freeze", and
  add them to the freeze's preconditions. No code change is needed.

## Follow-ups (not blocking)

1. **Test gap:** add a test that a near-zero positive RV (for example 1e-300) stays in the gate set. My mutation that
   dropped RV <= 1e-12 from the gate survived.
2. A "next session" return that spans a special session (for example Friday to Monday across a Saturday budget day)
   covers two real sessions. It is disclosed in section 2. The reports should count such dates.
3. The 5% spread limit for weekly ATM legs rests on one session of monthly spreads. G7 must report weekly spreads
   before the freeze, as section 1.4 says. I will check it then.

## Project rules

Lane 1 (rule document, executable rules, constants, tests). Pure functions; no I/O; no orders. Names live in
`constants.py`. Every file is under 350 lines. Nothing is frozen and no ledger row is written, which is correct for a
draft. No secrets, emails or model names.

**Verdict: FAIL for 51334daf6703fd85f3f4c9ccf0b601c5772b022c**, on must-fixes 1 and 2. The statistics are right. The
loss, the date sets, the bootstrap, the futility bound, the family, the look split, V4's units, V5's source, the
session set and the base rates all check out. A re-check needs only protocol sections 3.1, 3.2, 6 and 11 and
response 99. The code stays unless must-fix 1's choice needs an eligibility rule in `eligibility.py`.
