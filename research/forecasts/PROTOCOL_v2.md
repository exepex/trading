# Forecast protocol, version 2 (story G1 v2): the interim live input pack

**Status: version 2, frozen.** Written by Claude on 13 Oct 2026 from ChatGPT review 29 (section 2), whose eight
changes the orchestrator accepted in `reviews/claude/response_63_2026-10-13-on-review-29.md`. Claims and evidence:
`reviews/claude/response_62_g2-g3.md`, addendum "Protocol version 2". Judge 47 addendum 3 passed it (1b57cb3) and the
orchestrator confirmed the freeze. The commit that adds this text is the protocol commit;
`research/forecasts/FREEZE_v2.md` records it (section 8). No live forecast existed at the freeze. Any change from here
is a new version (a new file and a new freeze), never an edit. Registered in the research ledger as trials 37-41
(`forecasts-v2`, one per question).

**Relation to version 1.** Version 1 (`research/forecasts/PROTOCOL.md`, protocol commit
`cf489e4c53714ce0fffae61db8850b49648ac391`, freeze record `research/forecasts/FREEZE.md`) stays immutable and in force
for everything this file does not change: the five questions and their targets (v1 section 2), the IV30 estimator
(section 3), the three baselines (section 4), Book 1's method (section 5), scoring (section 7), the comparisons and
Holm adjustment (section 8) and the history back-fill (close proxy). Version 2 changes only v1 section 1's live inputs
("only the common market pack (story E2) ... until E2 exists there are no live forecasts") and adds the record columns
and the deadline below. When story E2's market pack exists, it needs a version 3.

## 1. The live pack (changes 1, 5 and 6)

- **Source:** the day's canonical A4 3 pm snapshot in the repository (`research/data/quotes/`), Groww's dataset first,
  then NSE's (story O6); its raw CSV and meta bytes. No snapshot: every same-day input is missing.
- **Per-field cutoff 15:00:00 IST (change 1).** A same-day field enters only if its own observation time is at or
  before 15:00:00 IST on `d`; otherwise it is missing and the methods that need it record "no forecast":
  - option quotes and the NIFTY spot: the row's `response_received_at`; the spot is the latest qualifying row's;
  - NIFTY futures: A4 reads them inside the capture with no time of their own, before the first quote request, so the
    snapshot's earliest `request_sent_at` bounds their retrieval and must be at or before 15:00:00;
  - India VIX (change 2): A4's NSE-timestamped record (`india_vix`, `india_vix_time`, story B7); NSE's stamp and the
    retrieval bound above must both be at or before 15:00:00. Without it there is no VIX forecast input; `d-1`'s VIX
    is never used as today's.
- **Mode (change 6):** every live value is labelled `live_1500_proxy`, its own mode, never mixed with history's
  `close_proxy`. The pack's 15:00 NIFTY spot and VIX stand for `d`'s close in the baselines' inputs (as B7's live
  features); outcomes stay as v1 defines them (official closes).
- **Provenance hash (change 5):** the pack lists every value it supplies with its name, source and observation time;
  the snapshot's dataset, id and the SHA-256 of its CSV and meta files; the official closes' source, last day and the
  SHA-256 of the closes supplied; the session calendar's SHA-256; the problems found; IV30 (points, status,
  expiries). The SHA-256 of its canonical JSON (sorted keys) is `pack_sha256` in every record of the day. Code:
  `fno/forecast/live_pack.py`.

## 2. IV30 from live mids (change 3)

v1 section 3 unchanged except the prices: each expiry's ATM IV is B7's live ATM rule
(`LiveAtmIvMinusRealised.atm_implied_vol_points`): the strike nearest the 15:00 spot (a tie to the lower), the call and
the put both valid and two-sided (bid and ask present), observed by 15:00, mid = (bid + ask) / 2, Black-76 on the same
expiry's future (rate 6.5%, solver bounds as B1). The monthly expiries are the futures in the pack; the same
total-variance interpolation, the same fallback (nearest expiry with at least 7 days) and the same flag apply. An
expiry without a valid two-sided ATM pair has no IV; if no expiry qualifies there is no IV30 and question 5 and
baseline (a) record "no forecast". Question 5 stays void on flagged or missing IV30 days (v1 section 2).

## 3. The history gate (change 4)

