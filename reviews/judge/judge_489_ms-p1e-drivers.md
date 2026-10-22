# Judge 489: MS-P1e, rule drivers and controls

**Scope:** story/ms-p1-drivers at 1acd1761 (builder session_01KidCrUZReQUeSnJ3xV9ZGF). The diff is
756e6545..1acd1761, `fno/school/drivers/`, `research/school/cards/` and `tests/school/drivers/` only. It carries a's
PASSed round-2 code (35458460, 19eb4206). Lane 1 (decides trades). Round 1 of 2, after early findings that I sent on
a496e135. Judge J (session_01Qg4Gxun1NvGRrtS9C68Dc1).

**Verdict: PASS.** No blocking and no should-fix findings; 2 minor.

## Criteria
| # | Criterion | Result | Evidence |
|---|---|---|---|
| 1 | Priced at the fill touch, kept only if max loss <= Rs 10,000 | MET | `proposals._at_touch`: ask to buy, bid to sell, C2's `max_loss` with the pad, `> cap` refused. Test at exactly the cap (kept) and 1 paisa under (narrower). Plants: 5% tolerance, `>=`, bid to buy, mid, payoff bounds: all caught |
| 2 | Exits through E4's `ExitRule` classes | MET | `ProfitTarget`, `StopLoss` and `ExitOnDay` from `fno/desk/exit_rules.py`; DR1's mean rule is wrapped as `ExitOnDay`. The close value is checked by hand (short bought back at the ask, long sold at the bid). 10 exit plants caught, including the close side, which had survived on a496e135 |
| 3 | RC1 seeded deterministically | MET | `random.Random(SHA-256(session, driver id, road))`; session, driver, road and unseeded plants caught; twin exits pinned (PS4 monthly, WS1 weekly, CS1, DR1, DB1) |
| 4 | Each family fires at its threshold; 19 vs 20 sessions; no look-ahead | MET | CS1, DR1, DB1 (now incl. exact equality), WS1 and PS window plants caught; `p.session < session` plant caught |
| 5 | PS5 and KL1 measurement-only, EDGE1's parameters | MET | `role: measurement_only`, no ranking estimate. Widths, offset, TP50 and T21 are tested against `research/edge1/edge1study`. Entry at the slot, not the next day: an accepted, stated departure |
| 6 | `expected_net_rs` is 0 with its reason | MET | all 7 ranked cards carry 0.0 with "EDGE1 found no edge"; the score is `expected_net_rs / max_loss`, tested with 500 and 0. See minor 1 |
| 7 | CalendarError handling | MET | exits: an unknowable day is not reached, while price and expiry rules still fire. Entry: WS1, DB1, PS5 and KL1 give `no_expiry_in_window`. Each path now has a test, and my plants on them are caught |
| 8 | PS3/PS4 collapse noted | MET | in the PS3 and PS4 cards and the Claims (orchestrator, 22 Oct: one family, not counted twice); wings 1, 3 and widest are pinned |
| 9 | 350 lines and DRY | MET | largest code file 100 lines, largest test 231. `session_days` now uses `TradingDays.next_after` and `last_on_or_before`; only `previous_session` and `sessions_between`, which `TradingDays` lacks, stay |
| - | Gates (my run) | MET | pytest -n auto: 10,444 passed, 16 xfailed. ruff check and format, `check_imports` and `check_records` are clean |

## Minor (no round needed)
1. No test pins the cards' `expected_net_rs` at 0.0. CS1's set to 500 passes every test. h freezes the card bytes,
   but until then a draft edit would silently reorder the 5-trade ranking. Add one test that every ranked card holds
   0.0.
2. The `no_valid_quotes` reason for a missing straddle is tested on PS4 only. Reverting it to
   `no_structure_under_cap` in RC1, CS1 or DB1 survives. The outcome stays `no_trade`; only the reason label in the
   counts would change.

## Plants
56 planted on 1acd1761, 52 caught:
- my 50 from round 1: 49 caught (14 had survived on a496e135);
- 6 on the round-2 code: 3 caught.

The 4 survivors are minors 1 and 2.

## Notes
- REF and RC1 hold no position limit, so C2's Rs 30,000 bucket will refuse most later REF entries. Those become
  `account_limit` tickets, which is a j requirement (orchestrator's ruling).
- "Loss 2x credit" is read as a net loss of 2x the credit. The card is a draft; h should confirm this reading when it
  freezes the cards.
