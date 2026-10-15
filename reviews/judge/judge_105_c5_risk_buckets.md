# Judge 105: story C5, risk buckets and the Rs 20 lakh paper account (branch, before merge; judge C)

Date: 15 Oct 2026 (UTC). Branch `story/c5-risk-buckets` at **f4f2e35258a2fe647b1222f2a858f3c10e41bb12**. Claims:
`reviews/claude/response_105_c5-risk-buckets.md`. Story: `docs/stories/C-code-roles.md` C5. Lane 1 (money and risk);
by quality rule 9 it goes to ChatGPT after a PASS.

**Owner rows judged against:**
- 15 Oct caps;
- "1 A" (no flat 3-open limit for the books) and "2 A" (no old stress or exposure limits for the books);
- the Manual account's 13 Oct limits;
- the owner's answers to the builder's Q1-Q5 (665c835): 1 B, 2 B, 3 A, 4 A and 5 A. The builder is adding 1, 3, 4 and 5
  on a new SHA. **These are judged in the addendum, not here.**

## Verdict: FAIL, 4 should-fix (no blocking); 5 minor

C2's side is sound:
- **Every cap passes at exactly its limit and refuses Rs 0.01 below it**, on the real wiring (`build_risk_manager`
  with `config.yaml`).
- **A held short fly's maximum loss** is Rs 3,354.54 by my own hand arithmetic, equal to C2's.
- **Every broken profile I tried stops C2 at start-up**, and the Manual profile is unchanged.
- **The "every book trade refused today" claim** is true, and nothing hides behind it.

The gaps:
- **The one-session margin age is wrong on muhurat days.** It refuses Friday's row on Mon 9 Nov 2026, a real date.
- **C4 is not fully in step.** It accepts a brake restart with no signer, and 5 of my mutations survive in C4's caps,
  3 of them in the loose direction.
- **P10's acceptance criterion** still names the old stress limit.

## Gates (my runs, at the exact SHA)

`PYTHONDONTWRITEBYTECODE=1`, `python -B`, `FNO_SLACK_BOT_TOKEN` unset.

- Full suite: **3,269 passed** (403 s).
- `ruff check fno tests tools`: clean.
- `ruff format --check fno tests tools research`: 772 files formatted.
- Imports: clean (727).
- `git merge-tree` with `origin/main` (94e06b6): clean. `main` changed only documents since the branch's merge.

## The orchestrator's six items

