# Freeze record: forecast protocol, version 4 (story G6 freeze; questions V1-V7)

Protocol commit: `1712a476b73b305c5f956a5911c14de48fbc80d7`

Frozen on: 2026-10-25

First counted session: 2026-10-26

**What this record does.** It freezes `research/forecasts/PROTOCOL_v4.md` as committed at the protocol commit above,
the last commit that changes it. It also freezes every file v4's code reaches, in three classes (protocol section 10):
- byte-checked files: a change to any of them, or a new file in their folders, is a new version (v5's own record),
  never an edit of this one;
- recorded files: shared files that decide a v4 value, each with its SHA-256 and lock; every v4 report prints the ones
  changed since;
- files named as not deciding.
The check is `fno.forecast_scoring.v4.freeze_check.check`. A confirmatory look refuses while it finds a problem, and
every v4 report prints its result first. Only live forecasts of sessions after `Frozen on:` count; the first is Mon 26
Oct 2026, the owner's choice (25 Oct 2026, `docs/DESK_DECISIONS.md`, "The owner's seven answers before Monday's market":
"I go for recommended option, which is Monday, 26 October").

## Preconditions (protocol section 10), as met

- **The judge's PASS:**
  - the protocol text: judges 414, 430 and 436 (pieces 1-3), then judge B's check of the final text;
  - the freeze story's text: judge 597.2;
  - the freeze code: judges 606.2 and 606.3.
- **ChatGPT's review:** paused by the owner on 22 Oct 2026 (`docs/DESK_DECISIONS.md`, "Cut-list accepted";
  `docs/JUDGE.md` quality rule 9). It is not a precondition while ChatGPT is inactive.
- **G7 and G8's code exists:** G7, G7b completion (432071d63), G8 and G10 completion are on `main`, and so is G11.
  Every byte-checked file matched a file at the freeze, and no v4 module reads `config.yaml`'s rate (the tool refuses
  otherwise).
- **The owner's items A-C, D and E:**
  - A-C: 15 Oct 2026, "A accept, B accept, C accept";
  - D: 15 Oct 2026, "3 B", rule E+D (section 5.3);
  - E: 15 Oct 2026, "merge G6, E option 2", the share cut (`confirmatory.crash_dominated`).
- **X of section 1.6:** 0.006104597099330481, from 1,661 sessions, source revision
  `1d68c4477ec2356ecc9a3c5583c5702152424b8f`, nearest rank (`terms.MOVED_AFTER_CUTOFF_X`,
  `research/forecasts/v4_moved_after_cutoff.json`).
- **The owner's sign-off:** 24 Oct 2026, "Consider v4 sign off"; W1, W2, W5, W6 and W7 signed on 25 Oct 2026 ("Keep all
  sign ... W1 to W7"); W3 and W8 decided on 24 Oct ("both", "W8 - yes"); W4 dropped.