- **Closes through `d-1` are a hard gate.** The official NIFTY 50 and India VIX closes come from
  `research/data/nifty-panel/warmup_closes.csv`, which story O6's GitHub Actions job (`index-closes.yml`, 21:11 IST)
  extends each trading evening from NSE's first archived index-close file. If any trading day from the file's first
  day to `d-1` lacks either close, the record carries `history_stale` and the methods that read the history (base rate
  and model) record "no forecast" for every question; a shorter window is never used. A close of `d` or later is
  never read (`OfficialCloses.through`).
- **Question 5's IV30 history:** its base rate needs the panel's IV30 up to the trading day 21 sessions before `d`
  (the last outcome known before `d`); otherwise `iv30_history_stale` and question 5's base rate records "no forecast".
- Book 1 follows v1 section 5 unchanged: with one baseline missing it is the other baseline alone.

## 4. The record, version 2 (change 7)

`fno/forecast/schema_v2.py`: v1's seven columns unchanged, then `input_mode` (`close_proxy` or `live_1500_proxy`),
`iv30_status` (`interpolated`, `flagged` or `none`: the day's input quality, never inside `method_or_version`) and
`generated_at` (with its time zone). `cutoff` is 15:00:00 IST on `d`. Baselines' `method_or_version` is
`<baseline>/v1`; Book 1's is `book1/v1/sha256:<method file hash>`.

## 5. Generation deadline and receipt (change 8)

- The forecasts are computed from the pack by **15:15:00 IST** on `d` (`ForecastRecordV2.on_time`); a record generated
  later is ignored by scoring. This replaces v1's "committed by 15:30" rule for live records.
- **Receipt lock:** the GitHub Actions run (`.github/workflows/forecast-capture.yml`, no AI) prints
  `receipt: <d> pack <pack sha256> records <records sha256> generated_at <time>` in its log and step summary, and
  saves the line in the O6 run summary (Drive pipeline area). The later Git commit of
  `research/forecasts/live_v2/<YYYY>/<d>_pack.json` and `<d>_forecasts.csv` is transport only; scoring checks that
  the committed files hash to the receipt.
- **Write once:** a day's pack and records are written once; a re-run with a different pack is refused
  (`CaptureRefused`).
- The run waits until 15:10 IST and pulls until the day's canonical snapshot is in, at most until 15:13 IST; then it
  generates with whatever is there (missing inputs give "no forecast", never a later retry with more data).

## 6. Golden values (behaviour, separate from `golden_iv30_rv20.csv`)

`research/forecasts/v2/golden/{case_a,case_b}/`: A4-layout inputs and the expected `pack.json` and `forecasts.csv` for
13 Oct 2026, with a fixed clock (15:05 IST) and a fixed calendar label. Case A: every field by 15:00, IV30 14.8151
interpolated (hand value). Case B: the 23 Nov ATM put received 15:00:01 and VIX stamped 15:00:30: IV30 14.0 flagged
(27 Oct alone), no VIX. `python tools/forecast_live_golden.py` must report them unchanged
(`tests/forecast/test_live_pack.py`).

## 7. Known limits (stated before any live forecast)

- A4 captures two monthly expiries; a bracketing third expiry has no IV, so live IV30 may flag more often than history.
- 15:00 values are not 15:30 closes: live and history forecasts are scored and reported apart (`input_mode`).
- The pack depends on the 3 pm recorder committing its snapshot by 15:13 IST; a later commit means "no forecast" that
  day.
- Question 5's base rate needs the panel rebuilt at least every 21 trading days (`iv30_history_stale` otherwise).

## 8. The freeze

`research/forecasts/FREEZE_v2.md` names the protocol commit and the SHA-256 of this file, of every forecast code file
(`fno/forecast/*.py`: the v2 pack, history, gate, schema, capture and freeze check, and the v1 code they use), of the
golden tool and of every file of the v2 golden cases. `fno.forecast.freeze_v2.require_version_frozen` checks it
before every capture (full history; a shallow clone refuses), so a change to any of them stops the live capture until
a new version is frozen. Shared libraries (B7's live ATM rule, B1's Black-76, the panel and quote readers) are
recorded, not byte-checked: the daily job recomputes both golden cases before it captures, and any difference fails
the run before a forecast is made.