| # | Item | My evidence | Result |
|---|---|---|---|
| 1 | C4 independence: no `fno.risk` import, own arithmetic, the bucket-breach case | `test_validity_independence` now lists `fno.risk.buckets`, `open_risk`, `caps`, `margin_age` and `profile_settings`, and passes. `validity_caps.py` imports only `validity_*` and constants. C4's held maximum loss is its own (one-point grid, own `order_charge` with the 0.05 floor) and equals C2's in the builder's test. The bucket-breach test exists. **But 5 of my C4 plants survive** (should-fix 3) | PARTLY |
| 2 | One-session margin age across weekends, holidays and special sessions | Real A7 calendar, C2 `SessionsOld` and C4 `MarginSettings.fresh` agree on every case: Fri 16 Oct row on Mon 19 Oct fresh; Mon 19 Oct row on Wed 21 Oct (Tue 20 Oct Dussehra holiday) fresh; Fri 16 Oct on Wed 21 Oct refused; Fri 30 Jan on Mon 2 Feb 2026 refused (Sun 1 Feb special session counts as a session; A14 writes a row for it, since `TradingDays` includes special sessions). **Muhurat:** Fri 6 Nov row on Mon 9 Nov 2026 is refused, because Sun 8 Nov (muhurat) counts as a session in `previous_session`, while A14 writes no row for it (`TradingDays.is_trading_day(2026-11-08)` = False). Should-fix 1 | NOT MET (muhurat) |
| 3 | Start-up validation of both profiles | 13 broken configs, my run: a Manual key removed, an unknown key, a rule typo, both ages, a brake above the account, a negative cap, a side typo, rules as a string, a cap as a bool or string, a missing paper account. **C2 refuses all at start-up.** C4 refuses only the missing setting; for malformed values C4 relies on C2's start-up check (stated in its docstring; minor 2). Dropping `bucket_cap` from the books' rules **and** its key starts both C2 and C4; only the test pinning the books' rule list catches it (config is lane 1; acceptable) | MET for C2; C4 by design |
| 4 | Brake restart only by a signed owner record | **C2:** `overrides.py` refuses a row with an empty `entered_by` or reason. "Signed" means a non-empty `entered_by`; any writer can type "owner" (minor 3). **C4:** `validity_account.restart_days` checks the action and reason but **not `entered_by`**. My probe: a row with `entered_by: ""` gives C4 a restart on 7 Oct. C2 refuses that row, so today the trade still fails, but C4 cannot catch a C2 regression here (should-fix 2) | PARTLY |
| 5 | Home's `limit_max` (P10) from Rs 30,000 to Rs 1,50,000: in scope, and correct? | **In scope:** the books' profile has no stress limit any more, so P10's `risk_settings(...).max_stress_loss_rs` no longer exists for them. **Correct in meaning:** "at risk now" against the Rs 1.5 lakh cap on the sum of open maximum losses; today `limit_used` is 0 and P10 refuses to publish with open trades, so the two cannot mismatch yet. **But the rule text is now false.** `docs/stories/P-publishing.md:318` says "`limit_max` = C2's `max_stress_loss_rs`". The pinned contract says `limit_used` is "C2's max_at_risk used", and its examples show 30000.0. My N22 plant (Manual profile) is caught. Should-fix 4 | PARTLY |
| 6 | Every book trade refused today, and fail-closed rather than a hidden bug | Real `journal/book1_rules` with the real `config.yaml`: `paper_account` refuses (opened with Rs 5 lakh), and `margin_room` refuses (`margins.csv` has a header and no rows). `max_loss_per_trade`, `bucket_cap`, `open_risk_cap`, `new_risk_per_day` and `drawdown_brake` all evaluate with real numbers (Rs 3,354.54 within each cap; drawdown 0). So nothing is masked; the refusal is fail-closed | MET |

## Per criterion