- **Earlier decisions quoted:** listed with keep or change in `docs/stories/G6-v4-freeze.md` (section 4, "Keep or
  change"). Rows 22a ("freeze with the AI slots unregistered") and 23 ("V2-V5 under their own later record") are
  replaced by the 24 Oct sign-off. Row 22b ("the AI files are hashed in their own registration") is kept: see "AI
  registration" below.

## Slot registrations (`research/forecasts/v4_slots.csv`, written in this commit; append-only after it)

All 15 family slots start on 2026-10-26 and are registered on 2026-10-25. The `rules` rows are this record's. The 10 AI
rows were printed by `python -m fno ai register-v4-slots --print` on this tree (story G11 C13). From 2026-10-26 every
baseline-observable day is either observed or a miss for each slot (protocol section 4). The AI books are live from the
same session: `daily.live_from.ai_books_v4: "2026-10-26"`, set in this commit, so no tree has the AI switch on without
this record. Books 2 and 3 count as forecasters only (owner, 25 Oct 2026).

The registrations as written (the file's first 15 rows after its header; a test keeps them unchanged):

```
question,slot,forecaster,effective_start,registered_on,decision
v1_rv_next_session,rules,v1_close_blend,2026-10-26,2026-10-25,"DESK_DECISIONS 24 Oct 2026 The owner signs off protocol v4; 25 Oct 2026 The owner's seven answers"
v2_rv_next_5_sessions,rules,v2_close_blend,2026-10-26,2026-10-25,"DESK_DECISIONS 24 Oct 2026 The owner signs off protocol v4; 25 Oct 2026 The owner's seven answers"
v6_abs_move_2pct_next_session,rules,weather_vix_v1,2026-10-26,2026-10-25,"DESK_DECISIONS 24 Oct 2026 The owner signs off protocol v4; 25 Oct 2026 The owner's seven answers"
v6_abs_move_2pct_within_5_sessions,rules,weather_vix_v1,2026-10-26,2026-10-25,"DESK_DECISIONS 24 Oct 2026 The owner signs off protocol v4; 25 Oct 2026 The owner's seven answers"
v7_vix_higher_in_5_sessions,rules,v7_vix_vs_mean20,2026-10-26,2026-10-25,"DESK_DECISIONS 24 Oct 2026 The owner signs off protocol v4; 25 Oct 2026 The owner's seven answers"
v1_rv_next_session,hybrid,book2_hybrid_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v1_rv_next_session,ai_team,book3_ai_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v2_rv_next_5_sessions,hybrid,book2_hybrid_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v2_rv_next_5_sessions,ai_team,book3_ai_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v6_abs_move_2pct_next_session,hybrid,book2_hybrid_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v6_abs_move_2pct_next_session,ai_team,book3_ai_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v6_abs_move_2pct_within_5_sessions,hybrid,book2_hybrid_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v6_abs_move_2pct_within_5_sessions,ai_team,book3_ai_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v7_vix_higher_in_5_sessions,hybrid,book2_hybrid_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
v7_vix_higher_in_5_sessions,ai_team,book3_ai_v2,2026-10-26,2026-10-25,DESK_DECISIONS 21 Oct 2026 v4 freeze answers (3); 24 Oct 2026 Close v4 in full first
```

## Ledger rows (B4, `research/ledger.csv`, written in this commit)

Trials 101-108: one row per v4 question, experiment `forecasts-v4`, kind `prospective`, `protocol_commit` the protocol
commit above. Hypothesis is `yes` for the family's questions (V1, V2, V6a, V6b); it is `no` for the reported-only V3, V4
and V5 and for the descriptive-only V7.

## Settings v4 reads from `config.yaml` (recorded with their values here; not frozen)

- The rate: none. v4's 6.5% is `fno/forecast_v4/pricing.py`, which is byte-checked; `risk_free_rate` is read by
  no v4 module.
- `quotes.windows.v4`: `{start: "14:30", end: "14:40"}`, when A4e captures. The cutoff itself is enforced by
  `terms.V4_CAPTURE_START` and `V4_PACK_WINDOW_END` in `fno/v4_pack/codec.py`.
- `daily.live_from`: `weather` 2026-10-22, `forecasts_v4` 2026-10-22, `v4_pack` 2026-10-26, `forecasts_v4_pack`
  2026-10-26 (set in this commit: the owner's standing 24 Oct rule, "Merge and turn on everything completed
  now", and the v4 sign-off; V2's primary baseline, V4's and V5's live rows), `ai_books_v4` 2026-10-26. These
  dates decide which days run; a late date makes misses, never better scores.
- `budget.cap`: none (owner, 24 Oct 2026, "No monthly budget cap for AI. Keep it unlimited."). The AI books' budget
  stop (`fno/ai/budget_stop.py`, recorded) can never fire while there is no cap. A later cap, which would be an owner
  decision, would start AI `not_fired` misses, never a better score.
- The freeze date for BG1's stop-rule review is read from this record's `Frozen on:` line (BG1-t); no config key
  holds it.

## Known limits

- **Replay libm limit (judge 508):** `math.erf`'s last bit differs between glibc 2.39 (sessions) and 2.43 (Actions since
  21 Oct). G1 v3's byte-comparing `forecast-scores replay` can therefore say "not reproduced" on a post-21-Oct day, and
  `fno/forecast_scoring/replay.py` is byte-checked by `FREEZE_v3.md`. Until v3's next version, such a result is checked
  by hand for last-bit-only differences. This freeze's platform is in the "Platform" section below.
- **v3's silent git read:** `fno/forecast_scoring/wiring.py`'s `last_commit` fails closed (NotFrozen). v4 does not use
  it; v3's next version fixes it.
- **2027 calendar:** NSE's 2027 rows are not in `nse_sessions.csv` yet. From Tue 22 Dec 2026 V4's terms are void until
  they are added, and from 29 Dec V5's. BG1's review date (Fri 30 Apr 2027) rests on a weekday fallback until then.
- **Not byte-checked by design:** the recorded files, the settings above, and the data that grows (O6's closes, A16's
  and A16b's rows, NSE's calendar, the Drive archives); each says what protects it.
- **An import walk covers imports, not injection:** a value handed in by a composition root (BG1's meter into the AI
  budget stop) is named in the lock of the recorded file that receives it.
- **The check runs at the look and on every report:** it is not a guard on every daily write. Rows written meanwhile
  by changed code carry its method hash and are found by G7's and M1's hash gates.

## Frozen files (checked byte for byte)

| File | SHA-256 |
|---|---|
| `agents/forecast/book2_hybrid_v2.md` | `c73e452042326029c6af757b303edf7db398b27da69df652f5699fe362368165` |
| `agents/forecast/book3_ai_v2.md` | `8f9dd780f81223cb5856b3ea76d6a3586c02c5a1eeedd1e9adb078672bb2f3cd` |
| `fno/ai/v4_book_inputs.py` | `518510a6c40d8eb9ee609576620d31ab87b3a46462e0f0171fe988f5cd1f053c` |
| `fno/ai/v4_collect.py` | `8699bd708a46322a6711209559cc999381aa8b49f351ec75f34d174475e8a791` |
| `fno/ai/v4_cost.py` | `780e619508cfb401333c782ce95a1704486858d1a74a963a40e1124438cda815` |
| `fno/ai/v4_fire.py` | `0333ae75335f670a3a2af77b9ba91c1ec433f130230c109b63592c66dbb2fa3d` |
| `fno/ai/v4_go_live.py` | `d745432f4fb192dcf6cfec891f0cb16c9774b3178686124fee346106c1b10eda` |
| `fno/ai/v4_input.py` | `185430fdf9a033c30577d79b054fc1314e9cce1ad29151a8889df3d657eaeeb8` |
| `fno/ai/v4_input_check.py` | `0e2a8c88434635dcb0583f0bb82590f69e4d22a1c365500f94f7383904948574` |
| `fno/ai/v4_pointer.py` | `9c9edb5210135116dc1195cee084f0478659456b10fb0c0a3ee7869f8f6a9731` |
| `fno/ai/v4_register.py` | `8aa65296743f86ec40f247f9ce605551d539b0153257d2c39117345de79d9e75` |
| `fno/ai/v4_rows.py` | `40c7619310e89b85aab6d83e3a0a1cc3b496a688b7ebc784d370032ac6f3b0a7` |
| `fno/ai/v4_settle.py` | `57f1c64a2bcb46d7c1812c1f5d6dd05ebbe38b6dd76c737661ceceaac19eb520` |
| `fno/forecast_scoring/scores.py` | `c729bf293210779544a3529a71e8f277cde5404a835dfd68b5602dcb19173e80` |
| `fno/forecast_scoring/v4/__init__.py` | `6b58ef5a674bb10e9a7d2c8215f9af7867d2247f37f243c57c47f66b9052d3f7` |
| `fno/forecast_scoring/v4/cli.py` | `4c5861b8f366f17711734f3b98385e9d5887cd5003ad17ecfef4ad61ddfde3c7` |
| `fno/forecast_scoring/v4/comparison.py` | `94c2595f5e0ca89c0030096312b2350a989c95cbf7446202ee9de0369b84e8fd` |
| `fno/forecast_scoring/v4/cutoff_moves.py` | `0713017f8fb4e6223d71890ccde2b6ef9e7bd3c8e032bc0b530f66dcbc2a32b7` |
| `fno/forecast_scoring/v4/days.py` | `62e484738d08010bdfa26a1fc254a773a1652a4a170bb9115c22c5b50bbff309` |
| `fno/forecast_scoring/v4/deadlines.py` | `bf6d6f8768c62e17dc71cbb655cf0d90dd6cbb370dd627b4bd2f6bab23cbe9b8` |
| `fno/forecast_scoring/v4/diagnostic_lines.py` | `392ca943187b9c6d2546205539a2e4070b86a7e7233063745d64fc9e1ce8d1b9` |
| `fno/forecast_scoring/v4/drive_forecasts.py` | `748b9989ff53af53fd7c6e9c93e207e7cd27acf92367a751c018592c145cf775` |
| `fno/forecast_scoring/v4/drive_records.py` | `0fdbbfb7ad041781a16a9e18fd339fff46b58e9e62b27247f618300a9de01757` |
| `fno/forecast_scoring/v4/freeze_check.py` | `50447549d2fcbe7dcac4c999dc62fd69a013e6b45bada43a493845c0a50ee4cc` |
| `fno/forecast_scoring/v4/freeze_classes.py` | `a22232893de12c0f9de71cdcbd8fbcccac11a66f5f96424727ef6528a54da4f2` |
| `fno/forecast_scoring/v4/freeze_disclosure.py` | `98824bc4748ec39bc05911ebbe855dcad1fbd2833ed7fabe7a393e06b853ce17` |
| `fno/forecast_scoring/v4/g7_series.py` | `e70a237a2ca028afa2e3e7d28e820f140866075b0596182c2e9d13ed103242b1` |
| `fno/forecast_scoring/v4/inputs.py` | `4d95ac454b4cbaf48c8cd20d4080105796f4351008b5e7dca47022119d34f628` |
| `fno/forecast_scoring/v4/look.py` | `ee68a1d58248cd2c496c9c40cb7a703e14776a809711f80acc4c5c0ce2fb9935` |
| `fno/forecast_scoring/v4/outcomes.py` | `2d7da5966ea9416fecb03f9b7677ac6b8132cbc68aea67dd23b9cfb64a2001b9` |
| `fno/forecast_scoring/v4/primary.py` | `e2af28ffac61e0cf1cc6190f7c9f8dbd11909aca15e697d37976d51922c14e61` |
| `fno/forecast_scoring/v4/reconcile.py` | `11c4adf055a0a367640413c616c3c681f0dc60786a96e4f589efe55216578501` |
| `fno/forecast_scoring/v4/records.py` | `b3789288c152b3bc36a939a63ba0c85efd5a75f65cadddac725a77b207cd8dc6` |
| `fno/forecast_scoring/v4/release_days.py` | `2eeb5a1e4a2028dc58777e6308f82855c1ef5c2a7f8d5221af94420379e35f96` |
| `fno/forecast_scoring/v4/render.py` | `31dbf63e43a61bbf8a7bed265d906b1b85ae307bcaa11ca235d7967b7b22f69a` |
| `fno/forecast_scoring/v4/scores.py` | `3d0d472017dc138c28195357f06361fc815f0293aa554faa9c4c483789fda609` |
| `fno/forecast_scoring/v4/scoring.py` | `b5120f91ff11443f00c70a4e50f09d8662ffe09e23a07a2ebe9504ea357c4652` |
| `fno/forecast_scoring/v4/slot_file.py` | `ae455875861eaf5c37882572910d7979415d3acf3fd4cfb72d45df72ac358fa9` |
| `fno/forecast_scoring/v4/thresholds.py` | `186a300fbc78eb6b22e244b9b2349ddd21541d6178f4f4f7a14395e8c889cf7b` |
| `fno/forecast_scoring/v4/wiring.py` | `7e9e8b823f81cd10d80602127cab4cad44a4369ec5c5e538c685c1d250de45cf` |
| `fno/forecast_v4/__init__.py` | `c9a2978ffa3ec3480e32f322876ac17d478658b367f7ded6891c53b86b3ca3f1` |
| `fno/forecast_v4/bootstrap.py` | `81117ab1003ca1222bb98b8c2954699ac0d6cc511d6b197ca7ec7aa56fc08a67` |
| `fno/forecast_v4/confirmatory.py` | `bd275443da99c0cfe1b457127a48d1d0f9df04f49836c243c07d8f8b528e904d` |
| `fno/forecast_v4/cutoff_move.py` | `c18b367b20cdaa83a134cbec5563de1859ba940607874ef9213f10f34de70982` |
| `fno/forecast_v4/diagnostics.py` | `1b339ba883a7f9eefca69c673687beb2767381097d8719f58a2398e206e5157b` |
| `fno/forecast_v4/eligibility.py` | `c00e4321dc335c7809f5eed3284e4567cc4981e36d156694de223a387fb7f74a` |
| `fno/forecast_v4/family.py` | `72d351be2a4813dabbf9b4bea779b62006ba2c1b001df83780c060ce3a997285` |
| `fno/forecast_v4/loss.py` | `69b15b2e0f5bc6393efd4099d8f40b55834f448088e4b32d5539c5b29884283e` |
| `fno/forecast_v4/misses.py` | `0516c4ddac8ae8d6b8c3336889f146b18edd3bb304a7393f713c47a8d6f203f8` |
| `fno/forecast_v4/pairs.py` | `d24afce6baf7a6f1371a4fc2d5169b72cb57dea988794385e3a1ac689ee6d88e` |
| `fno/forecast_v4/power.py` | `626e3eb2d723d30fdb83cd34b6f7c2dfe99a6a09f34fa13b6df9909338fbea04` |
| `fno/forecast_v4/pricing.py` | `386d1c685a70f8a76730d2e6570abaa1438f5f59351c9f9b74d932376f1bc371` |
| `fno/forecast_v4/regime.py` | `82c4b87bca1193d57c745f90d65ef86d5a020c530bd87535897077d12d231e53` |
| `fno/forecast_v4/sessions.py` | `0bbe19dace0731b20dcb8ce8dc1537c032e4d495f8bee4234ef964346002f3fd` |
| `fno/forecast_v4/settlement.py` | `e8b70fd396fb61824029cf0c9f79e440aaca7a4560ff6c5d8443800b91f7399d` |
| `fno/forecast_v4/stop_rule.py` | `762a7c71b479558f47853271cc59831321e89d88d22d21d726db9d7c7833bf7d` |
| `fno/forecast_v4/student_t.py` | `d0365236b58840e79263bfb3067ddbf3bf352c42e861254b651cb781bb1b36e6` |
| `fno/forecast_v4/terms.py` | `2b030bdd3c6eeeb17add9977f4408f955e7cb1b6ac9be102d1e913a145130a1b` |
| `fno/forecast_v4/units.py` | `a0d464a59c431dadffaa65f6e180ae6511e4c5174bbe011249a004d41a9b031c` |
| `fno/forecast_v4_rules/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `fno/forecast_v4_rules/backfill.py` | `d0bbb052fd30317ef142e296fcc1a4a8d005f504d0d5ffc5f49de5eb5bf63bb8` |
| `fno/forecast_v4_rules/baselines.py` | `cb2a7c67b4ef18c126c6753b4fd40b8b1fd558796c79a52bec3c5b8b45c19937` |
| `fno/forecast_v4_rules/candle_history.py` | `774323c0cb0e7796de43605f6f2b604a28a9f1782d55b63540666ff824901d5d` |
| `fno/forecast_v4_rules/capture.py` | `8fb33a160baff955a32412feef2ad177e14773c22c34bab1aaa260fc28437605` |
| `fno/forecast_v4_rules/cli.py` | `94d42831f95282d1206ef0f319b1c235c227dc801e1fb8e230725c707da1fcef` |
| `fno/forecast_v4_rules/constants.py` | `f0c6149773c3a1f730ac3ee74b1d69e24ad9ce9298a3c0d2257cdc34ebc25bbf` |
| `fno/forecast_v4_rules/drive_records.py` | `1396b81f39f50b0c792126df00ebe80962402b7405d1285e2a490a3a6f1e946e` |
| `fno/forecast_v4_rules/eod_iv30.py` | `73b93a2dc8be3baa8cf03d7c22bc7db5b2b027960f636dff4376ea2d9fa2ea44` |
| `fno/forecast_v4_rules/implied.py` | `5281c9f9bd0b9d59e595d928bd58ba1045559a1de86a6d4c5c4527a451d867b3` |
| `fno/forecast_v4_rules/implied_backfill.py` | `a20270401971d4a69cf4b8c969abc71e12d634911d19f150e6be4453809aa90c` |
| `fno/forecast_v4_rules/intraday_series.py` | `82ad6058a620c89d7ac90b746e355abacb1b48aa661c88b4fca534f3e9e54269` |
| `fno/forecast_v4_rules/live_quotes.py` | `02baa73db98817c538bf43de7aedb7e4680d26028672daef324e62c5a20b00bb` |
| `fno/forecast_v4_rules/option_history.py` | `2f13c823a1f67b8d02c823458d6d78ee2ff94d3ab793b2740b6d10ba1d98e6c8` |
| `fno/forecast_v4_rules/option_outcomes.py` | `5fc6ed327d4db29399175a6dd2e2aa4401c3b84b12851f029ba71b4f546e1578` |
| `fno/forecast_v4_rules/option_probabilities.py` | `1fd2be3394f258c6c9e72f0955bf1b66e30321b1a279d93ac0beb078a1c66712` |
| `fno/forecast_v4_rules/option_terms.py` | `b07a451696bebd50bed4a71666ff954368c7f39cf885f6e3eebff647818c2aab` |
| `fno/forecast_v4_rules/pack_adapter.py` | `ab936bd85d1dbaf8d4254b98ac79a8eb7799dcd35c71c8eeb3b9b00ee1801bd9` |
| `fno/forecast_v4_rules/pack_capture.py` | `50493f09f3f994c82f09ef9ffcf96d3a2b07e2cfd74d67434251420c4a4cad43` |
| `fno/forecast_v4_rules/pack_followups.py` | `59cfd37a1ebf58a340cf37634b31a5c656e7c145d139aaf4c6872756f9108239` |
| `fno/forecast_v4_rules/pack_wiring.py` | `b4629a9b5b734b5e6b0fca47158a451fcff019c2b2c2cae5355bdbad83e3966b` |
| `fno/forecast_v4_rules/ratio_store.py` | `0e5bc365331bb8e586e7e88f6afd3caf0053e85a79f0ab13d03f0edc646db147` |
| `fno/forecast_v4_rules/records.py` | `2c051d2b405ccdc23909408ae0ad34b50d9846187ddd57cbb3395f51c2610bd0` |
| `fno/forecast_v4_rules/rules.py` | `8b0cb418c772852f752a1e2c79faaf573039e8599de272bb5cd60bded171a101` |
| `fno/forecast_v4_rules/series.py` | `22ace826f4581414cd9d684ee0a774927cd333b548215e58bb7359088042cf05` |
| `fno/forecast_v4_rules/v4_expiry.py` | `2d2ba0cfd0c0b68a1b61ebbcd8854a1ee4ab9c1590643f9c69409d68a1836533` |
| `fno/forecast_v4_rules/vix_rule.py` | `43bf170cb3d9893f0613b6425768307cc2b6f4a8e75db9df7994b4dfb889b1dd` |
| `fno/forecast_v4_rules/wiring.py` | `83c6d7a1c10d4bc3875a7e4418a36796235b4848c01d8f8e683d944f077afa28` |
| `fno/intraday/realised_vol.py` | `a0b23a9677ebf7f256954c3c00360227e15fdee219939fa59b27457a6d98e882` |
| `fno/intraday/session_rv.py` | `dd2505a65d78326c156e305e924ab1a5fca029754c4b761d30e0db932a94ca3e` |
| `fno/intraday/slots.py` | `1b6209c767937831a62608eb68835f74882a8991c798dc09bb9defa86b2e77c0` |
| `fno/intraday/status.py` | `845082ff5894396975f6c2aa6c91019b10cbac6fb07ece6f7085e7135c31deb0` |
| `fno/quotes/v4_extras.py` | `375811c72ce90b2d8489e50f787d69b5a5b463b79bb3024f6735cd12c6100e93` |
| `fno/v4_pack/__init__.py` | `3e831cf57ea9a0b55dbea8744269254116ecaf9b5489626968429311395a92ee` |
| `fno/v4_pack/builder.py` | `ca5a19c6ba98627dae61b36ebca8f4db65d1796be0c46c31ad7593c4b32bcb21` |
| `fno/v4_pack/capture.py` | `3d36438e83378c0e4d391ea0dea682ecc5661618e284a7b41d500ccb7d43b860` |
| `fno/v4_pack/cli.py` | `05ddea8c84d5018d1d03b2512db08bedff228a662bc6c7065d8e83a78eb4cca4` |
| `fno/v4_pack/codec.py` | `cba6df986615e9c8942e504aac6ea58eab63c20c890656c5a73d42e2ed8cacf1` |
| `fno/v4_pack/commitment.py` | `3bb0ea3d9de62d5c12948afc50245befb444dc7c8c0fe9340142d4d122cb840e` |
| `fno/v4_pack/commitments.py` | `d33fb7c8d86ada9f02af86ba9da3e1d84989758c10e5e309553063d8179fb8f1` |
| `fno/v4_pack/deadline.py` | `61a24fd46fa15b03134bc48e4e407fb14d3d5feb7f26a77366db2432ecdae366` |
| `fno/v4_pack/guard.py` | `c4f7ef9d1f224883345ff17253fb18ad97bd305f98e347532e28fd0601f10b4c` |
| `fno/v4_pack/model.py` | `f99dd1c92163087ec1931c14dfe1082ecc4c43ac84d525e7ebd28e91d763c5f8` |
| `fno/v4_pack/overlap.py` | `1a70653e03d9aa2eb3ecff5d20faa12131c17317a432d586514d35b957d79981` |
| `fno/v4_pack/paths.py` | `580b50820d1aebc52bfd4ad21b2b771dbb99a7f9f812692e025faadee22a80b7` |
| `fno/v4_pack/release.py` | `44c3c97cfb7f5b700cc1f57379db547c9226d5dfecdf7b1c1c2363bdc1df86e6` |
| `fno/v4_pack/release_run.py` | `cf2b8d59576f55c6067e4bc9dc3d9660c17c7fab41632168b012c0d2d86593f1` |
| `fno/v4_pack/sessions.py` | `e02b487ec077616caad4b2684a2779a9009d3b5b703bb5ea2427c060f00cb5a6` |
| `fno/v4_pack/wiring.py` | `a5af48e578944de4c182388fdbc15a22d0f877f4429e5524e90df8651c2c42b3` |
| `fno/weather/checklist_v0.py` | `556ca2deb8f17b6de2d88365f71b8b61e50d965af3daa5c7b27a72af56e3f280` |
| `fno/weather/colour.py` | `549dfb71eee704d0fc7876e1aa32665392ebba3bfabb6e045cdecf63f783f1b5` |
| `fno/weather/constants.py` | `9da4da4211e009c9f306ac99f0fd3fa083f801772e966ae845c02b4cea0c3651` |
| `fno/weather/day.py` | `012a5927ec586c9e1cf46b3ee057ac0cfc680d794735fe60d8ab1c0ca1ad36a6` |
| `fno/weather/v0_live.py` | `dd68f4e6aecb6c505e85bb7ab6926689de03ac05eab03e2eddce61b5c4dd31b7` |
| `fno/weather/vix_scaled.py` | `b2b30ba432129ff0b5c334b9fff3f37f6a2ae3653aeea99255df1f302b5091e5` |
| `fno/weather/wiring.py` | `eaf9b051ac1f46cf93ce0bef918fca2fcbd40b8789d9f8483a80c14693769205` |
| `research/forecasts/PROTOCOL_v4.md` | `c639f67db5b6a2589d48f7d63bc8f92b0867938d736c35d4bcd483414008942d` |
| `research/forecasts/PROTOCOL_v4_calibration.md` | `e295c1a93c8c0fc2a395e16f013282013de0fa77a2f731f2152ef2517f5c39a2` |
| `research/forecasts/v4_brier_bands.json` | `13c44a218d40ed5b5087b9f482724061f3d1eb68020f54ffb511eb180dc524dc` |
| `research/forecasts/v4_brier_bands.md` | `fb778cc02782585e10f0c4c961654df4e5ba9858d279c5e61ba8741960136d96` |
| `research/forecasts/v4_brier_busy_stress.json` | `25459ce293e6822d9290489fe5efe1d125b62e7f870f4cbd31ec63b022a1dec8` |
| `research/forecasts/v4_brier_regimes.json` | `436617b9225bb96c3ca8ad0562769d3d52d8b5414fae37eec14c954821e7fda1` |
| `research/forecasts/v4_brier_regimes.md` | `ddb006df670a4104009ba1b05a88d6662450cc2cbd966cb8b2cc5c739d410484` |
| `research/forecasts/v4_claim_thresholds.json` | `70f4574a8f6b23f0b8fcd08ce509478363a49cecaf202e849c60738538cc3b5c` |
| `research/forecasts/v4_claim_thresholds.md` | `cbe67466f2f261cd3bf2a114a87db36242caa5b899173727ccfc0a45a10100bb` |
| `research/forecasts/v4_crash_cut.json` | `80effefc87441e07cfb5208c86438cdff7f9f72d0572e214a9f34d68b650cb90` |
| `research/forecasts/v4_crash_cut.md` | `028a9e03f65449222930fa221dc0a03dff8673c5f4f11fe803210a49353c6c04` |
| `research/forecasts/v4_futility_study.json` | `963dc5cae46d45a9ef6869390db72d201eb43f2436753308856a2a2d4ff6d4ac` |
| `research/forecasts/v4_futility_study.md` | `0d53080561cc28bf6fe8ebd785f11bc14345ddc5608dbfb362bf9b58e084d522` |
| `research/forecasts/v4_moved_after_cutoff.json` | `18bee96cb75073a9a74a20bef96b43b844287a33d9b86aa42c0aa180140c47cb` |
| `research/forecasts/v4_null_calibration.json` | `696a136688c38f99ab62edcf9cdfeda0b66333885b8bac3a26f29095774cec24` |
| `research/forecasts/v4_null_calibration.md` | `6ecb8cc802aa6ce60e26f69bb83245230a20def166d41747e2e507080c7218a9` |
| `research/forecasts/v4_regime_stress.json` | `ac0830a0ebafeb26dd2b8015dfc067db540217aa8a488c99868e3c76def4be31` |
| `research/forecasts/v4_regime_stress.md` | `d35db9243894e0ddd584893bc2167e040c61fc54c5208c45f6dd3b79bf1de0ab` |
| `research/forecasts/v4_size_study.json` | `eb96aad037cd5f3a25c7abbcedc8c1d94cffaa29644d8bd927e1c2ea489314e4` |
| `research/forecasts/v4_size_study.md` | `f56528b95e884b64479392964aa1b2abad07de73f52bf85b953f25cc41666ecc` |
| `research/forecasts/v4_vix_null.json` | `612fa39d76afa2df725195756eea3faa2195caf11ff5609bae6bece45db3c9b4` |
| `research/forecasts/v4_vix_null.md` | `2adf1d3f6bd31f006a676f15f821cd2bedb739554746148eadf327cb6d1fbf37` |
| `tests/fixtures/forecast_v4/v4_golden.json` | `2c155f186045008278703f976a219970e2dc338263afcd04d6257194d8af493b` |
| `tools/v4_brier_bands.py` | `96fdb51f8412a911f7f808532d44a1f99a6a08d53a02c0911b1f792a4ab13af5` |
| `tools/v4_brier_regimes.py` | `a65d12bd7f2fc8a3bff2d1bafba43fbaa973bfbeb2ebb5b72f2c9c88fce08960` |
| `tools/v4_claim_thresholds.py` | `21ee7490941320ae3730d4852b8210b5015989ccab62dc5092a6cb7e6928e574` |
| `tools/v4_crash_cut.py` | `6e7531ba5fa99845834454bcb0a7a4ae00c7d55749093909b46d65288c8cf57a` |
| `tools/v4_freeze_table.py` | `5e5150c403afa54874d3e34e03793f33c592674d1ea121c8cc7cf300b05ccc23` |
| `tools/v4_futility_study.py` | `43a2553d14c4042770ffe5afb1461456481f7427d2e4246a95cfd4cc29e2d1f6` |
| `tools/v4_moved_after_cutoff.py` | `71fd74f9d36b23003595a311be4bc27e13930585c2ebc4bbbadfc7ccbd0ad908` |
| `tools/v4_null_calibration.py` | `bf5a0b597c4e30c1eeaae61fcff0175a54c7dc81e3f9ef58b674b405ab0ca90c` |
| `tools/v4_regime_stress.py` | `3ba03c3494a3d932c69bcdda54b714b5a77bacc2cba5a942bc113bdd1724954c` |
| `tools/v4_size_study.py` | `278ea4bdb6bcbc984d0fae30b2afce37c3bdaca87f513e34a0011b1d084bef57` |
| `tools/v4_vix_null.py` | `a4a4d490ae68a635e1bafec54d098823c928c624cf82d6ced61475e23b4f58ac` |

## Recorded, not byte-checked

| File | SHA-256 | What it decides; its lock |
|---|---|---|
| `fno/analytics.py` | `2df14945232de7eff5920eca6e2dd9b249ef5ef367c935700ffdb9dde29b06f2` | `norm_cdf` in V5's option-implied probability; G7b's hand-computed probability tests |
| `fno/constants.py` | `5918d2af66f316931f892001509778ebd1e7c9d8f19a75cec5d19acdaa001665` | question, slot and label names; protocol section 10's list; v4's tests read every name |
| `fno/desk/settlement.py` | `e5fdea092005843519cb8dca55a0b1b6a2aa7317ce0cebdb4b661cb95fd4d18d` | V5's final settlement (`NseFinalSettlement`); section 10; E7's and G7b's tests |
| `fno/fo_bhavcopy.py` | `44f548e196678726bdae72807cbb033ccb319ac2fbf2cfd2373c096ad0c8c7e6` | parses NSE's daily F&O file: V5's `SttlmPric`; S1's protocol names it; E7's and A11's tests |
| `fno/forecast/iv30.py` | `911d623d4790ac19fdfd86e5ab8a4c1590821034bf78366d857661fa45c0f466` | the EOD IV30 proxy and the IV30 interpolation; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/forecast/live_pack.py` | `279eb12b15a798e0eefcabb3bfacfc28371be6852e74166beeea8c38fcef706c` | the pack builder's live quote reading; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/forecast/record_files.py` | `49a8fbb75485dcd45923549da8dccc950af931ba33dd64239cab8c6f3992c160` | the forecast record files the AI books read; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/forecast/schema.py` | `c465583109a1865ac2b629acfa6f332bb3fef3cb62fdb0f34b7efe57a680e60a` | the record schema under schema_v2; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/forecast/schema_v2.py` | `75da00476ef6f25d5da73d8fda66980f21391a902475e24bd52fdab7d1e10e62` | the record schema the AI timing reads; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/global_cues/table.py` | `a0e9262af4d89b4572961fd7d2e45e717b27988e6fc7ab5b48e44b29a3124312` | the provenance label `backfilled` W8's candle reader keeps (A16b rows); A17's tests |
| `fno/intraday/candle_rv_table.py` | `7e55c7ddc4abbc5d44b37103d19a749cf0e850fcf6b9aeafef998c41a761df77` | W8's ratio window rows (A16b candles, backfill_window, judge 596); A16b tests |
| `fno/intraday/clock.py` | `6963145197df17ccd7d7f094acff3b3fde894bc33cd5f357b55c26b1b466b97a` | the pack builder's clock check (honest times, protocol 1.6); A16's clock tests |
| `fno/intraday/document.py` | `bdd0a17442540d0acb3a19a073594e3b237ccb8461bdad42e7d7d054c5d43e22` | a mark's document read by the session RV; A16's tests |
| `fno/intraday/ledger.py` | `7e5196ed75e2087866e9e484df8fa6cd32da614ca6ea8b2c3ee1053eda07cb1c` | A16's 14:30 mark read by the pack's overlap watch; A16's tests |
| `fno/intraday/row_files.py` | `6f6baedb573d5686392de4c35818453dccbb687728a5ff71e9784ab821261947` | the rv tables' row files (judge 596); A16's and A16b's tests |
| `fno/intraday/rv_table.py` | `3c9650ef094b6d6c9b05721ec7ff51e7f7e5ada8b815d162604d0ab4f51a17d8` | V1's outcome rows (A16's `rv/`); A16's tests |
| `fno/intraday/snapshot_files.py` | `d6c668265535871bd5d53e334533677393087e00e88c70a10c75efe8d7b6fff6` | the marks' snapshot files read by the session RV; A16's tests |
| `fno/quotes/expiry_listing.py` | `9d267759fb085976c5d5a39e172e9f8a67b54f51c294dbc9485fa24c6928d39a` | which expiries the capture lists; A4's baseline-bytes test (tests/quotes/test_recorder_baseline.py) and the pack's codec checks |
| `fno/quotes/market_levels.py` | `4db33740a033983f27ecdf3df5ade7acbfdc3e522136554678a37d417850d56c` | the captured spot and VIX levels; A4's baseline-bytes test (tests/quotes/test_recorder_baseline.py) and the pack's codec checks |
| `fno/quotes/monthly_contracts.py` | `4c966fd0e5f6562ee49dd798709bf4669dbb40793f602ed4cbd25e220cc702b4` | which monthly contracts are captured; A4's baseline-bytes test (tests/quotes/test_recorder_baseline.py) and the pack's codec checks |
| `fno/quotes/quote_validity.py` | `79279499f5b1e02e429a6dceadc8e69bfc475be8db00edecad96f8e517246af8` | W5's live two-sided quote for V4/V5 legs and the future; G7b's live-quote tests |
| `fno/quotes/recorder.py` | `cbb1acf19b9e755c9c8bcefe7c1c56c3951f8099bbceb862469282052a9341ef` | A4's capture behind the pack (judge 597.2 m3); A4's baseline-bytes test (tests/quotes/test_recorder_baseline.py) and the pack's codec checks |
| `fno/quotes/slot.py` | `2c71ead4066a6dc60446c0d10fb88cd4c0d953da07901fbcc74946c4ba50ade4` | the capture's time slot; A4's baseline-bytes test (tests/quotes/test_recorder_baseline.py) and the pack's codec checks |
| `fno/quotes/weekly.py` | `7de1efe8347c762b93d9ad2cff08ef818f4ead30af650118d6b10e74e6ccc2c1` | which weekly contracts are captured; A4's baseline-bytes test (tests/quotes/test_recorder_baseline.py) and the pack's codec checks |
| `fno/research_data/calendar.py` | `279ae45b5dd689f06332cb217a32b9a7b261ee2cd7c2ddedfe54cd60b6c288f6` | the session set; section 10; A7's and v4's session tests |
| `fno/research_data/expiries.py` | `b2cbed5d0ae98da0962aa77c4f88f0b9ca0073fa004075423a2f7e2c1af75bd4` | V4's and V5's listed expiries; G7b's terms tests |
| `fno/research_data/panel_reader.py` | `6860c74633fd8533d245d59a6754c98be76740b59e3f99965ec59433d86ef317` | the EOD chains behind the premium ratio window; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/research_data/panel_rows.py` | `0fb6718d5067b8ab40c73123d0a599c8feff4420e8c789b8e1e62a4cb2f1267b` | the EOD panel's row rules; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/research_data/panel_store.py` | `27ea3b0089f488ace4000d3721f0d9464b1eeb6465a55396a694128b75d418b0` | the EOD panel's file layout; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/research_data/quote_snapshots.py` | `a18e675dfaa2742787154144c232b08b9cb6443740de1791286a4e1d42df0bd6` | the pack's quote snapshot at the cutoff; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/research_data/release_times.py` | `72ee39e2d07fc338dc002e679c14836bd4df18f786b8dacfac9cc486ddabb3b1` | V5's `first_seen_at` fallback from A8's release log (protocol 1.5); A8 test |
| `fno/research_engine/close_series.py` | `4b3a06c66037e696f83ce37f5db5d4040f50fa12d9af73fd50cec9fc1479356e` | the IV30's close series; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/research_engine/event_features.py` | `d3fab68c2a26b2fa04583aeb19be5f39264840e157783cf47f19e0761d09f1e3` | imported by the live IV30 rule's module; its bytes are in every pack's `iv30_method` (v4_pack/wiring.IV30_METHOD_FILES); v2's golden cases |
| `fno/research_engine/features.py` | `95deda07b86be6e7855d621d49195bdb3f03cd0bbcfc167315fe0b6717f3efcb` | the feature interface the IV30 rule implements; its bytes are in every pack's `iv30_method` (v4_pack/wiring.IV30_METHOD_FILES); v2's golden cases |
| `fno/research_engine/implied_vol.py` | `a752d5acaa41649ef6e02dde0e2dec22349fa1d44ee24fee09a7f144eeef60f0` | Black-76; section 10; v1 and v2 golden values |
| `fno/research_engine/live_features.py` | `249826bfda9971fce35b9d3ba28f708eb11cd0dde70d7fe53e805c998f61f10d` | the pack's live ATM IV30 (V2's implied input); its bytes are in every pack's `iv30_method` (v4_pack/wiring.IV30_METHOD_FILES); v2's golden cases |
| `fno/research_engine/volatility_features.py` | `22f371f681e09b83338f625d5532ba5c3b73f6d62c7b9175346738e21ccfb23b` | the IV30's volatility parts; named in FREEZE.md, FREEZE_v2.md or FREEZE_v3.md (byte-checked there or recorded with v1-v3's golden values) |
| `fno/server_clock.py` | `84beda5986935a4be3251d1534227e389cbe5c2ecc512dc7aa585389aaec4ef5` | the checked host clock behind honest times (protocol 1.6); its clock tests |
| `fno/storage/creation_times.py` | `4ee75064f552b2610fa024ff30cb196dd4f685150eba4b84160b1118921aaa97` | V5's `first_seen_at` (Drive's creation time); G7b's outcome tests |
| `fno/storage/raw_library.py` | `1deba6e68a896e09e31e884b7bbc6043bb1d38b447733f2ad8bd772cbb749a9a` | the archived raw file V5's settlement reads; O9's tests |
| `fno/storage/raw_source.py` | `1128d99428c56b2175496bc269a4f5c9c973817a50240496e342f0a26fa19ec6` | V5's settlement file path; E7's and G7b's tests |

