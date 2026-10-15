# Review 113 — G10 protocol v4 timeline

**Reviewed:** `story/g10-v4-timeline` at **4985c228424142f6818d75ced2139d02c8f45d25**; request 155; G10 story; response 152 revision 1; draft `PROTOCOL_v4.md`; G9 miss rules and work register. **Second reviewer:** ChatGPT, across the financial roles in `AGENTS.md`. **Verdict: PARTIAL — one real point-in-time error must be resolved before the v4 freeze.** The judge's reported text PASS is not an independent test of this data-timestamp issue. No code or simulation was executed in this review.

## 1. Equal family timing and look-ahead — PARTIAL (strong evidence)

**ACCEPT** one release, a common 15:10 GitHub receipt deadline, and the same 15:15 evaluation snapshot. Giving the rule book the same publication deadline as the AI books avoids an artificial speed advantage; rules may compute sooner but must not obtain a later market observation. A late family must not replace its original with a later revision.

**CHANGE — real cutoff contradiction.** G10's timetable declares **14:30:00 the market-data cutoff**, yet says the NIFTY recorder **starts capturing at 14:30** and can retry until 14:40; if it clashes with A16's 14:30 mark, it starts at about **14:31**. The fallback A16 14:30 mark also takes roughly 216 quote calls over ~50 seconds. These quotes are not necessarily observations known at 14:30:00. If their 14:31–14:40 values enter the pack as `live_1430`, the cutoff is false and a later move can change a forecast or decision. This is a normal path expressly described in G10, not a speculative attack.

**Exact fix:** define the cutoff as the **latest permitted underlying observation timestamp**, not the capture job's nominal label. Every live market field must have trustworthy `observed_at <= 14:30:00 IST`; retrieval after 14:30 is allowed only for a genuinely timestamped pre-cutoff observation. Otherwise that field is missing, and if required the pack is incomplete/`system_late`. Do not label a 14:31 quote as a 14:30 quote. If Groww/A16 cannot supply enough genuinely pre-cutoff observations, the owner must explicitly choose a later common cutoff (and adjust release) or an earlier capture window; do not silently change the cutoff by implementation. Add a fixture with 14:29:59 and 14:30:01 quotes plus the actual shared-key fallback; the latter must not pass as pre-cutoff. This can alter buy/sell decisions and IV-based forecasts.

## 2. Skill at 15:15, money at R=60 — ACCEPT with scope (strong evidence for economic separation; reasoning only for interpretation)

A fixed 15:15 market snapshot can compare the **direction/quality of a recorded desk decision** across fast rules and slower AI books without pretending the owner could fill there. The E8 60-minute owner-response fill (about 10:15 next session) is the proper economic basis for paper P&L, including gaps, charges, refusals and no-fills. Report both separately; never promote on the 15:15 skill score alone.

**Important interpretation:** the 15:15 score is a diagnostic against a *common market snapshot*, not proof that a forecast's official V1–V7 future outcome has resolved, and not a simulated 15:15 executable fill. Keep the actual v4 probabilistic scoring rules and horizons unchanged. A family that proposes an instrument not available at the 60-minute fill gets a no-fill, not a fabricated fill. This is an acceptance-test detail, not another design blocker.

## 3. Post-cutoff move flag at historical p95 — ACCEPT (reasoning only, some evidence for chosen calibration data)

Using `abs(ln(S_15:15/S_14:30))` and freezing its 95th percentile from checked 2020–26 regular-session candle **closes** is a clear, reproducible descriptive rule. A flag rather than exclusion avoids discarding volatile days and biasing apparent skill. Report flagged/unflagged counts and performance, including no-fills. A 95th percentile of history does not guarantee exactly 5% flagged in future regimes; it is not a safety brake or a reason to revise a trade after observing the move. Freeze the numeric X, sample count, source revision and exact quantile convention before v4's first scored record.

## 4. System lateness versus family lateness and G9 — PARTIAL (strong evidence for the G9 definition)

**ACCEPT** that a genuine common pack failure makes the whole day `system_late`, separate from an individual family's late/missing forecast; a family that misses 15:10 while others submit is charged under G9's overall and 2%-day miss caps. A GitHub push after 15:10:00 is late even if the model generated locally earlier. Do not let one family's late submission invalidate another's timely record.

**CHANGE only as a consequence of Q1:** a pack made of post-14:30 observations cannot be called an on-time `A` or `A2` pack. Its status is incomplete/`system_late` unless the owner changes the cutoff. Count such failures separately, and ensure they cannot improve any family's miss rate by being silently relabelled as a clean common day. For an A2 day, flagged/missing IV30 must follow the existing per-question baseline/void rules; it is not an automatic valid IV30 for every question.

## 5. Must anything change before freeze? — PARTIAL (strong evidence)

**One blocker:** the observation-time/cutoff rule in Q1 must be fixed and tested on the normal 14:30 A16+NIFTY collision/retry path. It changes which prices and IVs a family may use, hence signals and scorecards. Do not freeze the present contradictory text.

**Non-blocking implementation checks:** bind the one released pack's hash to all three families; distinguish GitHub receipt from author-supplied commit time; report A/A2/system_late and flagged counts; retain separate live-14:30 versus close-proxy historical cohorts; do not merge G1 v2's 15:00 records into v4. The G10→G11 rename and moving other-index recording away from A16's 14:45 mark are reasonable. Judge the live dry run before go-live; if the API cannot provide pre-cutoff observations, the design needs the owner's new cutoff decision rather than another retry hack.

## Financial-role check

- **Mathematician/statistician/quant modeller:** point-in-time eligibility, missingness and common opportunity sets determine whether any apparent advantage is causal; p95 is descriptive, not a calibrated risk test.
- **F&O trader/options strategist/volatility trader:** a few minutes of IV/spot movement can change strike, premium, spread and trade eligibility; stale/future quotes are not harmless.
- **Execution/microstructure:** next-session R=60 fills and bid/ask availability determine economic P&L, not a 15:15 mark.
- **Risk/portfolio/head of desk:** preserve hard stops and record no-fill/missed decisions; the common snapshot must not bypass risk checks at the actual entry time.
- **Market research/macro/flows/equity/investment banking:** event news arriving after cutoff cannot selectively enter one family's features; company events are not additional evidence unless timestamped.
- **Regulation:** no live orders; source/retention restrictions remain in force.
- **Behavioural finance:** avoid hindsight by treating a late model revision as the first decision.
- **Tax/cost accountant:** skill marks are not realised net profits; use modeled execution charges and capital at the actual fill.
- **Data/backtesting engineer/red team:** test a 14:31 quote labelled 14:30, a delayed GitHub push, fallback missing IV and shared-key contention.

**Final verdict: PARTIAL / CHANGES REQUIRED before freeze on the single cutoff-integrity issue.** No other proposed guard or new service is justified under the owner's simplicity rule.
