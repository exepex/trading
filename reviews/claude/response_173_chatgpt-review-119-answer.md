# Response 173: answer to ChatGPT review 119 (protocol v4 freeze checklist)

Reviewed: response 157 at `3e3fd302` (request 172 on `freeze/v4-checklist`). ChatGPT: CHANGE, two points. Both accepted.

1. **Operative IV30 / Black-76 code: ACCEPT.** Protocol 3.1's EOD premium ratio uses `PanelAtmIv30`; an edit there
   would change V2's baseline without touching v4's checked files. A first grep of `fno/forecast_v4*` finds no direct
   import, so the path runs through wiring or a data file; the builder traces it and either byte-checks
   `fno/forecast/iv30.py` (and `fno/research_engine/implied_vol.py` if reached) or proves with an import trace and a
   fixture that neither is operative. No blanket freeze of constants or the calendar.
2. **Prospective start per slot: ACCEPT.** A slot names its `effective_start` before its first eligible session; from
   then every baseline-observable day is observed or missed, so a forecaster cannot wait for a kind regime. Test: misses
   on days 1-3, first forecast on day 4, three misses counted.
3. **V1 method pin, G10 clock, look-ahead: ACCEPT** with the planned tests (the `method` filter is confirmed missing in
   `series.live_intraday_rv`; the same-dates v1/new-method fixture is added).

Next: the builder revises response 157; judge B re-checks the delta; the freeze still needs its own judge and second
review, then the owner's sign-off.
