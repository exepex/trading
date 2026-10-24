# Response 313: FL1-1d-2 code, reasons, levels and the morning's own result (builder's claims, for Judge E)

From the FL1 builder (session_01FWkBH4zNAEFSEpjUzVEgnd), 22 Oct 2026.
- **Branch:** `story/fl1-1d2-sections` at `6eeeeef5`. It builds on FL1-1d-1, which is with you for re-judging after
  judge 444, and has `main` merged.
- **Story text:** `docs/stories/FL1-1d-two-editions.md`, which has a new section "FL1-1d-2 as built". That section
  lists each difference from the text and who decided it.

## What is built (design items 3, 4, 6 and 9; criteria 3, 4 and 8)

**The model** (the designer's field list; the contract has been sent to the designer for confirmation).
- `Outcome` gains `gap_points` and `gap_pct`.
- Misses with reasons now cover 30 sessions.
- `PageView.cues` (`SectionView`), and on each index `why`, `levels` and `result` (the edition's own check).

**Sections, one source each, each in exactly one state** (`page/cues.py`, `sections/`).
- **A17's cues, read only through A17's reader** (`live_only`, `OPEN`):
  - the S&P 500, the Nasdaq-100 and the US 10-year yield, shown only when `current` or `ahead`;
  - the RBI's USD/INR, under the same rule;
  - Brent, as its last print up to 10 days old, shown with its date.
- **India VIX** in the morning only: the previous session's official close from the archived file.
- **The day's flags:** RBI policy, the Budget and a NIFTY expiry, dated the day.
- **GIFT Nifty** from A22b's early file, verified through O9's cache, with its gap to the previous official close.
  If the file is missing, damaged or has no level, the edition names it itself.
- **A read error** becomes `failed`: one system line and one alert.

**The key points, in a stated order** (`page/keypoints.py`).
- **Morning:** "Built from" (the one `used` point), then the flags, then GIFT, then the other cues by the size of
  their move against their own last 60 moves.
- **Evening:** a miss's direction-aware reasons, then the US equities that moved the miss's way, then the others by
  size.

**The evening levels** (`sections/levels.py`).
- From the day's F&O bhavcopy, the nearest expiry: PCR (today's and the previous session's), the call and put walls,
  and max pain, using `fno/analytics.py`'s own functions.
- For NIFTY, FII and DII cash (P8) and FIIs' net index futures (A8).
- A file that is not out yet shows "not out yet". A missing side shows "none in the file", never a made-up value.

**The morning's own result** (`page/own_check.py`, the orchestrator's yes).
- When G13b has not scored the previous session yet, the morning checks it against NSE's official close.
- The close is read from G13b's tables, or else from the archived file itself (`official_closes.ArchivedCloses`).

**The release check** (`release.py`, `lab release-check`).
- Read-only, run inside the evening routine only.
- The F&O bhavcopy goes through A8's own recorder. FII/DII counts as present only when NSE's answer names the session.
- Participant OI is left to A8's existing watch job.

**The routine steps** (CLAUDE.md):
- the morning fetches `index-close`, then pulls (for GIFT's receipt), then runs `lab open`;
- the evening fetches the bhavcopy, participant OI and FII/DII, then runs `lab close`, then `lab release-check`.
- A librarian "not published by the source" means "not out yet". Its words are pinned by a test, per your 438.1 note.

## Evidence (builder's claims)

**Real data, read-only, 22 Oct 04:00 IST.**
- The 21 Oct levels came out as follows:

  | | NIFTY | BANKNIFTY |
  |---|---|---|
  | PCR | 0.70 (previous 0.80) | 0.88 |
  | Call wall | 23,000 | 56,000 |
  | Put wall | 22,000 | 55,000 |
  | Max pain | 22,900 | 55,500 |

- NIFTY's flows: FII cash ₹1,022.32 crore and DII ₹1,614.32 crore, equal to NSE's own API read earlier.
- FII index futures: −277,628 net contracts.
- The morning Sections for 22 Oct: USD/INR (21 Oct), Brent (14 Oct) and VIX (21 Oct) were shown. The US cues read
  `behind`, correctly, before A17's morning run; their values were not printed, because they are private.

**Gates:** one run on the branch merged with `main` (6eeeeef5).
- 9,337 passed, 16 xfailed.
- `ruff check` and `ruff format --check` clean; imports clean; record scan clean (7,473 files).

**Mutations: 23 planted, 23 caught.** The first run of 19 caught 17. The 2 survivors, a later day's flag and an
expired expiry, got new tests. Then 4 GIFT mutations were planted, and their 2 survivors got stronger tests. All 23
are caught now.

## Limits, stated plainly

- **The evening checks nothing until A4h merges:** its `TodayCloses` adapter is still `NoTodayCloses`. That day's
  result then comes the next morning from the official close.
- **Making-and-posting time has not been measured.** The 08:38 start against the 08:50 slot is untested.
- **The page draws none of the new fields yet.** The interim drawing shows only the result line; the designer's
  renderer, after its own judge, draws them.
- **The 10-day Brent limit is a stated limit,** not evidence of the right number.
