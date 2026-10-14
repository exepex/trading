# Response 74: story A14, margins from NSE automatically (builder's claims)

Date: 14 Oct 2026. From: Claude (builder, session 01FVYzWZtDAZrZLDZ6DtmSYL), for the orchestrator and the judge.
Story: `docs/stories/A-data-foundation.md` A14; issue #89; branch `story/A14-nse-margins`, draft PR #90 (desk decision
14 Oct: no code to main without a judge PASS).

**Status: built; awaiting judge.** The job stays unscheduled (manual only) until the independent check below passes.

## What was built

| Part | File | What it does |
|---|---|---|
| Raw dataset | `fno/storage/raw_source.py` `NseSpanBodSource` | `nse/derivatives/span-bod`: NSE Clearing's beginning-of-day SPAN file `nsccl.<d>.i1.zip`, from 1 Oct 2026; A9 librarian, A11 revisions, coverage, content check (`content_checks.py`) |
| Manifest | `research/data/manifests/span-bod.csv` | SHA-256 of the 9 files 1-14 Oct 2026, from NSE's own bytes (each passed the content check) |
| Reader | `fno/nse_margins/span_file.py` | one pass over the 50 MB XML keeping NIFTY's index, futures, options and definition; refuses a file outside the modelled method |
| Calculator | `fno/nse_margins/calculator.py` | SPAN scanning risk + exposure margin per lot; `ExposureRule` interface, `NseIndexOptionExposure` |
| Rows | `fno/nse_margins/rows.py` | SF, SC, BF at 300-100 with B2's own `Structure` classes, first monthly expiry 30+ days out |
| Log | `fno/nse_margins/margin_log.py` | append-only `margins.csv`: same row again is a no-op, a different row for a key is refused |
| Job | `fno/nse_margins/job.py` | pending sessions (a week back), point-in-time check, one alert listing every problem |
| Composition root | `fno/nse_margins/wiring.py` | Drive's raw area, NSE's rule, B2's structures and widths, `config.yaml`, #fno-desk |
| CLI | `python -m fno margins nse-span [--due-day]` | `fno/nse_margins/cli.py`, registered in `fno/cli.py` |
| Workflow | `.github/workflows/nse-margins.yml` | librarian, revisions sweep, compute, commit; `workflow_dispatch` only (schedule written in its header) |

Nothing in `fno/forecast/`, `fno/ai/`, the forecast capture or C2 (`fno/risk/`) changed. `margins.csv`'s columns and
C2's `MarginTable` are unchanged, so E4's margin path is untouched. No file over 350 lines (largest new: 167).

## The method (strong evidence: NSE's own files, read and recomputed)

- **SPAN.** Each option in the file has a 16-value risk array: the loss of one bought unit under NSE's 16 price and
  volatility scenarios (the two extreme ones already weighted). Sign checked on the real file: a deep in-the-money
  call loses -697.83 (gains) when the price rises a third of its 2,113.14 scan range, delta about 1. A structure's
  loss in a scenario is the sum of side x array over its legs; SPAN margin = the largest loss, never below 0, times the
  lot (65). NIFTY's short-option minimum in the 2026 files is 0 and calendar-spread charges only apply between
  different expiries, so for a one-expiry structure this is the whole SPAN requirement.
