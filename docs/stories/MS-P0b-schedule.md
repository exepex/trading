# MS-P0b: the scheduled session the owner would create (option a)

The probe and its rules are described in [MS-P0b-capture-probes.md](MS-P0b-capture-probes.md); this file only holds
what to paste. Why a schedule: the owner's 25 Oct rule allows no hand-run Groww command from 09:15 to 15:35 IST, and
the probe measures market hours only. Only the owner creates this schedule; no session does. Lane 1.

- **When:** weekdays at 09:50 IST, from Thu 29 Oct 2026 (cron `CRON_TZ=Asia/Kolkata 50 9 * * 1-5`). The probe itself
  reads nothing on an NSE holiday, on 26-28 Oct, or after its fifth captured session. Delete the schedule after the
  fifth session (expected Wed 4 Nov).
- **Groww load:** at most 206 calls a day, one a second at most, only from :07 to :13 and from :37 to :43 IST. None
  before 10:07, so none inside A16's 10:00 mark.
- **Exits:** `0` on a clean day, an NSE holiday or weekend ("not a trading day; nothing read") and on 26-28 Oct;
  `1` on any source stopped for the day or for good, and on a sixth session.
- **Time:** about 4 h 20 min (09:50 to about 14:09). The 2-hour background limit stops it twice (about 11:50 and
  13:50), between slots; the prompt restarts it at once, and it resumes from its counts file.
- **Stored prompt** (paste exactly):

```
git fetch -q origin main && git checkout -q --detach origin/main; if that fails, post its error line to #fno-desk (C0C89E8QCCD) and stop. Then run `sh tools/routine_setup.sh --groww`; it must print "routine setup ok", otherwise post its last line to #fno-desk and stop. Then start `python -m fno capture-probe` in the background with the longest time limit (2 hours) and wait for it; it waits for its 10:07, 11:37, 13:07 and 14:07 IST slots by itself, so a "waiting" stretch is never a hang. If it is stopped at the time limit before its last line ("p0b <day>: done, ..."), start the same command again at once, in the same checkout, until that last line is printed (about 14:09 IST): a restart resumes from its counts file, never repeats a slot already started and never asks a source stopped for the day. Post any line containing "stopped for the day", "stopped for good", "alert NOT sent" or "NOT committed" to #fno-desk (C0C89E8QCCD) with the Slack connector, unless the same line was already posted by the command ("alert sent" after it). Research only: it never places, modifies or cancels orders, and no value, token or key is ever posted or committed.
```
