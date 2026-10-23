# Margins (story C2)

Inputs to the risk manager (`fno/risk/margins.py`). Since story A14 (14 Oct 2026) the rows are computed from NSE
Clearing's own beginning-of-day SPAN file (`nsccl.<d>.i1.zip`) and NSE's exposure-margin rule for index options by
`python -m fno margins nse-span` (`fno/nse_margins/`, job `.github/workflows/nse-margins.yml`). A hand row
needs the same three parts (a broker screen shows SPAN and exposure; the net option value is the legs' value). The tool never asks for or stores a broker login.

**Since story O9b step 2, the margins table and each run's `stress_evidence_<day>.csv` are in Drive, not in this
folder.** The table is write-once parts in Drive's `data/margins/margins/`, and the evidence is one snapshot per run
day in `data/margins/stress-evidence/<day>/`. Each file has its SHA-256 receipt under `receipts/data/margins/`. C2, C4
and A14 read the table through the verified cache (`config.yaml` `risk.margins.table`); if Drive cannot give it, no
trade (fail closed). These stay here: `stress_factor.csv` (a risk decision record), the `stress/stress_files_<day>.csv`
lists (file names with SHA-256) and the `stress/stress_evidence_<day>.md` write-ups. A factor row's `evidence_sha256`
equals its evidence receipt's SHA-256. The table keeps its name and columns:

`margins.csv`, one row per structure, wing width and date:

| Column | Meaning |
|---|---|
| `structure` | `SF` short iron fly, `SC` short condor, `BF` long iron fly (`fno/constants.py`) |
| `width` | wing width in NIFTY points, e.g. `100` |
| `scan_per_lot_rs` | SPAN scanning risk for one lot, rupees (never below 0) |
| `nov_per_lot_rs` | net option value for one lot: the legs' value at the prices used, bought legs plus (a credit structure's is negative) |
| `exposure_per_lot_rs` | exposure (extreme-loss) margin for one lot, rupees |
| `source` | where the figure came from: a computed row is `NSE SPAN <file name> sha256=<SHA-256>` (the file archived in Drive, A9); a hand row names its calculator (e.g. "Groww margin calculator") |
| `as_of` | the day it was read, `YYYY-MM-DD` |

The three parts are stored apart, never one netted figure (judge 75). C2 counts
`max(0, scan - NOV) + min(0, NOV) + exposure` per lot: scan plus exposure for a credit structure, its SPAN net of the
premium paid plus exposure for a debit one, which with MarginRoom's cash arithmetic leaves exactly what a broker that
nets the premium leaves free. A total not above 0 is refused by name.

Computed rows are written only after an independent broker check of the job's figures passed (judge 77, option a):
`config.yaml` `risk.margins.nse_span_check` must hold that check's `source` and `passed_on`. Until then a run prints
its rows and writes none. Set on 14 Oct 2026 from Groww's read-only margin API (SPAN equal to the rupee, exposure equal
on the same index base; claims response 77), subject to the judge.

Computed rows (A14): SPAN scanning risk (largest of the 16 scenario losses of the legs' risk arrays), the legs' value
at the file's prices (the previous session's settlement prices), and exposure margin (2% of the index's last close per
short option; 3% when more than 10% out of the money), per lot of
`lot_sizes.NIFTY`, for SF, SC and BF at widths 300, 250, 200, 150 and 100 on the first monthly expiry 30+ days after
`as_of`, with the ATM strike nearest the file's index close. `as_of` is the session the file is for; a file written at
or after 09:00 IST on that day writes nothing. The file is append-only: a row is never edited or removed, and a second
figure for the same structure, width and day is refused. Broker add-ons (if Groww charges more than NSE) are not in
these rows.

Rules: a trade's margin is the latest row dated on or before the decision day; older than `risk.margins.max_age_days`
(7) or missing means **no trade**. Never the broker's live total for an open short structure: it includes the marked
loss, which available cash already deducts.

Stressed margin (`config.yaml` `risk.stressed_margin`): with `multiplier`, k stresses the scan and the exposure, never
the premium (story C2c): `max(0, k x scan - NOV) + min(0, NOV) + k x exposure`. k is never in config (story C2d): it is
the `factor` of the latest row of `factor_file` dated strictly before the decision day (no trade otherwise; a row
expires after `max_age_days`, 30). With `scenario_lookup`, a file named in `scenario_file` with columns
`structure, width, scenario, margin_per_lot_rs, source, as_of` needs a fresh row for every configured scenario.

`stress_factor.csv` (stories C2d and A14c): `as_of, factor, computed, unrounded, status, peak, coverage_through,
evidence_sha256`, append-only, never edited. A14c's weekly job appends one row (`status` `applied`, or `held` when a
lower result waits for the owner; `factor` is always the one in force). Dates are `YYYY-MM-DD` only; of two rows with
the same date the later one wins (a correction); any unreadable row refuses every trade by name. The first row is the
owner's 1.45 of 14 Oct 2026 (response 77), with no measured value.

Empty on 13 Oct 2026: until margins (A14's job, or the owner) and the stressed-margin factor exist, every proposal is
refused by `margin_room`.
