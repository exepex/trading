# P0 probe 4: physical settlement of stock F&O, and expiry-day margin rules

Market school stage P0 (response 327, section 4). Builder session session_01G5EqV95Wi7yHJ5Hgy2giaY, 22 Oct 2026.
Labels: **strong evidence** (a primary circular quoted; the quotes marked "checked" were re-read word for word in the
downloaded file), **some evidence** (secondary), **reasoning only**.

## Answer

1. **Delivery margin before a stock expiry:** 10% of the delivery margin at end of day E-4, 25% at E-3, 45% at E-2,
   70% at E-1, counted in trading days, on in-the-money long options (and potential deliverable positions). With a
   Tuesday expiry it starts at the previous Wednesday's close. After expiry the full cash-market margin applies to the
   delivery obligation. **[strong evidence: NCL consolidated circular 050/2026, checked]**
2. **No opt-out:** "do not exercise" for close-to-money stock options ended with the March 2023 expiry. Every
   in-the-money stock option is exercised and delivered. **[strong evidence: NCL/CMPT/55330, checked]**
3. **Expiry day, index options:** an extra 2% ELM on every short index option expiring that day, from 20 Nov 2024.
   **[strong evidence: SEBI 2024/132 para 5.6; NCL/CMPT/64639, checked]**
4. **Expiry day, calendar spreads:** no offset across expiries on the expiring contract's own expiry day, for index
   derivatives from 1 Feb 2025 and single stocks from about 4-5 May 2026. **[strong evidence: SEBI 2024/132 para 5.2
   (checked); SEBI letter of 5 Feb 2026 (checked); NCL 023/2026 (agent-quoted)]**
5. **The November 2026 stock expiry is Monday 23 Nov**, not Tuesday 24 Nov: 24 Nov is an NSE holiday. The delivery
   margin starts at Tuesday 17 Nov's close. **[strong evidence: `research/data/calendar/nse_sessions.csv:157`
   (NSE/FAOP/71777); NSE's contract list (see "How" below)]**

## A. Physical settlement and delivery margin

**Current rule.** NSE Clearing (NCL) Consolidated Circular 050/2026 (NCL/CMPT/73997), 30 Apr 2026, Part B, section
10.2.7 (https://nsearchives.nseindia.com/content/circulars/CMPT73997.zip). **[strong, checked]**

> "Delivery margins shall be levied on lower of potential deliverable positions or in-the-money long option positions
> four (4) days prior to expiry of derivative contract which has to be settled through delivery. Example- If expiry of
> derivative contract is on Tuesday, the delivery margins on potential in-the-money long option position shall be
> applicable from previous Wednesday EOD"

> "o 10% of Delivery margins computed on Expiry - 4 EOD
> o 25% of Delivery margins computed on Expiry - 3 EOD
> o 45% of Delivery margins computed on Expiry - 2 EOD
> o 70% of Delivery margins computed on Expiry - 1 EOD"

Also in 10.2.7 (agent-quoted from the same file):
- "In-the-Money options shall be identified based on the closing price of the security in the underlying Capital
  Market segment on the respective day"
- "Delivery margins at the client level shall be computed as per the margin rate applicable in Capital Market segment
  (i.e. VAR, Extreme Loss Margins, Additional Margins)"
- "The delivery margins shall be recomputed only on an EOD basis"
- "Post expiry, positions which are converted to settlement by delivery, margins as applicable in Capital Market
  segment (i.e. VAR, Extreme Loss Margins, Mark to Market margins) shall be applicable and levied as delivery margins."

**History.**
- NCL/CMPT/43262 (Circular 009/2020), 17 Jan 2020, moved the steps from 20/40/60/80% to 10/25/45/70%, from contracts
  expiring 30 Jan 2020. https://nsearchives.nseindia.com/content/circulars/CMPT43262.pdf **[strong]**
- Consolidated circular 043/2025 (NCL/CMPT/67750), 29 Apr 2025: same steps, Thursday example ("previous Friday EOD").
  So the move to Tuesday expiries changed the days, not the percentages. **[strong]**
- Physical settlement of stock derivatives rests on SEBI/HO/MRD/DP/CIR/P/2018/67, 11 Apr 2018 (cited by SEBI's master
  circular; the circular itself was not opened). **[some]**

**E-n counts trading days.** NCL's own example, Tuesday back to the previous Wednesday, is exactly four trading days.
**[strong]**

**Final settlement price:** "based on the last 30 minutes volume weighted average price of the relevant underlying
security/index across Exchanges" (consolidated 2026, section 4.4.1). **[strong, agent-quoted]**

**Do not exercise ended.** NCL/CMPT/55330 (Circular 008/2023), 20 Jan 2023, item g: "The facility of do not exercise
available for stock options on expiry date shall be discontinued." From the March 2023 expiry.
https://nsearchives.nseindia.com/content/circulars/CMPT55330.pdf **[strong, checked]** Earlier: NCL/CMPT/49775 (29 Sep
2021) withdrew it, NCL/CMPT/51971 (11 Apr 2022) brought it back. The 2026 consolidated circular has no such facility.

