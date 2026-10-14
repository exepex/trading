# Freeze record: weekly options and weather study

Frozen at commit `650dd8f397db2676f8df54bc0ab383bde2722a95` (14 Oct 2026), before any weekly-option P&L or weather-signal outcome was computed. Only
`study.py --check` (data and fill counts, no P&L, no colours) and a synthetic-chain check of `trade()` (made-up prices,
no market data) ran before it. Ledger trials 43-52 name this commit.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `fd6098097faa4cd1c7d6feb54622f3cff969dea4691fbfc418e374339952ea30` |
| `study.py` | `7d82f69e756eb424381a819ba3806bb5f32bd934d7641602dd50bf73ce68cc24` |
| `report.py` | `b0dc8dc1d35ec7760a9c09e3ad83f1d55094696ac344be32ca5fa9e6ac0cf5be` |

Check before reading results: `sha256sum -c` on these three files at the run commit.
