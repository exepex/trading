# Response 78: P8 flows first day (judge 66 item 4): builder's claims

Builder session, 14 Oct 2026. Branch `story/p8-flows-first-day`; judge first, nothing on `main`. Orchestrator's task:
the 13 Oct flows page was published empty into Azure with no alert (run 38501152610).

**Verdict in one line:** the reader now starts at the first archived copy (13 Oct), a session without its flows fails
the run with a named reason and an alert, and the docstring now says where copies are filed. A second, more urgent
problem with the same root cause is in section 4: 14 Oct's flows will not be archived tonight unless filing changes.

## 1. Root cause (strong evidence: committed manifests and code)

- `research/data/manifests/fii-dii-cash.csv` (and `fpi-daily.csv`) has a row for `13/` and one for `14/`.
  - `13/` was written at 08:00 IST on 14 Oct by `market daily 2026-10-13`. Its archive step `_archive_session` calls
    `take(day)` with the **published session**, so the copy fetched on 14 Oct is filed under 13/.
  - `14/` was written at 02:18 IST on 14 Oct by a `flows-download` run, filed under the **IST fetch day**.
  - Both cash copies have the same SHA-256, so both cover session 13 Oct.
- `FiiDiiCashSource.first_day` and `NsdlFpiDailySource.first_day` were 14 Oct. `FlowsReader` walks folders from
  `first_day` up to the published session, so for 13 Oct it read nothing.
- Nothing required flows to be present, so an empty `days` list passed the W11 schema and was published.
- The old test hid the cause: it monkeypatched `first_day` to 13 Oct instead of the source being right.

## 2. The fix

1. **first_day = the true first archived copy** (`fno/storage/snapshot_source.py`): 13 Oct for both flows sources.
   - **Why not derive it at run time from the archive:** the store interface has no listing (`get`/`put` only), and a
     Drive listing on every publish adds calls and a failure mode. The committed manifest is the archive's own record
     of every copy. So `first_day` stays a constant, and a test holds every snapshot source's `first_day` to it:
     never after the first manifest row, and for the flows sources equal to it.
   - **The guard caught five more:** the P6 reference lists (equity list, Nifty 500, symbol changes, corporate actions
     and by-symbol) have copies under `12/` but `first_day` 13 Oct. Their readers search ±10 days and were not hurt,
     but the coverage check starts at `first_day` and skipped the `12/` copies. Set to 12 Oct.
2. **No silent empty page:** `FlowsReader.problems(day, flows)` names a published session that has no FII/DII cash
   copy covering it, or no NSDL copy at all, once the archive has begun (`day >= first_day`).
   - `SessionRowsBuilder.build` adds these reasons, **first**, to its missing list. That raises `IncompleteSession`, and
     `MarketRun` stops before publishing: exit 1, the #fno-desk alert led by the named reason, and the previous
     publication stays current.
   - They go first because the alert shows only the first five items; a named reason must not hide behind file paths.
3. **Docstring corrected** (`FlowsReader`, `FiiDiiCashSource`). A copy is filed under the run's `--day` folder:
   - the fetch day for `flows-download`;
   - the **published session** for the publish run's archive step.

   So a folder dated D holds a copy taken no later than D's own publication. A copy filed under a later day is never
   read for D, which means no look-ahead.

## 3. Evidence

`tests/market_read_models/test_flows_first_day.py` (5 tests) and the old flows test, now run without its monkeypatch:
- `first_day` never after the manifest's first copy (all seven snapshot sources), and equal to it for flows.
- A 13 Oct-like archive (13/ and 14/, both taken on 14 Oct, both covering 13 Oct) gives flows for 13 Oct: FII net
  -1,305.13, NSDL present, both copies recorded as filed 13/, no problem named.
- No look-ahead: a later copy of 13 Oct filed under 14/ is unread for 13 Oct and is the latest copy for 14 Oct.
- Copies exist but none can be read for the session, or 14/ holds only 13 Oct's values: both named. Before the first
  copy: nothing required.
- End to end: the real `SessionRowsBuilder` with copies only under 14/ raises `IncompleteSession` whose first item is
  the flows reason. `MarketRun` then exits 1 and sends one alert that names it.
- Mutations (`python -B`, caches cleared): **9 of 9 caught**:
  - each `first_day` set back (cash, NSDL, P6);
  - a look-ahead window of one day;
  - the missing-cash check off; the missing-NSDL check off;
  - the problems not stopping the build;
  - reasons appended instead of first;
  - flows required before the archive began.

## 4. Open, urgent: 14 Oct's flows will be lost tonight (same root cause; reported to the orchestrator)

- `14/` already holds the 02:18 IST copy, which covers **13** Oct.
- `SnapshotTaker.take` keeps an existing copy and never fetches again.
- So tonight's 21:10 IST `flows-download` (`take(14)`) and tomorrow's 07:10 publish for session 14 will both find
  `14/` occupied and keep the 13 Oct copy.
- NSE serves only the latest session, so session 14's values will never be archived. With the fix above, publication
  14 will fail loudly. That is correct, but the data is still lost.
- **Proposed design fix:** file each flows copy under the session it **covers** (read from its own content), as a new
  archive series so that no existing copy or manifest row is edited. **Not in this commit:** I asked the orchestrator,
  and it follows as a separate commit if agreed.

## 5. Gates

Full suite, `ruff check fno tests tools`, `ruff format`, `python tools/check_imports.py` and the 350-line limit: in the
commit message and the message to the orchestrator.
