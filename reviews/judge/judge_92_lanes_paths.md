# Judge 92: the lane-1 path lists, trading `story/x-lanes-paths` 50c6bc7 and dashboard `story/x-lanes-paths` 5cf5ca2

Rule documents are lane 1, so this text needs a PASS. I checked each listed path against the real trees (`fno/*`,
`tools/*` and the dashboard's top-level folders and `web/*`). I also checked the paths that were missing.

## Trading 50c6bc7: FAIL

The text matches judge 91 accurately, so this is not a transcription error. **My own judge 91 list was incomplete.** I
wrote it from memory, not from the tree, and the branch copied it faithfully. These lane-1 subjects (money, outside
services, secrets, records, trade decisions) fall to lane 2 under the list as written:

| Missing path | Lane-1 subject it carries |
|---|---|
| `fno/accounting/`, `fno/costs.py` | money: P&L, charges |
| `fno/nse_margins/` | risk: margin tables |
| `fno/providers/` | outside services (Groww and the other providers) |
| `fno/alerts/` | outside services (Slack) |
| `fno/record_scan/`, `fno/env_file.py` | secrets: the public-record scan, environment loading |
| `fno/research_engine/` | trade decisions and statistics (`statistics.py` is frozen; its neighbours are not) |
| `fno/research_data/` | data availability rules (look-ahead), NSE sources |
| `fno/market_read_models/` | the dashboard publisher (privacy rule) |
| `fno/filings/`, `fno/fo_bhavcopy.py`, `fno/http_pacing.py` | outside services (NSE), politeness limits |
| `fno/config.py`, `fno/models.py`, `fno/freeze_sections.py` | allowed settings, the IST clock, freeze hashing |
| `tools/forecast_golden.py`, `tools/forecast_live_golden.py`, `tools/gdrive_oauth_setup.py`, `tools/nse_raw_download/` | records, secrets, NSE |
| `research/forecasts/`, `research/evaluation/` (hand edits) | forecast and evaluation records |

Must-fix: invert the list. Lane-2 code then needs no list of exceptions at all.
- **Lane 1:** all of `fno/`, `tools/`, `.github/`, `.githooks/`, `.gitattributes`, `config.yaml`, `db/`,
  `requirements*.txt`, the rule documents, and any hand edit under `research/`.
- **Lane 2:** what is left, which is added tests and explanatory docs.

Reason: almost every module under `fno/` carries a lane-1 subject. A list of inclusions will always miss the next new
folder, and I just missed eleven. Any later lane-2 exception inside `fno/` would need my PASS as a rule-document change.

The other refinements (2 to 6) are correct as written.

## Dashboard 5cf5ca2: FAIL

Must-fix:
1. **Screen code is lane 1 by path.**
   - The text makes "any change to what data a screen reads or renders" lane 1. That is the description-based test
     that refinement 1 replaces.
   - `web/app/**` and `web/components/**` are left unlisted, and a `.tsx` change there can render a new field.
   - Proposal: every `.ts`/`.tsx` under `web/` is lane 1. Lane 2 covers only `web/styles/**`, CSS, `design/` and
     added tests under `web/tests/`.
2. **Name every gate and its allowlist, and add the vendored code.**
   - Both allowlists exist: `tools/code_size_allowlist.txt` and `tools/css_duplicate_allowlist.txt`. Put all of
     `tools/` in lane 1.
   - `scripts/` holds third-party vendored JavaScript (`lightweight-charts`), a supply-chain path, so it belongs in
     lane 1 too.
   - `web/tools/` is unlisted.

Correct as written: `api/`, `web/lib/`, `web/app/api/`, middleware, `next.config`, `vercel.json`, `package*.json`,
`config/`, `platform/`, `.github/`, the rule documents, the "Lane 2:" message and the revert rule. All listed paths
exist in the tree.

## Verdict

**FAIL for both.** These are small text fixes. When both lists are corrected, I re-check them against the trees.
