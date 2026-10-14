# Judge 76: W14 internals 2 (omenix-dashboard, branch before merge)

Date: 14 Oct 2026 (UTC). Repository exepex/omenix-dashboard, branch `story/w14-internals-2` at 9a1d587 (draft PR #6),
based on main 11ca4a3. Scope: judge 70's NOT MET list:
- no "bar", "threshold", "regime rule" or per-band thresholds on Trade story, Stock strategies or Track record;
- the same allow-list pattern on the lifecycle, strategies and track-record endpoints;
- the scan extended to these words.

## Verdict: FAIL, two must-fixes

The internals are gone from the three screens, and the guards catch my plants. But the new word filter now runs over
every payload and rewrites or withholds third-party text: news headlines, filings and company text. `npm test` also has
one failure.

## Gates (my runs; `.next/cache` cleared before each plant build)

- `npm ci`, `npm run build`: pass.
- **`npm test`: 461 passed, 1 failed:** `lib/assistant/tests/explainer.test.ts`, "a question is answered from a read
  tool, cites a verified id and logs its real cost". It expects `answered` and gets `not in data`.
  - The same file passes 22 of 22 on main 11ca4a3.
  - Cause: `runRead` (`lib/tools/reads.ts`) now passes every read through `publicView`, which turns the trade ID
    `acc:rule.model_news.v1:…` into `acc:rule-1:…` (my probe). The scripted model then cites the backend ID it never
    saw.
  - In real use the model would see and cite the public ID, so this is most likely a stale test, not a broken answer.
    It is still a red gate, and the builder's report did not mention it.
- `tools/check_code_size.mjs`: pass.
- Harness `--only w14-internals`: 24 cases, 0 failed. I did not re-run all 243.

## Must-fix

**1. The filter rewrites text that is not ours.**
- `publicView` runs at every boundary: `handler.ts` for every `/api/v1` page, `api-client.ts` for every page read,
  `reads.ts` for every assistant read tool, and the fixture adapters.
- `withPublicWords` rewrites any string with a space: "regime" becomes "market mood", "bars" becomes "daily prices",
  and a sentence with "bar", "threshold" or a chance tied to a percentage is replaced by "(withheld: this text said how
  a strategy decides)".
- My probe on a news payload (`node --experimental-strip-types`, the branch's own `publicView`):

  | Headline in | Headline out |
  |---|---|
  | "Budget 2026: most taxpayers move to the new tax regime" | "… move to the new tax **market mood**" |
  | "Gold bars see record demand ahead of Diwali" | "Gold **daily prices** see record demand …" |
  | "SEBI raises F&O contract size threshold to Rs 15 lakh" | **withheld** |
  | "Nifty crosses 25,000 bar for the first time" | **withheld** |

- The News page reads through `usePage` (the api-client), so these show on screen. The assistant's read tools also hand
  the changed text to the model.
- "New tax regime", "price band", "threshold" and "bars" are common words in Indian market news. This falsifies real
  news, and "withheld: this text said how a strategy decides" is untrue for a headline.
- **Fix (reasoning only):**
  - apply the word filter only to fields that hold our strategies' own sentences (an AI trader's reason, a back-test
    note, a prediction's reason), by field name or by page;
  - leave third-party text (news, filings, company descriptions, event names) untouched;
  - keep dropping the setting keys everywhere;
  - add one test: a news payload with "tax regime", "threshold" and "bars" passes through unchanged.

**2. `npm test` must pass.** Update the explainer test to cite the ID the read tool now returns, and say so in the
claims.

## Per item

| Item | Check | Result |
|---|---|---|
| Trade story: no "its bar" / "below its bar" | Removed (`story.tsx`, `lifecycle-page.tsx`). My plant of a fixed "its bar is 55%" sentence in the story card is **caught** by `w14-internals-paper-portfolio-v3-story`. `w14-internals-lifecycle-reliance` alone does **not** catch it: that case never opens a story. The story is covered only through the paper-portfolio case | MET |
| Stock strategies tooltips | Removed (`strategies-page.tsx`) | MET (by read and the scan) |
| Track record: per-band thresholds | The "Would buy when chance ≥" column becomes a neutral "Variant" letter. The letters keep only the order of the thresholds, not their values, which I accept | MET |
| Endpoints, allow-list | A registry entry is reduced to `PUBLIC_KEYS` (allow-list). **A row field outside the registry is dropped by a deny-list** (`SETTING_KEYS`: `threshold`, `bar`, `parameters`, …). A new row setting under another name (say `min_prob: 0.55`) would pass to the API; the tests plant only the listed keys plus a sentence. My plant removing `threshold` from `SETTING_KEYS` is caught (7 more failures) | PARTLY |
| Scan extended | `internal-words.ts` is one list for the API test and the screen scan, covering "bar", "threshold", "regime" and rule-tied numbers. It sees the stored mockups (its own "not blind" test) | MET |

**On the deny-list (should fix, not blocking):** judge 70 asked for an allow-list. For whole rows that is heavier,
because rows carry many public fields. The honest minimum is a test that fails when a stored row carries any numeric
field not on a known list for that endpoint, so a new setting cannot pass silently. Otherwise say plainly in the claims
that row settings are a deny-list.

## Claims vs reality

| Claim | Reality |
|---|---|
| "W14 harness at 243/243" | Not re-run in full; `w14-internals` is 24 of 24 for me. **`npm test` is not green** (1 failure) |
| No internals on any screen or API answer | True for our strategies, by my plants. But the same filter changes others' text (must-fix 1) |
| Allow-list on the three endpoints | Allow-list for registry entries only; deny-list for row fields |

## Project rules

- One list of words (DRY) and one public view at each boundary.
- Files within 350 lines (the check passes).
- The owner's "internals stay private" rule is served. "Show the news as it is" is broken by the global word filter.
