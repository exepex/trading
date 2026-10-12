# Sources for `events_draft.csv`

Built 2026-10-12 (agent research run). Draft: not yet reviewed by the owner. 61 rows: 49 `rbi_policy`, 10 `budget`, 2 `election_result`.
Every date below was read from a page that was actually opened during the run. Nothing was filled from memory.

## Column meaning (read this first)

- `date`: the day the decision or event was made public (RBI: the day the MPC resolution came out; budget: the day it was presented in the Lok Sabha; election: counting/result day).
- `scheduled`: `yes` if the final date was officially published before that day as a planned meeting or event. `no` only for RBI off-cycle meetings.
- `announced_on`: the **earliest official page found** that gives the **final** date. This is not always the date of the annual schedule:
  - For April MPC meetings, the date first appeared in the February resolution ("The next meeting of the MPC is scheduled ..."). That came before the annual schedule press release, so `announced_on` uses the February date. The annual schedule date is in `description`.
  - For rescheduled meetings, `announced_on` is the date of the reschedule press release. `revised_from` is the decision day that was originally announced, meaning the last day of the original meeting window.
- `announcement_source_url` and `source_url`: official pages (rbi.org.in, pib.gov.in, rajyasabha.nic.in, ECI press notes). Where a press article is cited, it appears only inside `description` and is labelled as press.

## 1. RBI MPC decision days (49 rows)

### How each date was verified
1. I read RBI's Monetary Policy page (`https://www.rbi.org.in/Scripts/Annualpolicy.aspx`) for every financial year from 2018-19 to 2026-27, using the page's year selector.
2. For every row, I opened the MPC resolution press release (`BS_PressReleaseDisplay.aspx?prid=N`, linked in `source_url`) and checked two things: the release date, and the line "MPC at its meeting today (<date>)". From Feb 2025 onward the resolutions no longer carry the "today (date)" phrase, so for those rows the date comes from the release date and the meeting window in the title. I also took each resolution's "next meeting is scheduled ..." line.
3. Annual schedule press releases opened:

   | FY | Published | URL |
   |---|---|---|
   | 2018-19 | 2018-03-21 | https://www.rbi.org.in/Scripts/BS_PressReleaseDisplay.aspx?prid=43436 |
   | 2019-20 | 2019-03-22 | ...?prid=46626 |
   | 2020-21 | 2020-04-20 | ...?prid=49700 |
   | 2021-22 | 2021-03-31 | ...?prid=51350 |
   | 2022-23 | 2022-03-30 | ...?prid=53486 |
   | 2023-24 | 2023-03-24 | ...?prid=55410 |
   | 2024-25 | 2024-03-27 | ...?prid=57580 |
   | 2025-26 | 2025-03-26 | ...?prid=60062 |
   | 2026-27 | 2026-03-23 | ...?prid=62422 |

4. Reschedule and off-cycle evidence I opened:
   - **Feb 2019:** the 2018-19 schedule listed Feb 5-6, 2019. PR 45659 (2018-12-05) moved the meeting to a 3-day format, with the statement on Feb 7. PR 46187 (2019-02-04) reconfirmed this.
   - **Mar 27, 2020 (off-cycle, advanced):** the Governor's statement (`bs_viewcontent.aspx?Id=3847`) says the MPC "decided to advance its meeting scheduled for 31st March, 1st and 3rd April 2020" and met on Mar 24, 26 and 27. That meeting had first been announced in the Feb 6, 2020 resolution (PR 49342).
   - **May 22, 2020 (off-cycle):** the Governor's statement (`Id=3859`) calls it "an off-cycle meeting ... in lieu of the scheduled meeting during June 3 to 5, 2020" (MPC met May 20-22).
   - **Oct 9, 2020:** the original meeting was Sep 29-30 and Oct 1, 2020. PR 50426 (2020-09-28) postponed it with "dates ... will be announced shortly". PR 50463 (2020-10-06) set Oct 7-9. The press release gives no reason for the postponement, so none is given here.
   - **Feb 10, 2022:** PR 53228 (2022-02-06) moved the meeting from Feb 7-9 to Feb 8-10 because Feb 7 was declared a holiday.
   - **May 4, 2022 (off-cycle):** the resolution is PR 53652. The Governor's statement (PR 53651) says "off-cycle meeting on 2nd and 4th May, 2022".
   - **Aug 5, 2022:** PR 54069 (2022-07-21) moved Aug 2-4 to Aug 3-5.
   - **Aug 6, 2025:** PR 60612 (2025-06-06) moved Aug 5-7 to Aug 4-6.

