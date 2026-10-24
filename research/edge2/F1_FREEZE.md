# EDGE2 F1 freeze

Frozen before the discovery run, after the inputs-only check (no trade priced): `python research/edge2/study.py
inputs` gave 702 tradeable cycles (NIFTY 398, BANKNIFTY 304), 4 skipped (`moved_expiry`, 2 an index), 160
expiry-future settlement checks, 0 disagreeing.

| What | Value |
|---|---|
| Commit holding the frozen protocol, cards and code | `47c01637cf7f19acdb8501900b816ab5874ffdff` |
| `research/edge2/F1_PROTOCOL.md` SHA-256 | `2105e3638d0c67f45f345ced2f72410490b7d074fe023f9b9e1b444c90ead1bf` |
| Study code SHA-256 (`study.code_hash()`: `research/edge2/f1study/*.py` then `study.py`) | `9cbe34ce270deb560a73e6375ee6b976401a9a44347e80216a58e8c16a1becea` |
| Ledger trials | 109-114 (`research/ledger.csv`) |

The discovery run's JSON records its head commit and code SHA-256; a run whose code hash differs from the one above is
not F1's run. Any later change to the protocol or code is a stated deviation (protocol section 11) or a new variant.
