# P0 probe 2: do NSE's and Groww's terms allow automated reading at the school's volume?

Market school stage P0 (response 327, section 4). Builder session session_01G5EqV95Wi7yHJ5Hgy2giaY, 22 Oct 2026.
Pages fetched live on 22 Oct 2026; the clauses below were checked word for word against the saved copies. Labels:
**strong evidence** (the exact clause quoted), **some evidence**, **reasoning only**. This is a reading of public
terms, not legal advice.

## Answer

| Source | Volume asked | Verdict |
|---|---|---|
| **NSE website** (nseindia.com JSON endpoints) | about 800 stock option-chain requests a day (200 stocks x 4 slots), plus index chains | **Forbidden. [strong evidence]** NSE's terms ban "any systematic or automated data collection" on the website, with no exception for personal use and no volume threshold. 800 a day and "a few a day" are both covered. |
| **Groww Trade API** | option chains and an LTP batch every 15 minutes, about 800 chains a day | **The volume is within Groww's published limits [strong evidence]** (probe 1). **Whether read-only use fits the contract is unclear [some evidence]**: the terms say API connectivity is "only" for automating buying and selling. Storing the data is a second, smaller doubt (below). |

**So the stock-option survey in P3 cannot be built on NSE's website, and P0b's NSE-based capture probes must not
start.** The only open route is Groww's API, subject to the doubt above, which the owner can settle by asking Groww in
writing. Nothing here is to be got around: no rotating addresses, no added keys to multiply limits, no disguised
clients.

## 1. NSE

Pages (fetched 22 Oct 2026; HTTP 200 unless noted):
- Terms of Use: https://www.nseindia.com/static/nse-terms-of-use ("Updated on: 29/10/2025"). The old address
  `/terms-of-use` now answers 404.
- Disclaimer: https://www.nseindia.com/static/nse-disclaimer ("Updated on: 21/10/2025").
- Copyright: https://www.nseindia.com/static/nse-copyright ("Updated on: 21/10/2025").
- Data policy: https://www.nseindia.com/static/market-data/nse-data-policy ("Updated on: 11/12/2025").
- robots.txt: https://www.nseindia.com/robots.txt.

**Clauses [strong evidence]:**

> "User is granted a non-exclusive, non-transferable, limited right to access the Website / Mobile Application and
> avail the services provided by NSE through the Website / Mobile Application. User is prohibited to conduct any
> systematic or automated data collection activities (including scraping, data mining, data extraction and data
> harvesting) on or in relation to our Website / Mobile Application." (Terms of Use)

> "User acknowledges, agrees and undertakes that it shall not, in any form and manner, use or make the data or Content
> available on the Website / Mobile Application, for any gaming, virtual trading or simulation activities under any
> circumstances whatsoever." (Terms of Use)

> "... Unless the information or Content is available for download, not to aggregate, copy or duplicate in any manner
> any of the content or information which is available on Website / Mobile Application." (Terms of Use)

> "Users may view, print copies and download the Content for personal, non-commercial or educational purpose without in
> any way amending, altering, deleting or modifying any part of the Content ..." (Copyright)

> "Research-oriented data (not including any data for commercial, speculative or investigative purposes), can be
> downloaded/accessed/made available without cost, provided it does not exceed in aggregate the volume threshold of 2GB
> set by SEBI via SEBI Circular dated December 20th, 2024. ... Access/use/download of research-oriented data is
> restricted to individuals from accredited academic institutions, recognized research organizations and think tanks."
> (Disclaimer)

robots.txt: `User-agent: *`, `Allow: /`, `Disallow: /market-data-test`. It does not block `/api/`, but robots.txt is
crawler etiquette, not a licence; the Terms of Use govern. **[reasoning only]**

**Reading:**
- The automated-collection ban is plain and has no personal-use or volume exception. **[strong evidence]**
- The copyright page's "personal, non-commercial" permission covers a person viewing, printing and downloading; it does
  not cancel the explicit ban on automated collection. **[reasoning only]**
- The "virtual trading or simulation" clause plausibly covers paper trading on NSE website data. The clause does not
  define the words. **[some evidence]**
- The free research-data route is for accredited institutions and excludes "speculative" use. It does not apply to the
  owner. **[strong evidence]**
- The legitimate route for systematic NSE data is a paid licence from NSE's data business (the data policy's
  "Subscribers" and "Relevant Agreement"). Price and terms not checked. **[some evidence]**
- An unauthenticated plain request to `/api/option-chain-equities?symbol=RELIANCE` returned HTTP 200 with an empty
  body: the endpoint does not serve a plain automated client. Not pursued. **[strong evidence: one request by the
  research agent]**

### This reaches beyond the school: what the project already reads from NSE [strong evidence: files]

