# Response 42: A6 events calendar, answers to judge 8

Builder: the orchestrator session (it built A6 on 12 Oct 2026). Verdict answered: `reviews/judge/judge_8_a6_events_calendar.md`.

| # | Finding | Decision and why | Fix and proof |
|---|---|---|---|
| 1 | Should fix: a rescheduled meeting vanishes from what was known before the reschedule | Accepted, with option (b). Root cause: one row held only the final date's announcement, so the calendar had no record of what was known before the move. Option (a) (first announcement with the final date) would be look-ahead for the date shift, so it was rejected. | New columns `first_announced_on`, `first_announcement_source_url` (the annual-schedule press release already named in each row's description) and `first_withdrawn_on` (Oct 2020 only: postponed 28 Sep before new dates on 6 Oct). `known_on` (`fno/research_data/events.py`) shows a moved meeting at its original date from its first announcement until the move was public (or until an unscheduled meeting replaced it). Tests: `test_a_moved_event_is_known_at_the_date_known_on_the_decision_day` (the judge's three cases plus 6 Feb 2022 and 1 May 2020), `test_a_postponed_meeting_is_unknown_between_postponement_and_new_dates`, `test_an_emergency_meeting_is_never_known_ahead_but_the_meeting_it_replaced_was`. Remaining gap, stated in SOURCES.md: 2020-03-27's replaced meeting has no opened first-announcement page, so it stays unknown before 27 Mar. |
| 2 | Pending: criterion 4 needs F3 | Agreed. Written into A6's story text: F3's story must test it through `known_on`. | story text |
| 3 | Pending: criterion 5 commit order | Agreed; checked at the challenge run. | story text |
| 4 | Minor: official domains not enforced | Accepted. | `OFFICIAL_HOSTS` and `_official` (https only; rbi.org.in, pib.gov.in, indiabudget.gov.in, eci.gov.in and subdomains) for every past event's `source_url`; all 61 rows pass; test `test_bad_sources_and_bad_revision_rows_are_refused`. |
| 5 | Minor: "conservative" is imprecise | Accepted. | Story text now says: never look-ahead, but it may hide a known event for a few days. |
| 6 | Minor: 2019-05-23 source shows 25 May | Accepted (note route). | Row description notes that the PIB page (25 May) reports the results and the counting date is stated by ECI Press Note 23/2019, the announcement source. |

Checks: `python -m pytest -q` 410 passed; ruff and import check clean; record scan clean; `events.py` under 150 lines.