### AI registration (G11's shared files)

| File | SHA-256 | What it decides; its lock |
|---|---|---|
| `fno/ai/activity_log.py` | `8bf3bb43e35bd51193f4ec47877d3dbbe6c28a3f66f2f243ea5ff26a93a2c3e2` | GitHub's activity log behind push times (late = miss); the deadline and receipt tests |
| `fno/ai/answer.py` | `7a5ba303683d52f8645deaf025ee0bd126e049c8f43084a407b083e07cbab445` | an AI answer's form; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/audit_plan.py` | `05d8b83bc370ae000f04b9ad0b3fc7a41d6e19e4a31f2388ef7a50cc620a44ae` | the audit draw; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/budget_stop.py` | `32f541ebc5c68533a92e3836b6b3b7f633caa320b3018440311a87da09d6128d` | whether an AI book fires on BG1's level: v4_fire logs a stop as a `not_fired` miss; G11 C8's tests (tests/ai/test_v4_budget_stop.py); BG1-u changed how the level is read (judge 606.1) |
| `fno/ai/close_archive.py` | `59377609205f86c578705f60d4a61ccfe496f0339920f82c192b40112fa71d31` | the audit draw's closes; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/coverage.py` | `9cf7ca11a06bc65261a0571e9826fc1ce44cc65e9a1dbbc489a1b4675a128875` | the stop rule's coverage; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/draw_seed.py` | `44d5a2db1c0cbc3c280303fc35d65b7d4c5f6e63f80af3cabe921ce37174aeb3` | the audit draw's seed; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/envelope.py` | `95f8a5cc53a9a097216e7e01de2f0f303951411cbc33394245bda86037a82a43` | the sealed envelope; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/export.py` | `224f5a4de8db5d8499cb2b910dab1e5db24a8d1b339c3fb869b5a4bb4efb1c33` | the sealed export; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/history.py` | `46184fbc3b3cd241f89c673b5bc4a41e0c29515c8ffb19ca988caf2730fecde3` | which earlier AI records exist; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/outcome.py` | `3f8071271001f3540a736e8be3520ea31e114a2f79c0f347affc33f9ba43754e` | the AI books' outcomes; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/paths.py` | `cd2c53527a8317e06d968fe575803e04fc17bb8393ba0fef7b47d7dad5835f27` | the AI record paths; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/pointer.py` | `031aac8413fcb21e888433b412528c573e68066536b555331cc8c641e4497aca` | the pointer an AI book is given; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/receipts.py` | `c20af37ad942bcc5832a2d08796375d7fec3e5b84abfb5695cbb003a99e71094` | GitHub push times behind the 15:10 deadline (late = miss); the deadline tests |
| `fno/ai/record_writer.py` | `00d1cb052268d10a7ae557a6cfad3d8f8c674e7800a42a77ff20a21698e9ca7b` | writes the AI books' collected records; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/run_terms.py` | `456f7de63ec7d77a33940b872153528654c069e69369af74a062b7799e242d75` | the v4 AI run's commitment, reveal and fire terms (deadlines read from `terms`); the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/scoring_gate.py` | `b862c36ff38b396b4e10fd122fad27e0da539c7d361314450b37a36347754f49` | which AI days are scored; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/seal.py` | `4a11b2fabfac2565d0434a8ffed135fc2a831387b519f5afaaa24f58f082e746` | the seal; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/stop_rule.py` | `43ce0d97116b634da72230a999f9a5d168595e5f1c147d2a80b9da0682a465db` | the AI books' stop rule; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/submissions.py` | `7a839e35db56b765002763131f2de7e4e206e4b0ea676e4d03b9e7ff81f676ee` | which submissions count; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/transcript_audit.py` | `dde31ad334bbb0ea5e2c50fb26bf9fc0afa82b5d5d4c3006723e48059655923b` | the transcript audit; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |
| `fno/ai/versions.py` | `896668a538df560bbec3323eac0eaba14375360f96fc0b7d6787f025840deec9` | the AI forecaster versions and prompt hashes; the v1/v2 AI run's too; hashed with G11's slot rows (owner, 21 Oct 2026 (3); judge 597.1 m2); G11's tests |

## Reached by v4's code, deciding no v4 value (named, not hashed)

- `fno/accounting/ledgers.py`: settlement.py's desk half: `NseFinalSettlement` (V5) does not use it
- `fno/alerts/sender.py`: sends an alert line; decides nothing
- `fno/books/fills.py`: settlement.py's desk half: `NseFinalSettlement` (V5) does not use it
- `fno/budget/constants.py`: BG1's level names, read by the AI budget stop
- `fno/budget/report.py`: the `MonthMeter` shape the AI budget stop reads; the meter itself is injected
- `fno/budget/usage_ledger.py`: BG1's AI minutes, read for G11's cost line only
- `fno/composition.py`: composition root (reached through v4_pack/cli.py)
- `fno/config.py`: loads config.yaml; v4's settings are recorded with their values in the record
- `fno/constants_channels.py`: Slack channel IDs
- `fno/constants_operations.py`: the daily run's step names and order
- `fno/daily/wiring.py`: composition root: the `daily.live_from` dates (recorded in the record)
- `fno/desk/execution.py`: settlement.py's desk half: `NseFinalSettlement` (V5) does not use it
- `fno/desk/pricing.py`: settlement.py's desk half: `NseFinalSettlement` (V5) does not use it
- `fno/desk/records.py`: settlement.py's desk half: `NseFinalSettlement` (V5) does not use it
- `fno/forecast_lab/wiring.py`: the paths of A8's release-check log, read by G7b's pack wiring
- `fno/global_cues/collection.py`: the cue value shape (`SourcedValue`) beside the provenance label
- `fno/global_cues/reading.py`: M1's US flag on the card, outside its METHOD_FILES
- `fno/global_cues/wiring.py`: composition root of the global cues (the card's flag)
- `fno/health/evidence.py`: O8's evidence history: a reader of push times' shape
- `fno/health/model.py`: O8's plain record types
- `fno/http_pacing.py`: network pacing
- `fno/intraday/backfill_wiring.py`: composition root of A16b (the X tool's reader)
- `fno/intraday/candle_levels.py`: A16b's candle levels read by the X tool; X is frozen as a number in `terms`
- `fno/intraday/pacing.py`: request pacing
- `fno/intraday/wiring.py`: composition root of A16
- `fno/models.py`: the clock and plain value types
- `fno/pipeline/trigger.py`: fires a routine; decides nothing
- `fno/providers/base.py`: the provider interface: quotes as received, checked by the pack's codec (byte-checked)
- `fno/quotes/book_fetch.py`: fetches quotes as received; the pack's codec checks every value and time
- `fno/quotes/capture_extras.py`: records quotes as received; the pack's codec checks every value and time
- `fno/quotes/capture_log.py`: the capture's log lines
- `fno/quotes/future_quotes.py`: fetches the future's quote as received; the pack's codec checks it
- `fno/quotes/snapshot_rows.py`: the quote file's row layout; the pack's codec checks every value and time
- `fno/quotes/window.py`: the capture window; the cutoff itself is enforced by `terms` in v4_pack/codec.py
- `fno/rehearsal/live_wiring.py`: REH1c's rehearsed live dates; a real run gets `daily.live_from` unchanged
- `fno/rehearsal/receipts_wiring.py`: REH1's rehearsal wiring; never on a counted day
- `fno/rehearsal/v4_pack.py`: REH1's rehearsal excuses; never on a counted day
- `fno/research_data/availability.py`: A8's availability rule; V5's fallback uses only `first_seen_times`
- `fno/research_data/events.py`: the desk's event feature; the IV30 rule does not read it
- `fno/research_engine/ledger.py`: git questions (this check's own reader)
- `fno/research_engine/statistics.py`: percentiles for G11's cost line only
- `fno/storage/data_store.py`: the write-once Drive store: moves bytes, checks their receipts
- `fno/storage/data_wiring.py`: composition root
- `fno/storage/drive_cache.py`: the verified Drive cache: moves bytes, checks their SHA-256
- `fno/storage/google_drive.py`: the Drive client
- `fno/storage/quote_wiring.py`: composition root
- `fno/storage/raw_store.py`: the raw file store interface
- `fno/storage/receipts.py`: the receipt files' format
- `fno/storage/retry_policy.py`: network retries
- `fno/storage/row_log.py`: where a cue table's rows are stored (repository or Drive); moves rows only
- `fno/storage/wiring.py`: composition root
- `fno/weather/drivers.py`: the card's drivers, outside M1's METHOD_FILES
- `fno/weather/model.py`: M1's plain record types
- `fno/weather/records.py`: M1's record writer: writes what its METHOD_FILES computed

## Platform

Python 3.13.17, numpy 2.5.3, C library glibc-2.39, x86_64

## Disclosure (protocol section 8), as of commit `5e99d57824e17fdfb4e3c59054f03f8d10fd3561`

### Exploratory back-fills in the repository (`backfill_exploratory`, never counted)

| Source | First day | Last day | Rows | Method SHA-256 (first 12) | Rows' SHA-256 |
|---|---|---|---|---|---|
| `research/forecasts/v4/base_rate/v6_abs_move_2pct_next_session.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `d1be59545d69aa8e6fddb4ca81d1d66ef34f54a04945c75aa13d12df118f4b9e` |
| `research/forecasts/v4/base_rate/v6_abs_move_2pct_within_5_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `be1a3e1fff3b3f6dfa7188d4dde0f17d6a7bccb63eb2bb322e288ebbc29d3696` |
| `research/forecasts/v4/base_rate/v7_vix_higher_in_5_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `948e3941cc1c59de5608b1dc4b0bcb4c540e0c165feeac96091d54b2040cfc62` |
| `research/forecasts/v4/ewma_094/v2_rv_next_5_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `02e90bd079c161f80918d428aabee4d20e77c743ea0d535280fd2e09e8c3e9c9` |
| `research/forecasts/v4/ewma_094/v3_rv_next_20_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `b54ce080e793e20f2dba604693f7f64b8d69bea2eb432cc130a8421c7e7c4ae0` |
| `research/forecasts/v4/har_daily/v2_rv_next_5_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `ac353ea13cac8471e393d7776f20fcd30ca0452812ec53affdaa81c87010f5a1` |
| `research/forecasts/v4/har_daily/v3_rv_next_20_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `0c76a0d30ef364e6b686bdaf59b526bde32dfdcd784a8735c26585816b1b5d81` |
| `research/forecasts/v4/trailing/v2_rv_next_5_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `6b8da85c8ccdf1e6b01a41646fb8a2d8638cbf1f6864c91b9cd42c595e9e37a7` |
| `research/forecasts/v4/trailing/v3_rv_next_20_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `cc04768bdeb093d42aca1e715e13a00063a0e4b4129558b20f4a7f3d08de26a5` |
| `research/forecasts/v4/v2_close_blend/v2_rv_next_5_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `8653b76b76f661d65ab350dbd911088b973a7fb8cde9526f7e911dddd9babe3b` |
| `research/forecasts/v4/v3_close_blend/v3_rv_next_20_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `a2ff63e90df7345fd9aee4fac2fc74d8a7ae1d89af61479c2fa06dbd84a5b1b6` |
| `research/forecasts/v4/v6_ewma_t4/v6_abs_move_2pct_next_session.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `82987080dc42dcc45f674f0af0f507d144bfebfc0e3c3850a1d4012f9da8b95a` |
| `research/forecasts/v4/v6_ewma_t4/v6_abs_move_2pct_within_5_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `4756cf6738469d7ccb326ed295b057a5b7df9180e6b3aca3c7e2a98cd1a09ce3` |
| `research/forecasts/v4/v7_vix_vs_mean20/v7_vix_higher_in_5_sessions.csv` | 2017-01-03 | 2026-10-15 | 2410 | `21f62594f26f` | `4aecc29496901ef33007c0b711e8a022042f13e8716762520ad240ed5b34aa46` |
| `research/forecasts/v4/weather_checklist_v0/v6_abs_move_2pct_next_session.csv` | 2017-01-03 | 2026-10-19 | 2412 | `a49c62612a46` | `adfbee43695d206efc38735042277f5aad0f1876fd6b7047284e5ca33075b953` |
| `research/forecasts/v4/weather_checklist_v0/v6_abs_move_2pct_within_5_sessions.csv` | 2017-01-03 | 2026-10-19 | 2412 | `a49c62612a46` | `5660d32d75354312befbe715b922034173283e84cf05592f38f351e6d9a43fdb` |
| `research/forecasts/v4/weather_vix_v1/v6_abs_move_2pct_next_session.csv` | 2017-01-03 | 2026-10-19 | 2412 | `a49c62612a46` | `85305db0dbcf7a5b38fe5dc7eb09860dfa4552a208ac0de08570d85fab6220ca` |
| `research/forecasts/v4/weather_vix_v1/v6_abs_move_2pct_within_5_sessions.csv` | 2017-01-03 | 2026-10-19 | 2412 | `a49c62612a46` | `55878002374c02f0f1ee0de1331fcdf0319ef0161be9be5cc2bd784af3abe661` |
| `research/forecasts/v4/weather/*/*.json` | 2017-01-03 | 2026-10-19 | 2412 | `a49c62612a46` | `ff3b5a1a9f133346a67660ac4d1f930dc6af19a908eea721bc996b993cee01db` |

