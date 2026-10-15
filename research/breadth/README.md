# The breadth track (BR1)

Research only: forecasts and their scores, never an order. The story is `docs/stories/BR-breadth.md`, the design
`reviews/claude/response_154_breadth-track.md`. The protocol is `PROTOCOL.md`; it is not frozen.

## How to read BR1's numbers (owner, 16 Oct 2026)

- **Breadth is a range.** Across forecaster pairs, the daily forecasts across F&O names behave like **6 to 42
  independent bets a day**. About 9 is only the common-tilt planning case.
- **The month estimates are planning projections from a normal approximation, never deadlines.** On 2024-2026 they
  were 3% skill in about 7.6 months and 2% in about 17, with about 21.5 in the worst year.
- **The 2% and 3% skills are hypothetical.** Whether any forecaster beats the frozen primary baseline by 2-3% is
  unknown.
- **The tilt is a planning case, not a good forecaster.** On 2024-2026 the 1.15 volatility tilt **lost** to `cal60`
  (t -8.06).
- **A BR1 claim means one thing only:** "family F beats the primary baseline on T1, end of day". It is never "beats
  all baselines", and never a trading or real-money result.

## Layout

- `studies/`: BR1a's three pre-registered history studies (`run.py panel`, then `run.py studies`). Their results
  are in `studies/results/`.
- `PROTOCOL.md`: the protocol items in S1's format, each a proposal until the owner decides it.
