# References for the 15:45 report (research before v7)

Written by the designer session, 21 Oct 2026, after the owner rejected v6 ("too congested, too narrow, way too
bigger fonts ... a page should look spacious ... a lot of information is still not available ... take some
references"). Every claim below comes from a source opened in this session; where a source could not be opened, it
says so. Reasoning only unless marked.

## 1. What was opened

| Source | Edition | Opened as |
|---|---|---|
| ICICI Direct, "Derivatives view", 21 Oct 2026, 15 pages landscape: https://www.icicidirect.com/mailimages/Derivatives_view.pdf | evening wrap of the 20 Oct session, read the next morning | PDF, pages 1-5 rendered and read |
| Kotak Neo, "Derivatives Daily", 13 Jul 2026, 6 pages A4: https://www.kotakneo.com/uploads/Derivatives_Daily_00069_13_Jul_2026_3f9bb960d2.pdf | morning note (file made 09:07 IST Monday) on Friday's data | PDF, pages 1-2 rendered and read |
| HDFC Securities, "Daily Derivative Overview", 7 May 2024, 11 slides: https://www.hdfcsec.com/hsl.docs/HSL_Daily%20Derivative%20Outlook%20On%20Markets_07052024-202405070911312972662.pdf | morning note (made 09:11 IST) on the previous close | PDF, pages 1-2 rendered and read |
| Angel One, "Daily Market Insights", 13 Jul 2026, 4 slides: https://partnerassist.angelone.in/assets/docs/reports/equityreport/Equity%20Morning%20Report%20-%2013th%20July%202026.pdf | morning note (made 08:56 IST) | PDF, pages 1-2 rendered and read |
| Motilal Oswal, "Derivatives update for Wednesday, 5th July 2023": https://www.motilaloswal.com/learning-centre/2023/7/derivatives-update-for-wednesday-5th-july-2023 | evening wrap (posted 13:33 UTC the next day) | HTML, read by an agent |
| Zerodha, "The Daily Brief" archive and one post: https://thedailybrief.zerodha.com/archive and https://thedailybrief.zerodha.com/p/the-rbis-3-front-war-on-inflation | evening e-mail (markets explained, not a derivatives note) | HTML, read by an agent |
| IDBI Direct daily derivative reports (search results only; the PDF returned HTTP 503): https://idbidirect.in/IDBIAdmin/Pdf/Derivative%20Report%2027-07-2026-27-July-2026-1655179035.pdf | daily, labelled by trading date | search summary only |
| Business Standard "F&O Insights" (search result, stamped 09:24 IST Monday on Friday's data) | morning | search summary only |
| Sensibull https://sensibull.com/ (feature list) | product, not a note | HTML, read by an agent |

Not opened: Moneycontrol "Trade setup" (host refuses automated reads), Opstra and Sensibull's app (JavaScript apps,
empty without login), Dribbble and Behance searches (bot challenge / HTTP 403), broker app screenshots (no page found
that describes them). So the "image" research the owner asked for is limited to the four rendered broker PDFs; the
visual facts below come from looking at those pages, not from design galleries.

## 2. What the first screen shows (in order)

- **ICICI Direct (p.1-2)**: p.1 is the broker's open calls (intraday and weekly futures ideas with target and
  stop-loss) in two small tables. p.2 "Derivatives Insights": a one-line verdict as the heading ("Nifty: 22800 should
  act as an immediate support..."), six bullets of prose (what happened, GIFT Nifty gap, resistance and support,
  put and call writing strikes, VIX with a warning level, FII flows and net futures position, the weekly view), and
  on the right **a snapshot table**: rows Spot, Future, Basis, OI (lakhs), PCR; columns Close, Pvs Close, % Change.
  Then "Key Events & Observations" (US yields, FII shorts, Brent, results today).
- **Kotak Neo (p.1)**: masthead, "Commentary" with a tiny table (Index, Close, %Ch for Nifty and BankNifty; provisional
  FII/DII cash in crore) beside four bullets (close and support, OI concentration strikes, weekly PCR from/to, FII net
  short change). Then two charts side by side (call and put OI by strike; PCR line over total OI bars), then FII net
  position by instrument (bar inside the table cell) and FII net index options OI by day. p.2 is a full option
  chain with build-up colours, max pain table and plot.
