# 8. Budget, stop rules, the real-money gate and SEBI

All numbers in this file are proposals (reasoning only) unless marked decided. The owner decides each one; once
decided, each is frozen like a protocol item and only changed as a new version, never lowered because time passed.

## 8.1 Monthly budget cap

**Decided (owner, 15 Oct 2026): accepted as proposed below** (half of measured plan minutes for books and roles; any
new recurring cash cost needs the owner's written yes; alert at 80%; AI roles stop at 100%).

| Item | Today | Proposal |
|---|---|---|
| Claude subscription | The owner's existing plan; cost recorded monthly by the owner for F8 | Books' and roles' allocated share shown monthly; **AI routine usage for books and roles capped at a share of the plan the owner sets** (proposal: half of the plan's measured session minutes, leaving the rest for development) |
| GitHub Actions, Drive | Free (public repositories; Drive within the owner's storage) | No cap needed; storage reported monthly |
| Azure Database for PostgreSQL | Running; cost known to the owner, not to this repository | Owner records it; reported monthly |
| Groww API | Read-only use today | Whatever Groww charges for API access, if anything, recorded by the owner |
| Hosting for the 15-minute recorder and monitor | None | Inside the Azure free grant if option (b) (section 6.6); else measured |
| Any paid data | None | Not without an idea that has passed the cost wall and needs it; owner approves each |

**Cap rule:** any new recurring cash cost needs the owner's written yes; at 80% of a cap a SYSTEM alert; at 100% AI
roles stop in the order of `07_ai_team.md` section 7.6, and code jobs keep running.

## 8.2 The whole-project stop rule (decided by the owner on 15 Oct 2026; Test B amended the same day)

The owner's idea: "no forecaster beats baselines after 6 months of daily scoring: stop or pivot". Made exact:

- **Review date:** the last session of the sixth full calendar month after protocol v4's freeze (if v4 freezes in early
  November 2026, about 31 May 2027). It moves only by a written owner decision recorded before the date.
- **Questions that can be judged by then:** only those with enough independent outcomes: V6 (one day, from daily
  closes), V1 (only if A16 has run long enough), V2. The 20-day questions (Q1-Q5, V3, V5) will have about 6 independent
  outcomes and **cannot** settle; they are reported, not judged (section 5.5).
- **Honest expectation:** 6 months give about 125 daily outcomes. Under section 5.5's arithmetic that settles a daily
  question only if its noise-to-effect ratio r is about 3 or less. The most likely result of Test A on this date is
  therefore "undecided", and the rule is written for that.
- **Decision unit (frozen with G6, before any v4 score).**
  - Test A counts only the primary comparisons of protocol v4's registered family (section 5.5) on the judgeable
    questions, one per forecaster and question. G1 v3's family is reported beside it, not counted. Void outcomes and
    missing forecasts are excluded from the statistic and counted in the report.
  - Test B counts only shadow strategies registered in the ledger before the review, each with its registered pass mark
    and minimum useful net per trade. A no-trade day is not a trade; screened-out ideas (section 3.1) count in the trial
    total, not in Test B.
- **Test A, forecasting.** Three results, never two:
  - **yes:** a forecaster (rules, hybrid, AI team) beats its primary baseline on a judgeable question under section 5.5
    (Holm, minimum effect);
  - **no (futility):** for every counted comparison, the one-sided 95% upper bound of the forecaster's improvement is
    below the registered minimum effect (3% QLIKE or Brier skill 0.02; the futility margin is the minimum effect
    itself). Failing to reject zero is never enough;
  - **undecided:** anything else. **Underpowered never counts as "no".**
