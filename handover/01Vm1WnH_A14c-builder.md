# Handover: A14c builder (session 01Vm1WnH8i9waM8EJG8zwWqg), 21 Oct 2026

## (a) Identity
Builder of story A14c (the stress factor k from NSE's archived SPAN files, and part 2, the daily read-only Groww
margin check). Branches and heads (all pushed):
- `story/a14c-families` 0082b931 (code tree 1f9db55f was the one gated and sent to judge D)
- `story/a14c-part2-broker-check` ebce3593 (code tree 3dc0ab9b gated)
- `story/a14c-stress-recompute` c73fd5f5 (part 1, merged earlier; branch kept)

## (b) Merged to main
A14c part 1 (global k, applied 2.1 on 16 Oct), the A14 cron catch-up (a89c621b), the calendar audit (response 239),
the k = 2.1 decomposition (response 252). Weekly run of Sun 18 Oct worked: incremental, 2.1 carried (1986afbf).

## (c) Done, not merged
- **Families code** (one k per family, debit and credit): text PASS judge 290; code with judge D, response 281
  (round 2 = the 21 Oct fixes). Gates on 1f9db55f: 8159 passed. The 2 failures were main's own and are fixed on main
  since.
- **Part 2 code**: text and allow-list PASS (judges 291 add. 2, 356 add. 1); code with judge D, response 291. Gates on
  3dc0ab9b: 8209 passed, 0 failed.

## (d) In progress
Nothing uncommitted. Waiting for judge D on both. On a PASS: merge main in, run the full gates on the exact tree,
then push to main (merge-race rule in CLAUDE.md and DESK_DECISIONS).

## (e) Reviews
Self-reviews by independent agents on both branches; every finding fixed or answered in responses 281 and 291.

## (f) Open questions and agreements
- Orchestrator: which DESK_DECISIONS commit approves the per-family fall below 2.1, before the approved full run
  (dispatch stress-factor.yml with full=true and approve_fall=<that commit>).
- Owner: `daily.live_from.margin_check` (first live day of the broker check).
- O1 builder (session_014zYLf18PgCzR7YoHs1X5Dp): reviewing the `fno/daily/wiring.py` change (margin_check commits
  `receipts/data/margins/broker_checks/`).
- Judge F asked for the account check (0 orders, positions, used margin) again after the first live day.

## (g) Risks a successor must not miss
- After families merges, the next Sunday run is FULL (no family has its own measured row yet): about 2-2.5 hours,
  inside the 330-minute limit. Any family result below 2.1 is HELD (C2 keeps 2.1) until the approved dispatch.
- Main's per-family k is unknown until that run; BF (debit) planted runs give about 1.0, so expect a large debit fall.
- The broker check's tolerances are some evidence only (one basket on 16 Oct, 15 baskets on the evening of 21 Oct).
- NSE's 2027 holiday circular is not out; add its rows to `research/data/calendar/nse_sessions.csv` when published, or
  the calendar stops runs that need 2027 dates.

## (h) First three actions for a successor
1. Read judge D's verdicts on `story/a14c-families` and `story/a14c-part2-broker-check`; fix any FAIL on its branch.
2. On each PASS: `git merge origin/main`, full gates, push to main; mark the register rows done.
3. After families merges: get the approving commit from the orchestrator, dispatch the full run, and report each
   family's k and the holding that sets it.