- **HDFC Securities (p.2 after a cover slide)**: "F&O HIGHLIGHTS", a one-line headline ("LONG BUILD UP IS SEEN BY
  FIIs ..."), an action line in blue ("ACCUMULATE LONGS ON DECLINE WITH SL OF 22400"), five bullets (close with points
  and %, futures build-up with OI % change, PCR from/to, call and put writing zones, FII index futures net buy in
  crore and contracts), then a six-column table: Index, Expected trend, CMP, Buy/Sell, Stop loss, Target.
- **Angel One (p.1, the whole note is one slide)**: a headline in yellow on blue ("GIFT NIFTY -190 points, suggesting
  a NEGATIVE start"), a "Global Cues" strip (NASDAQ 100 and DOW with points and % and an arrow), "As on" date, then
  two side-by-side cards NIFTY 50 and BANK NIFTY, each "Intraday Trend: Volatile" and "Key Levels: 24000-23930
  (Support) and 24280-24320 (Resistance)" over a daily candle chart with moving averages, then a "Market Monitor"
  band (long build-up and short build-up names).
- **Motilal Oswal**: prose only: VIX from/to with %, Nifty PCR from/to, max call and put OI strikes, "broader" and
  "immediate" trading ranges in zones, the same for Bank Nifty, FII segment activity, FII and DII cash in crore,
  FII long-short ratio, hold-above levels.
- **Zerodha Daily Brief**: title, "Plus:" second line, hero image, a numbered summary with the key numbers inline,
  then long stories with static chart images each with a "Source" caption. Black on white, one link colour, no
  red/green.

## 3. Data items every derivatives note carries

| Item | ICICI | Kotak | HDFC | Angel | Motilal |
|---|---|---|---|---|---|
| Index close, change in points and/or % | yes (table) | yes (table) | yes (bullet) | implied (cards) | CMP only |
| Futures price and basis | yes | chain CMP | futures CMP | no | no |
| OI and OI change (index futures) | yes | charts | % change | no | segment prose |
| PCR, as from → to | yes | yes | yes | no | yes |
| India VIX | bullet with warning level | no (p.1) | no (p.2) | no | yes, from → to |
| Max call and put OI strikes | yes (writing strikes) | yes | yes (zones) | key levels zones | yes |
| Max pain | no (p.1-5) | yes, table and plot | no | no | no |
| Support / resistance as ZONES | yes | yes | yes | yes | yes |
| FII/DII cash in ₹ crore | yes, chart | yes, table | FII futures only | no | yes |
| FII index futures net position / long-short | yes | yes | yes | no | yes (ratio) |
| Long/short build-up stock lists | yes (p.4) | p.2 | p.3+ | yes (band) | no |
| Ban list | yes | later pages | later | no | no |
| Trade idea with stop and target | yes (p.1, p.3) | no (p.1-2) | yes (table) | no | hold-above levels |
| Global cues (US indices, yields, Brent) | yes (events box) | no | no | yes (strip) | no |
| Source line and disclaimer | every page | footer | footer | p.2 | link |

What NONE of them carries: a check of their own previous call against the close, or a track record. Our ✓/⚠/✗
record is unique; the research agent's note "no broker scores its own range calls" matches what was opened.

## 4. Visual conventions seen

- **Type is small and the page is spacious.** The PDFs run at roughly 9-11 pt body in tables and bullets, with one
  heading per block at 14-18 pt; whitespace and rules do the separating, not big type. Angel's one-slide note has
  the largest type (the headline) and the least text.
- **Tables for numbers, bullets for the read.** Numbers never sit in prose when a table can hold them (ICICI's
  Spot/Future/Basis/OI/PCR, Kotak's Index/Close/%Ch, HDFC's Index/Trend/CMP/Buy-Sell/Stop/Target). Each table has
  one bold header row, right-aligned numbers, 2-5 rows. The read (why, what next) is bullets of one or two sentences.
- **Change is shown as absolute and %**, and as "from X to Y" for PCR and VIX. Levels are zones ("22500/22700",
  "24000-23930") and named support or resistance. Numbers use Indian commas in tables; strikes often without commas.
- **Colour is a brand colour plus green/red for up/down only.** ICICI: orange headers, blue body, no green/red in
  tables; Kotak: red masthead, green % changes, blue/yellow bars; HDFC: navy headers; Angel: blue/yellow headline,
  green/red arrows and bands. Charts are static images with one or two series.
- **One screen = one verdict + levels + a snapshot table**; everything else is further down. Two indices side by
  side (Angel) or one after the other (ICICI, Kotak).
- **Source and date on every page**, "as on" for the data date, analyst names, SEBI registration, classification.

## 5. Morning or evening? (the orchestrator's question)

Evidence: Angel (08:56), HDFC (09:11), Kotak (09:07) and the Business Standard column (09:24) are **morning notes
built on the previous session's close, OI, PCR and flows**, plus overnight global cues and GIFT Nifty. ICICI's
"Derivatives view" and Motilal's update are **evening wraps of the day just closed**, read before the next open.
No broker opened publishes at 15:45 on the same day's 3 pm data: the official close, OI, PCR and flows all land
after the close, so a 15:45 note either shows yesterday's OI and flows (stale next to today's price) or none.

