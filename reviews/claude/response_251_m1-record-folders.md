# Response 251: M1's record folders for the daily run (asked by the O1 builder)

Builder: session 013xqaNTCbSBytKgqpfaYFqZ (M1), branch `story/m1-record-folders`. Lane 1 (`fno/weather/`). For
judge B.

**Why (strong evidence: O1's step table on story/o1-daily-run):** O1's `weather` and `forecasts_v4` steps both commit
all of `research/forecasts/v4/`. So a weather step that fails after writing some files would have them swept into
`forecasts_v4`'s commit, and the reverse. The O1 builder will give each step exactly its owner's folders, and asked
each owner to name them, so O1 hard-codes nothing.

**What it adds:** `fno/weather/folders.py`, `record_folders()`:
- `("research/forecasts/v4/weather/", "research/forecasts/v4/weather_vix_v1/",
  "research/forecasts/v4/weather_checklist_v0/")`;
- built from M1's own constants (`WEATHER_FOLDER`, and the forecasters' names in `day.FORECASTERS`, under G7's
  `V4_FOLDER`).
- Checked against the code:
  - M1 writes its record through `WeatherRecords`, and its two forecasters' v4 rows through G7's `v4_writer`, one
    folder per forecaster;
  - the base rate goes into the record only and writes no `base_rate/` rows;
  - the private part goes to Drive.
- **Disjoint from G7's folders:** the G7 builder confirmed this to the O1 builder.

**Kept outside `wiring.py` on purpose:** `wiring.py` is in M1's `METHOD_FILES`, so a change there changes every new
record's `method_sha256`, and a re-run of an already captured day would then stop on `RecordConflict`. The new module
is not hashed, so the method hash is unchanged.

**Test** (`tests/weather/test_records_and_capture.py`): a real capture, laid out as in the repository, writes only
inside `record_folders()`.