- **Exposure.** NSE's daily `ael_DDMMYYYY.csv` lists stocks only (checked 13 Oct). For index options NSE's margins
  page: 2% of notional per short option (underlying's last close x quantity), 3% when more than 10% out of the money,
  5% beyond 9 months, +2% on expiry day; long options none. The last two are refused (no row), not modelled. The `i1`
  file's index price equals NSE's official previous close (22,363.35 on 12 Oct and 22,721.95 on 13 Oct, both checked
  against `ind_close_all_*.csv`), so it is the notional base.
- **Weekly expiry days.** On 13 Oct NSE gave the expiring weekly series its own scan tier. Scan risk is summed per
  tier and our legs are in one expiry, so the figure is that tier's; the calculator refuses an expiry that is not in
  exactly one tier. (My first version refused any file with two tiers; the real 13 Oct file showed that was wrong.)

Real rows for 14 Oct 2026 (`nsccl.20261014.i1.zip`, SHA-256 `d85b883a...e8b5b`, equal to the manifest row; expiry
23 Nov 2026, ATM 22,700, SC strikes 23,200/22,250):

| Width | SF | SC | BF |
|---|---|---|---|
| 100 | 59,899.32 | 61,727.77 | 59,908.42 |
| 200 | 60,769.67 | 64,500.67 | 60,722.22 |
| 300 | 62,679.37 | 67,594.67 | 60,834.67 |

Exposure is 59,077.07 of each (2 short legs x 2% x 22,721.95 x 65); SPAN is 822 to 8,518. **For these hedged
structures the margin is almost all exposure margin**, which does not shrink with the hedge.

## Validation (acceptance criterion 1)

**Pending: the broker check at market hours.** Zerodha's public SPAN calculator (`POST
https://zerodha.com/margin-calculator/SPAN`) returned empty answers at 05:41 and 06:22 IST (its backend serves only in
market hours, I believe; not proven). The orchestrator schedules a 09:25 IST check. NSE's own calculator
(`www.nseindia.com`) answers HTTP 403 from this environment. The job stays manual until a check passes.

What is already checked (not yet the independent figure the story asks for):
- **Second implementation, same file.** `marginism` 0.1.1 (PyPI, an open-source SPAN calculator for NSE files whose
  output mimics a broker basket) on `nsccl.20261014.i1`: **exposure equal to the paisa** for all 15 rows (59,077.07),
  same scenario losses; SPAN differs by exactly the position's premium (SF 100: 6,071.00; SF 300: 17,134.00), because
  it nets the net option value into SPAN (next section).
- **Public anecdotes fit the exposure rule** (some evidence): a NIFTY iron condor at about Rs 30,000 a lot in 2024
  (lot 25: 2 x 2% x ~22,000 x 25 = 22,000 exposure plus SPAN); an Angel One NIFTY put spread at about Rs 56,000 for 75.

Planned check and tolerance: the same legs in the broker calculator against my figure from the newest NSE file the
broker can be using at that time (the `i2` 11:03 file or later; I compute with that file, not `i1`, so prices match).
Tolerance **Rs 50 a lot or 0.1%, whichever is larger**: same file and rule leave only rounding (risk values have 2
decimals, x 65 units x 4 legs = at most Rs 1.30) and the broker's choice of the notional's price; anything larger means
a method difference and the job stays manual.

**One-time check for the owner (Groww), if the automatic one fails:** in the Groww app or web, F&O, NIFTY, expiry
23 Nov 2026 (or the first monthly 30+ days out that day), build a basket: SELL 22700 CE, SELL 22700 PE, BUY 22800 CE,
BUY 22600 PE, 1 lot each (65), as a NRML order; open "margin required" (do not place it). Note SPAN, exposure and
total with the time, and send them with the day's ATM if it moved. I compare them with that day's row (SF, width 100)
recomputed from the latest NSE file at that time.

## Point in time (criterion 3)

A row dated d comes only from `nsccl.<d>.i1`, and only if its own `<created>` stamp is before 09:00 IST on d. In 131
sampled files (Jan-Apr 2020, May-Jun 2024, Sep-Oct 2026) NSE wrote the file between 18:00 and 03:05 IST the evening
before, never after 09:00 on d; 2026's between 20:00 and 24:00. So the job runs in the morning (07:45 IST, retry 08:30)
for today's session; an evening run never races NSE's file. C2 uses the latest row on or before the decision day, so
a decision on d sees no file written after its decision time. Tests: `test_a_file_written_at_or_after_9_am...`
(09:00, 15:32 and next-day stamps write nothing), `test_c2_uses_a_computed_row_from_its_day_on_and_never_before`.

