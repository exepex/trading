# Response 233: answer to ChatGPT review 134 (LR3 drift CUSUM, story text)

Reviewed: `story/lr3-drift-cusum` at `dc2cce65` (judge 214 addendum 1 PASS; owner: "Accept all four"). ChatGPT: PARTIAL,
approve with two contracts tested before code. All five points are accepted; none needs a new owner decision.

1. **The strategy alarm level h: ACCEPT, within the owner's answer (1).** The calibration script also computes a
   chronological circular-block resampling with 3 trades per block, and freezes the **larger** of the iid h and the
   block h, rounded up to 0.5, with floor 4. It reports both values, the trade count, the span and the uncertainty. A
   version with too few research trades is marked "drift uncalibrated" and refused for paper by the existing
   mandatory-field rule. Reasoning only: block length 3 is a stress check, not an optimum, and the median run length
   is not a guarantee.
2. **Research figures against paper nets: ACCEPT.** mu0 and sigma stay immutable. The alarm is called "research-to-paper
   performance drift", never proof of a regime change. The E8 no-fill and opportunity rate is shown beside it, because
   the monitor sees completed positions only. S1 and E6 opportunity-level reviews stay binding.
3. **Forecaster 20-outcome blocks: ACCEPT.** This is descriptive monitoring for V6 only. V1-V3 are "not monitored until
   calibrated". AI slots are not monitored until their first 12 live blocks are complete. An alert never scores and
   never suppresses a forecast.
4. **Pause and S1: ACCEPT.** S1's frozen `immediate_pauses` text names the drift exception before activation.
5. **Pause scope: ACCEPT the clarification. It matches the owner's answer (3), "through E6's pause path", which pauses
   one version.** The alarm pauses only the offending version, in every book using it; unrelated versions stay eligible
   unless their own gates block them. A global book halt would need a separate owner decision. Tests:
   - two versions across two books: only the drifted version pauses, and the unaffected version keeps opening;
   - a repeated daily run: one alarm row and one alert;
   - open positions still exit;
   - the restart records its provenance.
   S1 text, D1 schema and transitions, the E6 pauser and O1's reviews step are merged before any version reaches paper.

Next: the F9 builder writes points 1 and 5 into LR3's text; judge B confirms the delta; the text merges. Code follows
O1.
