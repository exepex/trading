# Response 77: story A14, margins from NSE automatically (builder's claims)

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

Nothing in `fno/forecast/`, `fno/ai/` or the forecast capture changed. C2 changed only as judge 75 and the
orchestrator directed (`fno/risk/margins.py`: the three parts and the two formulas) plus one fix the ruling's test
exposed (`fno/risk/rules.py` MarginRoom, finding 5); its interfaces are unchanged (finding 6). No file over 350 lines
(largest new: 167).

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
23 Nov 2026, ATM 22,700, SC strikes 23,200/22,250), per lot, with what C2 counts (judge 75) and the stressed figure at
the proposed k = 1.45:

| Row | Scan | NOV | Exposure | C2 counts | Stressed, k 1.45 |
|---|---|---|---|---|---|
| SF 100 | 822.25 | -6,071.00 | 59,077.07 | 59,899.32 | 60,269.33 |
| SF 200 | 1,692.60 | -12,350.00 | 59,077.07 | 60,769.67 | 61,531.34 |
| SF 300 | 3,602.30 | -17,134.00 | 59,077.07 | 62,679.37 | 64,300.40 |
| SC 100 | 2,650.70 | -3,786.25 | 59,077.07 | 61,727.77 | 62,920.58 |
| SC 200 | 5,423.60 | -7,072.00 | 59,077.07 | 64,500.67 | 66,941.29 |
| SC 300 | 8,517.60 | -10,153.00 | 59,077.07 | 67,594.67 | 71,427.59 |
| BF 100 | 831.35 | 6,071.00 | 59,077.07 | 59,077.07 | 59,077.07 |
| BF 200 | 1,645.15 | 12,350.00 | 59,077.07 | 59,077.07 | 59,077.07 |
| BF 300 | 1,757.60 | 17,134.00 | 59,077.07 | 59,077.07 | 59,077.07 |

Exposure is 59,077.07 of each (2 short legs x 2% x 22,721.95 x 65). **For these hedged structures the margin is almost
all exposure margin**, which does not shrink with the hedge. NOV here is at the file's prices (the previous session's
settlement prices); C2's MarginRoom marks the proposal at today's mids, so the two differ by a day's move (finding 5).

## Validation (acceptance criterion 1)

