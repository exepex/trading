# Judge 597: v4 freeze story text (story/v4-freeze @ 2f48524dc, `docs/stories/G6-v4-freeze.md`), judge B, round 1 of 2

**FAIL (3 should-fix, 1 minor). Lane 1** (frozen files, forecast and score records). Judged by reading the story
against PROTOCOL_v4 sections 10, 5 item 6, 4, 8 and 11 and the owner's rows (DESK_DECISIONS 22 and 24 Oct). Doc-reading
tests: 853 passed, 15 xfailed (token kept); record scan clean.

## Criteria (the orchestrator's points and the protocol's requirements)

| Point | Result | My evidence |
|---|---|---|
| Blocker order (G7b, G11, rate, W1-W8, protocol commit, freeze commit) | MET | section 10 "frozen only once that code exists" plus the owner's 24 Oct row ("lands once G7b's live V2 baseline code is on main"); G11 first because `slot_file.py:66-69` refuses an `effective_start` after the first eligible session (read); no early freeze offered |
| The rate leak and its fix | PARTLY | `fno/v4_pack/wiring.py:54` reads `cfg["risk_free_rate"]` (confirmed); the fix's place and coverage: SF1, SF2 |
| Byte-check list | PARTLY | `fno/v4_pack/*`, `live_features.py`, `iv30.py` and G11's files all exist (G11 on `story/g11-ai-books-v4` 66db618e5); shared files: SF3 |
| Slots all effective 26 Oct; AI misses until `ai_books_v4` is live | MET | allowed by `slot_file.py` (after the freeze, not after the first eligible session, `registered_on` 25 Oct ≤ start) and protocol 4 ("from the declared start", owner 16 Oct); the consequence is stated plainly (section 5); see note 1 |
| `v4_freeze_date` and BG1's review date | MET | my run of `review_date`: freeze 2026-10-25 gives 2027-04-30; projected Nov 2026 gives 2027-05-31; both with the 2027 weekday-fallback note, as stated |
| ChatGPT's review paused | MET | owner, 22 Oct ("Cut-list accepted"; JUDGE.md rule 9); the protocol commit rewrites section 10's precondition, and the record states it |
| Section 10 contents, section 8 disclosure, gap list | MET | record items 1-12 cover the protocol hash, file list, recorded files, ledger, go-live (`Frozen on:` read by `records.py:20`), disclosure per source with hashes printed by the tool |
| Owner's sign-off | MET | DESK_DECISIONS 24 Oct, "The owner signs off protocol v4" (row 341, read) |

## Findings

1. **Should-fix SF1: the rate constant in `fno/forecast_v4/terms.py` moves M1's method hash.** `terms.py` is in M1's
   `METHOD_FILES` (`fno/weather/wiring.py:30`), and `tests/weather/test_method_hash_gate.py` requires every weather
   back-fill row (more than 2,400 day files plus the `weather_vix_v1` and `weather_checklist_v0` CSVs) to carry the
   tree's hash. A new constant in that file would make the freeze regenerate all of M1's back-fill. The story never
   says so; its gap list calls regeneration "out". G10 met exactly this and moved `V4_RELEASE_BY` out of `terms.py`
   (judge 584, change 1). Fix: put the rate in a new module under `fno/forecast_v4/` (frozen by the glob, outside
   M1's list) and name it in 1.4. Otherwise, state the regeneration, its size and its disclosure.
2. **Should-fix SF2: the rate leak list is incomplete.** `fno/forecast/wiring.py:17` `build_atm_iv30(cfg)` builds
   `PanelAtmIv30(Black76(), cfg["risk_free_rate"])`. `fno/forecast_v4_rules/wiring.py` (`build_implied_backfill`)
   uses it for the EOD IV30 proxy behind G7b's V2 premium-adjusted back-fill (and its proxy drift, once built).
   G7b's `OptionTermsRule(model, rate, calendar)` takes the rate injected, and its wiring is not built yet. Fix:
   criterion 3 names every v4 reader (the pack, the EOD proxy, V4/V5's terms) and adds a test that no v4 composition
   reads `risk_free_rate` from config.
3. **Should-fix SF3: shared files on the byte-check list break the story's own rule.** Section 2 records shared files
   "changed by other stories" without byte-checking them. Yet it byte-checks G11's `fno/ai/versions.py`, `fire.py`,
   `outcome.py`, `scoring_gate.py` and `stop_rule.py`, which also serve the v1/v2 AI run. v5 (owner, 24 Oct: "v5 in
   full" next) will add prompt versions to `versions.py`. `fno/v4_pack/*` has a known pending change: REH1c's live
   date in rehearsals (judge 594 note), and v4-pack's children read `live_dates(cfg)` directly. Freezing these files
   makes each ordinary change either a broken freeze or a copied file. Fix: rule per file. Byte-check the files whose
   bytes decide a v4 value. Record the shared ones and lock v4's behaviour with tests, as the four recorded files are,
   or land known changes before the freeze. State the consequence per file. Do not hand the decision on with "G11's
   builder confirms the list".
4. **Minor m1:** protocol 5 item 6 says each slot holds "the first forecaster version registered in the ledger", but
   the story registers ledger rows per question (section 6), and the forecaster per slot is in `v4_slots.csv`. The
   protocol commit should name `v4_slots.csv` as the slot registry, so the text and the records agree.

## Plants

None (a text round).

## Notes

1. For the orchestrator to put to the owner before the freeze: unless `daily.live_from.ai_books_v4` is 26 Oct, every
   session until then is a `not_fired` miss for 10 AI members. While fewer than 10 2% days exist, one missed 2% day
   makes a member "undecided, operations" at look 1 (protocol 4). This is a decision, not only a consequence.
2. Accepted as written: V7's `rules` row registered (it can never be registered later; Test A unchanged), the ledger
   ids 100-107, `Frozen on:` moving forward only, and "Asked of the orchestrator" (the keep-or-change list).
