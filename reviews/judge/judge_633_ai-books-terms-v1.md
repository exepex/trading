# Judge 633: the AI books' terms v1, Book 2's envelope and Book 3's constitution (story/ai-books-terms-v1 @ 7d44b51e2)

**PASS (2 minor, 1 note). Lane 1** (what a book may trade). Judge F, own session (session_01A8XfbTUVgeeEpqatHaWbtP).
Labels: strong, some, reasoning only.

## Criteria

| # | Check | Result | My evidence |
|---|---|---|---|
| 1 | Envelope = the 16 Oct terms and Q9 | MET | `b0-monthly-sc-v1.yaml`: follow_rule, choose_strategy, no_trade, choose_width, reduce_lots, all `allowed`, nothing else; DESK_DECISIONS 229 (5) "envelope v1 narrow" and 345 (2) Q9, word for word |
| 2 | Constitution = the 16 Oct terms and Q10 | MET | `constitution-v1.yaml`: NIFTY, monthly, structures BF CCS CDS LC LP PCS PDS SC SF (= C4's nine defined-risk codes, `STRUCTURES` + `STRUCTURES_ONE_SIDE`), `max_holding_days: 21`; rows 229 (1)-(3) and 345 (3). The Rs 10,000 cap is by reference: `risk: risk.profiles.books`, whose `max_loss_per_trade_rs: 10000` (`config.yaml:57`); D5 refuses a number in its place |
| 3 | They parse with D4's and D5's own parsers | MET | `parse_envelope` → `('b0-monthly-sc', 1)`, five `allowed`; `parse_constitution` → v1, the nine codes, 21; `ConstitutionFiles.by_sha256` and `EnvelopeFiles` accept the file names |
| 4 | Inert until registered in D6 | MET | C4's Book 3 mode takes the constitution only by the D6-registered SHA-256 and fails closed otherwise (`validity_constitution.py:34-40`); Book 2's `EnvelopeMode` is wired with the same `RegisteredComponents` (`checks/wiring.py:88-97`); this branch registers nothing (two files only) |
| 5 | The playbook named is a registered candidate (Q11) | MET | `playbook/registry.csv`: `b0-monthly-sc,1,...,research`, the only registered playbook |
| gates | | MET | trial merge with main 28035ce00 (clean): **16,543 passed, 1 skipped, 14 xfailed** (token kept); ruff, format, `check_imports`, `check_records` (9,276 files) clean |

## Minor

1. **The registration must pin exactly these bytes.** Edits that still parse but break the owner's terms (14 days
   instead of 21; `choose_width: forbidden`) pass all 1,578 tests that touch books, envelopes and playbooks. That is
   by design: D6's SHA-256 is the lock. So the D6 registration commit must name exactly
   `constitution` = `6d54094c32ae9737adf8c81433dc85b47cc7fb9562fb9aaa542c9a8c05d071c5` and
   `trade_envelope:b0-monthly-sc-v1` = `dfdc5a5447918aad710749b978b529f4f9e9924b3136d8141e160741c6323b7a`, and its judge
   checks those hashes against this verdict.
2. No story text or Claims for these two files (quality rules 1-6). They are data the owner approved, validated by
   D4's and D5's judged parsers, and broken edits are caught (my plants: a 22-day limit and an unknown status each fail
   a test). Accepted for two approved data files; put a line in D's story when it is next touched.

## Note (risk manager and red team, not a finding)

`b0-monthly-sc` is a measurement shadow. Its own file says P1 lost Rs 34,486 over 60 opportunities in 2019-23 and
"can never show an edge" [strong: research/2026-10-12-experiment-1/RESULTS.md]. Under Q11 Book 2 may now paper-trade
it, labelled "strategy not yet passed", with D2's one-open-trade limit. That is the owner's decision. Expect Book 2's
paper results on this envelope to be negative, and do not read them as evidence for or against the AI.

## Plants

4 planted on the merged tree: **2 caught** (a 22-day constitution; an unknown envelope status), **2 survived by
design** (a 14-day constitution; `choose_width: forbidden`), which D6's hash lock covers (minor 1).