**Result (14 Oct 2026, 08:05-08:10 IST, Zerodha's public SPAN calculator, `POST
https://zerodha.com/margin-calculator/SPAN`, no login): SPAN and NOV pass exactly; exposure FAILS by 5.6%. Not
passed: the job stays manual.** (It answered from about 08:05 IST; empty at 05:41 and 06:22.) Same legs (NIFTY26NOV,
65 each), my figures from `nsccl.20261014.i1`:

| Row | My scan | My NOV | max(0, scan - NOV) | Zerodha SPAN | Zerodha NOV | My exposure | Zerodha exposure |
|---|---|---|---|---|---|---|---|
| SF 100 | 822.25 | -6,071.00 | 6,893.25 | 6,893 | 6,071 | 59,077.07 | 62,393.11 |
| SF 200 | 1,692.60 | -12,350.00 | 14,042.60 | 14,043 | 12,350 | 59,077.07 | 62,393.11 |
| SF 300 | 3,602.30 | -17,134.00 | 20,736.30 | 20,736 | 17,134 | 59,077.07 | 62,393.11 |
| SC 100 | 2,650.70 | -3,786.25 | 6,436.95 | 6,437.25 | 3,786.25 | 59,077.07 | 62,393.11 |
| SC 200 | 5,423.60 | -7,072.00 | 12,495.60 | 12,496 | 7,072 | 59,077.07 | 62,393.11 |
| SC 300 | 8,517.60 | -10,153.00 | 18,670.60 | 18,671 | 10,153 | 59,077.07 | 62,393.11 |
| BF 100 | 831.35 | 6,071.00 | 0 | 0 | 0 | 59,077.07 | 62,393.11 |
| BF 200 | 1,645.15 | 12,350.00 | 0 | 0 | 0 | 59,077.07 | 62,393.11 |
| BF 300 | 1,757.60 | 17,134.00 | 0 | 0 | 0 | 59,077.07 | 62,393.11 |

- **SPAN: pass (strong evidence).** Zerodha's SPAN line is the netted figure (B), `max(0, scan - NOV)`, and equals
  mine within Rs 0.70 on all 9 rows (it rounds to the rupee); its net option value equals mine to the paisa (it shows
  a short's as positive). So the risk arrays, signs, scenarios and prices are read right, and judge 75's question is
  answered: the broker displays (B).
- **Exposure: fail.** Zerodha charges Rs 31,196.555 per short leg, the same for the 22,700 and 24,000 calls and for the
  October series, and 1.5 times that (46,794.83) for a 20,000 put more than 10% out of the money. So it applies NSE's
  2% and 3% rule, but on a base of **23,997.35** (31,196.555 / 0.02 / 65), not the 22,721.95 close in NSE's file and
  on `ind_close_all_13102026.csv`. 23,997.35 is no NIFTY close from 1 Sep to 13 Oct 2026 (checked) nor a futures
  price in the file. I cannot explain it from public data: a broker buffer, a stale price in Zerodha's tool, or a rule
  I have missed. Until it is explained, **my exposure is Rs 3,316 a lot (5.6%) below this broker's**, which would make
  C2 looser than Zerodha by that much per trade. Fail closed: the workflow stays `workflow_dispatch` only.
- Zerodha is not the owner's broker. The figure that matters is Groww's; the one-time Groww check below now has a
  sharp question: does Groww's exposure for this basket show 59,077 (NSE's close) or more?
- Raw answers (single legs, 08:10 IST): short 22700 CE Nov `{"span":149043.75,"exposure":31196.555,
  "netoptionvalue":35174.75}`; short 24000 CE `{"span":77610.5,"exposure":31196.555,"netoptionvalue":4348.5}`; short
  20000 PE `{"span":32403.5,"exposure":46794.8325,"netoptionvalue":383.5}`; futures queries returned `{}`.

Also checked:
- **Second implementation, same file.** `marginism` 0.1.1 (PyPI, an open-source SPAN calculator for NSE files whose
  output mimics a broker basket) on `nsccl.20261014.i1`: **exposure equal to the paisa** for all 15 rows (59,077.07),
  same scenario losses; SPAN differs by exactly the position's premium (SF 100: 6,071.00; SF 300: 17,134.00), because
  it nets the net option value into SPAN (next section).
- **Public anecdotes fit the exposure rule** (some evidence): a NIFTY iron condor at about Rs 30,000 a lot in 2024
  (lot 25: 2 x 2% x ~22,000 x 25 = 22,000 exposure plus SPAN); an Angel One NIFTY put spread at about Rs 56,000 for 75.

Tolerance used: before 11:03 IST the newest NSE file is the day's `i1`, so the 08:05 comparison is like for like.
Tolerance **Rs 50 a lot or 0.1%, whichever is larger**: same file and rule leave only rounding (risk values have 2
decimals, x 65 units x 4 legs = at most Rs 1.30) and the broker's choice of the notional's price; anything larger means
a method difference and the job stays manual.

**One-time check for the owner (Groww), now needed (the exposure question):** in the Groww app or web, F&O, NIFTY, expiry
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

## Findings

1. **What C2 counts: ruled by judge 75 and built.** The parts are stored apart (`scan_per_lot_rs`, `nov_per_lot_rs`,
   `exposure_per_lot_rs`; `fno/risk/margins.py` `MARGIN_COLUMNS`). C2 counts `max(0, scan - NOV) + min(0, NOV) +
   exposure` (`MarginParts.initial`), the multiplier stresses the scan only (`MarginParts.stressed`: `max(0, k x scan
   - NOV) + min(0, NOV) + exposure`; exposure not stressed, as the orchestrator set it; whether to stress it is the
   owner's), and a total not above 0, or a negative scan or exposure, is refused by name. Tests:
   `tests/risk/test_margin_formula.py`. Mutations: scan alone -> 6 tests fail; k x (the netted figure) -> 1 fails.
2. **The margin is almost all exposure.** For every row, 59,077 of 59,899-67,595 is exposure on the two short legs,
   which a hedge does not reduce. Risk manager's view: a Rs 5 lakh book can hold about 6 such lots at stressed 1.45 x
   62,000 = 90,000 each, before cash for losses; C2's 3-trade cap binds first.
3. **The `i1` file is not always out by evening.** 41 of 131 sampled files were written after 22:00 IST, some after
   midnight; the job runs in the morning (07:45, retry 08:30), never racing NSE.
4. **The manifest guard asked for a year of rows** (250); a dataset that begins on 1 Oct cannot have them. I changed the
   test to require every session from the first day instead, for forward-only datasets only, and say so here.

5. **C2's MarginRoom was looser than a broker in one case, found by judge 75's requested test; fixed (judge to
   confirm, it goes beyond the ruling).** With an open credit trade (a short fly, Rs 6,071 received, marked at a loss)
   and a new debit trade (BF, Rs 6,071 paid), `min(cash, marked equity)` left **Rs 6,071 more free than a broker**:
   the min takes either the debit's payment or the credit's liability, a broker deducts both. Root cause: netting one
   trade's value against another's liability. Fix in `fno/risk/rules.py`: the available cash after entry is also never
   above `cash + entry cash flow + sum over trades of min(0, trade value)` (the proposal included). It is the lowest of
   the old two figures and this one, so it can only be stricter than before. With the exact input and the same scan,
   C2 now equals the broker to the paisa in all 8 cases (credit or debit proposal; loss 0, 3,929, 20,000 and 60,000);
   removing the new term fails 4 of them. Limits (reasoning): it values open trades at today's mids, so it needs a
   quote for every open leg (the stress rule already needs them); and C2 uses today's row for a structure and width,
   not the held trade's own scan, so a held trade whose scan has grown is covered only by k.
6. **E4's interface is unchanged, its test fixtures changed.** `MarginTable.margin(terms, day)` and
   `StressedMargin.margin(terms, day)` keep their signatures; only the file's columns changed. On this branch I updated
   the margins rows in `tests/desk/test_entries.py`, `tests/desk/test_entry_limit.py` and `tests/risk/test_manager.py`
   (header from `MARGIN_COLUMNS`; the old 40,000 becomes scan 40,000, NOV 0, exposure 0, the same figure). The
   stressed-margin record gains `"stresses": "scan risk only (judge 75)"`.
7. **NOV basis.** The stored NOV uses the SPAN file's prices (previous settlement); the broker and MarginRoom use
   today's. For C2's arithmetic this shifts the debit/credit netting by the day's change in the legs' value; on the
   safe side for a credit (the scan term does not depend on NOV), not always for a debit (a BF whose value rose
   overnight). The size is small next to exposure (BF 100's SPAN is 0 either way unless its value fell below 831).

## Judge 77 must-fixes (built)

1. **Mirror never-looser case.** `tests/risk/test_margin_formula.py` now runs both orders: an open credit SF (losses 0,
   3,929, 20,000, 60,000) and an open debit BF (losses 0, 3,000, 5,000, kept above its scan, where the stored parts
   hold), each with a new credit SF and a new debit BF: 14 books, C2 equal to the broker to the paisa in each. The
   judge's plant (dropping the proposal's own liability, `+ min(0.0, marked)`) now fails 3 of them.
2. **Exposure gap: option (a).** `fno/nse_margins/independent_check.py` `IndependentCheck`, read from `config.yaml`
   `risk.margins.nse_span_check` (`source`, `passed_on`; both null now). Until both are set and `passed_on` is on or
   before the day, the job prints the day's rows and writes none, refused by name ("N rows computed, none written: no
   independent broker check has passed ...") in its one #fno-desk line, exit 1. Tests: unset, no date, no source and a
   date after the day each write nothing; the repository config is not passed; a planted switch-off fails 4 tests.
   **Criterion 1 stays NOT MET** until the owner's Groww check; option (b) (a broker-observed exposure floor) only if
   Groww also shows the higher base.

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
(it asked for 250 rows, a year of history, which a dataset begun on 1 Oct cannot have). Full suite 2,336 passed on the branch merged with main at a999d78 (47 A14 tests and 13 in `tests/risk/test_margin_formula.py`); ruff and
`tools/check_imports.py` clean.
