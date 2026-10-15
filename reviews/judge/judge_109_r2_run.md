# Judge 109: R2 run, part 1: pre-run amendment 1: `story/r2-run` 291760c (lane 1, story-text check, quality rule 1)

Judge D. Scope: `AMENDMENT_1.md` (new), `FREEZE.md` (its hash), `README.md` (one line), on parent `main` 32262d4. No
code, no data. The question: does anything in A-D change a registered rule or threshold, or choose anything with
outcome knowledge, and is D's data route acceptable.

**What I did:**
- read the diff and `AMENDMENT_1.md` in full against the frozen `PROTOCOL.md`, judge 97's follow-ups,
  `FACTORY_RULES.md`, `DATA_SPEND.md` and the owner's decision rows;
- checked the hashes, the freeze commit's ancestry and every data claim in D against the repository (manifests'
  headers and date ranges, `fno/filings/`, `fno/fo_bhavcopy.py`, a NIFTY index-future row of the 2 Jan 2024 fixtures
  for units). I read **no study data**: no stock row, results date, filing time or event move;
- re-derived the power arithmetic.

## Gates

- `PROTOCOL.md` SHA-256 at 291760c: `89947b4c...e40a6b`, unchanged. `AMENDMENT_1.md`: `8b36416b...1da47d`, equal to
  `FREEZE.md`'s new row. 93a19c3 (the freeze) is an ancestor of 291760c.
- `tests/research` (ledger guard included): 22 passed, Slack token unset. Record scan clean (1,275 files).
  `git merge-tree origin/main 291760c` merges cleanly. Files: 88, 25, 190, 6 lines.
- Docs only, so the full suite is not needed for this part; it runs on the `study.py` commit.
- Environment note: `requirements-groww.txt` does not install here (`clint`/`args` wheels fail, as the file itself
  warns). It does not affect a docs-only change; I record it for the code part.

## Claims vs reality

| Claim | Status | Evidence |
|---|---|---|
| A. Annualisation of criterion 3 | MET | Protocol §8.3: "at least 130 clusters a year (count of section 7) with an event meeting 1 and 2"; §7 does not say how a year is measured (judge 97 follow-up 2). A fixes it: clusters (Industry x ISO year-week of R) with at least one decision-window event that fits, is liquid and has EN > 0, divided by window days / 365.25. Reading criteria 1-2 per event is the stricter of the two readings (it can only remove clusters). The window holds 8 full results seasons plus the start of Oct-Nov 2026 in about 2.04 years, so the rate is biased slightly down, as stated. Chosen blind: it needs no data. |
| B. Depth descriptive only | MET | Per bucket: legs, median and p25 best quantities in lots, share with a lot on both sides; "no decision role"; raw quantities stay in Drive (owner row "Raw Groww quotes go to Drive only", 665c835) |
| C. 130 decides; 297 shown | MET | (1.645 x 0.60 / 0.05)^2 = 389.7, so 390 units, 130 a year; ((1.645 + 0.842) x 12)^2 = 890.7, so 891, 297 a year: both recomputed. 130 "alone decides"; a YES between 130 and 297 is labelled; changing to 297 "would be a new trial". No rule changes |
| D. Data details fixed before reading; none changes a threshold | MET for "no threshold changed, nothing chosen with outcomes"; **two should-fixes on the data route** (below) | No D item touches 25%, 50/100 contracts, Rs 10,000, e = 5%, T = 2%, 130, 80% or 10%. Items D5-D7 and D9 resolve ambiguities of the protocol mechanically (step arithmetic, session counting, stock-quarter definition, ANOVA n0 = (N - sum n_c^2/N)/(k - 1): correct; seeded cluster bootstrap) |
| D1. A12 has no board-meeting lists for 2019-26 | TRUE | `research/data/manifests/board-meetings.csv`: 1,020 rows, dates 2005-01-01 to 2007-10-17. A12's `day-lists` job (`fno/filings/sources.py:58`, daily files `board-meetings_YYYYMMDD.json`, run by `filings-archive.yml`) is walking forward from 2005 |
| D2. `filed_at` from `results-xbrl.csv` | TRUE as a source | Header `symbol,period_end,consolidation,filed_at,first_seen,...`, 15,995 rows (rows not read) |
| D3. Corporate-actions file covers about 400 days | TRUE | One file, `from_date=07-09-2025&to_date=12-10-2026`. So Oct 2024 - Sep 2025 of the decision window rests on bhavcopy detection alone, which the amendment states |
| D4. OI in shares in both formats; contracts = `TtlTradgVol` / `CONTRACTS` | TRUE | `fo_bhavcopy.py:37` maps them; NIFTY Jan-2024 future on 2 Jan 2024: 167,847 contracts x 50 x 21,756.75 = Rs 1.826e11 = `TtlTrfVal`, and OI 11,836,050 in both files (shares) |
| Exposure while testing reachability is harmless | ACCEPTED (some evidence: rests on the builder's attestation, as every freeze does) | Two November 2026 meetings of companies: future events, outside the decision window; the snapshot's stock list is mechanical (every F&O stock with a meeting in the next 10 sessions), so knowing two names steers nothing. Column names of one Jan 2025 answer: schema only. Results dates are event timing, not outcomes. No rule in A-D uses either |
| D1 is "an amendment, not a rule change" | ACCEPTED in substance | Protocol §3 names "A12 archive in Drive: NSE board meetings"; the amendment reads the same NSE list (the API A12 archives). Same data, same rule, different fetch path; §11 lets the script differ from the text only with the difference reported. Not a new trial. But see should-fix 1 on how it is fetched |

## Should-fix

**1. The study would be its own downloader of an NSE list that A12 already archives, against the owner's 13 Oct rule
and with an unproven request shape.**
- Owner, 13 Oct 2026: "One scheduled downloader fetches it and stores the raw files in Google Drive; every consumer
  ... reads only from Drive, never from third-party servers". D1 has the study script call NSE's
  `corporate-board-meetings` API itself, one month per request, writing its own files.
- That makes a second archive of the same list in a second layout (monthly files beside A12's daily
  `board-meetings_YYYYMMDD.json`), with its own manifest (`inputs.csv`) instead of A12's.
- A month-range request is not the shape A12 uses or has validated (one day per request, with `check_day_list`). Whether
  NSE returns a full month in one answer, or caps or pages it, is not known. A silently truncated month would lower
  results-date coverage and the event count, unseen.
- Fix (any one): (a) fill 2019-01-01 to the run day through A12's own `filings day-lists` (it already takes `--to`; a
  start day is a small lane-1 change to A12, judged on its own), then the study reads A12's Drive files and manifest; or
  (b) keep the study's fetch but write exactly A12's daily layout, file names and manifest through A12's classes, one
  day per request; or (c) get the owner's written exception for a one-off study fetch, and add a completeness check
  (each month's rows against the sum of the same days' daily answers on a sample). Whichever is chosen goes in the
  amendment before any data is read, and `DATA_SPEND.md`'s "Company results dates (A12)" row names the real source.

