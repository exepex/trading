# MS-P0b: the scheduled session the owner would create (option a)

The probe and its rules are described in [MS-P0b-capture-probes.md](MS-P0b-capture-probes.md); this file only holds
what to paste. Why a schedule: the owner's 25 Oct rule allows no hand-run Groww command from 09:15 to 15:35 IST, and
the probe measures market hours only. Only the owner creates this schedule; no session does. Lane 1.

- **When:** weekdays at 09:50 IST, from Thu 29 Oct 2026 (cron `CRON_TZ=Asia/Kolkata 50 9 * * 1-5`). The probe itself
  reads nothing on an NSE holiday, on 26-28 Oct, or after its fifth captured session. Delete the schedule after the
  fifth session (expected Wed 4 Nov).
- **Groww load:** at most 206 calls a day, one a second at most, only from :07 to :13 and from :37 to :43 IST. None
  before 10:07, so none inside A16's 10:00 mark.
- **Stored prompt** (paste exactly):

```
git fetch -q origin main && git checkout -q --detach origin/main; if that fails, post its error line to #fno-desk (C0C89E8QCCD) and stop. Then run `sh tools/routine_setup.sh --groww`; it must print "routine setup ok", otherwise post its last line to #fno-desk and stop. Then run `python -m fno capture-probe` and let it run to its last line (about 14:09 IST; it waits for its 10:07, 11:37, 13:07 and 14:07 slots by itself). Never stop it while it waits, and never run it a second time the same day. Post any line containing "alert NOT sent" or "NOT committed" to #fno-desk (C0C89E8QCCD) with the Slack connector. Research only: it never places, modifies or cancels orders, and no value, token or key is ever posted or committed.
```
