# ChatGPT reviews

Each review is a separate Markdown file in this directory.

## Naming

`review_<increment>_<filename>.md`

- Start at `review_1_...md`.
- Claim the number before writing the review, in `numbers/chatgpt-review.csv` on `main` (story O12; never "highest
  existing plus one" in your own copy: parallel sessions took the same number several times). On the newest `main`,
  in a separate copy (a worktree, a fresh clone, or GitHub's editor), never your own working checkout, append one row
  `<n>,review_<n>_<filename>.md,<who>,<UTC time YYYY-MM-DDTHH:MM:SSZ>` with the next number, commit only that file
  and push it to `main`. If the push or save is refused, never pull and merge: refresh that copy and take the next
  number (steps in `numbers/README.md`). The number is yours once the push is accepted. Those who can run Python use `python tools/claim_number.py chatgpt-review <filename> --session <id>`.
- Use a descriptive filename for the reviewed document or combined scope.
- Preserve earlier reviews. A follow-up or corrected review gets a new number and links to the earlier review.

## Review contents

Read the repository's root `AGENTS.md` before reviewing. Each review records:

- Date, reviewer, reviewed commit and source documents.
- Verdict, verified findings, agreements and disagreements.
- Confidence labels, evidence, limitations and recommended next steps.
- Proposed parameters clearly distinguished from validated results and approved changes.

Claude can read these files directly from the repository when responding to ChatGPT's findings. A saved review does not itself authorise implementation or real trading.

## Reviews

- [Review 1: 2026-10-12 backtest analysis and strategy proposal](review_1_2026-10-12-backtest-analysis-and-strategy-proposal.md)
- [Review 2: Claude response 1, cost feasibility and revised research plan](review_2_2026-10-12-backtest-analysis-and-strategy-proposal.md)
- [Review 3: independently reproduced response 2 evidence, gap attribution and capacity](review_3_2026-10-12-backtest-analysis-and-strategy-proposal.md)
- [Review 4: response 3 corrections and capacity-screen data requirements](review_4_2026-10-12-backtest-analysis-and-strategy-proposal.md)

- [Review 5: response 4 verified fixes, monthly-expiry selection and destructive download resume](review_5_2026-10-12-backtest-analysis-and-strategy-proposal.md)
- [Review 6: response 5 verified fixes, holiday-shifted weekly contracts and extract consistency](review_6_2026-10-12-backtest-analysis-and-strategy-proposal.md)
- [Review 7: research direction, role accountability and actual progress](review_7_2026-10-12-research-direction-and-status.md)
- [Review 8: owner's data-driven discovery mandate across all expert roles](review_8_2026-10-12-data-driven-multirole-research-mandate.md)
- [Review 9: desk design, expert inference, adaptive policies, costs and decision validation](review_9_2026-10-12-desk-design.md)
- [Review 10: desk design v2 section closure, economics, role scorecards and conditional buying thesis](review_10_2026-10-12-desk-design-v2.md)
- [Review 11: desk design v2.1 sign-off and closure checklist](review_11_2026-10-12-closure-checklist.md)
- [Review 12: implementation plan (28 stories) and Experiment 1 protocol](review_12_2026-10-12-implementation-plan-and-experiment-1.md)
- [Review 13: revised stories and Experiment 1 protocol v2](review_13_2026-10-12-revised-stories-and-experiment-1-v2.md)
- [Review 14: Response 16 closure and Experiment 1 protocol v2.1](review_14_2026-10-12-response-16-closure.md)
- [Review 15: judge A4 quote recorder and B4 ledger guard](review_15_2026-10-12-judge-a4-b4.md)
- [Review 16: A4/B4 blocker re-check — PASS](review_16_2026-10-12-recheck-a4-b4-blockers.md)
- [Review 17: AI plan re-evaluation against legacy behavior](review_17_2026-10-12-ai-plan-reevaluation.md)
- [Review 18: proposed three-paper-strategy design and Response 20](review_18_2026-10-12-three-paper-strategies.md)
- [Review 19: rewritten three-book design Section 12 — AGREED](review_19_2026-10-12-section-12-rewrite.md)
- [Review 20: clean-slate removal design — AGREED WITH CHANGES](review_20_2026-10-12-clean-slate.md)
- [Review 21: clean-slate design v2 re-review — AGREED WITH CHANGES](review_21_2026-10-12-clean-slate-v2.md)
- [Review 22: clean-slate cleanup judge — FAIL](review_22_2026-10-12-cleanup-judge.md)
- [Review 23: clean-slate cleanup re-judge — PASS](review_23_2026-10-12-cleanup-rejudge.md)
- [Review 24: proposed design section 13 — AGREED WITH CHANGES](review_24_2026-10-12-design-section-13.md)
- [Review 25: section 13 revision 2 — AGREED WITH CHANGES](review_25_2026-10-12-section-13-rev2.md)
- [Review 26: full implementation plan — AGREED WITH CHANGES](review_26_2026-10-12-full-implementation-plan.md)
- [Review 27: implementation plan revision 2 — AGREED WITH CHANGES](review_27_2026-10-12-plan-revision-2.md)
- [Review 28: Experiment 1 v2.2, G1 forecast protocol, and thin-slice build order](review_28_2026-10-13-protocols-and-build-order.md)
- [Review 29: Experiment 1 v2.2 holdout disclosure and forecast live inputs](review_29_2026-10-13-protocol-2-2-and-forecast-inputs.md)
- [Review 30: G1 v3 append-only panel extension](review_30_2026-10-14-g1-v3-panel-extension.md)
- [Review 97: design v2 revision 3 — changes required](review_97_design-v2-revision-3.md)
- [Review 98: design v2 revision 4 — APPROVE](review_98_design-v2-revision-4.md)
- [Review 99: G6 forecast protocol v4 — changes required](review_99_g6-protocol-v4.md)
- [Review 100: STR1 one- and two-leg structures](review_100_str1-structures.md)
- [Review 101: G6 v4 revisions 1–5 — changes required](review_101_g6-protocol-v4-revisions.md)
- [Review 102: G6 v4 final narrow re-review — APPROVE](review_102_g6-protocol-v4-final.md)
- [Review 103: C5 risk buckets](review_103_c5-risk-buckets.md)
- [Review 104: E4c entry refusal](review_104_e4c-entry-refusal.md)
- [Review 105: E2b derived packs](review_105_e2b-derived-packs.md)
- [Review 106: M1 weather](review_106_m1-weather.md)
- [Review 107: D3b first timely decision](review_107_d3b-first-timely-decision.md)
- [Review 108: E1b capital top-up](review_108_e1b-topup.md)
- [Review 109: STR1b-1 activation gates (relayed by the owner; ChatGPT's write was blocked)](review_109_str1b-activation-gates.md)
- [Review 111: E1b follow-up on response 140: accept; one docs correction (capital is cutoff-safe, ledger replay of fills is not supported); act on a non-zero top-up result (relayed by the owner)](review_111_e1b-followup.md)
- [Review 110: C5b owner-authorized brake restart](review_110_c5b-restart-decision.md)
- [Review 112: noise, fairness and scorecard](review_112_noise-fairness.md)
- [Review 113: G10 protocol v4 timeline — cutoff integrity change](review_113_g10-v4-timeline.md)
- [Review 114: E5b Book 1 commit failure and recovery — ACCEPT](review_114_e5b-book1-commit.md)
- [Review 115: E2c fills and accounts to Drive — changes required](review_115_e2c-fills-to-drive.md)
- [Review 117: C2c/C2d/A14c whole-margin stress — partial](review_117_c2c-a14c-stress.md)
- [Review 118: RM1 real-money gate — changes required](review_118_rm1-real-money-gate.md)
- [Review 119: protocol v4 freeze checklist — changes required](review_119_v4-freeze.md)
- [Review 116: BR1 breadth-track design — partial](review_116_br1-breadth-design.md)
- [Review 121: BR1a breadth protocol — ACCEPT](review_121_br1a-protocol.md)
- [Review 122: E8 owner-timing fills — CHANGE](review_122_e8-owner-timing-fills.md)
- [Review 123: E4c protective-leg entry check code — ACCEPT](review_123_e4c-entry-check-code.md)
- [Review 120: S3/S6 scoreboards — PARTIAL, changes before freeze](review_120_s3-s6-scoreboards.md)
- [Review 124: F9a role-value scoring — PARTIAL](review_124_f9a-role-value.md)
- [Review 126: E4d shared displayed size — PARTIAL](review_126_e4d-shared-size-code.md)
- [Review 130: D4/D5 envelopes and constitution — PARTIAL](review_130_d4-d5-envelopes.md)
- [Review 127: G11 AI books on v4 — one audit reconciliation change](review_127_g11-ai-books-v4.md)
- [Review 129: R3 first forward shadows — PARTIAL](review_129_r3-forward-shadows.md)
- [Review 131: E6b missed executions in scorecards — PARTIAL](review_131_e6b-missed-executions.md)
- [Review 128: E8 owner-timing fills code part 1 — PARTIAL](review_128_e8-owner-timing-code.md)
- [Review 125: RM2 real-money test record — PARTIAL](review_125_rm2-real-money-record.md)
- [Review 132: R3 shadow accounts code part A — PARTIAL](review_132_r3-code-part-a.md)
- [Review 133: BR1a code and studies — PARTIAL, descriptive only](review_133_br1a-code.md)
- [Review 134: LR3 drift CUSUM — PARTIAL](review_134_lr3-drift-cusum.md)
