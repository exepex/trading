# Global cues (story A17)

Daily cues an NSE session may know before its 09:15 IST open. Derived tables; the raw copies are in Google Drive
(`fno-research/raw/<publisher>/...`, one copy per fetch, filed under the fetch time). First fill: 15 Oct 2026, 06:15 IST.

| Table | Cue | Rows | Dates | Source |
|---|---|---|---|---|
| `us10y.csv` | US Treasury 10-year par yield, percent a year | 4,950 | 2 Jan 2007 - 14 Oct 2026 | US Treasury |
| `brent.csv` | Europe Brent spot price FOB, US dollars a barrel | 4,992 | 2 Jan 2007 - 6 Oct 2026 | US EIA |
| `usdinr_rbi.csv` | USD/INR reference rate, rupees per dollar | 3,871 | 2 Jan 2007 - 14 Oct 2026, **none 25 Jul 2018 - 11 Apr 2022** | RBI |
| `usdinr_fbil.csv` | the same reference rate | 1,981 | 10 Jul 2018 - 7 Oct 2026 | FBIL |

**Not collected: the previous US closes (S&P 500, Nasdaq 100).** No permitted source was reachable; see "Blocked".

## Columns

`value_date` (the publisher's date, in its own time zone), `value` (as published, never rounded), `source_sha256` (the
archived copy it came from; its path, URL and fetch time are in `research/data/manifests/global-cues/<cue>.csv`),
`first_seen_at` (IST, when that copy was fetched), `provenance`:
- `live`: first seen before 09:15 IST on the first NSE session after the value date: really known in time;
- `backfilled`: fetched later. **Every row before 15 Oct 2026 is `backfilled`** (2 rows are `live`: the 14 Oct 2026
  US 10-year and RBI rate, fetched at 06:15 IST on 15 Oct). Back-filled history was never known at the time by this
  tool; when it would have been known is an assumption (below), not an observation.

## Sources, time zones, lags and terms

