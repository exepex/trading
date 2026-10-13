# Independent judge verdicts

Written only by the independent judge session (`docs/JUDGE.md`). One file per verdict:
`judge_<n>_<story>.md`, newest last.


| # | Story | Verdict | File |
|---|---|---|---|
| 1 | E1 paper accounts per book, single-writer lock | PASS (5 minor) | `judge_1_e1_paper_accounts.md` |
| 2 | O5 public-record safety scan | FAIL (3 should fix, 3 minor) | `judge_2_o5_record_scan.md` |
| 3 | X1 Azure PostgreSQL (omenix-dashboard platform/) | FAIL (1 blocking = owner real-server runs pending, 2 should fix, 4 minor) | `judge_3_x1_azure_postgres.md` |
| 4 | O5 public-record safety scan, round 2 (re-judge) | PASS (judge 2 findings all accepted; 4 new minor) | `judge_4_o5_record_scan_rejudge.md` |
| 5 | X1 Azure PostgreSQL, round 2 (re-judge; omenix-dashboard 00c44ed/8ea2757) | FAIL (owner runs pending; 1 should fix: exception 2 understated, large objects in other databases; 1 minor) | `judge_5_x1_azure_postgres_rejudge.md` |
| 6 | C1 cost and tax accountant, three ledgers | FAIL (1 should fix: no test that a non-reconciling ledger fails; 4 minor) | `judge_6_c1_three_ledgers.md` |
| 7 | A5 monthly-expiry identity | FAIL (1 should fix: quote recorder still uses the last-of-month rule, picks the 30 Apr 2025 weekly; 2 minor) | `judge_7_a5_monthly_expiry.md` |
| 8 | A6 events calendar | FAIL (1 should fix: rescheduled meetings unknown before the reschedule; criteria 4 and 5 pending F3 and the challenge run; 3 minor) | `judge_8_a6_events_calendar.md` |
| 9 | X1 Azure PostgreSQL, round 3 (omenix-dashboard 0fa812f) | FAIL for owner action only (judge 5 findings A, B accepted; builder side clean; 2 minor) | `judge_9_x1_azure_postgres_rejudge2.md` |
| 10 | C1 three ledgers, round 2 (re-judge) | PASS (judge 6 findings all accepted; 1 new minor) | `judge_10_c1_three_ledgers_rejudge.md` |
| 11 | A6 events calendar, round 2 (re-judge) | FAIL pending only (judge 8 findings all accepted; criteria 4 and 5 wait on F3 and the challenge run); C1 58323c5 spot-checked | `judge_11_a6_events_calendar_rejudge.md` |
| 12 | A7 recorder uses the session calendar | PASS (4 minor; trigger prompt stale) | `judge_12_a7_session_calendar.md` |
| 13 | A5 monthly expiry, round 2 (re-judge) | PASS (recorder now uses monthly_as_of, verified on real NSE files; judge 7 minors 2-3 accepted as open; 2 new minor) | `judge_13_a5_monthly_expiry_rejudge.md` |
| 14 | A3 NIFTY option-chain panel | FAIL (criteria 1-10 met, 2019 and 2024 rebuilt byte-identical; 1 should fix: futures in scope but not built or rescoped; 6 minor) | `judge_14_a3_nifty_panel.md` |
| 15 | A8 participant open interest | FAIL (parser, coverage code, look-ahead guard and fingerprints verified; 1 should fix: 105 rewritten days used without a flag; Drive coverage and measured rule pending) | `judge_15_a8_participant_oi.md` |
| 16 | A8 participant OI, round 2 (re-judge) | FAIL pending only (judge 15 finding 1 fixed: 105 rewritten days bounded by last write, verified; Drive coverage and measured rule pending; 1 new minor) | `judge_16_a8_participant_oi_rejudge.md` |
| 17 | W10 API contract and data catalog (omenix-dashboard 7aa81a3) | PASS (23 small endpoints, 0 mapping gaps, independence measured per block, 4 own breaks caught, 10 traces; 4 minor) | `judge_17_w10_api_contract.md` |
| 18 | A1 raw NSE archive and calendar | PASS (real coverage run reproduced; independent Drive listing 3,985 files equals it; 10 files hashed; 3 minor) | `judge_18_a1_calendar_coverage.md` |
| 19 | W8 app frame in the real app (omenix-dashboard 068f774) | FAIL (1 should fix: import-graph test misses the @/ alias and re-exports; 346 tests, 147 UI cases, lot 65 verified; 3 minor) | `judge_19_w8_app_frame.md` |
