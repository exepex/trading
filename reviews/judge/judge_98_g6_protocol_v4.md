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

## Addendum 1 (15 Oct 2026): 3aa781848c456a6db5151438f1a3b88b7c06bd70 (51334da..3aa7818)

One commit (parent 51334da). It changes the protocol, `eligibility.py`, `constants.py`, two test files and response 99.

| Item | Status | Evidence |
|---|---|---|
| Must-fix 1: the premium-ratio history | MET | Protocol 3.1 names the source: `iv30_eod_close_proxy` is G1 v1's frozen `PanelAtmIv30` on A3's first-archived end-of-day chains, unflagged days only. The window runs from 1 Jan 2024 only (outside the 2019-2023 holdout). It is labelled point in time by content, not by archive time (said plainly), and the 15:00-vs-EOD mismatch is named as noise. `eligibility.premium_ratio_window` keeps t >= 1 Jan 2024 with the outcome resolved before the refit day, the latest 750, and None below 500. My count: **685 regular sessions** from 1 Jan 2024 to 14 Oct 2026 in `warmup_closes.csv`, as the protocol says. (It names "2 Jan 2024" as the first; the first is 1 Jan 2024. The count is right.) |
| Must-fix 2: owner flags | MET | Section 11 lists A (0.02 at the review), B (no power report, so option 2) and C (the EOD proxy, and that without it V2 waits until about late 2028), each "for the owner's confirmation before the freeze". Section 10 makes the owner's written confirmation of A-C a freeze precondition |
| Follow-up 1: near-zero RV in the gate | MET | My earlier surviving mutation (gate drops RV <= 1e-12) now fails a test |

**Checks on 3aa7818:**
- `tests/forecast_v4`: 94 passed. A trial merge with `origin/main` gives **3285 passed**; ruff, format (723 files) and
  `check_imports` are clean.
- **Merge note:** the trial merge conflicts in `reviews/claude/README.md` (both sides added rows). It is resolved by
  keeping both rows. The merger must do the same.
- **New mutations:**
  - Dropping the 2024 start: caught.
  - The 500 minimum written as > 500: caught.
  - Allowing outcomes resolved **on** the refit day (`<=` for `<`): **survived**. The code is right (`<`), but the
    boundary has no test. See follow-up A.

## Follow-ups (not blocking)

- **A.** Add a test that an outcome resolving on the refit day itself is not in that refit's window (point in time).
- **B.** In section 3.1, write "1 Jan 2024" instead of "2 Jan 2024" as the first session.
- **C.** Judge 98's remaining follow-ups stand: count dates whose "next session" spans a special session, and G7's
  weekly spread report before the freeze.

**Verdict: PASS for 3aa781848c456a6db5151438f1a3b88b7c06bd70** (the draft, not frozen). The freeze still needs
ChatGPT's review, G7 and G8's code, the owner's written A-C, and then my check of the freeze record against these
hashes.

**On merging the unfrozen draft:** I have no objection; nothing counts under v4 before its freeze, and the file says
DRAFT. But ChatGPT's review may change it, and any change after this PASS needs a judge re-check. Waiting avoids a
second merge round.

## Addendum 2 (15 Oct 2026): revision 1 at dbba5744ea675b6bc4ba50ec63cf2071ce1b6e34 (3aa7818..dbba574)

Range: ChatGPT's review 99 (89d7419, 5d18cbc) and dbba574, which adds `confirmatory.py`, `student_t.py`,
`diagnostics.py`, the calibration tool and its committed results, two-look futility, and protocol and test changes.

**First, my own miss.** In judge 98 I rebuilt the centred bootstrap's p to every digit and checked its direction, but I
never checked its **size** under a true null. ChatGPT's review 99 did, and the builder's simulation confirms it: the
test rejected 13-32% at a nominal 5% with n = 2L. "The code matches the formula" is not "the test is valid". From now
on, I check the null size of any new confirmatory test myself.

## Gates

Trial merge with `origin/main`: **3308 passed**. As before, the trial merge conflicts in `reviews/claude/README.md`;
keep both rows. Ruff, format (728 files) and `check_imports` are clean. Largest files: the protocol at 320 lines and
the tool at 107.

## What I verified

| Item | Result |
|---|---|
| Simulation code and seeds | Read in full. Every cell is seeded by `SeedSequence([20261015, 99, cell])`, and the null series have mean zero: centred lognormal `exp(Z) - e^0.5`, AR(1) with a 200-step burn-in, moving-sum overlap. I re-ran the cell skew_right, L = 5, n = 125 (cell 19). Its rates match the committed JSON **exactly**, and it took 9 s |
| max(t, studentized) | It is a valid conservative combination: rejecting needs both p <= alpha, so its size is at most the smaller of the two sizes, and it is valid whenever either part is. It cannot repair a case where **both** parts over-reject, which is the right-skew case |
| Futility, 97.5% per look | Correct Bonferroni over two looks for the futility "no". The seed has a look word, there are golden tests for both looks, and a futile verdict at look 1 is final |
| `proxy_drift` | Descriptive only and never feeds the ratio, as review 99 asked |
| Refit-day test, 1 Jan 2024, A-C marked confirmed | Done. My earlier surviving mutation (`<=` refit day) is now covered |

