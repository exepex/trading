# Response 98: R1 factory documents and R2 registration (branch `story/r1-factory-docs`, lane 1)

Builder's claims for the judge. Scope: REPLAN slice A items 4 and 5. Documents plus one test change: `tests/research/test_ledger_guard.py` expected 52 repository trials and now expects
53, with a new assertion that trial 53 is prospective and names the freeze commit (a tighter test, not a looser one).
R2 is registered, **not run**: no stock-option data was read.

## Files

| File | What |
|---|---|
| `research/FACTORY_RULES.md` | Gates G0-G6; G1 feasibility-screen rule; `exploratory_shadow` rules; G2; multiple testing |
| `research/ideas/TEMPLATE.md` | Idea-card template (G0-G6 fields) |
| `research/ideas/R2.md` | R2's idea card, filled from the template |
| `research/DATA_SPEND.md` | Data-spend register: status words, 12 rows, update rule |
| `research/2026-10-15-r2-stock-options-results/PROTOCOL.md` | R2 registration |
| `research/2026-10-15-r2-stock-options-results/FREEZE.md`, `README.md` | Freeze commit and hash; folder note |
| `research/ledger.csv`, `research/LEDGER.md` | Trial 53 (prospective, hypothesis `no`), total 53 |

## Claims (each with its label)

1. **Feasibility screen (R1):** `FACTORY_RULES.md` section 2 says pass only if expected net after costs **and tail
   losses** is above zero on a conservative bound, defines the bound, uses the worse of the card's and the measured
   maximum-loss rate, and makes 2x a labelled `thin margin` warning, never a pass mark; screened-out ideas keep their
   row and stay in the trial count. Strong evidence (read the text against design 3.1 G1).
2. **`exploratory_shadow` (R1):** section 3 rules 1-7: frozen before collection; cumulative Holm family per
   registered research question, including active, stopped, retired, judged and new shadows; p = 1 for unfinished
   ones; earlier verdicts never relabelled; one judgement at the frozen sample unless alpha-spending was registered
   before collection; a change after looking makes a new idea and a new row. Strong evidence (text).
3. **Ledger status gap, said plainly:** `research/ledger.csv` has no status column and B4's guard fixes its columns
   (`fno/research_engine/ledger.py` `COLUMNS`), so statuses (`idea`, `screened_out`) live in the idea card and
   `LEDGER.md` until R1's code (slice B) adds a field. Strong evidence (code).
4. **R2 registered before any outcome:** the protocol was committed in `93a19c318003994c6cedd070d038ee89d45dd74e`;
   trial 53 and `FREEZE.md` (protocol SHA-256 `89947b4c...a6b`) were committed after it, naming it. No data of the
   study was read in this session (I read only manifests' first rows to name sources: file URLs and dates, no
   stock-option rows). Some evidence (git history proves the order; "nothing read" is my statement, checkable only
   from the session's commands).
5. **R2 covers REPLAN item 5:** question (section 1); data: NSE archive volume, open interest, lot values against the
   Rs 10,000 cap, one Groww bid/ask snapshot (sections 3, 5, 6.2); yes/no decision rule (section 8: fit at least 25%,
   median and mean EN > 0 at a 5% edge, at least 130 clusters a year); effective clusters by sector and results week
   (section 7); early failure (section 9, stages 0-4). Strong evidence (text).
6. **Thresholds are reasoning only:** e = 5%, SD 60% (hence 130 clusters a year), the 2% tail term for S7, 50
   contracts and 100 open interest, 25% fit. None is measured. The registered prior is that NO is more likely.
7. **Data exposure kept small:** only 2019-21 event moves are read (for the within-week correlation the story asks
   for); 2022-26 moves stay fresh; decisions use only Oct 2024 onwards. Reasoning only.
8. **Checks:** full suite `env -u FNO_SLACK_BOT_TOKEN python -m pytest -q`: 3161 passed; `ruff check fno tests
   tools` clean; `python tools/check_imports.py` clean. On the container's first shallow clone, 8 freeze tests failed
   with "freeze is not in the history" (also on `origin/main`); after `git fetch --unshallow` all pass. Strong evidence
   (command output).
9. **Line limit:** largest new file 190 lines (protocol). Strong evidence (`wc -l`).

## Open points for the judge and the owner

- **Dependency:** the Groww snapshot needs the owner's check of Groww's terms on storing quotes (REPLAN item 3). Until
  then R2 can run stages 0-2 only.
- **Merge rule:** the branch must be merged (never squashed or rebased) so that `93a19c3` stays in `main`'s history;
  otherwise the ledger guard refuses trial 53.
- **Possible challenge:** e = 5% may be called too strict (it could make NO a foregone result) or too loose. The report
  prints the break-even edge e\* per structure so the answer at any e is visible; changing e itself would be a new
  trial.
- The analysis script is written later and hashed into `FREEZE.md` before the run (protocol section 11); it is tested
  only on synthetic data before then.