**2. The lot size must be the traded contract's, not the near-month future's.**
- D4 takes the lot from "the stock's near-month future on the entry session", and D3 detects an adjustment when "the
  stock's lot size differs between the entry session and R".
- But the options traded are those of the chosen expiry, which by §4 is often the next month: R plus at least 5
  sessions, with pushes to the second month counted. NSE's lot revisions apply to new or far-month contracts while
  the near month keeps its old lot. So near-month and next-month lots can differ, and the decision window includes
  such transitions (reasoning only for which exact dates; I did not read the data).
- Two effects. Fit and EN would be computed on the wrong lot: a smaller old lot makes the cap look easier to meet,
  which overstates feasibility. And the near-month future rolling between entry and R can show a "lot change" that is
  not a corporate action, so events are wrongly excluded.
- Fix: the lot of the chosen expiry's own contracts (the options' `NewBrdLotQty`, or the same-expiry future) on the
  entry session, and the adjustment test on that same contract on R. Legacy rows (descriptive only) are derived on the
  same-expiry future.

## Minor

1. **Legacy lot "at R" reads exit-session prices.** For legacy rows (to Jul 2024, which covers 2022-24 events), a
   lot on R can only be derived from R's `SETTLE_PR` and `VAL_INLAKH`. Protocol §2 says exit-session data is read only
   for contracts traded, and 2022-26 moves stay unread. The value is internal and rounded, so the harm is nil, but the
   statement should stay literally true. On legacy rows, detect adjustments by the K0-listing test on R and the
   corporate-actions file only (split and bonus adjustments rescale strikes, so K0 disappears).
2. **Report `filed_at` coverage.** A12's XBRL backfill is not complete for every symbol (judge 51). Missing
   `filed_at` falls back to the conservative R rule, and "filing before entry" exclusions cannot be seen. Report the
   share of decision-window events with a matched `filed_at`, descriptively.

## Project rules

Lane 1 (a hand edit under `research/`, a freeze record). No code, no secrets, no model names; files under 350 lines;
labels present. The amendment is append-only beside an unchanged protocol, as judge 97 asked.

**Verdict: FAIL for 291760c60ecfb1739995e163b07b3c89d8c518b1**, on should-fixes 1 and 2. A, B and C pass. D changes
no threshold and uses no outcome, and the exposure is harmless. A re-check needs only `AMENDMENT_1.md` (D1, D3, D4),
its new hash in `FREEZE.md` and, if the source changes, `DATA_SPEND.md`. Nothing may read study data until this
amendment and the `study.py` commit both pass.
