# EDGE2 F8 freeze

Frozen before the discovery run, after an inputs-only check (no trade priced, no participant-OI file read): 305 NIFTY
weekly cycles with an expiry from 21 Feb 2019 to 26 Dec 2024, none without opening quotes, a forward at the open, a
lot or a settlement close.

| What | Value |
|---|---|
| Commit holding the frozen protocol, cards and code | `1f69681c60ffc2bc5a42ddd90b39690654963996` |
| `research/edge2/F8_PROTOCOL.md` SHA-256 | `ca31babb82d54b32ffe285fb1c1fa27abc0b452daf8cfd44ce8e6ff90ac4d631` |
| Study code SHA-256 (`study_f8.code_hash()`: `research/edge2/f8study/*.py` then `study_f8.py`) | `f4fd512ccdd02f7f864b6e280b63782265b6083c11e7c9eddc1e4edd0982a008` |
| Ledger trials | 121-123 (`research/ledger.csv`; 124-126 reserved, unused) |

Discovery measures the spreads alone (both sides) and applies the futility rule; the held-out read (2025-26, the
side filter) needs a lane-1 judge's pass on these frozen rules first.

**Later (25 Oct 2026): the held-out read is WAIVED by the orchestrator** (`F8_RESULTS.md`, "Decision"). Never run
`python research/edge2/study_f8.py heldout`: `f8/discovery.json` names P0W5 and P5W5 as `nominated`, so the command
would open the seal and read participant OI 2025-26, which stays unread.
