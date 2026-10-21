# Response 299: every earlier decision the v4 freeze rests on, re-checked against today's direction

From the R2/G7 builder (session 0185gR5DmoDh2zBAvgRU4CEB), 22 Oct 2026 IST, for the owner through the orchestrator.
Asked by the owner on 21 Oct (DESK_DECISIONS 195b3f0f): "we need to see if those decisions are still relevant and
still acceptable as per new design changes and new expectations ... We should not stop ourselves just because we took
certain decision in the past."

Each earlier decision is checked against today's direction:
- the **Innovation Lab** (93e01804): strict, pharma-style stages; nothing reaches the owner until proven;
- **sharper ranges**, study GR1 (3b03e2c5);
- **use the data we collect**, including markets outside the US (2f1e3b63, 3532b997);
- the **report's purpose** (194aa8b3): can tomorrow's and the 3-day forecast be trusted; NIFTY and BANKNIFTY.

Evidence marks: **strong** (measured on our data), **some** (measured, small sample), **reasoning** (no measurement).

## First, what v4 is, and a correction to my message of last night

**What v4 is, in plain words.** v4 is a fixed rulebook for scoring NIFTY volatility forecasts every day. It asks
questions such as "how much will NIFTY move tomorrow?", "will it move 2% or more?" and "will India VIX be higher in 5
days?". A forecaster earns a "beats the baseline" verdict only under very strict statistics. Freezing it means the
rules and code are locked (by their SHA-256 fingerprints) before any counted forecast, so nobody can bend them
after seeing results.

**Correction.** Last night I told the orchestrator V6b could be claimed in "about 3-4 years" and V1 in "about 1.7".
That was wrong. Those figures come from section 11 D, and section 11 D uses an assumed noise level that judge 128
showed is far too low for these questions. Judge 128's measured numbers (strong for this forecaster):
- V6b would need about **14-22 years**, even if its full back-filled skill is real;
- V6a and V1 can effectively never be claimed;
- V2 needs 8-22 years;
- V7 is descriptive only.

**So no v4 member will say "proven" in useful time.** v4's real value is a sealed, honest, daily scored record of how
our rule forecasts do against simple baselines: an early-warning yardstick, not a proof machine. Item 9 below fixes
the protocol sentence that still says otherwise.

## The decisions, one by one

