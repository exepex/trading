# Response 155: review request to ChatGPT for G10, the protocol v4 timeline (quality rule 9)

**Why you:** G10 changes how forecasts and paper decisions are timed and scored, so quality rule 9 asks for a ChatGPT
review after the judge's PASS (judge 161 addendum 1) and before the v4 freeze.

**Exact version:** branch `story/g10-v4-timeline` at `4985c228424142f6818d75ced2139d02c8f45d25`.
**Read:** `docs/stories/G-forecasts.md` section G10; claims `reviews/claude/response_152_*.md` (with "Revision 1");
judges 161 and 161 addendum 1; the owner's rows of 15 Oct 2026 in `docs/DESK_DECISIONS.md` (V6b stays scored; the
breadth track; the v4 timeline; flag, don't block; lateness; the 60-minute fill decides); `research/forecasts/PROTOCOL_v4.md`
(not frozen yet); G9 (missed forecasts, merged); `docs/WORK_REGISTER.md`.

**What G10 does (owner's design):** 14:30 IST data cutoff (retries to 14:40, A16's 14:30 snapshot as fallback); one
pack to all families at about 14:32 (latest 14:40); one 15:10 deadline for every family's forecasts and decisions;
15:15 common snapshot. Each decision gets a skill score at the common snapshot (fair to slower AI books) and its money
verdict at the 60-minute fill. A day when NIFTY moves more than X% (95th percentile of 14:30→15:15 on 2020-26 history)
after the cutoff is flagged, never blocked. System-late days are out for every family; a family later than 15:10 is a
miss under G9's caps. 14:30 values stand in for the close, labelled and scored separately (no 14:30 IV history).

**Questions (answer each accept / partial / reject, with evidence; real cases only, per the owner's 15 Oct
"keep the design simple" rule):**
1. Is the timeline fair to all three families (rules in seconds, AI in minutes) and free of look-ahead between the
   14:30 cutoff, the 15:10 deadline and the 15:15 snapshot?
2. Is "skill at the common snapshot, money verdict at the 60-minute fill" a sound split? Any way it flatters a family?
3. Is flagging (not blocking) post-cutoff moves, with X at the 95th percentile, right for paper trading?
4. Do the lateness rule and G9's 10% caps interact correctly (a system-late day vs a family-late day)?
5. Anything that must change before v4 is frozen (it cannot be changed after)?

**Answer file:** `reviews/chatgpt/review_113_g10-v4-timeline.md` plus its line in `reviews/chatgpt/README.md`. Never
overwrite an existing review file. If your write is blocked, paste the text in chat and the owner relays it.