- **Test B, money (owner decision 7 as amended on 15 Oct 2026: "A ... => I accept").** Three results: **yes** when a
  counted shadow strategy's one-sided 95% lower bound of net per trade after costs is above zero; **no** only when
  every counted strategy reached its registered sample and its one-sided 95% upper bound is below its registered
  minimum useful net; **undecided** otherwise. **Zero eligible or resolved shadows gives `undecided /
  no_economic_test`, never "no"**: with no observations there is no bound (ChatGPT's full review 95, B2). So a review
  with A "no" and zero shadows leads to the "undecided" options below, not to stop or pivot.
- **Stopping for cost is a separate, non-statistical decision.** If no idea ever reaches a test, the owner may still
  stop or cut the project for cost or product reasons; that is recorded as such, never as a statistical "no edge".
- **Outcomes (both tests must say "no" to stop or pivot):**
  - A no and B no: **stop or pivot** (owner chooses). Stop means: keep only the cheap code jobs (data collection,
    weather as a risk aid, baselines), switch off AI roles. Pivot means one named new direction (for example, stock
    options around results only) with its own registered test and its own stop date.
  - A yes and B not yes: continue 6 more months with the AI budget halved, then the same test.
  - B yes: continue; the idea follows the evidence ladder.
  - **Any other combination ("undecided"):** the owner's choice among the options below is **recorded in
    `docs/DESK_DECISIONS.md` before the first v4 outcome is scored**, so it cannot be shaped by results:
    1. **Continue to the projected settle date** of the best-powered question (section 5.5's 60-outcome report), if it
       is at most 2 years after the review, with AI roles cut to the forecasters at half the AI budget. If the re-run on
       that date is still undecided, the AI forecasters stop and the question is closed as "not shown, not disproven";
       the code forecasters may continue at no AI cost.
    2. **Code only:** switch off every AI role, keep the code forecasters and baselines running at no AI cost until the
       projected date, then re-run the test. The AI books' question stays unanswered.
    3. **Stop now**, accepting that the forecasting question was not answered.
    **Decided (owner, 15 Oct 2026, before any v4 score):** option 1 when the projected date is within 2 years;
    option 2 when it is later, because an answer more than 2 years away does not justify the AI cost of waiting.
- **The owner's original rule stays as the last gate:** if paper trading shows no net profit, no real money is used
  and the tool is shut down (AGENTS.md).

## 8.3 The pass mark for real money (accepted by the owner on 15 Oct 2026; frozen by RM1 before any paper result)

Story RM1 writes `research/evaluation/REAL_MONEY_GATE.md` and freezes it before the first counted paper decision. A
strategy version may start the real-money test only when **all** hold:
1. S1's uncertainty criterion on paper: one-sided 95% lower bound of net per unit of risk above zero, after all costs,
   and the whole period's net above zero (decided 14 Oct), with at least the sample its registration named.
2. After 31.2% tax, its net per rupee of capital tied beats the do-nothing index fund over the same months.
3. Every trade's loss stayed within its cap; its crash replay (2020, June 2024) stayed within the cap.
4. Paper fills were honest: the mean gap between paper fill and the next real snapshot is within the pad.
5. **Selection-adjusted evidence, always** (owner decision 8 as amended on 15 Oct 2026: "B ... => I accept"): a
   one-sided 95% bound after dozens of screened ideas is not enough on its own. The strategy needs either a second,
   untouched forward paper period with the same pass mark, or a multiplicity adjustment (Holm) across every idea in the
   trial count at the time, with the sample predeclared.
6. Before the test starts: the chosen structure fits the smaller real cap (Rs 4,000-5,000), and current SEBI and tax
   rules are re-verified.
7. The owner approves in writing.

## 8.4 The small real-money test (accepted by the owner on 15 Oct 2026)

- 1 lot, a real account the owner funds (about Rs 2 lakh), with a per-trade cap of about Rs 4,000-5,000 (2-2.5%). The
  exact account size and cap are confirmed by the owner in writing before RM1 freezes (owner decision of 15 Oct 2026).
- The owner places every order by hand; the tool only records the card, the owner's actual fill and whether the card
  was followed (the discipline record).
- Duration: its registered number of trades or 6 months, whichever is later.
- **Pass (owner decision 8 as amended on 15 Oct 2026): a predeclared paired test.** Real and paper trades come from the
  same cards, so the test is paired: the mean real-minus-paper net per trade, and real-minus-paper slippage per unit,
  each with its interval. The real trades' mean must lie inside a **prediction interval** for the mean of that many new
  trades given paper's mean and spread (never the narrower confidence interval of paper's own mean), and real slippage
  per unit must be no worse than the paper pad plus Rs 0.50. **Stop:** real losses reach Rs 20,000 (the drawdown stop),
  or slippage twice the paper pad over 5 trades.
- Scaling beyond 1 lot only after a pass and the owner's decision. Groww API automation only later, as the owner's
  explicit decision after checking SEBI's retail algorithmic trading rules (SEBI circular of February 2025 on retail
  algo participation; its effective dates were extended, as far as known here: must be re-checked then).

## 8.5 Personal use and SEBI

- The tool is for the owner only. Giving calls to others for money needs SEBI research-analyst registration (SEBI
  Research Analysts Regulations, 2014); this design never does that.
- **Decided (owner, 15 Oct 2026, option b): card records are kept in Google Drive only.** The repositories are public
  during development (owner decision of 12 Oct 2026 on the shared dashboard repository and Azure Postgres), and daily
  trade cards with strikes and entry ranges in a public repository would be publicly readable calls, even if unpaid
  (reasoning only, not legal advice). So before the first `TRADE` card, card records go to Drive, delivery stays Slack
  #fno-desk, and the public repositories hold no live strikes or entry ranges; only scores and hashes are committed.
- Nothing in the tool places real orders; the hard lines stay.