### Live rows made on or before 2026-10-25 (before the freeze, never counted)

| Source | First day | Last day | Rows | Method SHA-256 (first 12) | Rows' SHA-256 |
|---|---|---|---|---|---|
| `research/forecasts/v4/base_rate/v6_abs_move_2pct_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `836997e3fcb87c6b8c7d46eb2289113550ed141867948ad35cd1e2197bc1939c` |
| `research/forecasts/v4/base_rate/v6_abs_move_2pct_within_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `2e34c491c26b16dbd9318889d63f66aab63bccb8369dad196202a6bd30173087` |
| `research/forecasts/v4/base_rate/v7_vix_higher_in_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `0e713a33403afc86508a337fa1b33feb7ac02d6c9d3a83f46760039dd08cb4fc` |
| `research/forecasts/v4/ewma_094/v1_rv_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `fca5a33fd98e30b91e0f98f9bef62e43f700ee7fa8d61cc3a229a174a41ecc8a` |
| `research/forecasts/v4/ewma_094/v2_rv_next_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `8814a0529aa63587b32df49b28307ca1432373c5dcb40244bbae33615023d8de` |
| `research/forecasts/v4/ewma_094/v3_rv_next_20_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `fb66d7eb8af25d369639be4f5bdd703ae65d161441b9cb645d501e2f2f8334c8` |
| `research/forecasts/v4/har_daily/v1_rv_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `fca5a33fd98e30b91e0f98f9bef62e43f700ee7fa8d61cc3a229a174a41ecc8a` |
| `research/forecasts/v4/har_daily/v2_rv_next_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `175392a5634438a9362d61cb36b89496a054420e2e707fcb6a1e15d998f6f6e6` |
| `research/forecasts/v4/har_daily/v3_rv_next_20_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `e4c12e31b1c7490d412f7f167402a3d3f6c34828d229f8bbf713dc06cfd6d9b9` |
| `research/forecasts/v4/har_intraday/v1_rv_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `fca5a33fd98e30b91e0f98f9bef62e43f700ee7fa8d61cc3a229a174a41ecc8a` |
| `research/forecasts/v4/trailing/v1_rv_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `fca5a33fd98e30b91e0f98f9bef62e43f700ee7fa8d61cc3a229a174a41ecc8a` |
| `research/forecasts/v4/trailing/v2_rv_next_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `a3047adb568ef23cd669702431388091091b38ef19604d66a28815e8571144ae` |
| `research/forecasts/v4/trailing/v3_rv_next_20_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `4fdcc5afd3c3a85a0376eecbaee471cad88fcfcbdabf493a9ef3215a33d2338c` |
| `research/forecasts/v4/v1_close_blend/v1_rv_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `22f419dd39842b78e5a58405cd6399c2afd910ca26109ff660bcc70f077e22df` |
| `research/forecasts/v4/v2_close_blend/v2_rv_next_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `dda40f4e93519ea445044f6c4ec3187432e81cdf36bd193144d6f0f7f0eeccd6` |
| `research/forecasts/v4/v3_close_blend/v3_rv_next_20_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `d0e1efd0f0cf06a2d25c0152821832b94ccc285ddc1bf38808fd21d1898370f1` |
| `research/forecasts/v4/v6_ewma_t4/v6_abs_move_2pct_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `b6d1a2de4ac8c8b80b07efa55074c5b2ad91703ec0e5ad252c578bce334bd762` |
| `research/forecasts/v4/v6_ewma_t4/v6_abs_move_2pct_within_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `441c231bf7f4bb2d778c097e9d2f3475a3753025eaf8d54e73ea98cca351d813` |
| `research/forecasts/v4/v7_vix_vs_mean20/v7_vix_higher_in_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `21f62594f26f` | `900883e612095f6c5d07f2664a0b1283ac431b27bedc26f80881d7f1af785a90` |
| `research/forecasts/v4/weather_checklist_v0/v6_abs_move_2pct_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `a49c62612a46` | `692cffc858fc4c32e7db71a955fdce7e49d5c4fc8550c2337da36e99399f3bd0` |
| `research/forecasts/v4/weather_checklist_v0/v6_abs_move_2pct_within_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `a49c62612a46` | `6c25371546c752752399f5cceb42e18d5fc5781ab8456ebf5c9f936a029c594b` |
| `research/forecasts/v4/weather_vix_v1/v6_abs_move_2pct_next_session.csv` | 2026-10-22 | 2026-10-23 | 2 | `a49c62612a46` | `6b2df14c199b99dbef8b8492f38bb5d2b79e1ac5bf87d2ca8593190ff51a3650` |
| `research/forecasts/v4/weather_vix_v1/v6_abs_move_2pct_within_5_sessions.csv` | 2026-10-22 | 2026-10-23 | 2 | `a49c62612a46` | `5ba43707f4596cde15441f029bcbce36d1c3e0bacd9bd895c0da7b0d63d4bcdb` |
| `research/forecasts/v4/weather/*/*.json` | 2026-10-22 | 2026-10-23 | 2 | `a49c62612a46` | `d5708b76b56878f54e3adfc50548923ecf688821513fe54b8e63c06aa12070ce` |

### G8's reports dated on or before 2026-10-25 (exploratory)

- `research/forecasts/v4_scores/2026-10-10.json`
- `research/forecasts/v4_scores/2026-10-10.md`
- `research/forecasts/v4_scores/2026-10-17.json`
- `research/forecasts/v4_scores/2026-10-17.md`
- `research/forecasts/v4_scores/2026-10-24.json`
- `research/forecasts/v4_scores/2026-10-24.md`

### Exploratory back-fills in Drive (by receipt; never counted)

| Receipt | File SHA-256 |
|---|---|
| `receipts/data/v4/records/backfill/cc8196ac2a7f/premium_adjusted_implied/v2_rv_next_5_sessions_to_2026-10-23.csv.sha256` | `5b3f74eaec01823cecb97ec75836bd4026552a3c840701094d150199cedf9ac9` |
| `receipts/data/v4/records/backfill/cc8196ac2a7f/premium_adjusted_implied/v3_rv_next_20_sessions_to_2026-10-23.csv.sha256` | `307776467cff384336865add370c1be4ff5d54063c384dda553c1d3720f5e784` |
| `receipts/data/v4/records/backfill/cc8196ac2a7f/raw_implied/v2_rv_next_5_sessions_to_2026-10-23.csv.sha256` | `25c23374e10adf4accfeef0b9d2e4ce5620d133012621e26dd03e7aac5bd3317` |
| `receipts/data/v4/records/backfill/cc8196ac2a7f/raw_implied/v3_rv_next_20_sessions_to_2026-10-23.csv.sha256` | `0554127dd7d66a530cb89a2dad62d350eded4f9ce082ce2a35350cc53b259862` |

### Live rows in Drive made on or before 2026-10-25 (by receipt; before the freeze, never counted)

- none