### Deliberately excluded (not policy decision days)
- **Nov 3, 2022:** an additional MPC meeting under Section 45ZN, held to draft the report to Government on missing the inflation target. It made no rate decision. Announced by PR 54597 (2022-10-27); held per PR 54639.
- **Apr 17, 2020 and May 5, 2021:** Governor's addresses or statements announcing liquidity and regulatory measures. Neither was an MPC meeting.

### Gaps and uncertainties
- **Off-cycle rows (2020-03-27, 2020-05-22, 2022-05-04):** `announced_on` is empty. I scanned RBI press releases in the days before each date (prids 49540-49581, 49790-49842 and 53600-53650) and found no advance notice. The decision appears to have been made public on the day itself. Still, "no notice found" is not proof that none existed.
- **2026-12-04:** this is a future scheduled meeting (Dec 2-4, 2026) and had not happened as of 2026-10-12. `source_url` is empty. The date is confirmed by the 2026-27 schedule and the Oct 7, 2026 resolution (PR 63742), but it can still be moved.
- **2026-12-04 and every row from 2026-10-07 back:** these come from the live RBI site as fetched on 2026-10-12.

### Where sources disagree
- **2025-26 schedule:** the original press release (PR 60062, 2025-03-26) lists **August 5, 6 and 7, 2025**. RBI's Monetary Policy page today shows the same schedule entry with **August 4, 5 and 6, 2025**, meaning RBI edited the listing after the 2025-06-06 reschedule. The CSV follows the original press release for `revised_from` (2025-08-07) and the actual decision for `date` (2025-08-06).
- **Feb 2019:** the 2018-19 schedule (PR 43436) says Feb 5-6, while the actual decision came on Feb 7. This is explained by PR 45659, so it is a reschedule, not an error.

## 2. Union Budget days (10 rows)

### How the presentation day was verified
Each `source_url` is the Ministry of Parliamentary Affairs session wrap-up on PIB. Each one states "The Union Budget for <year> was presented on <weekday>, <date>":

| Budget | Presented | PIB release |
|---|---|---|
| 2019-20 interim | Fri 1 Feb 2019 | PRID 1564292 |
| 2019-20 full | Fri 5 Jul 2019 | relid 192521 |
| 2020-21 | Sat 1 Feb 2020 | relid 200625 |
| 2021-22 | Mon 1 Feb 2021 | PRID 1707544 |
| 2022-23 | Tue 1 Feb 2022 | PRID 1814503 |
| 2023-24 | Wed 1 Feb 2023 | PRID 1914356 |
| 2024-25 interim | Thu 1 Feb 2024 | PRID 2004900 |
| 2024-25 full | Tue 23 Jul 2024 | PRID 2043862 |
| 2025-26 | Sat 1 Feb 2025 | PRID 2118954 |
| 2026-27 | Sun 1 Feb 2026 | PRID 2253254 |

All 10 dates match the dates given in the task. There are no disagreements.

### Announcement date: the weak part of this file
In most years the session and budget dates were first made public by the Parliamentary Affairs Minister's post on X, or by Lok Sabha Secretariat posts or letters. I could not open those posts. The CSV therefore uses the earliest **official page I could open**. In several years that page appeared only one to three days before the budget. **Treat `announced_on` for budgets as a late bound, not the true first announcement.** The press-reported earlier dates are listed below and in `description`. They come from press articles I opened; I did not open the underlying official posts.

