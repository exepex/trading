# Judge 42: W11 item 3, the examples after the Sunday 1 Feb 2026 session fix

**Verdict: PASS for item 3.** The session fix is correct, every changed value is listed, and the new calendar check
bites. The orchestrator's question is answered separately below: yes, unadjusted prices make W11 examples wrong today,
and the contract does not say they must be adjusted. That is a should-fix for the separate corporate-action fix, not
for item 3.

**What I judged**
- **Repository:** `exepex/omenix-dashboard` at 996e764 (after design's 3a12c6c, merged as 348fe34).
- **Claims:** `reviews/claude/response_21_w11_item3_sessions_examples.md`.

## Checks run by the judge

```
$ python3 tools/api/check_contract.py     (openapi-spec-validator 0.7.2)
  contract: 70 paths (43 block endpoints), 82 block examples, 137 block schemas, 873 catalogued leaf fields, 58 planted breaks, 5 daily series on NSE's sessions
  contract: OpenAPI 3.1 valid; examples valid and current; catalog complete; screen rules hold; every planted break caught
$ python3 tools/api/examples.py --check   examples current
$ git diff --stat f3e7f5f 996e764 -- api/paths api/schemas api/examples/blocks.json api/examples/blocks-32.json
  (empty: no served schema changed; the frame, Home and chain examples are unchanged)
$ diff design/mockups/_platform/nse_sessions.csv exepex/trading research/data/calendar/nse_sessions.csv
  identical (one calendar; design's copy equals trading's)
```

### Against NSE's own files (fetched by me)

| Claim | NSE file | Value | Result |
|---|---|---|---|
| Nifty Pharma's 52-week low becomes its 1 Feb close, 21,535.30 | `ind_close_all_01022026.csv` | Nifty Pharma 21,535.3 (Nifty 50 24,825.45) | **confirmed** |
| The 1 Feb session exists | A1 calendar `2026-02-01,special` (FAOP/72352), and NSE's index file for that Sunday exists | – | confirmed |

## Item 3: decision

| Part | Judge's evidence | Decision |
|---|---|---|
| The examples regenerated from the session-fixed data | Checks green; the changed values match design's change list (the builder's script); the Pharma low verified against NSE | ACCEPTED |
| `check_calendar.py` (as_of on a session; daily series equal NSE's run of sessions) with 3 plants | Runs inside `check_contract` ("5 daily series on NSE's sessions"); 58 plants caught. It reuses the single vendored calendar, which equals trading's. | ACCEPTED |
| Stated limit: 34's `closes` and 33's 1Y figures carry no dates, so the example check cannot see their days | True. Those are guarded in design's fetch scripts (`sessions()`, `nse_calendar.py --check`) | ACCEPTED as a limit |

## The orchestrator's question: do the unadjusted prices make W11 examples wrong, and should the contract guard it?

**Yes, examples are wrong today (strong evidence for KOTAKBANK).** NSE's own equity files give:

| Date | KOTAKBANK close |
|---|---|
| 13 Oct 2025 | ₹2,152.10 |
| 1 Apr 2026 | ₹356.05 |
| 1 Jul 2026 | ₹400.45 |
| 12 Oct 2026 | ₹443.40 |

A large bank moving from about ₹2,150 to about ₹356 inside six months fits a 5:1 split, not an 80% fall. Adjusted, the
year-ago close is about ₹430, so the true 1Y change is about **+3%**. The served example `getScreenerStocksIndia_india`
shows **−79.15%** on its first page, with a 52-week high of 2,266. I did not check NSE's corporate-actions file
itself, so the split is inferred from the price path. The builder's other 87 rows are its pattern, unverified by me.

**Does the contract guard it? No.**
- The W11 screener and Markets schemas never say whether prices, period changes (`d1`…`y1`) and 52-week `h`/`l` are
  adjusted for splits and bonuses.
- The older company contract does say so (`api/schemas/company.yaml`: "split-adjusted sessions", plus an `adjusted`
  flag per bar).
- So a publisher can serve unadjusted figures and still pass every check, and the frozen notes (33 row 5: "% change on
  the close 1, 5, 21, 63 and 250 sessions back") do not settle it either.

**Expected, for the separate corporate-action fix (should fix there, reasoning only on the form):**
1. **The contract states the rule.** Every period change, 52-week high and low, and 1Y close series is adjusted for
   splits and bonuses as of the close, as in `company.yaml`.
2. **The publisher is guarded.** The publishing story (`TR-NSE-proposed`) adjusts using NSE's corporate-actions file,
   and its acceptance test includes a known split (KOTAKBANK: 1Y change about +3%, not −79%).
3. **No heuristic in the contract** (such as "h above 3 × p"). A real crash would trip it, and a small split would
   pass it. The definition and the publisher's test are the right guard.
4. **33 is rebuilt and the examples regenerated,** with the changed values listed, as was done for item 3.

## Addendum: the contract-side fix (omenix-dashboard c48860a, `response_22_w11_split_adjusted.md`)

**Points 1 to 3: ACCEPTED. Point 4: pending.** The builder's pushback (no per-row `adjusted` flag) is **ACCEPTED**.

**Checks:** `check_contract` and `check_mapping` are green.

**What the diff says now:**
- **`PeriodChange`:** "% change on the close … back, that past close adjusted for every split and bonus since (NSE's
  corporate-actions file …), so a 5:1 split is not a −80% year".
- **`ScreenerStock`:** `h`, `l` and RSI are computed from adjusted closes; `p` and `v` are as traded.
- **`OverviewQuote`:** `closes`, `hi52` and `lo52` are adjusted (index levels have none).
- **The catalog sources** are updated.
- **`TR-NSE-proposed`** names the KOTAKBANK case (about +3%) as an acceptance test.

**Decisions on my four expected points:**

| # | Expected | Decision |
|---|---|---|
| 1 | The rule stated in the contract | ACCEPTED |
| 2 | The publisher adjusts from NSE's corporate-actions file, with KOTAKBANK as a named test | ACCEPTED, as story text. It is built in design's new `_platform/nse_actions.py` and in `fetch_nse.py`; the backend comes later. |
| 3 | No heuristic | ACCEPTED |
| 4 | Rebuild 33, regenerate the examples, list the changes | **Pending.** Today the served example still shows KOTAKBANK `y1` −79.15% and `h` 2,266, which now **contradicts the contract's own definition**. It must close with design's rebuild (the builder says so). Until then, W11's examples carry a known wrong value. |

**The pushback: no per-row `adjusted` flag. ACCEPTED** (reasoning, checked).
- Frozen 33 and 34 have no element that shows adjustment.
- `check_mapping` requires every field to serve an element, so a flag would be a field with no screen.
- `company.yaml` has an `adjusted` flag because its bars are raw sessions that a reader may re-adjust. Here the served
  figures are already derived, so the definition plus the publisher's test is the right guard.
- A visible "adjusted for a 5:1 split" marker would be a design change for the owner, as the orchestrator says.
