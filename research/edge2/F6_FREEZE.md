# EDGE2 F6 freeze

Frozen before the discovery run, after the inputs-only check (no trade priced): `python research/edge2/study_f6.py
inputs` read 1,478 regular sessions (2019-2024): 0 without a readable participant-OI file, 1 without NIFTY futures
prices. Research only: futures are on hold (owner, 25 Oct 2026).

| What | Value |
|---|---|
| Commit holding the frozen protocol, cards and code | `026652848f7dd3d95aee9068d9c8345e9169cbac` |
| `research/edge2/F6_PROTOCOL.md` SHA-256 | `3c3ac99b47b86f299f828fa1a7167ddc5354dcbb9bafe68d4cc31ac718704403` |
| Study code SHA-256 (`study_f6.code_hash()`: `research/edge2/f6study/*.py` then `study_f6.py`) | `48250512eff73dfc371f9253f0369d9afc2844395b5c21f39bc9f5932f0201d5` |
| Ledger trials | 115-120 (`research/ledger.csv`) |

The discovery run's JSON records its head commit and code SHA-256; a run whose code hash differs is not F6's run. The
held-out read (2025-26) needs a lane-1 judge's pass on these frozen rules first (orchestrator, 25 Oct 2026).
