# Response 279: story C5d, NSE contract IDs in C5's bucket map (claims for judge D)

Builder 012eM7Ti, 16 Oct 2026. Branch `story/c5d-nse-symbols`. Lane 1: it touches what decides a trade (C2's and C4's
bucket caps) and a line of the S1 protocol draft.

## The bug (strong evidence: reproduced)

The O11 replay found it, and the O1 builder traced it (`fno/composition.py:94-99`). The desk's captures take
`quotes.provider: auto`: Groww when its credentials are set, else NSE's public option chain. NSE's contract IDs read
`OPTIDXNIFTY13-10-2026CE21950.00` (real, in `tests/fixtures/nse_nifty_chain.json`). C2's and C4's rule ("the
letters before the first digit") turned that into the underlying `OPTIDXNIFTY`.

On the old code, C2 says `RiskInputError: unmapped bucket: underlying 'OPTIDXNIFTY' is not one of ('NIFTY',
'BANKNIFTY')`. C4 fails its caps the same way. So on any day the routine loses Groww's settings, every trade is
refused.

## The fix (root cause: one symbol rule, two formats)

- **New `fno/contract_symbols.py`:** `underlying_of(symbol)` drops NSE's instrument code first (`OPTIDX`, `OPTSTK`,
  `FUTIDX`, `FUTSTK`), then takes the letters before the first digit. Groww's symbols have no code and read as before.
  The codes are NSE's own, the keys of `fno/fo_bhavcopy.py`'s `LEGACY_INSTRUMENTS`, so they are not typed twice.
- **One copy of the rule.** C2 (`fno/risk/buckets.py`) and C4 (`fno/checks/validity_caps.py`) both import it. Each had
  its own copy before. C4 still imports nothing from `fno.risk`: the rule is the symbol format's, not C2's arithmetic
  (judge 83).
- **`research/evaluation/PROTOCOL.md`:** the "Score-time computation" bullet of `frozen_files` adds
  `fno/contract_symbols.py`. `tests/evaluation/test_scoring_closure.py` requires it, because `buckets.py` is hashed and
  now imports it. The protocol is a draft, not frozen. I have asked the S1 text owner (0185gR5D) to agree the line.

## Tests (`tests/risk/test_contract_symbols.py`)

- **Real NSE IDs:** every identifier in NSE's real option-chain fixture reads as NIFTY.
- **Both formats:** NSE (index and stock options) and Groww (NIFTY, BANKNIFTY, `M&M`) give the right underlying.
- **C5 (C2):** a fly on NSE IDs is bucketed NIFTY/short-volatility. A position with one leg from each provider is
  still one underlying.
- **C4:** its own `buckets_of` buckets the NSE fly the same way.
- **Mutation:** removing the instrument-code step fails 6 of the new tests.
- The existing bucket and C4 cap tests pass unchanged.

**Gates:**
- pytest: 7,788 passed;
- ruff check and format clean;
- `check_imports` clean;
- every file under 350 lines.

**Not in this change:**
- An end-to-end run on an NSE day is O2's NSE row (orchestrator).
- Whether the refusal's reason reached the owner is O1's alert path.
- A stock or an index whose name holds a digit (e.g. `NIFTYNXT50`) still reads only its letters before the first
  digit. 6.2 maps neither, so such a position is refused, which is the fail-closed rule, as before.