| # | Criterion | Builder's claim | My evidence | Result |
|---|---|---|---|---|
| 1 | Bucket cap at Rs 30,000, Rs 0.01 over refused, other buckets not counted | tests | **C2** (real wiring, 2 held flies plus the proposal, Rs 10,063.63): limit = total passes, total − 0.01 refused; N7 (group ignored) caught. **C4**: my probe at exactly 2× one trade passes and one paisa less refuses, but no test pins it. N1 (`<=` to `<`) and N2 (bucket compared on group only) **survive** | PARTLY |
| 2 | Open-risk cap at Rs 1,50,000 | tests | C2 at exactly the total passes, 0.01 below refuses. C4 exact limit untested (N1) | PARTLY |
| 3 | New risk per day Rs 50,000; first fill day; unknown day refused | tests | C2 boundary as above. N8, N15 and N16 caught; C4 N3 caught. **Owner 3 A** (same-session open-and-close counts) changes this criterion: waits for the addendum | PARTLY (pending owner change) |
| 4 | A cap only refuses; lots unchanged | test | My runs: every decision's proposal keeps its lots; caps return verdicts only | MET |
| 5 | Buckets per 6.2; unmapped refused | tests | `underlying_of` on real Groww ids (`NIFTY26OCT21500CE` gives NIFTY); NIFTYNXT50, FINNIFTY and MIDCPNIFTY fall outside the two groups, so they are refused. C2 N18 caught. **C4 N17 (mixed underlyings accepted) survives.** Directional codes wait for owner 1 B | PARTLY |
| 6 | Held maximum loss = B2's; net short tail refused; locked-in counts 0 | 3,000 random positions | **My hand calculation** (short fly 25,000/200, padded fills, C1 charges, worst level 25,200 or 24,800): **Rs 3,354.54**, equal to C2's `HeldMaxLoss` and to B2's proposal figure. C2 N6 (negative allowed) and N20 (units ignored) caught. **C4 N5 (negative allowed) survives**, which is the loose direction | PARTLY |
| 7 | New books open with Rs 20,00,000; any other opening refused | tests | N14 and N11 caught; the real books are refused | MET |
| 8 | Brake at Rs 1,20,000; only a signed restart row lifts it | tests | C2 boundary tests read; config Rs 1,20,000. C4 accepts an unsigned row (item 4) | PARTLY |
| 9 | Daily stress line, 5 scenarios, below the sum of maximum losses | test | The 5 config scenarios match 6.2 (−5% and −10% with VIX +50% and +100%; +5%). N21 caught. Owner 4 A accepted the assumptions. I did not recompute a stress row by hand (it uses C2's judged `StressEngine`) | MET |
| 10 | Books run exactly their rules; any setting problem stops start-up | tests | Item 3; N12 caught | MET |
| 11 | Manual keeps its 13 Oct limits | tests | Config: Rs 5 lakh, Rs 10,000, 3 open, Rs 30,000 brake, stress Rs 30,000, exposure Rs 15,000, 7 days: equal to the 13 Oct row and to C2's old values. N22 caught | MET |
| 12 | Books' margin older than one session refused; weekends and holidays never age a row | tests | Item 2: a muhurat Sunday ages Friday's row | **NOT MET** |
| 13 | C4 in step | tests | Items 1 and 4: an unsigned restart is accepted; N1, N2, N5, N17 and N19 survive | PARTLY |

## My mutations (22; `PYTHONDONTWRITEBYTECODE=1`; each restored; `git status` clean)

Tests run: `tests/risk`, `checks`, `playbook`, `books`, `desk`, `decisions`, `market_read_models`, `timetable`.

| Plant | Result |
|---|---|
| N1 C4 cap passes strictly below (`<=` to `<`) | **survived** |
| N2 C4 bucket compared on group only (side ignored) | **survived** |
| N3 C4 new risk counts nothing held | caught |
| N4 C4 held loss drops exit pads | caught |
| N5 C4 held maximum loss may be negative | **survived (loose)** |
| N6 C2 held maximum loss may be negative | caught |
| N7 C2 bucket ignores group | caught |
| N8 C2 unknown first-fill day not counted | caught |
| N9 C4 paper account always ok | caught |
| N10 C4 caps skipped | caught |
| N11 C2 paper account "at least" | caught |
| N12 cap above the account allowed | caught |
| N13 C4 margin age two sessions | caught |
| N14 E1 opens at Rs 5 lakh | caught |
| N15 ledger first-fill day unknown | caught |
| N16 D3 codec drops `opened_on` | caught |
| N17 C4 mixed underlyings accepted | **survived (loose)** |
| N18 C2 any underlying accepted | caught |
| N19 C4 proposal's loss on one lot's units (`lot_size` for `units`) | **survived (loose for multi-lot)** |
| N20 C2 held loss ignores units | caught |
| N21 stress line without the maximum-loss sum | caught |
| N22 Home `limit_max` from the Manual profile | caught |

## Claims vs reality

| Claim | Reality |
|---|---|
| "28 planted breaks caught" | Not re-run. My independent 22: 17 caught and 5 survive, all in C4 |
| "Books' margin older than one session refused; weekends and holidays never age a row" | False for the Sun 8 Nov 2026 muhurat (should-fix 1) |
| "C4 in step … C4 refuses to start on a missing setting" | True for missing settings. Malformed values rely on C2 (minor 2). The restart signature is not in step (should-fix 2) |
| "Only a signed restart_brake row lifts it" | C2: a non-empty `entered_by`. C4: not checked |
| "Home's `limit_max` is now the books' open-risk cap" | True in code. P10's story criterion and the contract wording still say the stress limit (should-fix 4) |
| "Every book trade is refused today" | True, by `paper_account` and `margin_room` only; the other rules compute (item 6) |
| Tests changed, not weakened | I read every edited assertion. Old C2 limits move to the Manual profile with the same values, brake cases scale to Rs 1.2 lakh, and C4's old tests run on the Manual profile. None was loosened |

## Should-fix (all small; the addendum SHA can carry them)

1. **The margin age must count sessions as A14 does.**
   - C2's `SessionsOld` and C4's `MarginSettings.fresh` step with `previous_session`, which includes muhurat sessions.
   - A14 writes rows only for `TradingDays` (muhurat excluded).
   - So on Mon 9 Nov 2026 Friday's row is refused, and the books can trade only if the 9 Nov row was written in time.
     The direction is safe, but criterion 12 is false on a date 3 weeks away, and the two halves disagree on what a
     session is.
   - **Fix:** count with `TradingDays`' definition in C2 and C4 (or have A14 write muhurat rows). Add a test for
     6 Nov to 9 Nov 2026 in both.
2. **C4 must require `entered_by` on a restart row, as C2 does.** Add a test where C4 alone gets an unsigned row.
3. **C4 cap tests for my 5 survivors:**
   - each cap exactly at its limit passes (N1);
   - a held position in the other side's bucket is not counted (N2);
   - a locked-in held position counts 0, never negative (N5);
   - a mixed NIFTY and BANKNIFTY position is refused (N17);
   - a 2-lot proposal is counted at its units (N19).

   N5, N17 and N19 are the loose direction. C4 is the independent gate, so its own tests must bite.
4. **P10's rule text.** Amend `docs/stories/P-publishing.md:318` to "`limit_max` = the books' `open_risk_cap_rs`
   (owner, 15 Oct 2026, 2 A)", and say that `limit_used` is the sum of open maximum losses once P10 publishes open
   trades. The dashboard owns the contract (owner, "contract A"), so tell the dashboard to change the description of
   `limit_used` ("C2's max_at_risk") and the 30000 examples.

## Minor

1. **Stray keys under `risk` are ignored.** A leftover `risk.max_open_trades: 3` at the top level starts C2 and C4
   silently (my run). It looks like a limit but nothing runs it. Refuse unknown keys under `risk`, as the profiles
   already do.
2. **C4 alone does not check value types.** C4 relies on C2's start-up check for malformed values. If C4 ever runs
   without C2 in the same process, a `rules` string becomes characters and no cap runs. Note it or add C4's own type
   check.
3. **"Signed" is a typed name.** Any session can commit a `restart_brake` row with `entered_by: owner`. The protection
   is process: `journal/` is lane 1 by path. A CI guard (an `owner_overrides.csv` change must match a
   `DESK_DECISIONS.md` row quoting the owner) is a separate story. The owner should know this.
4. **Dependency for owner 2 B (Rs 15 lakh top-up, story E1-topup):**
   - `PaperAccountSize` compares the opening row only, so a topped-up book would stay refused.
   - The top-up must count as capital, never as a closed-equity gain that raises the brake's high-water mark.
   - Write both into E1-topup's criteria.
5. **Brake per book.** Each book has its own Rs 20 lakh account and its own Rs 1.2 lakh brake. That is consistent with
   the design (one account per book), but the owner's row says "the account". Confirm the reading is per book.

## Project rules

- Files within 350 lines (the size test passes).
- New rules behind `RiskRule` and `MarginAge`. Wiring in `fno/risk/wiring.py` (a `RULES` table), `fno/checks/wiring.py`
  and `fno/composition.py`. Constants (`BUCKET_*`, `RISK_PROFILE_*`) live in `fno/constants.py`.
- C4 keeps its independence test.
- No orders, secrets, Slack posts or edits to S1's text.

**Verdict: FAIL for f4f2e35258a2fe647b1222f2a858f3c10e41bb12** on should-fixes 1-4. Everything else on C2's side is
correct and well tested. I re-judge on the addendum SHA, which also carries the owner's 1 B, 3 A, 4 A and 5 A.
