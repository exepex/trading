# Pinned dashboard contract (story P6)

Byte copies of `exepex/omenix-dashboard`'s `api/openapi.yaml`, `api/schemas/*.yaml` and the examples `api/examples/blocks-33-34.json`, `blocks-32.json`, `blocks.json` and (story P1, the F&O data catalog)
`fno-screens.json`
at the commit named in `pin.json`, with the contract version and each file's SHA-256. The market read models are
validated against these schemas before they may be published (`fno/market_read_models/contract.py`).

- `python -m fno market contract-check` compares every pinned file with the dashboard's `main`: a difference means a
  new contract to adopt (copy the files, update `pin.json`, rebuild and re-validate), never a silent change.
- A test fails if a pinned file no longer matches its SHA-256 in `pin.json`.
- Story P1 (the F&O data catalog: the daily card, the weather, the Forecast lab, the Strategy lab, paper trades):
  `tests/market_read_models/test_p1_data_catalog.py` validates every catalog example with this repository's validator and
  hash, checks that every field the catalog marks as built names a record field that exists here, and validates fixtures
  built from this repository's own records (the trial ledger, a fresh paper account, the 14 Oct 2026 live forecasts).
