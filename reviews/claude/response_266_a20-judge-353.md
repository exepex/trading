# Response 266: A20 story text, answer to judge 353 (builder)

Story `docs/stories/A20-rules-and-dates.md` at e50ca714 (branch `story/a20-rules-and-dates`). Every finding was
checked before accepting or rejecting it. The claims files of the code parts are `response_266a_a20a-fo-masters.md`
and `response_266b_a20b-circulars.md` (number reserved by the orchestrator).

| Finding | Verdict | Reason and evidence | Where in the text |
|---|---|---|---|
| B1 no gap list | **Accepted** | JUDGE.md quality rule 2 is explicit. Election result days are already in A6 (`election_result` rows); state elections have no user in the design [reasoning only]; heavyweight results dates are in A12's daily board-meetings list (manifest `board-meetings.csv`, latest row 14 Oct) | "Out" with reasons; "Gap list" |
| SF1 boundaries, real sample, workflow criterion | **Accepted** | Rules 5, 6 and 8 apply. "Runs on schedule" replaced by a YAML-reading criterion | criteria 1-16 |
| SF2 next-session ban list refused | **Accepted** | Re-checked: NSE wrote 16 Oct's list at 18:12 IST on 15 Oct; refusing it on a late or evening run throws away a real list. Now filed under its trade date; 18:45 IST slot added; stale = no copy for today's session on a trading day | Design 1; criteria 1-2 |
| SF3 file failure holds the circular back | **Accepted** | Holding back moves `first_seen_at` and re-alerts hourly. Now listed at first sight with `file` status; retries write a new row carrying the first `first_seen_at`; `abandoned` after 3 days | Design 2; criterion 8 |
| SF4 "yesterday to today" loses a dropped day | **Partly accepted** | The loss is real. Rejected the "since the last successful run" mechanism: a fixed 14-day window on every run covers every gap up to 14 days identically with no stored state (KISS, owner 16 Oct), and a longer outage is caught by the calendar stale rule and O8/O10 first. Cost about 320 items per run | Design 2 "Window" |
| SF5 empty answer reads as nothing new | **Accepted** | Measured: every one of NSE's 196 sessions in 2026 had at least one circular (5,665 items, A7 calendar), so "no circular dated the previous session" is stale. SEBI: 45 days (twice the longest gap, 22 days, in its latest 25) | Design 2 "Stale"; criterion 7 |
| Minor 1 one line per failed run | **Accepted for the hourly job** | Episode state in a committed keys-only file (O8b's pattern); fo-masters (3 runs a day) keeps one line per failed run | Design 4; criterion 9 |
| Minor 2 identical lot-size copies | **Answered** | Stored again as a new file each trading day (about 48 KB): NSE gives no date, so the copy is the daily proof | Design 1 |

Code consequences: A20a (head with the judge's first look) changes for SF2 (next-session list, 18:45 slot, stale =
today's copy missing); A20b changes for SF3, SF4, SF5 and minor 1. Both claims files are renumbered 266a and 266b.
