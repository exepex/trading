# Judge 352: A19 news capture, story text (story/a19-news-capture @ 57f2eda1)

Judge F (independent), quality rule 1 (story check before code). Story `docs/stories/A19-news-capture.md` at
`57f2eda167b20027c28a1ba7b679c86e4fe3875e`. The orchestrator sent b973a3b0; I judged the branch head, which carries
two later text commits. Only the story and a register row change. Labels: **strong**, **some**, **reasoning only**.

## Verdict: FAIL (5 should fix, 3 minor). Code must not start until these are answered in the text.

What is right:
- Step 0 is real work.
- The no-duplicate split with A12 and A20b is clear.
- Point-in-time rules are in the reader.
- Versions are never overwritten.
- No item text goes to the repository, Slack or logs.
- Errors use O10's one format.
- The criteria cover at, under and over each limit.

The design for "continuous" capture has holes that would make first-seen times or alerts wrong, and one platform
term needs the owner.

## Step-0 claims I re-checked (16 Oct 2026, about 16:45 IST, from this session)

| Claim | My check | Result |
|---|---|---|
| Moneycontrol feed dead, newest 23 Apr 2024 | `rss/latestnews.xml`: 15 items, 23 Apr 2024 11:46-13:41 | **True** |
| ET Economy 50 items, about 2 days | 50 items, 14 Oct 17:17 to 16 Oct 16:44 IST | **True** |
| Mint Economy 35 items, 6 days | 35 items, **11 Oct 00:06 to 16 Oct 16:42 IST (5.7 days)** | **True**; this matters for SF3 |
| SEBI date only, `16 Oct, 2026 +0530` | 30 item dates all `dd Mon, yyyy +0530`; one other `pubDate` with seconds, apparently the channel's | **True** |
| Owner's terms answer in DESK_DECISIONS | main, row 249: "News: ET, Mint and BusinessLine RSS headlines ... private Drive only" (owner: "Yes, use them (Recommended)") | **True** |
| participant-oi-watch: 3 runs in total | GitHub run list (judge 350) | **True** |
| O10's `CaptureErrorLog` "3dc1675f, merged first" | 3dc1675f is on the O10 branch, not on main; O10 part 1 is at judge 350 FAIL, re-judge pending | dependency, not yet met |

## Should fix

**SF1. A permanent polling loop on GitHub-hosted runners needs the owner's decision under GitHub's Actions terms
[some: the terms are quoted; how they apply is reasoning only].** GitHub's Additional Product Terms, "Actions"
section, say Actions should not be used for "Any activity that places a burden on our servers, where that burden is
disproportionate to the benefits provided to users (for example, don't use Actions as a content delivery network or
as part of a serverless application ...)". They also exclude, on GitHub-hosted runners, "any other activity unrelated
to the production, testing, deployment, or publication of the software project". The listed sanctions include
"disabling of repositories" and account suspension.

A job that runs 340 minutes, re-dispatches itself and polls third-party feeds around the clock is the clearest case
of this in the repository. If GitHub acts, every capture job goes with the repository, not only news. Existing jobs
already lean the same way: filings-archive runs 355 minutes every 6 hours.

