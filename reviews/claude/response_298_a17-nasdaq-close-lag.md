# Response 298: A17 schedules, judge F's condition: first-seen versus value-date lag of the 03:41 US copies

Builder: A16b/A17 builder (session 01MBnbVU). This answers judge 351 addendum 1's condition, due 23 Oct: "measure
within a week whether the 03:41 Cboe and Nasdaq copies already hold the US close ... Cite the first-seen versus
value-date lags per day."

## Measured (strong evidence)
Method: every Cboe and Nasdaq copy the scheduled runs archived from 17 Oct on was read back from Drive (read-only) and
parsed with the cue's own parser. "Newest final" is the newest date the copy holds whose close was published before
the fetch time (A17's `final_values` rule).

| Copy fetched (IST) | US trading day expected | S&P 500 (Cboe) newest final | Nasdaq-100 (Nasdaq) newest final |
|---|---|---|---|
| Sat 17 Oct 05:53 | Fri 16 Oct | 16 Oct: on time | **15 Oct: one day late** |
| Sun 18 Oct 06:27 (Cboe), 05:29 (Nasdaq) | Fri 16 Oct | 16 Oct | 16 Oct (a day later than the 16 Oct close's own morning) |
| Mon 19 Oct 05:40 | Fri 16 Oct | 16 Oct | 16 Oct |
| Tue 20 Oct 06:34 | Mon 19 Oct | 19 Oct: on time | **16 Oct: one day late** |
| Wed 21 Oct 06:04 | Tue 20 Oct | 20 Oct: on time | **19 Oct: one day late** |

On every weekday morning, the S&P 500 close of the previous US session was in the copy, so the lag is 0. The
Nasdaq-100 close was missing every time, so the lag is 1 US trading day. The weekend copies only look on time
because the Friday close had a day to arrive.

## Cause (tested)
Nasdaq's history API publishes a day's close late. On 21 Oct it still lacked that day's close at 17:02 and 17:17 New
York (21:02 and 21:17 UTC), more than an hour after the 16:00 close. A background poll in this session records when it
appears; its result is added below once it has run. Because Nasdaq is downloaded only once an IST day (the owner's
condition) and the 03:41 run is the first, that day's copy lacks the close and nothing alerts. This is exactly the
silent one-day lag judge F asked about.

## Fix: through A17e (story text PASSed, judge 431 addendum 3)
Yahoo's public chart API held the 21 Oct Nasdaq-100 close (29,822.52, market time 17:15 New York) by 21:28 UTC, while
Nasdaq's API did not. Its 15, 16 and 20 Oct closes equal Nasdaq's; on 19 Oct they differ by 0.01 (29,529.35 against
29,529.34). A17e's design already gives the right fix:
- a `nasdaq100_yahoo` cue (one more `YahooChartSource` line, A17e scope 2);
- A17e's one reading per index takes Nasdaq's official value where it has the date, and Yahoo's otherwise. So the
  03:41 run gives the previous close on time from Yahoo, and Nasdaq's own value replaces it a day later;
- the overlap check compares the two, so a Yahoo error still shows up.

The A17e text gets this as amendment 1 (scope 2: the Nasdaq-100 is a twelfth Yahoo cue; criterion 3: the reading
for `nasdaq100` uses Yahoo before Nasdaq has the date).

Rejected options:
- **A second Nasdaq download later in the day:** it breaks the owner's once-a-day condition, and the close would
  still miss the 09:15 open.
- **Leaving it:** a silent one-day lag on one of two US equity cues.

## Until A17e's code merges
The Nasdaq-100 is one US trading day late at the open (reasoning: one day late, never wrong). The S&P 500 is on time
and is the open's US equity cue.
