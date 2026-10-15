# Stories P2 and W3: the F&O screens with real data (pages in the daily publish, screens on the dashboard)

**Repository:** trading (P2) and exepex/omenix-dashboard (contract, mockups, W3 screens) · **Lane:** 1 (what a screen
reads or renders, outside services, `api/`, `.ts`); dashboard `design/` mockups lane 2 · **Size:** L, split by screen ·
**Owner decision:** 16 Oct 2026 (`docs/DESK_DECISIONS.md`, "F&O screens start now, all of them, with real data through
the existing Azure path"; reverses "F&O screens wait for slice C"), and "the weather screen never shows input
thresholds" (16 Oct). **Replaces:** P2's old text (`P-publishing.md`, a separate builder writing `reports/dashboard/`);
P3's remaining scope is covered by the existing publisher (REPLAN: "No new publisher").

**Description:** As the owner, I want every F&O screen (card, weather, Forecast lab, Strategy lab, paper books and
trades, scoreboards A and B, budget and AI usage, data health) on my dashboard with the real numbers, so that I see what
the desk did and how its forecasts and books stand, while nothing private ever reaches a public repository or log and
no strategy's internals are ever shown.

**Builders (orchestrator, 16 Oct):** contracts and mockups: this builder (01XFXpbkyixX7SuXeQCp5EnX, dashboard `api/`
and `design/`); trading's page builders (P2): the BR1 builder (013xqaNTCbSBytKgqpfaYFqZ); the screens (W3): the
E4c/E4d builder (0134MoC6f7aAJVcHRBiyATo6, dashboard `web/`). One builder per function; nothing below is built twice.

## What exists (checked 16 Oct; strong evidence unless marked)

- **The publish path works:** `market-publish.yml` (07:10 IST, previous session) builds every page through
  `fno/market_read_models/` (`BlockBuilder`s in `build_market_blocks()`), validates each against the pinned contract,
  writes them in one transaction to Azure Postgres (`fno.pages_history`, pointer `fno.current_publication`, writer
  role append-only) and reads the hashes back. About 1,245 pages a day, most of them per-contract chain histories.
  The log prints counts and hashes, never payloads.
- **The dashboard reads it:** `web/lib/fno/` (`PublicationReader`, `AzureFnoRowStore`, TLS verify-full, role
  `dashboard_app` with SELECT only); the four `OMENIX_FNO_PG_*` settings are on the Vercel `omenix-dashboard` project
  (owner, 16 Oct). The dashboard is behind Vercel Authentication; the public gateway serves no F&O data.
- **P1's five screen operations** exist in the contract (2.7.0) but no handler serves them, and none of their page keys
  is in `web/lib/fno/pages.ts`. Mockups on the catalog: 39 (card), 40 (weather). Older drafts: 37 (Forecast lab), 38
  (Strategy lab, its F&O half). None for paper books, scoreboards, budget or data health. No contract schema for
  scoreboards, budget or data health.
- **Real data per screen:**

| Screen | Source in trading (public unless marked) | Real records today | Refreshed |
|---|---|---|---|
| Weather | `research/forecasts/v4/weather/<YYYY>/<day>.json` (M1) | 2,409 days, 2017-01-03 to 2026-10-14, all `backfill_exploratory`; GREEN 1,634, AMBER 149, RED 121, not scored 505; **0 live** (M1's live job is not built) | back-fill once; live daily when M1 runs |
| Trade card | `research/cards/deliveries/` (T1); the full card (strikes, entry ranges) **in Drive only** | 1 delivery (a test, NO TRADE) | each session ~15:08 |
| Forecast lab | `research/forecasts/live_v2/`, `scores/` (G4), `v4_scores/` (G8, exploratory until the v4 freeze), `ai_v1/` (G5) | v2: 2 live days; G4 summaries for 3 days; one exploratory v4 report; AI books 2 days (no on-time day) | 22:41 IST (G4); weekly (G8) |
| Strategy lab | `research/ledger.csv`, `research/2026-10-*/results*.json`, `playbook/registry.csv` | 54 trials; 0 passing policies; registry empty | on each trial |
| Paper books and trades | public `journal/<book>/daily_totals.csv`; **Drive only**: `journal/<book>/account/` (ledger, positions, equity, fills; E2c) | 3 books, 2 rows each, 0 open trades | after each daily run |
| Scoreboards A and B | `research/scoreboards/{A,B}/<date>.json`, **Drive only**, no workflow runs them yet | none | when S2/S3 run |
| Budget and AI usage | `accounting/ai_usage.csv`, `operating_costs.csv`, `accounting/budget/<month>_signal.json` (BG1) | 1 usage row; 1 cost row; no signal file | per routine run |
| Data health | `research/data/manifests/` (CSVs), `vix/checks/`, `global-cues/checks/`, `fno.run_status` (P7), O8's `research/ops/health_runs.csv` | 33 manifest CSVs, 57,178 lines (`find research/data/manifests -name '*.csv' -exec cat {} + \| wc -l`); the 19 top-level files hold 17,910 data rows (lines minus one header each); check files; O8 runs not committed yet | daily |

## Privacy rules for every page (no shortcuts)

1. **Where private fields may go:** only Azure Postgres (read by the owner's signed-in dashboard through
   `dashboard_app`). Never a committed file, an example with real values, a public Actions log, Slack or the gateway.
2. **Private inputs stay in memory:** pages that need Drive-only inputs (accounts, full cards, scoreboards) read them in
   the run through E2c's `PrivateFiles` and write nothing from them to the runner's tree or the log. If Drive cannot be
   read, the page is **not built** (it stays at the previous publication, the run status says why); never a fallback
   value. Today's publish already does this for Home's books: `fno market publish` first runs E2c's
   `download_private_records()`, which stops the command, named, when Drive cannot be read (`fno/market_read_models/
   cli.py`, `fno/desk/wiring.py`). That stop is the whole run's: every page, public ones included, stays at its
   previous publication until the next run (judge 216).
3. **Logs:** counts and hashes only, as today. A validation failure prints the field path and the rule, never the
   value: today `ContractBroken` prints jsonschema's `e.message` (`fno/market_read_models/contract.py:71`), which
   quotes the failing value (for example "25000 is greater than the maximum of 10000"), into the public Actions log.
   P2 changes that line for every page before the first private F&O page is published.
4. **Never sent at all (strategy internals and owner rules):** a strategy's rules, thresholds, filters, parameters or
   prompts (P1's `x-never-sent`); AI model names and session ids (`DESK_DECISIONS.md`: no screen names an AI model);
   the US cue (`us_move`, Drive only). **The weather's input levels are a screen rule, not a secret** (judge 216, strong
   evidence): the trading repository is public, the levels sit in its code (`fno/weather/checklist_v0.py:22`
   `RED_LIMITS`, `fno/weather/constants.py:23`) and every one of the 2,409 committed weather records carries each
   input's value beside its `reaches` colour. So the screen never shows the levels or `reaches` (owner, 16 Oct: the
   colour, the input values and the reason only), and the pages do not carry them, but this protects nothing that is
   not already public. **Owner question:** (a) accept the weather levels as public (they already are), or (b) make
   them private from now on (code levels and future records' `reaches` moved to Drive; git history keeps every past
   value public). Recommendation (a), reasoning only: (b) costs an M1 change and hides only future values of a rule
   whose past values stay public.
5. **Owner-only fields** (`x-visibility: owner`, P1) are published to Azure and shown only on the signed-in dashboard;
   the gateway never imports the F&O screen code: an import-graph test over everything the gateway serves
   (`web/middleware.ts`; under `MB_GATEWAY=1`, `web/lib/tools/gateway.ts` lets through only `app/slack` (POST),
   `app/mcp` and its OAuth rewrites to `/mcp/oauth/*`, `app/brief/<market>/<date>-<hex>`, the legal pages and the
   site-verification file, and `/` rewritten to `/about`) fails if any of them reaches `lib/fno-*` or an F&O screen
   page, proven with a planted import.
6. **Paper** on every money figure; **Example** labels on states real data does not have yet; empty and
   not-published states are shown honestly, never as zero.

## Part 1: P2, the F&O pages in the daily publish (trading, BR1 builder)

**Expected design:** one `BlockBuilder` per screen in `fno/market_read_models/` (the existing pattern: a `SessionRows`
field filled by `SessionRowsBuilder`, the builder appended to `build_market_blocks()`), validated against the pinned
contract like every page; page keys as the contract names them (`weather`, `card`, `forecast_lab`, `strategy_lab`,
`paper_trades`, and the new `scoreboards`, `budget`, `data_health`), none colliding with `risk`, `today`, `session`,
`indices`, `flows`. A page whose source has no record yet publishes its empty state; a page whose private input cannot
be read is not built (rule 2). No new publisher, job or schedule: the pages ride the 07:10 run.

**Known limit (reasoning only):** one 07:10 run means the screens show the previous session (the card and today's
weather appear the next morning). A second publish after the daily run is a later decision for the owner, not built
here.

**Acceptance criteria (each page):**
1. The page is built from the real source in the table, validates against the pinned contract and is read back by
   hash; a fixture test re-reads the source and compares every number.
2. No value from a Drive-only input reaches a committed file or the log (a test runs the build with a planted Drive
   value and scans the tree and the captured log); a Drive failure leaves the page at its previous publication.
3. A validation failure prints the path and rule only (a test with a bad value).
4. The never-sent list holds (a test over the payload's keys and the weather's text fields: no threshold, no
   `reaches`, no model name).

## Part 2: the dashboard (contract and mockups by this builder; screens by the E4c/E4d builder)

**Contract (lane 1, `api/`):** add `FnoScoreboards` (scoreboard A and B as separate objects, never one number, each
per book, `status` not_run / ok), `FnoBudget` (minutes used against BG1's cap and its level ok / alert / stop / unknown,
by role group, never a model or session; the plan's monthly cost, labelled) and `FnoDataHealth` (per source: last day,
rows, gaps, check result; the last publish run's status from `fno.run_status`; O8's last result), each with Mock
examples in the positive, negative and empty cases and its field table, as P1; and `FnoWeatherHistory` (page
`weather_history`, agreed with the P2 builder, 16 Oct): one row per session (day, operative colour, label, the two
probabilities and their base rates) plus counts by colour and label, one page (about 2,400 rows; paged only if it
proves slow). Today's weather stays P1's page `weather`, with no field change (it already has no threshold); its
`drivers[].text` is stated as values only; no per-input `reaches`, no method page with levels. All in a new contract
version 2.8.0 (additions only). Trading re-pins in the same story (its pin bump is the
P2 builder's).

**Mockups (lane 2, `design/`):** paper books and trades, scoreboards, budget and AI usage, data health, each per the
dashboard's rules (data.json from the catalog's examples, template, deterministic build, notes, rationale, shots at
1280 and 390, every case shown); 37 rebuilt on the catalog; 38's F&O tab on the catalog. 39 and 40 stand.

**Screens (W3, lane 1, `web/`):** the E4c/E4d builder's pattern per screen (`lib/fno-<screen>/`: contract types,
one source interface, the Azure adapter through `lib/fno`'s reader, the fixture adapter only without a database, one
wiring, a pure view mapping); each page key added to `web/lib/fno/pages.ts` with its contract test; every screen
renders published, not published, empty and Example states; India only (absent, not empty, in the US).

