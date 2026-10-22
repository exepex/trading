# Market school P0 probes

Stage P0 of the market school (response 327 revision 2, section 4; owner approval: DESK_DECISIONS "Market school
approved"; WORK_REGISTER "MS-P0 market school probes"). One dated note per probe. Every claim carries a label (strong
evidence, some evidence, reasoning only) and a source (a URL, a file and line, or a measured run). Research notes only:
no driver, fleet, capture or account code, and no raw Groww answer in the repository.

| # | Probe | Note | One-line answer |
|---|---|---|---|
| 1 | Groww option-chain fields and rate-limit types | [2026-10-22-p0-1-groww-chain.md](2026-10-22-p0-1-groww-chain.md) | The chain has no bid, ask, sizes, timestamp or lot. Two-sided prices need one quote call per leg. LTP, OHLC and Quote share one Live Data budget (10 a second, 300 a minute), which A16 already fills during its marks. |
| 2 | NSE and Groww terms for automated reading | [2026-10-22-p0-2-terms-automated-reading.md](2026-10-22-p0-2-terms-automated-reading.md) | NSE's website terms **forbid** automated collection at any volume, which also reaches the project's existing NSE reads. Groww's API allows the volume; whether read-only use fits its "only for ... buying and selling" clause is unclear, so ask Groww in writing. |
| 3 | Google Drive write quota | [2026-10-22-p0-3-drive-write-quota.md](2026-10-22-p0-3-drive-write-quota.md) | 1,000 files a day is fine for speed (0.83 vs 3 writes a second). The wall is about 500,000 files per owner (about 2 years). Use one JSONL archive per slot before capture grows to hundreds of files a slot. |
| 4 | Physical settlement and expiry-day margins | [2026-10-22-p0-4-settlement-expiry-margins.md](2026-10-22-p0-4-settlement-expiry-margins.md) | See the note: the delivery-margin steps before a stock expiry, and SEBI's 1 Oct 2024 expiry-day rules (extra 2% ELM on short index options, no calendar-spread offset on expiry day), with circular numbers. |
| 5 | Futures and calendar/diagonal payoff and margin model | [2026-10-22-p0-5-futures-calendar-model.md](2026-10-22-p0-5-futures-calendar-model.md) | The code is one-expiry, options-only. No futures charges or margin, no second expiry. A NIFTY put calendar can lose 2.4 times its debit; the diagonal example loses 17 times. |

## What P0 means for the next stages (orchestrator and owner to decide)

- **P0b on NSE: blocked** by probe 2. P0b on Groww: possible within the Live Data budget, between A16's marks and
  outside A4 and A22, once Groww's written answer on read-only use is in. A lane-1 change adds `get_ltp` to the
  read-only allow-list if the LTP batch is wanted.
- **P1 pilot** uses existing captures only (response 327), so probes 1-3 do not block it. Probe 2's finding on the
  project's existing NSE reads (story O6's NSE chain among them) is for the owner.
- **Futures, calendars and diagonals** stay closed until a story builds the missing parts listed in probe 5.