## The question asked: does "p at most a quarter of the Holm step" fix right skew? No, not fully.

The committed calibration cannot answer this: its bootstrap uses B = 2,000, so p cannot fall below 1/2,001 = 0.0005,
and 0.0013/4 = 0.00033 is below that. So I simulated it myself.
- Same centred-lognormal null as the tool.
- **100,000 series per cell**, production **B = 10,000**, the repository's own `batch_means_p` and
  `studentized_bootstrap_p`.
- The bootstrap runs only where the t-test already rejects at the loosest threshold. The max rule needs both, so this
  is exact, not an approximation.

Max-rule rejection rates. "Real step" is Holm's first step at that look: 0.00133 at look 1, 0.002 at look 2.

| L, n | Look 1, at the step | Look 1, quarter rule (0.00033), vs the real step | Look 2, at the step | Look 2, quarter rule (0.0005), vs the real step |
|---|---|---|---|---|
| 5, 125 | 0.00539 (4.0x) | 0.00221 (**1.7x** the real step) | 0.00718 (3.6x) | 0.00297 (**1.5x**) |
| 10, 125 | 0.00512 (3.8x) | 0.00190 (**1.4x**) | 0.00680 (3.4x) | 0.00255 (**1.3x**) |
| 20, 125 | 0.00354 (2.7x) | 0.00102 (0.8x) | 0.00529 (2.6x) | 0.00161 (0.8x) |
| 5, 10 | 0.00298 (2.2x) | 0.00078 (0.6x) | 0.00455 (2.3x) | 0.00118 (0.6x) |

Each rate rests on 102-718 rejections out of 100,000, so the Monte Carlo SE is 0.0001-0.0003.

The quarter rule brings L = 20 and n = 2L inside the real step. It does **not** fix L = 5 or 10 at n = 125 (V1, V6a:
L = 5; V2, V6b, V7: L = 10). Those are 13 of the 15 members, about 125 outcomes is what the stop review will have,
and they stay 1.3-1.7x over the real Holm step. For reference, the batch-means t on its own (200,000+ series) is
4-10x over at n = 125. The bootstrap half is what helps.

## Must-fix

**1. Item D offers a remedy the numbers do not support.** Section 11 D puts "for example p at most a quarter of
Holm's step" to ChatGPT and the owner as the stricter option. As measured above, it still over-rejects for the members
with L = 5 and 10 at about the review's sample size. Fix:
- Item D must state the measured size of every option it offers, with enough simulations to resolve it (the
  conditional method above is cheap: about 40 s a cell at 100,000 series and B = 10,000).
- It must offer at least one option that is measured within tolerance at the real Holm steps for every member's L at
  n = 125. Candidates, all reasoning only until measured: a stricter divisor (1/8 or a per-L calibrated critical
  value); a skew-corrected statistic (Hall's or Johnson's modified t); a minimum number of batches or outcomes before
  a claim.
- It must say how the simulated skew (centred lognormal, sigma 1, skewness about 6) relates to real QLIKE differences.
  Measuring the skewness of a **baseline-vs-baseline** difference on already exposed close-proxy data (2024-26) would
  show whether D matters in practice; that disclosure belongs in the protocol. I have not done this myself, to avoid
  new data analysis on the judge's side.

**2. The calibration overstates its own resolution.** Section 5.3 says the measured size is "within nominal + 2 Monte
Carlo SE" in almost every cell (strong evidence). At 1,000 series and Holm's first step (0.00133), that tolerance is
0.0036, which is **2.7x nominal**. A test 2.5x over size passes it. The same holds at 0.002 and 0.004. Fix: either
re-run the small thresholds with enough series (at least about 50,000 per cell; the conditional method keeps this
cheap) and B = 10,000, or label the claim "some evidence" for thresholds below 0.01 and say why.

## Follow-ups (not blocking)

- The AR(1) L = 5, n = 125 cell (7.6% at 5%) is disclosed. The large re-run of must-fix 2 should include it.
- The calibration's B = 2,000 differs from the scoring B = 10,000. State that the size claims hold for B = 10,000, or
  run them at B = 10,000 (cheap with the conditional method).

**Verdict: FAIL for dbba5744ea675b6bc4ba50ec63cf2071ce1b6e34**, on must-fixes 1 and 2. Both are about measuring and
stating the size honestly; the code changes are sound. Replacing the centred bootstrap was the right call, and the
two-look futility is right. A re-check needs section 5.3, section 11 D, the calibration files and any new test. If the
chosen remedy changes `confirmatory.py`, I re-run my 100,000-series check on it.