**Answers to the screens builder's questions (16 Oct; route and nav choices are reasoning only, the owner may move
them):**
- (a) Existing nav groups, no new "F&O" group: weather in Markets ("Market weather"); card in Strategies ("Today's
  card"); Forecast lab = the existing "Forecasts" item; Strategy lab = the existing page with an F&O tab (stocks and
  F&O never combined, except the owner's one total line); paper books in Portfolio as its own page
  `/india/paper-books` (each book its own account, shadow tests apart, never summed with the stock portfolios);
  scoreboards in Strategies (A and B as tabs); budget in Control ("Budget and AI usage"); data health = the existing
  Control item, with an F&O section.
- (b) Story ids: W3a weather, W3b Forecast lab, W3c paper books, W3d Strategy lab F&O tab, W3e data health, W3f card,
  W3g budget, W3h scoreboards; P2a to P2h match them on trading's side.
- (c) No F&O screen page is published yet. With the database set (it is), a screen shows "not published" until its
  P2 page lands; the fixture adapter serves only without a database. So each screen ships when its page does.
- (d) Mockup 40 stands for W3a; its "recent" strip shows the back-fill history labelled "back-fill, exploratory" until
  live records exist.
- Weather test (the screens builder's): the view model and the rendered page contain none of M1's threshold constants
  and no threshold wording ("turns RED at", "floor"), checked against M1's own configured levels, not bare numbers.

## Build order (each step: page, contract or mockup, screen; each its own judge)

1. **Weather (W3a, P2a):** pages `weather` and `weather_history` from 2,409 real records; today's colour "not
   published" until M1's live job runs; history, red share and scores from the back-fill, labelled exploratory.
2. **Forecast lab (W3b, P2b):** G4's live-v2 scores, G8's v4 report (exploratory until the freeze), the AI books with
   their real record (no on-time day yet); 37 rebuilt first.
3. **Paper books (W3c, P2c):** daily totals and the Drive accounts (rule 2, through the existing download).
4. **Strategy lab F&O tab (W3d, P2d):** 54 trials, "no strategy has passed".
5. **Data health (W3e, P2e):** manifests, checks, the publish run status.
6. **Card (W3f, P2f):** T1's delivery records; the full card from Drive, owner-only fields behind sign-in.
7. **Budget and AI usage (W3g, P2g):** BG1's meter and signal; no model names.
8. **Scoreboards (W3h, P2h):** "not run yet" until S2/S3 runs exist (none today).

**Judge verifies:** per step, the page's numbers against its source; the privacy rules 1-6 (planted private value,
log capture, never-sent keys, gateway imports); no second publisher, reader or adapter.

**Depends:** P1 (merged), the existing publish path (P6-P10), E2c's `PrivateFiles`, M1 (live weather), G4, G8, T1,
S2/S3, BG1, O8 · **Status:** story text for the judge (`reviews/claude/response_219_fno-screens.md`)
