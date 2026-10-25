# Result-derived inputs: EDGE2-F1-WF-G15

The G1-G3 inputs of `EDGE2-F1-WF-G15.md`, measured by its family's discovery run and kept here so the frozen card stays
byte for byte as frozen (judge 642 S1; `fno/factory/card.py`). Copied exactly from the card as committed at
`b9b23f9d`, where its G1 row was screened (`research/factory/gates.csv`). Exploratory.

**Never re-test WF-G15 on this data** (NIFTY and BANKNIFTY weeklies 2019-2026): its +Rs 795 mean on 28 trades is a
small-sample winner the family's Holm rejected (`research/edge2/F1_RESULTS.md`); a new version needs fresh data.

```factory-inputs
gross: {kind: measured, mean: 1204.6339285714291, sd: 7309.614408650992, n: 28, source: "EDGE2 F1 discovery, research/edge2/f1/discovery.json (run at 270959dd, code 9cbe34ce); exploratory, spent data"}
tail: {probability: 0.0, loss: 0.0, in_gross: yes}
cost: {measured: 410.0318962729286, source: "EDGE2 F1 discovery, mean C1 charges plus the Rs 1 entry pads, same file; exploratory"}
sd_per_trade: 7337.368769809355
frequency_per_year: 3.61
pass_level: 0.05
```
