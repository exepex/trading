# Judge 274: G10 part 2 story text, the pack, its release record and the AI fire (story/g10-part2-text at 338080fe)

Judge B, 16 Oct 2026. Lane 1 (a new story part; forecast records; a workflow), before the v4 freeze. Builder: A16/G8.
Register: the "G10 v4 timeline" row. One new subsection in `docs/stories/G-forecasts.md`, before G11.

**Verdict: FAIL.** One should-fix: the pack-SHA rule leaves an empty SHA open for the records it is meant to bind.

## What holds

- **Storage through O9** from day one: `DataStore.put` for writes, `DriveCache` for reads, receipts in GitHub. Groww
  values stay in Drive (A4b).
- **The pack:** outside the frozen `fno/forecast_v4/`; its SHA is of the stored canonical bytes; every field has its
  own `observed_at`, with `last_trade_time` never used as observation time; a field after 14:40:00 is out; a missing
  required field means `system_late`. Criterion 1 is testable.
- **The deadline:** 15:10:00 on GitHub's receipt time through O8's `file_pushed_at` behind an interface, never the
  commit time; criterion 4 pins 15:10:00 against 15:10:01.
- **The fire:** a `push` trigger on `receipts/v4/days/**`, no cron (a test refuses any `schedule:`); `V4_LATEST_FIRE`
  14:55. The evidence that the owner's routine push starts workflows is cited (15 Oct, bf16247a, run 38714143717).
- **The design point (G7 and M1 rows carry `pack_sha256` empty): ACCEPT.** They commit before 14:30 from closes up
  to d-1, before any pack exists; their method hashes and part 1's proofs show they read no pack. Requiring a SHA
  would push them past their own cutoff.
- **Criterion 6 says plainly** that the "push starts the fire" proof needs the owner's schedule change. That is
  honest, and it is the owner's call.

## Should-fix: an empty SHA must be refused for every pack-reading record

Section 4 says "a live record naming any other SHA is refused". Criterion 3 says "a pack-reading record with another
SHA is refused; G7 and M1 rows carry it empty". As written, an **empty** `pack_sha256` names no SHA, so a pack-reading
record (an AI book's) that leaves it empty passes. That is exactly what the binding exists to stop. Because G7 and M1
legitimately carry it empty, the rule cannot be "empty is fine".

The text needs:
1. Which records must carry the pack SHA is decided by the **forecaster** (a fixed list in code: the AI books, and V4
   and V5 when built), never by the record's own field.
2. For those, an empty or different SHA is refused before writing. For the others, a non-empty SHA is refused (they
   read no pack).
3. Criterion 3 gets both cases as tests.

## Notes only

- **Label `A` versus `A2` in practice.** The 3 pm routine starts at 14:33 IST (CLAUDE.md) and runs its setup first,
  so a 14:30-14:40 capture cannot start at 14:30 until the routine moves. Until then, `A2` (A16's 14:30 mark) is the
  normal path, not the fallback. Say so, so the day-label counts are read right.
- **Ownership.** Moving the capture's window is A4's recorder (`fno/quotes/`, the A4b/A4c builder), and the routine's
  timing and prompt belong to O1 (register "Handover / routines": "A4c, G10 and A14c send their lines through O1").
  Name O1 beside A4's owner.

Story text only; I checked the claims above against the register, CLAUDE.md and the cited code paths.
