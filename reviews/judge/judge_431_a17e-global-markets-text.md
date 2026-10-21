# Judge 431: A17e global markets beyond the US, story text (story/a17e-global-markets @ a95591c0), for response 297

Judge F (independent), quality rule 1. Story `docs/stories/A17e-global-markets.md`, claims response 297. Lane 1
(outside services, Drive, a schedule). Labels: **strong**, **some**, **reasoning only**.

## Verdict: FAIL (1 blocking, 3 minor). The fix is small.

What is right:
- Step 0 tests every market the owner named. It quotes each publisher's terms with a URL and sorts sources into
  allowed, restricted and none, so nothing restricted is built without an owner decision.
- KOSPI without a key reports "not configured" and does not fail the run, so there is no daily red masking real
  failures (unlike judge 408's A20c).
- A same-day Asian close is never `live` at 09:15.
- Everything is private in Drive, and nothing new is scheduled.
- The boundary with A22 is agreed, and the evidence-based "Asia opens: out" closes A22's question.

## Re-checked by me (21 Oct 2026, about 21:30 UTC)

CSIndex `index-perf?indexCode=000001&startDate=20261001&endDate=20261021`: HTTP 200, 11 rows. The first row is
`20261001 3811.9` and the second `20261008 3811.9`. 1 Oct was a Chinese holiday, so the start-date row is a copy of the
next session, exactly as step 0 says **[strong]**.

## Blocking

**B1. No gap list (quality rule 2, `docs/JUDGE.md`).** As in judges 353 and 355: every requirement must map to a
criterion, or to "Out" with its reason. Here those are:
- the owner's 21 Oct words (Australia, Singapore, Hong Kong, Japan, South Korea, China; "don't consume US data only");
- A17's point-in-time rule;
- the private rule (a927390);
- O9;
- the A22 boundary;
- quality rules 5, 6 and 8.
The text covers most of them, but in prose. Add the table, with each market the owner named mapped to built / owner
decision n / out (no usable source).

## Minor

1. **Boundaries (rule 5).** Criterion 2 should pin each market's `available_at` at, just before and just after its
   close (Shanghai 15:00 CST = 12:30 IST, Taipei 13:30 = 11:00 IST, Seoul 15:30 KST = 12:00 IST). Criterion 1's
   fake-row rule should cover a real start-date session whose close equals the next one's.
2. **The text says "the Asian closes of day d ... are out by 21:10 IST on d".** They are out by about 11:00-12:30 IST
   on d. That does not change the 09:15 use (only d-1 counts as known), but the 14:11 IST run of day d can already hold
   them, which matters to the 15:45 report. Correct the sentence, and say whether the 14:11 run should take them (it
   is cheap: the same `once_a_day` rule decides).
3. **The fake-row rule drops a start-date row "whose values equal the next row's".** That is right for CSIndex's
   behaviour, but a calendar-based rule is safer: drop the start-date row only when the start date is not a trading
   date in a wider window of CSIndex's own answers. If you keep the equality rule, add the flat-close test from
   minor 1.

## Owner decisions

The six questions (VIX, Nikkei, TAIEX history, Europe and Singapore, a paid API, the KRX key) are correctly the
owner's, each with a recommendation and its label. Nothing restricted is built before an answer.
