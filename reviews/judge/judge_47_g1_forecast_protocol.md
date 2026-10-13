# Judge 47: story G1, forecast protocol and the 30-day ATM implied-volatility estimator

**Verdict: FAIL.** There is 1 should-fix finding (the freeze design) and 1 minor finding (process).
- **The numbers and code are right.** My hand values equal the builder's: IV30 14.4937, the holiday and muhurat
  window, both realised volatilities and the 6.18% return.
- **The freeze order is right.**
- **The multiplicity method** is named exactly (Holm, 5%, 45 comparisons, a moving-block bootstrap with L = 20 and
  B = 10,000, and seeds).

**What I judged**
- **Repository:** trading at 0dcedf8 (protocol f936156, freeze ef5b818).
- **Claims:** `reviews/claude/response_53_2026-10-13-g1-forecast-protocol.md`.
- **Story:** `docs/stories/G-forecasts.md`, G1.

## Checks run by the judge

```
$ python -m pytest -q tests/forecast tests/research/test_ledger_guard.py     48 passed
$ git merge-base --is-ancestor f936156 ef5b818                               order ok (12:56:34, then 12:57:44 UTC)
$ (full suite at 46fe709: 1215 passed; ruff and imports clean)
```

### Hand recomputations

**IV30, bracketed day** (d = 2 Mar 2026; expiries 18 Mar at 16 days and 15 Apr at 44 days):
- ATM IV of 18 Mar = (12% + 14%) / 2 = 13%; of 15 Apr = 15%.
- w1 = 0.13² × 16 = **0.2704**; w2 = 0.15² × 44 = **0.99**.
- w30 = 0.2704 + (0.99 − 0.2704) × (30 − 16) / (44 − 16) = 0.2704 + 0.3598 = **0.6302**.
- IV30 = √(0.6302 / 30) = 0.144937, so **14.4937 points**. **Equal.**

**IV30, not bracketed** (the 15 Apr put did not trade): 18 Mar alone (16 days, at least 7), so **13.0**, flagged.
**Equal.**

**A target window with a holiday and a muhurat session** (fixture holidays 26 Jan and 17 Feb, muhurat Sun 22 Feb;
d = Mon 2 Feb 2026), counted by hand:
- **d+10:** 3, 4, 5, 6, 9, 10, 11, 12, 13 and **16 Feb**.
- **d+20:** 18 Feb (17 Feb skipped), 19, 20, 23, 24, 25, 26, 27 Feb, 2 Mar and **3 Mar** (the 22 Feb muhurat
  session is skipped).
- **Realised volatilities:** next RV = √((19 × 0.0004 + 0.0016) / 20 × 252) = **34.0470**; trailing RV
  = 0.01 × √252 = **15.8745**.
- **Return:** the log change is 0.02 + 0.04 = 0.06, so e^0.06 − 1 = **6.18%**. Q2 (at least 3%) is yes, and Q3
  (34.05 > 15.87) is yes.

All equal the builder's.

## Criteria

| # | Criterion | Judge's evidence | Result |
|---|---|---|---|
| 1 | Every target equals hand-worked values, all five questions, a holiday in the window | My counts and values above; `test_targets.py` passes | MET |
| 2 | IV30 equals a hand computation on two days (bracketed and not) | Above | MET |
| 3 | Protocol frozen; its commit precedes the first scored forecast (G4 checks) | The order is checked. `require_frozen_before` is tested (an earlier commit, an edited file and a wrong version are all refused). No forecast exists. | MET (see finding 1 on what is frozen) |
| 4 | The multiplicity method is named with its exact procedure before scoring | Protocol section 8: 45 comparisons in a fixed order, p = 1 for comparisons not yet possible, a centred bootstrap p-value, Holm's step-down at 5%, only Brier tested, at least 40 paired dates. `comparisons.py` matches. | MET |

## Finding 1 (should fix): the freeze locks shared library files for the life of the forecasts

- **What is frozen:** `FREEZE.md` checks the bytes of B1's `implied_vol.py`, `volatility_features.py` and
  `close_series.py`, and `test_freeze.py` fails on any edit.
- **Why that is wrong here:**
  - Forecasts are scored continuously for months (the first review is at 6 months).
  - Those three files are shared by F1, live F1 (B7), C2's stress engine and IV30.
  - Any refactor or unrelated fix in them then turns CI red and forces a new forecast-protocol version, even when no
    forecast number changes.
  - That couples three stories to one test and pushes builders either to stop improving the library or to cut
    protocol versions for no reason. It breaks the owner's mandatory "design for change, loose coupling" rule.
- **Why the experiment 1 freeze is different:** it hashes engine files for a short window, from the freeze to the
  challenge run. This freeze has no end.
- **What must be protected is behaviour, not bytes.** Expected (reasoning only on the form):
  - Check the bytes of `fno/forecast/*` and `PROTOCOL.md` only.
  - Commit a **golden file** of the estimator's outputs, with its SHA-256 in the freeze record: IV30 (value, flag and
    expiries) and trailing RV20 for every panel day 2019 to the freeze day. Both are known at the forecast date, not
    outcomes, so they can be computed before scoring. Add the hand fixtures' values.
  - A test recomputes them with the current library and requires equality (for example within 1e-12).
- **The result:** a refactor that keeps every number passes, and a change to any number fails and needs version 2.
  The library files can then be recorded but unchecked, as the calendar and the panel manifest are.
- **One caveat to write into the protocol:** a panel rebuild that changes a past day's data (A11 revisions) would
  also move the golden values. That is correct, because the inputs changed, and it must name the A11 revision that
  explains it.

## Minor 1 (process): frozen before any outside review

**Did the G1 story allow a freeze at this stage? Yes, by its text.**
- It asks for `PROTOCOL.md` "frozen (FREEZE record with commit and hashes, like B5)" and has no review step.
- "Like B5" refers to the record's form.
- The owner's "freeze only after ChatGPT agrees" (DESK_DECISIONS, 13 Oct) is written for experiment 1's protocol.

**But it is premature against the project's practice.**
- CLAUDE.md requires every proposal to go to ChatGPT through the repository, and experiment 1's protocol needed both
  sides' agreement before freezing.
- The builder's own "choices, please challenge them" (baselines, book 1 rule, muhurat exclusion, tie rule) are
  exactly what a review would change.

**The harm is limited.**
- No forecast exists, so a version 2 before the first scored forecast loses nothing.
- What it costs is the meaning of "frozen": version 1 is effectively a draft with hashes.

**Expected:**
- Send the protocol to ChatGPT now, and record in the ledger that version 1 is superseded if anything changes.
- The orchestrator or owner should decide whether G-protocols need agreement before freezing, as experiment 1 does,
  and write that into G1's story.
- **My recommendation (reasoning only):** yes. The protocol's whole purpose is that its choices cannot be tuned
  later, so they should be challenged before they are fixed.

## Notes (agreed, or for others)

- **Muhurat sessions** are not trading days for the targets (as B1), and special weekend sessions count.
  **Cross-project inconsistency:** W11's 33 screener counts the 21 Oct 2025 muhurat session among its "250
  sessions" (judge 42 addendum 2). Both are internally consistent. A one-line project convention would prevent
  confusion.
- **IV30's flag rate** (13%, mostly 2019-20 where the next month's ATM leg did not trade) is measured and stated.
- **Book 1 = the mean of two baselines** is fixed in the protocol, as G3 requires.