The same clause applies to reads the project runs today, outside this story's scope. Listed so the owner and the
orchestrator can decide; no change is made here.
- `fno/providers/public.py:20-28`: NSE option chains (story O6's `quotes record --source nse`), sent with a desktop
  browser `User-Agent` and a warm-up visit to `/option-chain` for cookies. Presenting a script as a browser to a site
  that bans automated collection is hard to defend. **[reasoning only]**
- `fno/preopen/parts.py`: `/api/market-data-pre-open?key=FO` and GIFT Nifty via `/api/NextApi/...` (story A22).
- `fno/vix_history/source.py` (VIX history), `fno/circulars/feeds.py` (circulars), `fno/filings/sources.py`
  (corporate actions, announcements, board meetings), `fno/storage/snapshot_source.py` (FII/DII).
- `fno/storage/raw_source.py`: archive files on `nsearchives.nseindia.com` (F&O bhavcopy, participant OI, SPAN files,
  index closes). These are files NSE offers "for download", so the "unless ... available for download" carve-out
  helps them; but fetching them by script is still "automated data collection". **Unclear [some evidence]**.

**Recommendation [reasoning only]:** the owner decides whether to (a) stop NSE website API reads, (b) keep only the
daily archive downloads (closest to "available for download"), or (c) ask NSE or buy a data licence. Until then, the
school adds **no** new NSE reads.

## 2. Groww Trade API

Pages (fetched 22 Oct 2026, HTTP 200): https://groww.in/trade-api, https://groww.in/trade-api/docs/curl (rate limits),
https://groww.in/trade-api/docs/python-sdk, https://groww.in/trade-api/docs/python-sdk/live-data,
https://groww.in/terms-and-conditions ("last updated on August 19, 2026"). There is no separate trade-API terms page
(several candidate addresses answer 404); the API terms are section "XI. ALGORITHMIC TRADING" of the main terms.

**Clauses [strong evidence]:**

> "You shall use API connectivity only for implementing automated trading systems, computer algorithms, or other
> software-based trading solutions to automate the buying and selling of securities/ contracts in the secondary
> markets." (Terms, XI)

> "You shall use the algo only for yourself or your family i.e. self, spouse, dependent parents and dependent children
> and not for other users/investors." (Terms, XI)

> "You agree that You shall not copy, reproduce, sell, redistribute, publish, reverse engineer, enter into a database,
> display, perform, modify, alter, transmit, license, create derivatives from, transfer or in any way exploit any part
> of any information, content, materials, services available from or through the Platform, except that You may
> download the Platform for Your own personal, internal, non-commercial use and limited to the extent that are
> permitted by the Terms of Use." (Terms, general)

> "The rate limits are applied at the type level, not on individual APIs. ..." Live Data (Market Quote, LTP, OHLC):
> 10 a second, 300 a minute. (docs/curl, "Rate Limits"; full table in probe 1)

Product page: "Who can use Groww APIs? Anyone with a Groww account!" and "Groww provides APIs for market data,
historical data, order placement, portfolio management, and margin monitoring." The paid plan lists "Full Live Data
API (LTP, Quote, OHLC)".

**Reading:**
- **Volume:** 800 chains a day plus 4 LTP calls every 15 minutes is far under 300 a minute. **Allowed by the published
  limits [strong evidence]**, with the shared-key timing problem in probe 1.
- **Purpose:** the literal "only for ... automate the buying and selling" does not fit a tool that never orders.
  Groww's own product page sells market data as an API feature, which points the other way. **Unclear [some
  evidence]**. The fix is a written question to Groww support: "May I use the Trade API's live-data and option-chain
  calls for my own research and paper trading, with no orders?"
- **Storage:** "enter into a database" and "redistribute" are literal. Keeping raw quotes in the owner's own Drive for
  the owner's own research is arguably "personal, internal, non-commercial"; posting values to anyone else, or into the
  dashboard repository if it is public, would be redistribution. **[some evidence]** Same written question should ask
  about storing quotes.
- **Second key:** the docs say "You can manage all your keys from the same page", so several keys look possible
  **[some evidence]**; whether each gets its own budget is not stated. Using extra keys to multiply the rate limit would
  go against the limits' purpose; the school should not plan on it. **[reasoning only]**

## 3. SEBI's retail algo circular (orders only)

SEBI circular SEBI/HO/MIRSD/MIRSD-PoD/P/CIR/2025/0000013, 4 Feb 2025, "Safer participation of retail investors in
Algorithmic trading" (https://www.sebi.gov.in/sebi_data/attachdocs/feb-2025/1738665456458.pdf):

> "Algos developed by tech-savvy retail investors themselves, using programming knowledge, shall also be registered
> with the Exchange, through their broker, only if they cross the specified order per second threshold."

It regulates **orders** only; it sets no limit on reads. Our tool places none. **[strong evidence from its wording]**

## Not verified

- Whether Groww treats read-only use as allowed (needs Groww's written answer).
- Whether Groww's limits are per key or per user, and whether the option chain counts in Live Data.
- Whether NSE gives any individual permission for automated reads; none was found. The price of an NSE data licence.
- When NSE's automated-collection clause was added (live pages only; no archive history checked).
