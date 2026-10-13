# Margins (story C2)

Inputs to the risk manager (`fno/risk/margins.py`), entered by hand from the broker's margin calculator or NSE's SPAN
parameter files. The tool never calculates a broker margin itself.

`margins.csv`, one row per structure, wing width and date:

| Column | Meaning |
|---|---|
| `structure` | `SF` short iron fly, `SC` short condor, `BF` long iron fly (`fno/constants.py`) |
| `width` | wing width in NIFTY points, e.g. `100` |
| `margin_per_lot_rs` | initial margin for one lot (SPAN plus exposure), rupees, as the calculator shows it **before** any marked loss |
| `source` | where the figure came from (e.g. "Groww margin calculator", "NSE SPAN file nsccl.20261013.s") |
| `as_of` | the day it was read, `YYYY-MM-DD` |

Rules: a trade's margin is the latest row dated on or before the decision day; older than `risk.margins.max_age_days`
(7) or missing means **no trade**. Never the broker's live total for an open short structure: it includes the marked
loss, which available cash already deducts.

Stressed margin (`config.yaml` `risk.stressed_margin`): with `multiplier`, the factor, its source and its date must be
set (no trade otherwise; expires after 30 days). With `scenario_lookup`, a file named in `scenario_file` with columns
`structure, width, scenario, margin_per_lot_rs, source, as_of` needs a fresh row for every configured scenario.

Empty on 13 Oct 2026: until the owner enters margins and the stressed-margin factor, every proposal is refused by
`margin_room`.
