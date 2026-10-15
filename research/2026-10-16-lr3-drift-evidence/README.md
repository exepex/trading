# LR3 drift detection: the evidence behind the story text (16 Oct 2026)

These are exploratory research checks, not a registered test. No trade, no score and no record is changed. Each script
runs from the repository root with `python3 research/2026-10-16-lr3-drift-evidence/<script>.py`, and its output is
the `.out` file beside it.

| Script | What it checks | Result |
|---|---|---|
| `arl.py` | Markov-chain average run lengths of a one-sided CUSUM on normal data | k 0.5, h 4: 334; h 5: 925 (design 5.8's 340 and 900). Detecting a 0.3 SD shift: 60 and 103 |
| `strategy_arl.py` | Design 5.8's strategy CUSUM (k 0.5, h 4) on experiment 1's per-trade nets, resampled | In-control median 40 (SF challenge, skew -2.6) to over 3,000 (BF, skew +2.4); 1 SD worse: 6-9 trades; edge gone: not detected |
| `calibrate_h.py` | LR3's per-version threshold (ten years of trades, in-control median) on the same samples | h* 1.0 to 5.5; a 1 SD collapse in 2-12 trades. Hence LR3's floor of 4 |
| `backfill_cusum.py` | Design 5.8's forecaster CUSUM on the v4 back-fill (V6a, 2019-2026), then LR3's 20-outcome blocks | As written: 287-503 alarms. Blocks with the back-fill SD: 0 alarms in 95; 1 block-SD worse: about 7 blocks |

The experiment 1 nets are close-proxy history (2019-2023), and the v4 back-fill is labelled `backfill_exploratory`.
