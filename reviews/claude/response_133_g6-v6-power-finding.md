# Response 133: finding for the owner and the G6 session before the v4 freeze: V6 cannot settle in useful time

**Status:** G6 protocol v4 is merged (597487f) but NOT frozen, so this can still be changed through G6's review path.
**Source:** G8 builder (response 126), confirmed independently by judge D (judge 128 addendum 1). Strong evidence.

**The finding.** Protocol v4's power report sizes V6 (a 2% NIFTY day: V6a next session, V6b within 5) for its
minimum effect: a Brier improvement of 2% of a ~4% event's Brier, about 0.00095. Daily Brier differences are up to
about 0.3, so the ratio r is 60-87 and the required number of independent outcomes is
n = ceil(13.837·r²): judge D rebuilt V6a with r = 86.5 (base-rate mean Brier 0.0475), giving **n = 103,648**
(about 400 years of trading days).

**Even the observed skill is slow.** G7's simple forecaster already shows about 14.5% Brier skill on 1,908 days
(exploratory; judge D's rebuild BSS 0.1449). Detecting even that at the protocol's error rate needs about 1,976
independent outcomes, about 8 years for V6a.

**Consequence.** The stop-rule review (~31 May 2027) needs a projected settle date within 2 years for option 1, so
under v4 as written V6 will almost surely land on option 2 (code only), whatever the forecasts show.

**Options for the owner and the G6 session (reasoning only; no recommendation from the judge):**
- **A:** keep V6 confirmatory as written and accept it will not settle; V1-V3 carry the confirmatory weight.
- **B:** make V6 descriptive (reported, like V7), so it never blocks the stop rule.
- **C:** resize V6's minimum effect to a skill that matters for trading (for example 10% Brier skill), so it can settle
  in years, not centuries; this changes thresholds and needs G6's review path (judge and ChatGPT) before the freeze.

**Orchestrator's view (reasoning only):** B is simplest and honest; C only if V6 is meant to gate a trading decision.
Either must be decided before the freeze, because the freeze hashes the protocol and the thresholds.

Also for the freeze commit (from G8): FREEZE_v4.md must carry `Frozen on: YYYY-MM-DD`; G8's look refuses without it,
so pre-freeze and back-fill rows are never counted.
