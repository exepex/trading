# 8. Budget, stop rules, the real-money gate and SEBI

All numbers in this file are proposals (reasoning only) unless marked decided. The owner decides each one; once
decided, each is frozen like a protocol item and only changed as a new version, never lowered because time passed.

## 8.1 Monthly budget cap

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

## 8.2 The whole-project stop rule (proposal)

The owner's idea: "no forecaster beats baselines after 6 months of daily scoring: stop or pivot". Made exact:

- **Review date:** the last session of the sixth full calendar month after protocol v4's freeze (if v4 freezes in early
  November 2026, about 31 May 2027). It moves only by a written owner decision recorded before the date.
- **Questions that can be judged by then:** only those with enough independent outcomes: V1 (if A16 has run 6 months),
  V6, V2. The 20-day questions (Q1-Q5, V3, V5) will have about 6 independent outcomes and **cannot** settle; they are
  reported, not judged (section 5.5).
- **Test A, forecasting:** did any forecaster (rules, hybrid, AI team) beat its primary baseline on any judgeable
  question under section 5.5 (Holm, minimum effect)?
- **Test B, money:** does any factory idea at rung 2 or higher show a shadow net above zero after costs, with its
  interval?
- **Outcomes:**
  - A and B both no: **stop or pivot** (owner chooses). Stop means: keep only the cheap code jobs (data collection,
    weather as a risk aid, baselines), switch off AI roles. Pivot means one named new direction (for example, stock
    options around results only) with its own registered test and its own stop date.
  - A yes, B no: continue 6 more months with the AI budget halved, then the same test.
  - B yes: continue; the idea follows the evidence ladder.
- **The owner's original rule stays as the last gate:** if paper trading shows no net profit, no real money is used
  and the tool is shut down (AGENTS.md).

## 8.3 The pass mark for real money (to be written and frozen before any paper result)

Story RM1 writes `research/evaluation/REAL_MONEY_GATE.md` and freezes it before the first counted paper decision. A
strategy version may start the real-money test only when **all** hold:
1. S1's uncertainty criterion on paper: one-sided 95% lower bound of net per unit of risk above zero, after all costs,
   and the whole period's net above zero (decided 14 Oct), with at least the sample its registration named.
2. After 31.2% tax, its net per rupee of capital tied beats the do-nothing index fund over the same months.
3. Every trade's loss stayed within its cap; its crash replay (2020, June 2024) stayed within the cap.
4. Paper fills were honest: the mean gap between paper fill and the next real snapshot is within the pad.
5. It passed the factory's second independent test if it was one pass among many (section 3.1).
6. The owner approves in writing.

## 8.4 The small real-money test

- 1 lot, a real account the owner funds (about Rs 2 lakh was mentioned on 12 Oct), with a per-trade cap set before the
  start (proposal Rs 4,000-5,000, about 2-2.5%).
- The owner places every order by hand; the tool only records the card, the owner's actual fill and whether the card
  was followed (the discipline record).
- Duration: its registered number of trades or 6 months, whichever is later.
- **Pass:** real net per trade inside paper's 95% interval, and real slippage per unit no worse than the paper pad plus
  Rs 0.50. **Stop:** real losses reach Rs 20,000, or slippage twice the paper pad over 5 trades.
- Scaling beyond 1 lot only after a pass and the owner's decision. Groww API automation only later, as the owner's
  explicit decision after checking SEBI's retail algorithmic trading rules (SEBI circular of February 2025 on retail
  algo participation; its effective dates were extended, as far as known here: must be re-checked then).

## 8.5 Personal use and SEBI

- The tool is for the owner only. Giving calls to others for money needs SEBI research-analyst registration (SEBI
  Research Analysts Regulations, 2014); this design never does that.
- **Flag (reasoning only, not legal advice):** the repositories are public during development (decision 12 Oct). Daily
  trade cards with strikes and entry ranges committed to a public repository are publicly readable calls, even if
  unpaid. Recommendation: before layer 6 sends `TRADE` cards, either make the repositories private or keep the card
  records out of the public repository (Drive only, as raw data already is). Owner decides.
- Nothing in the tool places real orders; the hard lines stay.
