# Response 225: answer to judge 217 (dashboard contract 2.8.0 and mockups 37, 41-45)

Screens lead, 16 Oct 2026. Judge 217 (`reviews/judge/judge_217_fno_contract_2_8_and_mockups.md`): FAIL, 2 should-fix,
2 notes. All four accepted; new heads below.

| Branch (exepex/omenix-dashboard) | Was | Now |
|---|---|---|
| `story/fno-contract-2-8` | 5f6ab3c4 | 39d1829 |
| `story/fno-mockups-2` (merges the contract branch) | 04ae2091 | f04cb50 |

## Should-fix 1: weather history colour and chances together. Accepted, fix (i)

The judge is right: the schema required `colour` with `p_big_1d/5d` and `base_rate_1d/5d` while its own header said
that choice waits for the owner. Strict form now: each session sends `session`, `colour` and `label` only; the chances
and usual chances are listed in `x-never-sent` with the reason. Colour, not the chances, is kept because the history's
screen job is the colour strip, and the day's chances are already on the weather page (`getFnoWeather`), which the judge
found safe on its own. If the owner chooses (a), a minor version adds the chances back.

Evidence: `check_fno_screens` and `check_contract` pass; only the two `getFnoWeatherHistory` examples changed (diff of
the examples file by key).

## Should-fix 2: mockup 37 dropped the owner's 13 Oct requests silently. Accepted, partly rebuilt

Not only listed: the views the catalog can feed are back, the rest are listed with why.
- Kept, now drawn from `FnoForecastLab`: today on top and the past below (said plainly), which forecaster beats the
  yardstick on which question, the test's numbers folded "for the curious", lab name, plain words.
- Changed: ranking within each question, not across them (Brier and QLIKE are different scales; reasoning only);
  "how long it runs" becomes each question's settle date.
- Dropped for now: the period chooser and race chart, and "what made the difference" (costliest misses). The
  contract has no per-day series or settled forecasts with outcomes; drawing them would invent data. A 2.9 proposal
  (both fields, public-safe) is in 37's `notes.md` for the owner and the orchestrator to decide.

Checks: `check_page.js` on the three states (no console errors, overflow or external requests), `check_text.js` 0
findings.

## Note A: accepted

The 2.8 version note now says the new required fields reject a 2.7 payload, and that no F&O screen page is published
yet.

## Note B: accepted, with its limit

`check_fno_screens.py` gains `check_never_sent_values` (`fno_rules.py`): no example's weather driver may be
`us_overnight`; a planted `us_overnight` driver is caught (run by hand). Its limit: it checks the catalog's examples,
not the producer's pages. The producer side belongs in P2's page test (asked of the P2 builder). Removing
`us_overnight` from the enum would enforce it everywhere through the pinned schema, but that is a removal the
orchestrator asked me not to make in 2.8; I'd support it in 2.9 (reasoning only).

## Note C

Agreed; no change.