## Fail closed (criterion 4)

Refused with no row and one #fno-desk line naming the cause: missing file, damaged zip, invalid XML, no NIFTY, a
non-zero short-option minimum, an adjustment rate or contract value factor other than 1, a scaled series, no scan
tier, a 15-value risk array, an unreadable value, an expiry in two tiers, no monthly expiry 30+ days out, a Drive read
error. A structure and width with an unlisted leg gets no row and is named. All problems of a run go in one alert.

**Mutation checks (run on the branch, then restored):**
1. Accept a file written up to 2 days late (`created >= deadline + 2 days`): 3 tests fail.
2. Disable the short-option-minimum refusal: 3 tests fail.
3. On an invalid file, write rows from a valid one instead: 2 tests fail.

## Append-only (criterion 5)

Old bytes are a prefix of the new file (test); a second run is a byte-identical no-op with no alert (test); a hand row
with a different figure for the same structure, width and day is refused and nothing is written (test).

## Stressed-margin factor: proposal only (criterion 7; C2 and config unchanged)

Question asked: how much can the margin of a position we already hold rise before we exit? I recomputed the margin
(today's method) of the same legs on every later day's `i1` file from entry to exit (exit = 21 days before expiry),
for every entry day in three windows, SF, SC and BF at widths 100, 200 and 300:

| Window | Entries | Largest rise while held | Where |
|---|---|---|---|
| Sep-Oct 2026 (calm) | 29 | 1.127 | BF 100 |
| May-Jun 2024 (election result 4 Jun) | 32 | **1.407** | BF 300 entered 5 Jun; SC 100 1.347 |
| Jan-Apr 2020 (COVID) | 67 | 1.265 | all structures alike |

Caveats (plain): the 2020 files charged a short-option minimum of 5% of the index per short unit, a different method,
so 2020's margins simply tracked the index (+26.5% from 7 Apr 2020); the windows are hand-picked crises, not a full
history; NSE can also raise its rates by circular in a crisis (as 2020's minimum shows), which no history of today's
rule captures.

**Proposal (some evidence):** set `risk.stressed_margin.multiplier` from the archive by a fixed rule: the largest
held-position rise of any structure and width over every entry day since 1 Jan 2020, rounded up to the next 0.05, with
`source` naming the rule and file range and `as_of` the run day; recomputed monthly by the same job. On today's three
windows that gives **1.45**. This needs the `i1` archive from 2020 (about 1,700 files, 16 GB in Drive; the librarian
can fill it with `--from 2020-01-01`). Until the owner chooses, a hand value of 1.45 with this file as its source is
the evidence-based choice; the owner's answer is needed either way.

## Findings to decide (not changed by me)

1. **What the margin figure should mean for C2 (judge to rule; C2 not changed).** Two ways to state SPAN margin:
   (A) scanning risk alone (what the job writes now), or (B) scanning risk minus net option value, floored at 0 (CME
   style; `marginism`, and probably the broker's basket screen). For 14 Oct, per lot:

   | Row | (A) scan | net option value | (B) | (A)+exposure | (B)+exposure |
   |---|---|---|---|---|---|
   | SF 100 | 822.25 | -6,071.00 | 6,893.25 | 59,899.32 | 65,970.32 |
   | SF 300 | 3,602.30 | -17,134.00 | 20,736.30 | 62,679.37 | 79,813.37 |
   | BF 100 | 831.35 | +6,071.00 | 0.00 | 59,908.42 | 59,077.07 |

   C2's MarginRoom already moves cash and marked equity by the entry and uses min(cash, marked equity). Working it
   through against what a broker leaves free (cash - (B) - exposure): for a credit structure (SF, SC) C2 is exact with
   (A); with (B) it counts the premium twice (too strict by 6,071-17,134 a lot). For the debit BF, C2 is exact with (B)
   and too strict with (A) by 831 a lot. The exact C2 input for every structure is **max(0, scan - NOV) + min(0, NOV)**
   (= A for credits, = B for debits). The README defines the column as "as the calculator shows it", which would be
   (B) if the broker nets the premium. Both errors are on the safe side (never too loose). My recommendation (reasoning
   plus the arithmetic above): store the exact C2 input, and name the definition in the README; the broker check
   tells us which figure the broker shows, so the validation compares like with like.
2. **The margin is almost all exposure.** For every row, 59,077 of 59,899-67,595 is exposure on the two short legs,
   which a hedge does not reduce. Risk manager's view: a Rs 5 lakh book can hold about 6 such lots at stressed 1.45 x
   62,000 = 90,000 each, before cash for losses; C2's 3-trade cap binds first.
3. **The `i1` file is not always out by evening.** 41 of 131 sampled files were written after 22:00 IST, some after
   midnight; the job runs in the morning (07:45, retry 08:30), never racing NSE.
4. **The manifest guard asked for a year of rows** (250); a dataset that begins on 1 Oct cannot have them. I changed the
   test to require every session from the first day instead, for forward-only datasets only, and say so here.

## Groww as a margin source (orchestrator's (a)-(e); public docs only, read 14 Oct 2026, no login, no key)

Pages: https://groww.in/trade-api/docs, .../python-sdk, .../python-sdk/margin, .../curl, .../curl/margin,
.../curl/orders, .../python-sdk/exceptions, both changelogs, https://groww.in/trade-api, https://groww.in/pricing. No
doc page shows an update date; the SDK changelog runs to 1.5.0 (3 Dec 2025).

- **(a) Margin before an order: yes, for F&O baskets.** `POST https://api.groww.in/v1/margins/detail/orders` (SDK
  `get_order_margin_details(segment=..., orders=[...])`): "for a single order or basket of orders"; "Basket orders are
  only supported for FNO Segment". It returns `span_required` and `exposure_required` separately, plus
  `option_buy_premium` and `total_requirement`. The docs do not say whether a basket gets the hedge benefit or a
  per-leg breakdown. Added in SDK 0.0.3 (25 Mar 2025).
- **(b) Read-only key: not documented.** No scopes or read-only option on any public page; only
  `GrowwAPIAuthorisationException` for "issues with the API key or access permissions". The key pages need a login.
  So no evidence that a key can be made unable to place orders: under our rule ("no broker key in GitHub"), Groww stays
  a validation source, not the daily feed.
- **(c) Auth and expiry.** Access token "Expires daily at 6:00 AM"; or API key + secret ("Requires daily approval on
  Groww Cloud Api Keys Page") with a SHA-256 checksum; or API key + TOTP code. The SDK page calls the TOTP flow "No
  Expiry", the cURL page says it "Requires daily approval": the docs contradict each other.
- **(d) Static IP: not mentioned** anywhere in the public docs (no SEBI retail-algo, IP whitelisting or algo-ID text),
  so whether margin calls work from any IP is not documented. Unknown, not "no".
- **(e) Unattended session: not documented.** No refresh token. The only route that looks headless needs the TOTP
  seed stored on the server (the docs build the code with `pyotp.TOTP(secret)`), which is a credential that can trade.
- Price: Rs 499 + taxes a month ("early bird", Rs 2,000 struck through); rate limit for non-trading calls 20/s, 500/min.

Conclusion (strong evidence for (a), absence of evidence for (b), (d), (e)): Groww's margin endpoint would be the best
independent check because it is the owner's own broker, but using it means a trading-capable key. Use it, if at all,
by the owner by hand (the one-time check above), not from a job.

## Tests

47 new tests in `tests/nse_margins/`; `tests/test_librarian.py` names the new librarian dataset; the manifest guard in
`tests/test_fingerprints.py` accepts a forward-only dataset when every session from its first day to 14 Oct has a row
(it asked for 250 rows, a year of history, which a dataset begun on 1 Oct cannot have). Full suite 2,147 passed (47 A14 tests); ruff and
`tools/check_imports.py` clean.
