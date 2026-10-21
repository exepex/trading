# Handover: Judge E (session_01HkXMVPDEqVsmJZtghFrGzM)

Written 21 Oct 2026, on the handover order of 16 Oct (orchestrator). The session was stopped before it could act on
that order, and restarted on 21 Oct.

## (a) Identity
- **Role:** independent judge (docs/JUDGE.md).
- **Area:** the core engine:
  - D3 (no owner override), F1t, F2, F4, F5, F6/F7, G13, E2e, T1c;
  - O11 (the core-engine plan and the end-to-end acceptance harness).
- **Branch:** `judge-e-handover` (this file only). Every verdict is a lane-3 judge file pushed straight to `main`, under
  `reviews/judge/`. Nothing else is uncommitted: the worktrees under the scratchpad held only checkouts and planted
  mutations, all restored.
- **Numbering:** judges 300-310 came from the interim range (300-349). Since O12, numbers come from
  `tools/claim_number.py`: 400, 401, 307.5, 308.1, 309.1.

## (b) Done and merged (verdict on `main`, code merged by the orchestrator)
| Story | Verdict file | Final |
|---|---|---|
| D3, owner_override refused in every book | judge_300 (add. 1 at ac966350, F4 text) | PASS; merged (e5906769, then ac966350's F4 text, both on main) |
| O11 acceptance harness | judge_306 (add. 2 at 9601a13e, add. 3 at bc6a9ec1) | PASS; 9601a13e on main |
| E2e, BookSheet port plus canonical_snapshot | judge_309 (+ 309.1 at b1838eb3) | PASS; b1838eb3 on main |

## (c) Done, not merged (story texts PASS; code to come)
| Story | Branch head judged | Verdict |
|---|---|---|
| F1t story text | f1204a5a (+ note on 13653f05) | judge_301 add. 1: PASS. Its F4 port is still missing (see e) |
| F2 story text | f68b50e8 | judge_303 add. 1: PASS (1 minor: `previous_pack`'s first-seen time before O9) |
| F5 story text | 95cd4b8c | judge_307 add. 4 + 307.5: PASS; depends on F1t's F4 port |
| F6/F7 story text | c625151e | judge_302 add. 2: PASS |
| G13 story text | 85eba3a8 | judge_304 add. 1: PASS (my own unit error, withdrawn there) |
| T1c story text | 2538c8cd | judge_401: PASS (1 minor: older weather records lack `v0_status`) |
| O11 core-engine plan | 467a4433 | judge_305 add. 2: PASS (lane 2), plus a correction (nse-margins cron was my error) |

## (d) In progress at the stop
**G13 code re-judge** (judge 310's should-fix), at the builder's head **3600b911** (main merged). Verified so far:
- `recorder.py` now carries a stored record's `problems` (its own `missing` placeholder included) into a rerun:
  "already recorded with N problems", exit 1.
- My earlier surviving mutation (`<= MAX_STRIKE_GAP` changed to `<`, `density.py:120`) is now caught (1 failed, 110
  passed).

**Not yet done:**
- the full gates on 3600b911 merged with today's `main`;
- planting the "stored problems dropped" mutation myself;
- reading the back-fill containment and the clip test.
Then write the addendum to `judge_310_g13_code.md`, its number claimed with the tool.

## (e) Open verdicts (FAIL) and their findings
1. **F6/F7 code, judge_400** (c58117f3; branch now d46379c7, not re-judged). Two should-fix findings:
   - one damaged registered spec stops Book 3's whole day: `strategies.py:33-37` catches only `NotRegistered`, while
     D5's `require_registered` raises `PlaybookError` on invalid YAML; `proposals._registered_rules` is the same;
   - criterion 15's edit alert is not built, and nothing tests that the exit stays fixed at the decision (mutant M20
     survived).
   - Minor: test that served's `playbook`/`config` always win (M18); `no_trade` absent from the reader (M30); list
     strategies from the committed registry; reword criterion 1 and item 8.
2. **G13 code, judge_310:** being re-judged (see d).
3. **F4 story text, judge_308 + 308.1** (992a3f89). FAIL only because F1t's text lacks F4's port: the `JudgeStep`
   call before `decide()`, `AcceptedDecision.judge` and `judge_blocks`, `judge_failed`, and the run check that refuses
   a blocked run holding a chosen trade. F1t's branch is now c2d2b922 and has not been checked by me.

## (f) Open questions and agreements
- Owner decisions recorded (DESK_DECISIONS, 16 Oct):
  - F4 is a code judge daily plus a monthly AI re-check (line 257);
  - paper trading uses sealed same-day isolation, "not full F1" (line 255);
  - F4 is built before Book 2;
  - F5 uses one slot per rule-default trade.
- Agreed interfaces I verified across texts: F1t's `AiBookDecider`/`AcceptedDecision`/`DecidedRun`; the answer
  `{"model_reported", "decision": {action, reason, ...}}`; `check_decision`; F2's `analyst_cards` in the pointer; the
  BookSheet `evaluation` item in the private pack; F1t's snapshot restore; per-book `OrderBuilder` and `ExitRules`
  owned by F5 and F6.
- 21 Oct (orchestrator): Book 2/3 work is parked. My queue is the G13 re-judge, then the G13b and FL1 story texts.

## (g) Risks a successor must not miss
- **Model reporting:** the AI books reported model "unknown" on 3 of 4 answered forecast days, and "unknown" means no
  trade (F1t's criterion 3c covers the fix). Watch it at go-live.
- **Tonight's first-run checks** (from 16 Oct, now old): `health-check.yml` (cron 12:21 UTC) and `nse-margins.yml`
  (22:00 UTC). Confirm on GitHub that both have run since.
- **Judge-file pushes race** with other sessions on `reviews/judge/README.md`. Resolve by keeping both sides' rows,
  never by dropping one.
- **Code reviews:** always gate on the head merged with today's `main`; branches fell behind often (O11, G13).

## (h) First three actions for a successor
1. Finish the G13 re-judge at the builder's current head: full gates on the head merged with `main`; plant the
   "stored problems dropped" mutation; check the back-fill containment and the clip test. Write
   `## Addendum <k>` in `judge_310_g13_code.md`, its number from `tools/claim_number.py judge-addendum ... --report
   310`.
2. Then judge the G13b and FL1 story texts, as the orchestrator asked on 21 Oct.
3. When Book 2/3 resumes: re-judge F6/F7 code at its new head (judge_400's two should-fix findings), and check F1t's
   new head for F4's port to close judge_308.
