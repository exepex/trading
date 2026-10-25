# Result-derived inputs: EDGE2-F6-FL-H5

The G1-G3 inputs of `EDGE2-F6-FL-H5.md`, measured by its family's discovery run and kept here so the frozen card stays
byte for byte as frozen (judge 642 S1; `fno/factory/card.py`). Copied exactly from the card as committed at
`ed28d6b7`, where its G1 row was screened (`research/factory/gates.csv`). Exploratory.

**Trial 118 is closed:** its G1 `passed` rests on the plain SD over 1,451 overlapping 5-session trades; with the
protocol's Newey-West error the bound is -Rs 316 (`research/edge2/F6_RESULTS.md`). The factory's own next gate
(`factory spend`) logged G2 `exploratory`, its last gate (judge 642 S2).

```factory-inputs
gross: {kind: measured, mean: 1397.1588559614058, sd: 20090.0626044408, n: 1451, source: "EDGE2 F6 discovery, research/edge2/f6/discovery.json (run at 06646081, code 48250512); exploratory; H5 trades overlap, so n overstates the independent count"}
tail: {probability: 0.0, loss: 0.0, in_gross: yes}
cost: {measured: 657.6870930414473, source: "EDGE2 F6 discovery, mean futures charges plus the 1-point pads, same file"}
sd_per_trade: 20082.56217797329
frequency_per_year: 245.0
pass_level: 0.05
```
