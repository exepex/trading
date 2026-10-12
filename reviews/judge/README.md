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