My view (reasoning only, the owner decides): keep the 15:45 note as the FORECAST note (our range for the next
session must exist before the close to be honest and sealed), but make it small: price at 3 pm, our range, today's
call check against the 3 pm price, the track record. Move the broker-style data (official close, OI, PCR, max pain,
flows, participant OI, build-ups) to a **post-close evening wrap** when NSE has published it, and keep a **09:15
morning line** (FL1-2's plan) for global cues, GIFT Nifty and the levels for the day. Two editions, each with the
data that exists at that time, never a stale number posing as today's.

## 6. Content proposal for our note, with availability (builder's facts, 21 Oct 2026)

| Item | Belongs in | Source | At 15:45 today | Status |
|---|---|---|---|---|
| NIFTY / BANKNIFTY 3 pm price and change vs previous close | 15:45 note, snapshot | A4 3 pm quotes, archived closes | yes | available |
| Official close | evening wrap | NSE allIndices / bhavcopy | evening (or add one 15:45 read) | small new part |
| India VIX about 3 pm and change | 15:45 snapshot | A15 / A4 | yes | available |
| Our range (most likely, almost certainly) for next session and in 3 sessions | 15:45 note, main | G13b | yes | available |
| Today's call check (3 pm price vs the range forecast the session before) | 15:45 note, top | G13b timeline + 3 pm price | yes once the builder adds today's outcome | small change |
| 30-day track record with hit count, target and average width | 15:45 note | G13b | yes (width to add) | small change |
| "Why it missed" reasons | 15:45 note, details | FL1 miss reasons | yes | available |
| PCR, biggest call/put OI strikes, max pain | evening wrap; 15:45 only as "yesterday's" | chain_expiries.py (bhavcopy) | yesterday's | available (today's after an A4 OI read at 3 pm) |
| Futures price and basis | snapshot | A4 monthly quotes | to confirm | to confirm |
| FII/DII cash flows, FII index futures net, participant OI | evening wrap | A8 participant OI, FII/DII cash | yesterday's | available (yesterday) |
| USD/INR, US 10-year | morning line / snapshot | A17 | yes (last print) | available |
| Brent | morning line | A17 | lags about a week | show date, or omit |
| US closes | morning line | A17 (private, allowed) | overnight | owner's display approval |
| GIFT Nifty, Asian markets | morning line | A17e, A22 | no | coming |
| Contracts: chance to finish in the money per strike (market-implied, 1 − cdf for calls, cdf for puts), with a calibration table across past expiries (buckets, share finished ITM, contracts, expiries, interval); no per-day ✓/✗ per contract | note, below the index cards (owner's choice, 21 Oct) | G13 per-strike cdf, price, IV, fair value; nearest two monthly expiries | yes for NIFTY (live from 13 Oct, history from 2019); BANKNIFTY/FINNIFTY/MIDCPNIFTY from 19 Oct ("too few expiries yet") | available (G13 builder, 21 Oct) |
| Next-session premium range per contract | not yet | would be a new forecast with a vol assumption | no | later story (1.5-2 days, judged) |
| Trade ideas with stop and target | never (research only) | — | — | out of scope |
