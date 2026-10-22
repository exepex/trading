# Response 319: OSS1, the open-source clean-up: none of the three items can be done as asked; what can be done

From the A4 builder (session 01MKtUHByHsR9cNwaP5KhFYH), for the orchestrator, 22 Oct 2026, on
`docs/OSS_REVIEW_2026-10-22.md` sections 3-4. No code has changed. Each finding gives its check.

## Short answer

| Item asked | Finding | Can it be done now? |
|---|---|---|
| 1. One Black-Scholes/Black-76/IV module instead of three copies | Already one where merging is allowed. The "third copy" is a deliberate independent implementation, required by judge 83 and guarded by a test | **No.** Merging it would break C4's independence rule and its test |
| 2. One Brier instead of two | Both copies are byte-checked by the v4 freeze | **No, not before protocol v5.** Noted for v5 |
| 3. nselib as a backup NSE source | nselib downloads the same files from the same hosts we already use, and returns DataFrames, not NSE's bytes | **No value as asked.** A second NSE host does give some independence (below) |

## 1. Black-Scholes, Black-76 and implied vol

**What exists** (read in the code):
- `fno/analytics.py` holds `norm_cdf`, `bs_price`, the Greeks and a spot-BS `implied_vol`.
- `fno/research_engine/implied_vol.py` (B1) holds the `ImpliedVolModel` interface with `Black76` and
  `SpotBlackScholes`. It **already imports** `norm_cdf` and `bs_price` from `analytics.py`; it does not copy them.
- `fno/price_distribution/pricing.py` (G13) routes every Black-76 price and IV through B1's `Black76` ("the project's
  one IV inverter"). It is thin wrappers, not a copy.
- `fno/checks/validity_pricing.py` (C4) has its own `_norm_cdf`, `black76` and bisection IV.

**Why C4's copy must stay** (strong evidence):
- Its docstring says "written apart from B1's model".
- Judge 83's must-fix 3 required C4 to recompute stress and exposure "with C4's own Black-76", so that a pricing bug
  in the proposer cannot pass C4 too.
- `tests/checks/test_validity_independence.py` refuses any import of `fno.research_engine.implied_vol` (and the other
  proposer modules) from `fno/checks/validity*.py`.
- So deleting the "duplicate" would remove a safeguard that is there on purpose, and would fail that test.

**Freezes** (read in each freeze file):
- `implied_vol.py`'s SHA-256 is recorded in `research/forecasts/FREEZE.md` (v1) and `FREEZE_v2.md`, with its
  behaviour locked by the golden values.
- It is also in v4's `RECORDED_NOT_CHECKED` (`fno/forecast_scoring/v4/freeze_check.py`).
- `analytics.py`'s SHA-256 is recorded in `research/2026-10-12-experiment-1/FREEZE.md`.

**What is left:**
- One small overlap remains: `analytics.implied_vol` (spot BS) beside `ImpliedVolModel.implied_vol`. Both files are
  under freeze records, so it is for protocol v5, not now.
- vollib cannot replace any of them now either: every non-frozen user already goes through B1, and C4 must stay
  independent.

**The numbers already match vollib** (my run, this session, py_vollib 1.0.12 in a separate folder):
- I compared B1's `Black76`, C4's `black76` and `analytics.bs_price` with vollib's `black` and `black_scholes`.
- The grid: F 20,000 and 25,000; K 19,000, 25,000 and 26,500; T 1, 7 and 30 days and half a year; r 0 and 6.5%;
  σ 5%, 13% and 40%; calls and puts.
- The largest difference was **4.3e-12**. **[strong]**

## 2. Brier

- `fno/forecast_scoring/scores.py` and every `fno/forecast_v4/*.py` (so `loss.py`) are in v4's `BYTE_CHECKED_GLOBS`.
  Any edit fails the v4 freeze check.
- The review itself says "Do not touch". **Noted for protocol v5:** one Brier, imported by both.

## 3. nselib as a backup source

**What nselib 2.5.1 calls** (read in its wheel):

| Data | nselib's source | Ours |
|---|---|---|
| F&O bhavcopy | `nsearchives.nseindia.com/content/fo/BhavCopy_NSE_FO_...zip` | the same file (`fno/storage/raw_source.py`) |
| Participant OI | `nsearchives.nseindia.com/content/nsccl/fao_participant_oi_*.csv` | the same file |
| Ban list | `nsearchives.nseindia.com/archives/fo/sec_ban/fo_secban_*.csv` | the same file |
| India VIX | `www.nseindia.com/api/historicalOR/vixhistory` | the same endpoint (`fno/vix_history/`) |

So nselib fails exactly when we fail. It also hands back parsed pandas frames, while O9 archives NSE's own bytes
with their SHA-256. A backup that changes the bytes cannot feed that store. **[strong]**

**What would give real independence: a second NSE host.**
- `archives.nseindia.com` serves the same four files **byte for byte**. I checked 21-22 Oct: the same SHA-256 for the
  bhavcopy, participant OI, the ban list and the index-close file.
- It sits on a different Akamai edge: `e9776.dscb` against `nsearchives`' `e164355.dsca`.
- So it survives an edge or DNS fault of `nsearchives`, but probably not an origin outage. **[some evidence:
  one day; reasoning for the origin]**
- It would be one alternative base URL in A9b's one retry policy (`fno/storage/raw_source.py`), and the receipts and
  SHA-256 stay the same.
- That is A9b's code (last changed by sessions 01MBnbVU and 013u1Ac2), so it needs its owner's agreement.

**A correction to the review:** `www.nseindia.com/api/allIndices` returns **200** from this container today (22 Oct,
twice: 03:57 and about 11:17 IST). The review's "403 from this cloud container" is not true today.

## What I propose instead of OSS1 as written

| # | Change | Lane | Gain |
|---|---|---|---|
| a | A test (`tests/checks/test_pricing_reference.py`) comparing B1's Black-76, C4's Black-76 and spot BS with vollib on the grid above, within 1e-9; `py_vollib` added for tests only | 2 (tests) plus one dev dependency | An outside reference for all three pricers. It does not touch C4's independence, because the test imports both and the code imports neither |
| b | `archives.nseindia.com` as A9b's second host for archived files, same bytes and same receipts | 1 (NSE) | Real resilience against an `nsearchives` edge fault |
| c | v5 notes: one Brier; `analytics.implied_vol` and B1's inverter as one | protocol v5 | Recorded now, done at the next protocol |

**What I recommend** (reasoning only):
- (a) is cheap and safe, and can go after Monday's merge window.
- (b) is worth asking A9b's owner.
- Close the rest: about 700 lines could come from libraries, but those not frozen are deliberate or already shared.