| # | Earlier decision (row) | What it says, plainly | Verdict | Why (evidence) |
|---|---|---|---|---|
| 1 | Item A (15 Oct, "A accept") | A "yes" at the May 2027 review needs a strict 2% error rate | **Keep** | Fits the Lab's strict bar. In practice no member can reach "yes" by May 2027 anyway (judge 128; strong) |
| 2 | Item B (15 Oct) and the stop-rule review of about 31 May 2027 | With no power report at the review, keep only the code forecasters (cut the AI) | **Change, small** | The Lab now decides what runs, with no AI cap for now (93e01804). Keep the text, but make the review's result advice to the owner, not an automatic cut (reasoning) |
| 3 | Item C (15 Oct) | V2's main baseline uses an end-of-day option-volatility stand-in from 1 Jan 2024 | **Keep** | Affects V2 only, and V2's baseline is not built yet (G7b part b), so V2 is dormant at the freeze (reasoning) |
| 4 | Item D (15 Oct, "3 B") | A stricter pass rule, because these losses are lopsided | **Keep** | Fits "strict, pharma-style". Its cost (almost nothing claimable) is stated above (strong) |
| 5 | Item E (15 Oct, "option 2") | Periods where more than 10% of days moved 2% or more give no verdict | **Keep** | Removes the known false results of the 2020-21 crash, at a cost of 13-16% of periods (some evidence: one crash) |
| 6 | Misses: observed days only, 10% caps; Test A stays "undecided" while a member is "undecided, operations" (15 Oct) | A missed day is never filled in; a forecaster missing over 10% of its days is not judged | **Keep** | A filled-in day would call a forecaster that never ran "useless" (shown from the code in response 144; strong). Matches the Lab's "no shortcuts" |
| 7 | Misses count from the declared start (16 Oct) and from go-live (21 Oct) | A forecaster cannot skip hard days by starting late | **Keep** | Written in piece 1b. Same reasoning as 6 |
| 8 | V6b stays a scored member (15 Oct, "New breadth track") | The 5-day 2%-move question is judged | **Keep, with the true expectation** | Judged, but realistically never claimed (about 14-22 years, judge 128; strong). It stays useful as a scored yardstick |
| 9 | Section 11 D's sentence "only V6b can be claimed, slowly" (protocol text, 15 Oct) | Suggests V6b is claimable in 3-4 years | **Change** | Judge 128: it rests on an assumed noise level of 3 against a measured 61.5, and "should not guide the owner's choice" (strong). Replace it with judge 128's numbers before the freeze; I add this to piece 1b |
| 10 | The family: V1, V2, V6a, V6b, V7 × rules, hybrid and AI slots; V3-V5 reported only (15 Oct) | Which questions can earn a verdict | **Keep** | v4 asks about NIFTY volatility. The owner's report asks "is tomorrow's and the 3-day price range right?" for NIFTY and BANKNIFTY (194aa8b3); G13b and GR1 answer that. Reshaping v4 to 3 days or BANKNIFTY means re-running every calibration study: about 2 weeks and a new judge round (reasoning). Better: v4 stays the volatility yardstick; ranges are judged by the Lab's own measure |
| 11 | The clock: 14:30 capture, 14:40 pack, 15:10 deadline, 15:15 snapshot; honest times (15 Oct) | Every forecaster sees the same data at the same moment, early enough for a desk trade | **Keep, with one warning** | It is needed for desk decisions before the close. **Warning:** G13b's ranges are made at 15:45 with the day's close. Comparing them with v4's 14:30 forecasts is not like for like, because G13b sees 75 more minutes (reasoning) |
| 12 | Flag a sharp move after 14:30; do not block (15 Oct) | A day when NIFTY moved over 0.61% between 14:30 and 15:15 is marked, not dropped | **Keep** | X is measured on 1,661 sessions (strong) |
| 13 | Lateness (15 Oct) | A day the system was late is excluded for everyone; a forecaster that is late is charged a miss | **Keep** | Fair to every family (reasoning) |
| 14 | A2 dropped (16 Oct evening, orchestrator) | Each day is labelled only "A" (complete pack by 14:40) or "system_late" | **Keep** | The 14:30 intraday mark has no India VIX and no next monthly on expiry days, so it can never make a complete pack (some evidence: the orchestrator's check of that mark's fields, 16 Oct) |
| 15 | When the routine moves to 14:05: "before the freeze, proven on real days first" (16 Oct, row 251) against "from the go-live day" (21 Oct) | Two rows disagree | **Change: switch on before the freeze** | If the first counted day is also the first real run, any setup fault becomes a counted miss. The code counts only live forecasts of days **after** "Frozen on", so live forecasts made before the freeze are never counted (`scoring._counted`; strong, read in code). Proposal: move the routine to 14:05 and set the weather and v4 live dates now; freeze once 3 sessions run clean; go-live the next session. This also starts using the VIX and intraday data at once (2f1e3b63) |
| 16 | The core engine's 10-day go-live gate (16 Oct, row 247) | 10 trading days in a row with no silent failure before "live" | **Question** | Does v4's go-live wait for it? My view (reasoning): no. Item 15's clean pre-freeze sessions plus the 10% miss cap protect the scoring. The 10-day trial is for the whole engine and runs in parallel |
| 17 | G7b wording (i): V5's settlement level (judge 258 PASS) | Counts only if first seen in the archive or the release log; never stamped "now" | **Keep** | Prevents using a number before it was really known (reasoning). V5 is reported only |
| 18 | G7b wording (ii): trailing and EWMA baselines | Use data up to the session before the day | **Keep** | The day's own close is not known at 14:30 (strong: by the clock) |
| 19 | G7b wording (iii): a flagged IV30 | A single-expiry volatility reading gives no implied baseline that day: missing and counted, never filled | **Keep** | No made-up values (reasoning). Affects V2 and V3 only |
| 20 | G7b wording (iv): V4's and V5's base rates | Use live outcomes only, so about 2 years with no value | **Keep** | V5's history has no bid and ask prices, so the spread rule cannot apply (strong). Both are reported only |
| 21 | V6's rules slot is the weather model `weather_vix_v1` (decision 70; 15 Oct "operative, unproven"; 26-week check) | The scored 2%-move forecaster uses yesterday's India VIX close and the last 3 years' tail shape | **Keep, and say what it does not use** | It uses VIX only. Events, US and Asian markets and FII/DII flows feed no scored v4 number, only the weather card's colour. Adding them now means a new method, a new back-fill and a judge round (about 1-2 weeks), and the Asia data (A17e) does not exist yet (reasoning). Better: freeze it as the plain VIX benchmark. Data-rich methods enter the Lab as candidates scored on the same v4 questions beside it, and beat it or not |
| 22 | VIX close missing: the scoring stops with an error, never a silent void (16 Oct, orchestrator) | A missing VIX close blocks the report until fixed | **Keep** | A quiet gap would shift the regime counts (reasoning) |
| 23 | Freeze with V6a and V6b (V1 when A16 is ready), V2-V5 later (16 Oct) | The order of members | **Keep** | V1's rules slot is registered at the freeze, and its days are scored as A16's daily RV comes in. V2 stays dormant until its baseline exists |
| 24 | At the freeze, the AI's v4 run replaces the v2 AI run (16 Oct, "v4 replaces v2") | The v2 AI forecasts stop at the freeze | **Change** | The owner chose (21 Oct) to freeze with the AI slots unregistered, because G11's v4 run is not live. Stopping v2 at the freeze would leave no AI forecasts at all. Proposal: v2's AI run continues until G11's v4 run goes live; then v4 replaces it (reasoning) |
| 25 | Next-session focus (owner, 21 Oct) | Next-day questions matter most | **Keep** | V1 and V6a are next-session questions and stay members |

**Not a decision, a dated risk.** NSE's session calendar ends on 31 Dec 2026. A question whose horizon runs past it
gets a void outcome: V3 (20 sessions) from about 1 Dec, V2, V6b and V7 (5 sessions) from about 23 Dec. The calendar
file is data, not frozen code, so adding NSE's 2027 holiday list when it is published (usually mid-December) fixes it
with no new version. Whoever owns A7 should add it the day it appears.

## What the owner is asked to decide

1. **Keep** items 1, 3-8, 10-14, 17-23 and 25 as they are? (Recommended)
2. **Item 2:** the May 2027 review's result becomes advice, and the Innovation Lab decides what runs? (Recommended)
3. **Item 9:** replace section 11 D's "only V6b can be claimed, slowly" with judge 128's measured numbers before the
   freeze? (Recommended; a text fix in piece 1b)
4. **Item 15:** switch on the weather and the v4 forecasts and move the routine to 14:05 **now**, and freeze after 3
   clean sessions, instead of switching on at go-live? Pre-freeze forecasts are never counted. (Recommended)
5. **Item 16:** v4's go-live does not wait for the core engine's 10-day trial? (Recommended)
6. **Item 24:** the v2 AI run keeps going until G11's v4 AI run is live? (Recommended)
</content>
</invoke>