| Budget | CSV `announced_on` (official page) | Earlier press-reported announcement |
|---|---|---|
| 2019-02-01 | empty (not found) | 2019-01-09 The Quint, citing ANI "sources" (not an official announcement) |
| 2019-07-05 | 2019-05-31 PIB Cabinet decision (relid 190187) | none earlier found |
| 2020-02-01 | empty (not found) | 2020-01-15 ETV Bharat/PTI, quoting Rajya Sabha and Lok Sabha secretariat communications |
| 2021-02-01 | 2021-01-30 PIB (PRID 1693556) | 2021-01-15 Onmanorama (CCPA recommendation) |
| 2022-02-01 | 2022-01-31 PIB (PRID 1793884) | 2022-01-14 Scroll, quoting a @LokSabhaSectt post |
| 2023-02-01 | 2023-01-15 Rajya Sabha Bulletin Part-II No. 62715 | 2023-01-13 Deccan Herald, quoting Pralhad Joshi's X post |
| 2024-02-01 | 2024-01-29 PIB (PRID 2000336) | 2024-01-12 Deccan Herald/PTI, quoting Joshi's post |
| 2024-07-23 | 2024-07-06 PIB (PRID 2031304) | same day (Scroll 2024-07-06) |
| 2025-02-01 | 2025-01-30 PIB (PRID 2097713) | 2025-01-17 Scroll, quoting Kiren Rijiju's X post |
| 2026-02-01 | 2026-01-27 PIB (PRID 2219294) | 2026-01-09: session dates only (AIR newsonair, Scroll); Scroll says the post did not give the budget date |

Context worth knowing (reasoning only, not used in the CSV): since 2017, the regular budget has been presented on 1 February by convention, so the market expects it long before any formal notice. The exceptions are election years (interim budget on 1 Feb, then a full budget on a date announced after the new government forms: 5 Jul 2019 and 23 Jul 2024).

Things I tried that failed:
- Probing Rajya Sabha Bulletin Part-II PDFs by date for the other years found nothing at the URL pattern that worked for 2023.
- The Rajya Sabha provisional calendars (`TableCalender/Session_<n>`) confirm the budget day but carry no issue date.
- The Lok Sabha summons bulletins were not located.

## 3. Lok Sabha election result days (2 rows)

- **2019-05-23:** ECI Press Note No. ECI/PN/23/2019 dated 10 March 2019 lists "Counting of Votes: 23-05-2019". The ECI's own URL returned HTTP 406 (blocked by its firewall), so I read the identical press note hosted by the Chief Electoral Officer, Meghalaya (the URL in the CSV). Post-event confirmation: PIB PRID 1572600 (25 May 2019) says the ECI gave the President the notified list of members elected to the 17th Lok Sabha. That page does not itself repeat "23 May". I did not open an official page stating "counting was held on 23 May 2019" after the event.
- **2024-06-04:** the ECI Press Note of 16 March 2024, hosted on PIB (`static.pib.gov.in/.../GESchedule.pdf`), lists "Date of Counting of Votes 04.06.2024". PIB PRID 2022466 (1 June 2024) confirms that counting would be held on 4 June 2024. PIB PRID 2023272 (6 June 2024) records that the list of elected members was given to the President.
- No disagreements were found. Note: in 2024 the counting for the Arunachal Pradesh and Sikkim assemblies was separate from the Lok Sabha count. It is not covered by this file, and this was not checked further.

## Summary of open items
1. Budget `announced_on` values are late bounds (official pages only). Two are empty: 2019-02-01 and 2020-02-01.
2. RBI off-cycle rows have an empty `announced_on`; no advance notice was found.
3. 2026-12-04 is a future meeting and has no `source_url`.
4. For 2019-05-23 the ECI's own site could not be opened (HTTP 406); the CEO Meghalaya copy was used.
