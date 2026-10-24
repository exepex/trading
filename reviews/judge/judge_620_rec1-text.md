# Judge 620: REC1 recommender story text, story/rec1-recommender-text at c0c6980dc (judge J, round 1 of 2)

**FAIL** (text), lane 1: 3 should-fix, 1 minor. Diff: only `docs/stories/REC1-recommender.md` (+190). Doc-reading
tests with `FNO_SLACK_BOT_TOKEN` set: 922 passed, 14 xfailed.

## What holds (my evidence)
- **The owner's decision:** quoted correctly (DESK_DECISIONS line 343 (4): "built in full ... with no proven edge it
  says NO TRADE").
- **Real money:** a closed two-member enum with no "buy" value (criterion 1's plant), matching response 327 item 9
  (`response_327_market-school-agreed.md:51`: "never buy").
- **Rungs:** backtests, the simulator, rehearsals and uncounted days count 0, each with a plant (criterion 3); day
  conditions only lower a rung (criterion 4).
- **One record:** Drive write-once with the receipt pushed before any post, read by the card, the editions and the
  contract.
- **The assumptions:** A1-A4 are each marked with a recommended answer.

## Findings
**S1 (should fix) "Proven" means one counted session, so the paper answer can recommend an unproven version.**
- Section 1 makes `PAPER_TRADE` the paper answer for "a version at evidence rung 1 or higher". `no_proven_version`
  is defined as "no version above rung 0". Rung 1 is 1 to 29 valid sessions.
- So after one forward session the card would say "Paper: PAPER_TRADE <version>" with the reason line of a
  recommendation. Section 6 says "no proven version means ... paper `NO_TRADE` or measurement only".
- Response 327 calls nothing proven before a one-sided 95% lower bound above zero (item 4, line 38). Rung 2 "may
  include zero" and P2 is "descriptive, no licence" (line 66).
- Fix: "proven" is rung 3 only, and the reason code names what it tests (e.g. `no_established_version`). A paper trade
  of a rung 0-2 version is shown as "paper, not a recommendation: <rung and numbers>". `PAPER_TRADE` as a
  recommendation exists only at rung 3. One test per rung (0, 1, 2, 3) with a planted promotion of rung 1.

**S2 (should fix) The point-in-time rule for the rung's inputs is not stated.**
- The rung is "from frozen forward records", but no criterion says which sessions it may count at 15:20 on day d.
  The day's own trades and outcomes are unresolved then.
- Fix: a rung counts only sessions whose outcome record's receipt time is before `made_at` (never day d), and the
  record carries that cutoff. One planted record of day d that must not count.

**S3 (should fix) The evening check of `NO_TRADE` can be chosen with hindsight.**
- It reports what "the day's candidates and the matched controls made", but the 15:20 record does not fix which
  candidates. An evening choice (the best, or only the closed ones) would flatter or punish abstaining.
- Fix: the recommendation names its candidate set at decision time (version, decision path, SHA-256). The check
  reports all of them, each and as a total, never a subset; "not known yet" until every one has closed. A planted
  test drops a losing candidate at check time and must fail.

**m1 (minor)** The acceptance header promises a planted failure for each criterion, but only criteria 1, 3 and 7
name one. Name the plant for 2, 4-6 and 8-11 as well (quality rule 4).

## Notes
- RM1x touches the real-money line, and the recommender "decides what a trade would be". Whether a second judge is
  needed (JUDGE.md, two judges for money pieces) is the orchestrator's call; the text's "one judge each" should name
  that ruling.

## Plants
0 (text round).
