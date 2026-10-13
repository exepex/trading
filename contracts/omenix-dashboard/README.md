# Pinned dashboard contract (story P6)

Byte copies of `exepex/omenix-dashboard`'s `api/openapi.yaml`, `api/schemas/*.yaml` and `api/examples/blocks-33-34.json`
at the commit named in `pin.json`, with the contract version and each file's SHA-256. The market read models are
validated against these schemas before they may be published (`fno/market_read_models/contract.py`).

- `python -m fno market contract-check` compares every pinned file with the dashboard's `main`: a difference means a
  new contract to adopt (copy the files, update `pin.json`, rebuild and re-validate), never a silent change.
- A test fails if a pinned file no longer matches its SHA-256 in `pin.json`.
