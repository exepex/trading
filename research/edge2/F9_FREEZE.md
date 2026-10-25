# EDGE2 F9 freeze

Frozen before the discovery run, after an inputs-only check (no trade priced): `python research/edge2/study_f9.py
inputs` read 1,930 sessions (2019 - 23 Oct 2026, regular and special): 56 of the 58 scheduled events qualify (46 RBI,
8 Budget, 2 election results); the 2021 and 2022 Budgets are left out by the point-in-time rule (A6's official
announcement dates, 30 and 31 Jan, are not before their entry sessions; stated, not changed). 110 of 112 event setups
are buildable (the 2 others are the 4 Dec 2026 RBI meeting, still ahead); 1,656 ordinary control days.

| What | Value |
|---|---|
| Commit holding the frozen protocol, cards, event list and code | `80fdcd3428d3510831e22472c349d3ed033886a2` |
| `research/edge2/F9_PROTOCOL.md` SHA-256 | `9536e524791188bfe1ee08103c194aa271e3b5199dd6db47a51b5e66daa03aa1` |
| Study code SHA-256 (`study_f9.code_hash()`: `f9study/*.py`, `study_f9.py`, `f9_events.csv`) | `a255a04c540cae2d2c3585c14b8b20540f6109191d4e3a234a4dae4d30e804a4` |
| Ledger trials | 124-127 (`research/ledger.csv`; 128-132 released) |

The held-out read (FINNIFTY and MIDCPNIFTY monthlies) is not built; it needs a nomination, a lane-1 judge's pass and
`research/edge2/LOT_CHECK.md` first.
