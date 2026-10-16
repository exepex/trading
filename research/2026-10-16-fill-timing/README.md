# FT1: the fill-timing study (story E8a)

Registered, **not run**. `PROTOCOL.md` is the frozen registration (ledger trial 54); `FREEZE.md` names the commits and
hashes; `probe.csv` is the price-free coverage probe run before the freeze (68 of 68 contracts answered). Idea card:
`research/ideas/FT1.md`.

Every figure is exploratory measurement: how far an entry price moves between a 15:00 or 14:00 decision and E8's fill
(R = 5, 30 and 60 minutes), and how often a winning trade flips. No edge and no strategy verdict.

## Running (steps 2-4 are built and tested after the freeze)

1. `python study.py --probe` (done, 15 Oct 2026): symbols and candle counts only.
2. `python study.py --dry-run`: 5 decision days with real answers, giving the call count and duration.
3. `python study.py --fetch`: every planned contract, raw answers to Drive with a manifest row each.
4. `python study.py --run`: once, from the archived answers only; refuses unless the frozen files match `FREEZE.md`.

Groww is reached only through A16's `ReadOnlyGroww`; nothing here can place, change or cancel an order.
