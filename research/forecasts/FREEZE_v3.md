# Freeze record: forecast protocol, version 3 (story G1 v3: the panel extends daily; live Q5 against the 15:00 pack)

Protocol commit: `904c03697bf1f7d8256865ab3057fe2c2e9bcf50`

Frozen on 14 Oct 2026 (IST), after:
- ChatGPT review 30 ("AGREED WITH CHANGES") and the orchestrator's decisions in response 69;
- judge 64 and its addenda: the split freeze passed in addendum 2 (b312262), with its two should-fixes built in the
  protocol commit;
- the orchestrator's confirmation to freeze, in the order: protocol commit, then this record together with
  `panel-days.yml`'s schedule (that workflow is in the `panel-days` section, so both change in this one commit).

**Amended before confirmation, 14 Oct 2026:** `panel-days.yml`'s hash was re-recorded, from `5a7ec8dd156a6588c11edfb6cb592f3bdb3290d6aa6819c20bf7a96a0d1f9587` to `6971c6876c1bb4c157e74bb960653430eb8704c53e83f9364a7260b17f124b5a`.
The change fixes the archive steps' end day and the alert, two bugs found on the first run (38474280810). The protocol
commit is unchanged. The orchestrator approved this before confirming the freeze and before the judge's check of this
record. The protocol text, the `forecast-scores` section and every other hash are unchanged.

No append under v3 and no live question 5 score existed at the freeze. Versions 1 and 2 stay frozen and unchanged
(`FREEZE.md`, `FREEZE_v2.md`).

**The check:** `fno.freeze_sections.require_section_frozen` (PROTOCOL_v3.md section 5). One section per job that runs
it, so a change fails only the job whose files it touches. The protocol commit and this record must be in the running
commit's history, the protocol text at the protocol commit must hash to the value below, and every file of the job's
section must still have these bytes. A change to any of them is a new version (a new protocol and a new freeze),
never an edit.

## Recorded, not byte-checked

| File | SHA-256 at the protocol commit | Why not checked |
|---|---|---|
| `fno/research_data/nifty_panel.py` | `fb3a4bfdd3fe2a1f57f2e1fff22d44825d2e22c444f97ae99748943a92cdc51f` | A3's builder, which every appended day is built with (rules unchanged; also in experiment 1's record) |
| `fno/research_data/panel_rows.py` | `0fb6718d5067b8ab40c73123d0a599c8feff4420e8c789b8e1e62a4cb2f1267b` | A3's row rules (experiment 1's engine record) |
| `fno/research_data/panel_store.py` | `27ea3b0089f488ace4000d3721f0d9464b1eeb6465a55396a694128b75d418b0` | A3's file layout constants (experiment 1's engine record) |
| `fno/research_data/panel_reader.py` | `6860c74633fd8533d245d59a6754c98be76740b59e3f99965ec59433d86ef317` | the panel reader (v2's recorded code) |
| `fno/forecast_scoring/wiring.py` | `c24a4e9f422baba764ef85e6dea95652140ab9043052cddef9dc514cca87eb4f` | G4's shared composition root: run by tests/forecast_scoring/test_scoring_wiring_q5.py, which fails if the live resolver gets the panel's IV30 |
| `research/data/nifty-panel/manifest.json` | `89a063763de5159cf9ce1b4bc259ed4288ffdbb493a3369ceb8e3a8e75bf7636` | the panel's manifest, which grows by appends from here |

## Checked by `panel-days`

The daily NIFTY panel job (story A13) checks this before every run.

| File | SHA-256 |
|---|---|
| `research/forecasts/PROTOCOL_v3.md` | `0a79e7b1385bd0303cb2ba586e3fecdd063b5bb73d0722a8dc958de93865ab14` |
| `fno/freeze_sections.py` | `55e575aa18014bedd0b56bd113b6c59a60ecb6980162561316e9e4e600e6f485` |
| `fno/research_data/panel_append.py` | `ccd187c5eda4b09d1043067578ea02497dcddb1aacec1231f78e37be98eafdde` |
| `fno/pipeline/panel_days.py` | `57b16a6c1025b87c0e1a8ba6d721cb4f3624aa6bc540ac81dd440c33981421a0` |
| `fno/pipeline/panel_wiring.py` | `980d0e374a8eb17891337a16639809e62fd108c6ae8c203fb6ca3c58baa717bc` |
| `.github/workflows/panel-days.yml` | `6971c6876c1bb4c157e74bb960653430eb8704c53e83f9364a7260b17f124b5a` |

## Checked by `forecast-scores`

G4's `score_forecasts` checks this whenever live records exist.

| File | SHA-256 |
|---|---|
| `research/forecasts/PROTOCOL_v3.md` | `0a79e7b1385bd0303cb2ba586e3fecdd063b5bb73d0722a8dc958de93865ab14` |
| `fno/freeze_sections.py` | `55e575aa18014bedd0b56bd113b6c59a60ecb6980162561316e9e4e600e6f485` |
| `fno/forecast_scoring/q5_thresholds.py` | `a55516df4373163808ec05215e211f3f86a34c69f9b3cbfa0d85bb71d3023b02` |
| `fno/forecast_scoring/resolution.py` | `89cc9a4f17658d5a082920316a12b4d8747f9da1ce13bc9f1541b4c729b1bcf3` |
| `fno/forecast_scoring/score_sources.py` | `bf7924937375083c354a382eba0aa20f9aa125c02eddd41b4c38615be3b22182` |
| `fno/forecast_scoring/scoring.py` | `247c6b34790be5d8eb743ecf2b9b9f8c77a9edc09f822823c8f428f32ffc4cb4` |
| `fno/forecast_scoring/replay.py` | `894c307de6280e3b6d1bdf9539bab6b1255e4e1f88429ccfabc004046b981e58` |