**Groww is stricter (some evidence: Groww help page via the research agent).** It lists "T-4: 10% ... T-3: 25% ...
T-2: 45% ... T-1: 70% ... T Day (Expiry Day): 100% of the full delivery value" and applies it to futures and short
options too. Whether Groww blocks each step at the start of the day or after NCL's end-of-day run is not stated; some
brokers block at the start of E-4, a day earlier than NCL. **A paper model must use Groww's schedule, one day early,
as the conservative case. [reasoning only]**

### Worked calendar: November 2026 stock monthly

The real case. 24 Nov 2026 is a holiday ("Prakash Gurpurb Sri Guru Nanak Dev", `nse_sessions.csv:157`, NSE/FAOP/71777);
NSE's contract list shows the November stock expiry as 23-Nov-2026. No other holiday falls in 16-20 Nov in the same
calendar file.

| Day | Step | Delivery margin (NCL, end of day) |
|---|---|---|
| Tue 17 Nov | E-4 | 10% |
| Wed 18 Nov | E-3 | 25% |
| Thu 19 Nov | E-2 | 45% |
| Fri 20 Nov | E-1 | 70% |
| Mon 23 Nov | E | expiry; then full cash-market VaR + ELM + MTM on the delivery (Groww: 100% on the day) |

If 24 Nov were a session (the brief's hypothetical): E-4 Wed 18, E-3 Thu 19, E-2 Fri 20, E-1 Mon 23, expiry Tue 24.

**Rupees [reasoning only, assumed margin rate].** One in-the-money long call, lot 500, strike 1,000: value at strike Rs
5,00,000. At an assumed 20% cash-market VaR + ELM rate, the full delivery margin is Rs 1,00,000: Rs 10,000 at E-4,
25,000 at E-3, 45,000 at E-2, 70,000 at E-1. Taking delivery then needs the whole Rs 5,00,000. A Rs 10,000-capped
paper trade cannot hold such a leg into expiry; a stock-option driver must exit before E-4 or be refused.

## B. SEBI's expiry-day rules, circular of 1 Oct 2024

SEBI/HO/MRD/TPD-1/P/CIR/2024/132, 1 Oct 2024, "Measures to strengthen Equity Index Derivatives framework for increased
investor protection". https://www.sebi.gov.in/sebi_data/attachdocs/oct-2024/1727786261636.pdf

| Para | Rule | Effective | Implementation |
|---|---|---|---|
| 5.6 | Extra ELM of 2% on short options expiring that day: "applicable for all open short options at the start of the day, as well on short options contracts initiated during the day that are due for expiry on that day" | 20 Nov 2024 | NCL/CMPT/64639 (Circular 125/2024), 21 Oct 2024: "an additional Extreme Loss Margin (ELM) of 2% shall be levied on short index options contracts" **[checked]**. Consolidated 2026 section 10.4.2 still says "short index options" **[checked]**: stock options do not get it. |
| 5.2.1 | "the benefit of offsetting positions across different expiries ('calendar spread') shall not be available on the day of expiry for contracts expiring on that day" **[checked]** | 1 Feb 2025 (para 5.2.4) | NCL/CMPT/65314 (Circular 146/2024), 29 Nov 2024 **[agent-quoted]** |
| 5.2.2 | On expiry day the worst scenario loss is computed separately for the expiring contracts and the rest; futures calendar ELM ignores an expiring leg as an offset | 1 Feb 2025 | as above |
| 5.2.3 | Spreads between later expiries keep the benefit on the near expiry day | 1 Feb 2025 | |
| 5.1 | "the upfront margin collection requirement shall also include net options premium payable at the client level" | 1 Feb 2025 | NCL/CMPT/65315 (Circular 147/2024) |
| 5.3 | Index position limits also monitored intraday, at least 4 snapshots | 1 Apr 2025 | |
| 5.4 | Contract value Rs 15 lakh at introduction, Rs 15-20 lakh on review | new index contracts after 20 Nov 2024 | |
| 5.5 | One benchmark index with a weekly expiry per exchange | 20 Nov 2024 | |

**Single stocks:** SEBI letter HO/47/15/11(2)2025-MRD-TPD1/I/4226/2026, 5 Feb 2026: "the benefit of offsetting
positions across different expiries shall not be available on the day of expiry for contracts expiring on that day for
single stock derivatives" **[checked]**, effective three months later. NCL/CMPT/72906 (Circular 023/2026, 20 Feb 2026)
gives 4 May 2026 **[agent-quoted, not re-checked]**.
https://www.sebi.gov.in/sebi_data/attachdocs/feb-2026/1770288869049.pdf

**Rupees for one NIFTY lot on its expiry day [arithmetic]:** ELM on a short NIFTY option goes from 2% to 4% of notional
(3% to 5% if more than 10% out of the money): at 22,811 x 65 = Rs 14,82,715, from Rs 29,654 to **Rs 59,309**, before
SPAN. Our calculator does not model this day (`fno/constants.py:318`).

## C. Later rules worth knowing (2025-2026) [strong, agent-quoted; not re-checked]

- SEBI/HO/MRD/MRD-TPD-1/P/CIR/2025/76, 26 May 2025: each exchange's equity derivatives expire on Tuesday or Thursday
  only; NSE chose Tuesday from 1 Sep 2025 (the NSE circular number not found; news reports only, **some**).
- SEBI/HO/MRD/TPD-1/P/CIR/2025/79, 29 May 2025: delta-based (future-equivalent) index-option limits per PAN, new MWPL
  for stocks, ban-period rules, futures pre-open; phased from 1 Jul 2025 to 6 Dec 2025.
- SEBI/HO/MRD/TPD/CIR/P/2025/122, 1 Sep 2025: intraday index-option limits (net Rs 5,000 crore, gross Rs 10,000 crore)
  from 1 Oct 2025. None of these binds a one-lot paper account.

## How

A research agent downloaded the circulars from nsearchives.nseindia.com and sebi.gov.in (22 Oct 2026); the quotes
marked "checked" were re-read in those files by this session. **One disclosure:** the agent also read NSE's
`/api/holiday-master` and `/api/option-chain-contract-info?symbol=RELIANCE` once each. Those are the website API reads
that probe 2 finds NSE's terms forbid. They were two single reads, not repeated; the holiday is confirmed from our own
calendar file, and no further NSE API read was made.

## Not verified

- Exactly what "lower of potential deliverable positions or in-the-money long option positions" nets, and whether NCL's
  steps also apply to futures and short in-the-money options (Groww applies its own schedule to them).
- When Groww blocks each step (start of day or after end of day).
- The NSE circular moving expiries to Tuesday; the text of SEBI 2018/67.
- Whether NSE's 2026 closing auction session (NCL/CMPT/73370) changes the close used for the daily in-the-money test.
