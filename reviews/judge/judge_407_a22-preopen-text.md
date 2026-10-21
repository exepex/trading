# Judge 407: A22 pre-open data, story text (story/a22-preopen @ 5fbc44c9)

Judge F (independent), quality rule 1. Story `docs/stories/A22-preopen-data.md`. Lane 1 (new story; NSE, Groww, Drive,
Slack, a Claude routine). Labels: **strong**, **some**, **reasoning only**.

## Verdict: FAIL (1 should fix, 3 minor)

What is right:
- Step 0 reads every source and names what cannot be read: NSE's terms page, and NIFTY/BANKNIFTY pre-open in the
  evening.
- Asia opens are Out with a reason.
- The design reuses A16b's read-only Groww adapter rather than copying it.
- "No data" is never "complete".
- Raw answers and the day row go to Drive under O9, and failures use O10's `record-error`.
- The clock choice is right: a Claude routine, because GitHub's crons start 4-5 h late (judges 350, 351).

## Should fix

**SF1. If the 08:38 routine does not start, nothing alerts that day, and there is evidence it will sometimes not start
[strong for A16's record].** Every alert in the text is raised by the run itself, so a routine that never fires leaves
no line and no O10 row. A16's 15-minute recorder is the closest precedent: a Claude routine with a 09:00 first fire.
Its committed slot files show the first fire missed on 16 Oct (09:15, 09:30 and 09:45 `missed` / `not_taken`; first
good mark 10:00). It ran on 19 and 21 Oct (09:15 `good`, request at 03:45:00 UTC). 20 Oct was an NSE holiday
(Dussehra). So 1 of 3 sessions on record missed the first fire, a small sample [some].

A21's text faced the same question and said so plainly, naming A16's heartbeat and O8 as witnesses (judge 355 add. 1).
A22 has no witness at all.

Fix expected:
- name the witness;
- either an O8 freshness row "pre-open day row receipted by 09:20 on a trading day", agreed with O8's owner, so the
  evening check reports and the trial counts a missed morning;
- or a check by A16's 09:00-fired routine that today's GIFT Nifty and pre-open rows exist, alerting once if not;
- add a criterion for it;
- state the measured miss rate of the 08:38 routine in the first live week's claims.

## Minor

1. **Window boundaries (quality rule 5).** Criterion 4 should name exact instants: GIFT read at 08:39:59 (waits),
   08:40:00 and 08:44:59 (on time), 08:45:00 (late); pre-open retry at 09:13:59 and 09:14:00.
2. **"Trading day"** should be A20a's `is_trading_day` (regular or special, not muhurat-only), not just "a session of
   A7's calendar". A muhurat evening has no 09:08 pre-open.
3. **GIFT Nifty "one read"** should retry within 08:40-08:44 (for example each 30 s) before failing. One NSE hiccup
   would otherwise cost the 08:45 forecast its only input.

## Open questions, correctly sent to the owner

Step 0b (whether `key=NIFTY` / `key=BANKNIFTY` and BANKNIFTY's Groww pre-open candle answer at 09:08) and the
personal-research rule for NSE's pages are open questions, as the text says. Criterion 3 stays unmet until step 0b
proves at least one index source.