The story's own step-0 table checks every news site's terms but not the platform's. Fix expected: add GitHub's
Actions terms as a step-0 row and put the choice to the owner. Options: (a) accept the risk on GitHub; (b) run the
poller outside GitHub (the owner's machine, a small VM, or a scheduled Claude session) with GitHub as the record
store; (c) poll less often during closed hours to reduce the load.

**SF2. Crons plus self-dispatch in one concurrency group create cancelled runs that raise false alerts and
`restart_stopped` rows [strong for GitHub's rule; the sequence is reasoning only].** GitHub keeps at most one pending
run per concurrency group and cancels the older pending one when a newer one queues. A run is active nearly all day.
The sequence is:
1. Each backup cron that fires during a run queues a pending run.
2. When the active run ends, it dispatches its successor.
3. The successor now queues behind the cron's run and cancels it.

That cancelled run lasted under 10 minutes. So scope 7 writes a `restart_stopped` row and alerts, and O10's
capture-watch (which alerts on `cancelled`) alerts again. Up to six crons a day means up to about 12 false lines a
day: noise the owner ruled out, and noise that hides real alerts. Fix expected:
- say how a run that GitHub cancelled before any step ran is treated: the restart workflow ignores it, and O10
  counts it as replaced, not failed;
- or make the crons stand down when a run is active;
- add a criterion with that sequence planted.

**SF3. The seen set covers 2 IST days, but feeds hold items for up to 6 days, so restarts re-store old items as new,
with a false late first-seen time [strong: my Mint Economy fetch spans 5.7 days].** Scope 6 loads the seen set "from
the last 2 IST days' receipted parts". An item first stored 3-5 days ago and still in Mint's Economy feed is unknown
after any restart (every 340 minutes at least). It is stored again as a new item, with `first_seen_at` days after
its real first sighting. That breaks the story's own first-seen promise and criterion 6 ("a restarted run does not
store a known item again").

Fix expected: a load window longer than the longest feed span, with a margin. Either a fixed span (for example 10
days) checked against each feed's measured span, or each feed's oldest listed item compared with the window, failing
loudly when the feed reaches past it. Add a boundary test: an item 2 days plus 1 minute old, then 9 days old,
across a restart.

**SF4. Coverage gap and `previous_poll_at` are measured from data parts, which exist only when a poll found
something new [strong, from the text].** Scope 8 says "if the newest receipted part is older than 15 minutes, a gap
record". Scope 4 makes `previous_poll_at` "that feed's last successful poll". Scope 4 also says "A poll with nothing
new writes no part" (criterion 5).

So on a quiet night or weekend, when no feed has a new item for hours, every restart records a false coverage gap and
alerts. After a restart, `previous_poll_at` can only be rebuilt from the last part that held an item from that feed,
so it can be hours early. The window "the true first sighting lies between the two" then becomes falsely wide.

Fix expected: a small per-poll heartbeat (time and per-feed status, no item text), kept the same way as the parts.
The gap and `previous_poll_at` are taken from it. Criterion 8 should then plant a quiet hour with polls but no items
and expect no gap.

**SF5. The stale rule ignores the calendar, and its limits come from feed spans, not measured quiet spells [some:
step-0 spans; nights and weekends are reasoning only].** Publisher feeds go stale after 6 hours, at any hour. Step 0
measured each feed's span at one moment (ET Markets 50 items in 7 hours), not the longest quiet spell overnight, at
weekends or on NSE holidays. If any publisher feed posts nothing for 6 hours on a Saturday night, that is one episode
alert and one row each time.

My brief asks whether staleness follows NSE's session calendar. Here it does not. Fix expected: limits by NSE
session calendar (strict in session hours, loose on closed days and nights), or limits from a measured longest gap
per day type, recorded in config with their evidence. Add tests on a session afternoon, a session night, a Sunday and
an NSE holiday.

## Minor

1. Run logs of a public repository are public. Scope 7's `news probe` "prints each feed's answer from the runner".
   Say it prints only status, size, item count and newest item time, never a title or link; criterion 5's grep of
   printed lines should cover the probe too.
2. Episode state (failing or recovered) lives in memory, so a feed that keeps failing re-alerts at each run start,
   which is up to about 4-5 times a day. State it, or keep the episode state in O10's log (an open episode row
   without an end row).
3. The dependency "O10 part 1's `CaptureErrorLog` (3dc1675f, merged first)" should read "after O10 part 1 passes its
   re-judge and merges". O10 is at judge 350 FAIL, with a fix 97213d61 pending.

## Gap list check

Each design line maps to a scope item or criterion, or to "Out" with a reason. Two lines are covered on paper but
not in substance:
- "Up to date, every failure alerted and recorded": SF2 (false alerts) and SF4 (false gaps) undercut it.
- "Stale feed detected": SF5.
The "Silence when no run is alive" line is honestly left to O10 and O8.

## Rules

- Lane 1 (new story, outside services, workflows). Interface plus adapter, strategy for time formats, composition root.
  This is the simplest design that can work, so no over-engineering, except that SF1 may change where the loop runs.
- Terms: news sites' RSS terms read and quoted, owner decided, bodies never fetched, Google News excluded by robots.txt.
  Good. The platform's own terms are missing (SF1).