| Cue | Publisher and URL | Date's time zone | When a value of date t is out | Terms (evidence) |
|---|---|---|---|---|
| us10y | US Treasury, daily par yield curve CSV per year, `home.treasury.gov/.../daily-treasury-rates.csv/<year>/all?type=daily_treasury_yield_curve` | US Eastern (New York business days) | Quotes near 15:30 ET on t; posted the same US evening, i.e. early morning IST on t+1 (reasoning only on the posting time: on 15 Oct 2026 the 14 Oct value was there at 06:15 IST) | US Government work, public domain (some evidence: US law for federal works; Treasury's own page not quoted) |
| brent | US EIA, Europe Brent Spot Price FOB (RBRTE) daily, `www.eia.gov/dnav/pet/hist/RBRTED.htm` | London trading days | **Weekly**: the page of 7 Oct 2026 ended on 6 Oct, next release 15 Oct. So a value is up to about 9 days old when published, never in time for the next open | EIA: "U.S. government publications are in the public domain ... You may use and/or distribute any of our data" (strong evidence, eia.gov/about/copyrights_reuse.php, read 15 Oct 2026). But EIA credits the Brent prices to Thomson Reuters (LSEG), and the same page says items licensed from others "may be protected": **some doubt** whether this series counts as EIA's |
| usdinr_rbi | Reserve Bank of India, reference rate archive (form), `www.rbi.org.in/Scripts/ReferenceRateArchive.aspx` | IST | Computed from about 13:00-13:30 IST quotes on t, i.e. after t's open: first usable on t+1 | Not found on RBI's pages; RBI is a public authority publishing it for the public (reasoning only) |
| usdinr_fbil | FBIL reference rates, `www.fbil.org.in/wasdm/refrates/fetchfiltered` | IST | Rate of t at 13:00 IST (13:30 before about 2025), but **FBIL's public site trails by about a week** (on 15 Oct 2026 it ended on 7 Oct) | Not read: FBIL's site is a script page whose terms could not be fetched; FBIL licenses its benchmarks commercially, so **republishing them in a public repository may need permission (reasoning only, a risk)** |

RBI's and FBIL's rates are the same benchmark: on every date both publish (10-24 Jul 2018 and 12 Apr 2022 on) they are
equal (`checks/overlap_usdinr.csv`: no `differs` row). FBIL fills RBI's 2018-2022 hole.

## The date rule (as-of)

For an NSE session on India date d, a cue's usable value is the latest one dated **before d**
(`fno/global_cues/as_of.py`). Why it is safe for each cue:
- US data of date t (US Eastern) is final after t's US close, 16:00 ET = 01:30 IST on t+1 (US summer time) or 02:30 IST
  (winter); never before d's 09:15 open when t < d, and a value dated d itself is never used. A US holiday has no row,
  so a Tuesday after a US Monday holiday gets Friday's value; US early closes change nothing.
- USD/INR of date t is fixed at 13:00-13:30 IST on t, after t's open: usable from t+1.
- Brent: the rule gives the value dated before d, but EIA published it up to a week later. **For research on Brent the
  rule-based answer is look-ahead by up to a week; only `live` rows (first seen before d's open) are honest.**
- For a live decision, `value_for(..., live_only=True)` also requires `first_seen_at` before 09:15 IST on d.

## Rules

- Raw copies are never overwritten (each fetch is a new file); a later copy that changes a value already in a table
  is logged in `revisions.csv` (`changed`, old and new value, the copy and when) and the table keeps its first value;
  a value that appears late for a date before a table's last date is logged (`late`) and never inserted. This is
  A11's rule (both versions kept, nothing rewritten) applied to publishers that rewrite whole files every day.
- Tables are append-only: old bytes stay a prefix.
- A failed download or a file that is not the publisher's writes nothing for that cue and is named; others still run.
- Gaps are listed, never filled (`checks/gaps.csv`): weekdays without a value (unverified: no US, UK or RBI holiday
  calendar is in the repository, so holiday and gap are not told apart) and values equal to the previous date's.

## Blocked: previous US closes (S&P 500, Nasdaq 100)

Tried on 15 Oct 2026 from the cloud session:
- **FRED** (`fred.stlouisfed.org`, series SP500, NASDAQ100, and also DGS10, DCOILBRENTEU, DEXINUS): refused by this
  environment's network policy (the proxy closes the connection). FRED's API host answers but needs an API key.
- **S&P Dow Jones Indices** (`spglobal.com/spdji`): HTTP 403.
- **Nasdaq** (`api.nasdaq.com`): reachable, but its terms of use (nasdaq.com/legal) say users must "Not access or use
  the Service, or any process, whether automated or manual, to capture data or content from the Service". **Not used.**
- **Cboe** (`cdn.cboe.com` SPX history): reachable, but its disclaimer (cboe.com/global-disclaimers) says index values
  may not be "stored in a database or retrieval system, without the prior written permission of Cboe". **Not used.**

Both were downloaded once before their terms were read; the copies are not in this repository. Four files remain in
Drive, listed in `reviews/claude/response_103_a17-global-cues.md`, for the owner to keep or delete.

Proposal (owner decision): allow `fred.stlouisfed.org` in the environment's network settings (or add a FRED API key as
a secret), and keep FRED's S&P 500 and Nasdaq 100 values **only in Drive, not in this public repository**. From
memory, not checked here (FRED is blocked): FRED shows S&P's and Nasdaq's copyright notices on those series, S&P's
forbids reproduction without permission, and FRED keeps only about 10 years of S&P 500 history. The owner should read
those notices before deciding.

## Commands

```
python -m fno global-cues fill     # download, archive in Drive, extend the tables, rewrite checks (first run back-fills)
python -m fno global-cues check    # rewrite checks/ from the committed tables (no network)
python -m fno global-cues verify   # recompute every row from the archived copy it names (read-only)
```

Not scheduled (no schedule was added by this story).
