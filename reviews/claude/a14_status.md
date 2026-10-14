# A14 status (builder session 01FVYzWZtDAZrZLDZ6DtmSYL)

Updated: 14 Oct 2026, about 08:07 IST. Branch `story/A14-nse-margins`, draft PR #90, issue #89.

**Ready for judge** at code tip `e2e4de9` (main merged at 513b2d6; this status file is the only later commit).
Full suite 2,336 passed on the merged tree; ruff and `tools/check_imports.py` clean.

Judge 75 implemented (claims `reviews/claude/response_77_a14-nse-margins.md`, findings 1, 5, 6, 7):
1. `margins.csv` stores `scan_per_lot_rs`, `nov_per_lot_rs`, `exposure_per_lot_rs` apart; no netted figure.
2. C2 counts `max(0, scan - NOV) + min(0, NOV) + exposure` (`MarginParts.initial`).
3. Stressed: `max(0, k x scan - NOV) + min(0, NOV) + exposure`, k from config (exposure not stressed; 1.45 only a
   proposal).
4. Test with an open losing trade: it first FAILED. C2 left Rs 6,071 more free than a broker when a debit trade (BF) is
   proposed while a credit trade is open, because `min(cash, marked equity)` nets one trade's value against another's
   liability. Fixed in `fno/risk/rules.py` MarginRoom: also never above cash + entry cash flow + each trade's own
   liability (only ever stricter). Now equal to the broker to the paisa in 8 cases. **This goes beyond the ruling:
   judge to confirm.**
5. A total not above 0, or a negative scan or exposure, is refused by name.
6. Claims file is response_77.

For E4: `MarginTable` and `StressedMargin` signatures unchanged; the margins file's columns changed. On this branch
I updated E4's fixtures in `tests/desk/test_entries.py` and `tests/desk/test_entry_limit.py` (same figures). MarginRoom
now needs a quote for every open trade's legs (the stress rule already does).

Broker check done early (Zerodha answered from 08:05 IST; claims "Validation"):
- SPAN: PASS. Zerodha's SPAN = max(0, my scan - NOV) within Rs 0.70 on all 9 rows; its NOV equals mine to the paisa.
  The broker displays the netted figure (B).
- Exposure: FAIL by 5.6%. Zerodha charges 2% (3% deep OTM) on a base of 23,997.35, not NSE's 22,721.95 close;
  unexplained from public data. Mine is Rs 3,316 a lot lower. The workflow stays manual. Needed: the owner's one-time
  Groww check (claims) to see which base Groww uses; or the orchestrator's 09:25 re-run may show a different base.

Not merged into main.
