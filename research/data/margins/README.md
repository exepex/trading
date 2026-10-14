# Margins (story C2)

Inputs to the risk manager (`fno/risk/margins.py`). Since story A14 (14 Oct 2026) the rows are computed from NSE
Clearing's own beginning-of-day SPAN file (`nsccl.<d>.i1.zip`) and NSE's exposure-margin rule for index options by
`python -m fno margins nse-span` (`fno/nse_margins/`, job `.github/workflows/nse-margins.yml`). Rows can still be
entered by hand from the broker's calculator. The tool never asks for or stores a broker login.

`margins.csv`, one row per structure, wing width and date:

| Column | Meaning |
|---|---|
| `structure` | `SF` short iron fly, `SC` short condor, `BF` long iron fly (`fno/constants.py`) |
| `width` | wing width in NIFTY points, e.g. `100` |
| `margin_per_lot_rs` | initial margin for one lot (SPAN plus exposure), rupees, as the calculator shows it **before** any marked loss |
| `source` | where the figure came from: a computed row is `NSE SPAN <file name> sha256=<SHA-256>` (the file archived in Drive, A9); a hand row names its calculator (e.g. "Groww margin calculator") |
| `as_of` | the day it was read, `YYYY-MM-DD` |

Computed rows (A14): SPAN scanning risk (largest of the 16 scenario losses of the legs' risk arrays) plus exposure
margin (2% of the index's last close per short option; 3% when more than 10% out of the money), per lot of
`lot_sizes.NIFTY`, for SF, SC and BF at widths 300, 250, 200, 150 and 100 on the first monthly expiry 30+ days after
`as_of`, with the ATM strike nearest the file's index close. `as_of` is the session the file is for; a file written at
or after 09:00 IST on that day writes nothing. The file is append-only: a row is never edited or removed, and a second
figure for the same structure, width and day is refused. Broker add-ons (if Groww charges more than NSE) are not in
these rows.

Rules: a trade's margin is the latest row dated on or before the decision day; older than `risk.margins.max_age_days`
(7) or missing means **no trade**. Never the broker's live total for an open short structure: it includes the marked
loss, which available cash already deducts.

Stressed margin (`config.yaml` `risk.stressed_margin`): with `multiplier`, the factor, its source and its date must be
set (no trade otherwise; expires after 30 days). With `scenario_lookup`, a file named in `scenario_file` with columns
`structure, width, scenario, margin_per_lot_rs, source, as_of` needs a fresh row for every configured scenario.

Empty on 13 Oct 2026: until margins (A14's job, or the owner) and the stressed-margin factor exist, every proposal is
refused by `margin_room`.
