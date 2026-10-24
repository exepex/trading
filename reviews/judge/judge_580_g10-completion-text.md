# Judge 580: G10 completion story text, v4's daily clock (story/g10-completion @ c876ede53), judge B

**FAIL (round 1 of 2; 3 should-fix, 3 minor). Lane 1, rule 1 (text first).** Markdown only (`docs/stories/G-forecasts.md`,
+305 lines from main d5ee18d02): judged by reading. Doc-reading tests on c876ede53: 829 passed, 15 xfailed.

## Criteria (is the text complete, true and safe?)

| # | Check | Result | My evidence |
|---|---|---|---|
| Why 1-6 | the audit's facts | MET | `QUOTE_PARTS` has nifty, nse, indices (`quote_parts.py:66-75`); `V4_DAYS_FOLDER` is `research/data/v4_days` (`forecast_scoring/v4/wiring.py:29`); `days.py:1-5` leaves a no-file day unlabelled vs `PROTOCOL_v4.md:115`; `commitment.on_time` has no caller (my grep) |
| Gap list vs 1.6 | 14 rows | PARTLY | every 1.6 line has a row; row 10 is wrong (finding 3) |
| Steps, pathspecs | order and O1's parts | MET | the clash is real: `GROWW_QUOTES` `groww/**/nifty_*` matches `groww/derivatives/quote-snapshots-v4/...` (`window.py:32-33`, `config.yaml` `quotes.windows.v4`); the narrowed glob keeps all 44 `quote-snapshots/` files and does not match `niftyweekly_*`; the 14:03 early limit is 14:30 - 30 min + `START_MARGIN` 3 min |
| Takeover | the three commits | MET | 1fe605bd1, 7cab92b06, f313ae15f on `story/g10-part2b-pack` with the files listed; `v4-fire.yml` there runs `ai fire --protocol v4` on `receipts/data/v4/days/**` |
| G7b/G11 interface | names, paths, triggers | PARTLY | names exist on main (`release.py`, `guard.py:12`, `commitment.py:26,42`); G7b's pack reading is not tied to the guard (finding 3) |
| Groww load | timing and safety | PARTLY | 23 Oct 14:55:00-14:57:38 and 22 Oct 14:58:58-15:01:30 complete, as written (sidecars); counter-evidence left out (finding 2) |
| Monday | what runs, record-only | MET | no merge window 14:00-16:15 (DESK_DECISIONS 24 Oct); nothing counts without `FREEZE_v4.md` |
| D1, D3 | clear for the owner | MET | each gives the value, the reason, the alternative and its one code place; see minor 2 |
| Rehearsal | DRY reruns | NOT MET | finding 1 |

## Findings

1. **Should fix: the text never says what a rehearsal does with the three new pieces, and DRY reruns are the owner's
   first goal.** In a rehearsal every step that is not live runs anyway (`rehearsal/live_wiring.rehearsed_live`, REH1c;
   handover section 1). So the `v4` part, `v4_release` and `v4_deadline` all run there. REH1b's recorded quote source (also for the named window: `quotes/window_wiring.py:31`)
   serves only recorded attempts (`recorded_quotes.py:49-71`), and no `quote-snapshots-v4` attempt exists. So every
   rehearsal ends the `v4` part with "no recorded in-window attempt", writes `system_late` for the day and the
   catch-up days into `dryrun/`, and, under D3, ends "day done with problems: v4_release" with the card's warning
   [strong: code read]. Fix: add a criterion naming each piece's rehearsal outcome and line, and say whether the
   `v4_pack` key goes through `rehearsed_live` and whether D3's failure is right in a rehearsal of a day with no
   capture. Add a test with the mode on.
2. **Should fix: the Groww-overlap evidence leaves out the one overlap that failed, and the fallback's trigger cannot
   be seen.** The text cites 22 Oct's 15:00 overlap as clean. The repository's sidecar
   `quote-snapshots/2026/10/nifty_20261022_151500.meta.json` was the capture that ran over A16's 15:15 mark. It had
   four `GrowwAPIException (provider message withheld)` failures and was incomplete; 23 Oct's 15:15 was clean (both
   checked). Also, A16 was decided "from Fri 23 Oct" (`conversations/2026-10-22.md:319`); the 22 Oct 15:00 mark row
   cited is in Drive, so name its receipt. Because Groww's messages are withheld, "its failures name a rate limit" can
   never be true. Fix: state both overlaps (one failing). Make the trigger observable, for example any failure in
   either job during 14:30:00-14:31:30, reported with the counts.
3. **Should fix: gap row 10 and criterion 7 contradict the interface on who reads the pack.** Interface row G7b 5
   says `forecasts_v4_pack` reads the released pack. Protocol 1.6 says such a forecaster names the pack's SHA-256 or
   is refused. Yet row 10 says "its first pack reader is G11", and `PACK_READERS` is only the two AI books
   (`guard.py:12`), which criterion 7 relies on ("outside PACK_READERS ... later V4/V5"). As written, G7b's V4/V5 rows
   would never be checked against the released SHA. Fix: name G7b's step as the first pack reader in row 10, and say
   who brings it under `check_pack_binding` (G7b, in the interface table). Keep the 15:10 check keyed on something
   other than `PACK_READERS`, or say how the two sets differ.

## Minor

1. `v4_release` "waits for the `v4` part to end (at most until 14:45:00), never runs while it records": say what
   happens at 14:45 with the part still running (stop it and write `system_late`, or wait).
2. "Until the owner answers D1 and D3, the code waits for their values": say whether the code may be built and judged
   with the recommended values and only the merge waits.
3. Criterion 4's good case "`A` at 14:33" does not match the timeline (capture to about 14:34, release about 14:35).

## Plants

None (text). The planned plants are sound; add: the narrowed NIFTY glob widened again in CLAUDE.md only (criterion 9
catches it), and `v4_release` run with the mode on and no capture (finding 1).

## Notes

- D1 and D3 are clear enough for the owner to answer. I do not rule on them. D2 (catch-up from 22 Oct) matches 1.6's
  "no release record at all".
- The builder session_011hvvn9CahAD5dCPHS3kowN and the orchestrator share no context with this judge.
