# Judge 221: four screens heads (16 Oct): the 2.8.0 integration, mockup 46, P2a part 2, W3d

All four verdicts are **PASS**. The dashboard heads were checked in a read-only clone of exepex/omenix-dashboard;
P2a part 2 in a trading worktree.

## 1. The 2.8.0 integration: story/fno-2-8-merge at c70d1a9 (only the edits made at the merge)

**PASS.**

- **Gates:** `npm test` gives **493 passed, 0 failed, 0 skipped**; `check_contract` and `check_fno_screens` exit 0;
  `check_code_size` is clean.
- **The regenerated fixture:** I re-ran `node tools/sync-design.mjs` on c70d1a9 and the working tree stayed clean, so
  `fno-screens.generated.json` is exactly the 2.8.0 examples. The merge's other edits (three lines of `.mb-howto` in
  each mockup's `page.html`) are the design system's own rule, rebuilt in. Nothing else differs from git's automatic
  merge of 7ea7194 and f04cb50.
- **`pages.test.ts`:** the four 2.8.0 operations join `notRead`, with the reason that they are W3a part 2 onward. The
  test's strictness is unchanged: any other unread F&O block still fails.
- **8d31be1 (the weather's 2.8.0 labels):**
  - `recent[].label` gives a "rebuilt" mark, plus a how-to sentence;
  - `red_share.basis` gives "rebuilt from history (exploratory)" in the share's words;
  - `scores[].exploratory` gives "Exploratory: scored on days rebuilt from history, not a confirmed result";
  - a new test pins all three both ways.
- **The `startsWith` question: a small weakening, not a should-fix.** The old exact assertion
  ("No session counted yet.") had to change because 2.8.0's empty example now carries a back-fill share. The new
  check pins the part that matters, "RED on 13 of the last 250 sessions rebuilt from history (exploratory) (5.2%)",
  but no longer the tail (the 15% limit and "RED still blocks until you approve it"). An exact assertion of the full
  sentence would restore the old strength; it is a one-line change.
- **c70d1a9 (my judge 220 note):** the how-to now reads "…over many days, and by enough to matter, not one lucky
  month". Done.

## 2. Mockup 46, weather history: story/fno-weather-history-mockup at d6429b4

**PASS.** It is built on the catalog's `FnoWeatherHistory` examples (`check_fno_screens` exits 0 with the new
`MOCKUPS` line).

- **Colour and label only:** nothing in its `data.json` or scripts names a chance, a base rate, a level, `reaches` or
  a threshold. The lede says today's chances stay on the weather page.
- **Honest labels:** every state is Mock; rebuilt tiles and counts say so; the notes say plainly that rebuilt is not
  live and that "was it right" lives on page 40.
- **Mockup 40's edits:** only the link to 46 and the two 2.8.0 wordings, matching the screen's.

## 3. P2a part 2: trading story/p2a-weather-2-8 at 63bb7c9c

**PASS.**

- **The re-pin:** every `api/` file in `contracts/omenix-dashboard/` is byte-identical to the dashboard's c70d1a9.
  I compared the SHA-256 of every file; none differed. `contract_version` is 2.8.0. The one-line follow-up (`pin.json`
  `commit` set to the dashboard's main merge SHA) is expected and is the orchestrator's to show.
- **`weather`:**
  - each recent day carries its record's label;
  - the red share counts the live records once any exists, else the back-fill, and says which in `basis`;
  - on real data it is 13 of 250 back-fill records (5.2%), not over-alarming;
  - scores are still G8's alone (not_enough_data, null) with `exploratory` true;
  - today's colour is still only a live record's.
- **`weather_history`:** every M1 record up to the day as `{session, colour, label}`, nothing else. On real data:
  2,409 rows (2017-01-03 to 2026-10-14), GREEN 1,634, AMBER 149, RED 121, not scored 505, live 0, back-fill 2,409.
  These are exactly judge 216's recount, and a test re-counts them from the folder.
- **Gates on a trial merge with origin/main:** `-n auto` gives 6836 passed and 4 failed. The 4 are again only
  `test_routine_gate.py`'s shard count, caused by my trial merge leaving `reviews/claude/README.md` unmerged (the
  branch's response 227 row against main's newer rows). **At the merge:** keep both rows, then run the full suite.
  `ruff check` and `check_imports` are clean.

## 4. W3d, the Strategy lab's F&O tab: story/w3d-strategy-lab-fno at e796467

**PASS.** `npm test` gives **500 passed, 0 failed**.

- **No strategy rules:** `FnoStrategyLab` never sends entry or exit rules, filters, thresholds, parameters or a
  card's structure details (its `x-never-sent`). The view shows only the trial number, plain title, the question it
  rests on, the last gate reached (G0-G6), the status and the evidence label.
- **Books never added:** `resultsOf` gives one row per strategy with its book. There is no total anywhere in the
  view or components. The owner's "both books together: total only" line is honestly left out as a separate story
  with the stock lab's owner (B16).
- **Real money always "Not eligible":** the type is `real_money: { eligible: false; … }` (the contract allows only
  false), and the results component prints "Not eligible", then each check as met, not met or not checked yet.
- **The stock lab's client code is untouched:** only its server `page.tsx` gains the tab bar. `LabTabs` returns null
  outside India, so the US stock page shows no tab, only an empty scoped `div`.
- **CSS moved into `fno-common`:** the verdict band, chips and `.marks` (renamed from `.verdicts`) move out of the
  weather and Forecast lab CSS. Every rule is scoped by `:where(.fno-screen)`, so importing it into the stock page
  cannot restyle the stock lab.
- **`/us/strategy-lab/fno`:** India-only route, the same `notFound` pattern as W3a and W3b.
- **The conflict with (1):** the shared CSS may conflict when the second of the two merges. Re-check that resolution
  then.
