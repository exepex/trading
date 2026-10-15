# Response 163: story RM1, the real-money gate (story text, draft gate and the owner's questions)

Builder session: session_01CHxE3ywfyCMxFLx6HGLwRo · Orchestrator: session_01VG1RqxLFUVdvvPuMRYZtDH · Branch:
`story/rm1-real-money-gate` · Issue #107 · Lane 1, JUDGE.md rule 9 (judge, then ChatGPT, then the owner).

Files: `docs/stories/RM-real-money.md` (story text), `research/evaluation/REAL_MONEY_GATE.md` (draft gate),
`docs/WORK_REGISTER.md` (row). No code. Nothing here places or enables any order.

## 1. Claims for the judge's story check

| # | Claim | Evidence |
|---|---|---|
| 1 | Every 8.3 condition (1-7) and 8.4 element has one gate item with an exact rule (table in section 2) | strong evidence (read side by side) |
| 2 | No decided owner number is changed: Rs 20,000 stop, pad + Rs 0.50, 2× pad over 5 trades, 1 lot, 6 months, R = 60 fills, 31.2% tax, prediction interval, condition 5 always | strong evidence |
| 3 | Reusing S1's freeze (one more `frozen_files` entry, the freezer refusing an undecided gate) meets "frozen and hashed before the first counted paper decision" without a second freeze tool, because S1's `order` check already proves the freeze precedes each book's first counted decision | some evidence (read of `fno/evaluation/freeze.py`, `order.py`; not yet tested) |
| 4 | Judge 158's open point (several books' `beats_index_after_tax`) is answered: the gate reads one record, Book 1's (shadow records are shown, never counted; judge 171 SF1) | reasoning only |
| 5 | Condition 6's fact: at NIFTY lot 65, a Rs 5,000 cap allows about 76 points of maximum loss per unit; a single bought ATM monthly option usually costs more, so mainly spreads fit | some evidence (lot from `config.yaml`; premium from general market levels, not measured here) |

## 2. Trace: source → gate item

| Source | Gate item |
|---|---|
| 8.3 c1 (S1 lower bound, whole-period net, registered sample) | `paper_evidence` |
| 8.3 c2, decision 168 | `index_benchmark` |
| 8.3 c3, principle 4 (2020 and 2024 crashes) | `loss_caps` |
| 8.3 c4 | `fill_honesty` |
| 8.3 c5, decision 8 amended | `selection_adjustment` |
| 8.3 c6 | `real_cap_fit` |
| 8.3 c7 | `owner_approval` |
| 8.4 account, cap, 1 lot | `real_test_account` |
| 8.4 duration | `real_test_sample` |
| 8.4 paired test, prediction interval, slippage pad + Rs 0.50 | `real_test_pass` |
| 8.4 Rs 20,000 stop, 2× pad over 5 trades | `real_test_stops` |
| hard line; scaling and automation decisions | `scope` |

## 3. Questions for the owner (through the orchestrator; none answered by the builder)

Background: decision 8 says the account size and cap are confirmed in writing before RM1 freezes. The other
questions are gaps 8.3 and 8.4 leave open; each needs an exact rule before the freeze (ChatGPT review 98).

| Q | Question | Options | Recommendation (label) |
|---|---|---|---|
| Q1 | Real account size | (a) Rs 2,00,000; (b) Rs 1,50,000; (c) Rs 3,00,000 | (a), as 8.4 (reasoning only) |
| Q2 | Per-trade cap, all charges included | (a) Rs 5,000 (2.5%); (b) Rs 4,000 (2%) | (a): at lot 65, Rs 4,000 leaves about 61 points per unit and fewer spreads fit; the Rs 20,000 stop is then 4 full losses (some evidence) |
| Q3 | 8.4 already fixes the test length: the version's registered number of trades or 6 months, whichever is later. Only the floor is asked: the minimum number of real trades when a registration names fewer | (a) 20; (b) 30; (c) no floor (the registered number alone) | (a) 20, S1's paper gate; honest: even 20 finds only a large shortfall (some evidence) |
| Q4 | Condition 5 default route | (a) second untouched forward period; (b) level 0.05 ÷ trial count; (c) each registration chooses, no default | (a): cleaner; (b) at 50 ideas needs a 99.9% bound set by about 10 resamples (some evidence) |
| Q5 | Prediction interval side | (a) one-sided 95% lower; (b) two-sided 95% | (a): only real underperformance should fail (reasoning only) |
| Q6 | t-based lower bound for real money | (a) a pass condition here (both bounds above zero); (b) a warning only, as on scoreboards (decision 167) | (a): stricter only; few skewed positions make the bootstrap claim too often (some evidence) |
| Q7 | Crash-replay cap | (a) the real cap at 1 lot; (b) the paper cap Rs 10,000 | (a): the replay asks whether the real trade would have broken its cap (reasoning only) |
| Q8 | Discipline: minimum share of cards the owner places | (a) 80%; (b) 90%; (c) none, report only | (a) (reasoning only) |
| Q9 | Rs 20,000 stop measured from | (a) cumulative net from the first real entry; (b) peak to trough | (a): simplest and stricter early; (b) stops later after early gains are given back (reasoning only) |
| Q10 | May S1's owner-decided `frozen_files` list add the gate file and `fno/evaluation/gate.py`? | (a) yes, one freeze; (b) no, a separate gate freeze record and command | (a): one freeze, one order check, no duplicate tool (some evidence) |
| Q11 | Paired-net margin (`real_test_pass` 1): the one-sided 95% lower bound of mean(real net − paper net) per trade, 1 lot, charges included, must be at or above | (a) −Rs 500 (ChatGPT's proposal); (b) −Rs 1,000; (c) Rs 0 (real no worse than paper at all) | (a) −Rs 500 (reasoning only). Honest: with 20 trades and a paired SD near Rs 1,000, the bound sits about Rs 390 below the mean, so real must average within about Rs 110 of paper; (c) would almost always fail on noise alone (some evidence: arithmetic on an assumed SD; the real SD is unknown until trades exist) |
| Q12 | Quote-age limit and source for a "valid quote" (execution slippage, fill honesty, cap fit). Also: share of real legs with unknown slippage that fails the test | Source: (a) the owner notes Groww's bid and ask at each real order (screenshot to Drive), A16 within the limit as fallback; (b) recorders only. Age: (i) 15 minutes (always one A16 snapshot); (ii) 5 minutes. Unknown share: 10% | (a) with (ii) 5 minutes for real orders, (i) 15 minutes for recorder-only uses; unknown share 10% (reasoning only). The owner's own note is the only quote truly at the order moment |
| Q13 | Fill honesty's independent check when fewer than 20 paper legs have a quote from a second recorder at fill time | (a) condition 4 rests on (a) quote validity alone and reports the independent check as "unknown"; (b) strict: not met until 20 independent legs exist; (c) build a second recorder later and wait | (a): E8 fills at about 10:15 next session from A16 and no second recorder runs then, so (b) would block every version indefinitely, while `real_test_pass` 3 measures the real execution cost anyway (some evidence) |

## 4. Coordination

- Work register: no row covered RM1 (read on main at 35e999af). Overlap to agree: S6 (builder 0185gR5DmoDh2zBAvgRU4CEB)
  will later change `PROTOCOL.md` and `fno/evaluation/protocol.py`; RM1's code changes `completeness.py`,
  `freeze.py`, `cli.py` and one line of `PROTOCOL.md`'s `frozen_files`. Different lines; order of merging to be set by
  the orchestrator.
- Next: judge story check → ChatGPT (rule 9) → the owner's answers to Q1-Q10 → code.

## 5. Judge 171 (FAIL, 3 should-fix, no blocking): all three accepted, fixed at the commit after d29934f5

| Finding | Check | Fix |
|---|---|---|
| SF1 evidence not tied to the freeze; shadows outside the order check | Agreed (strong evidence): `order.py` checks only book D3 runs; a shadow decision is never in a book, and Book 1 pilot positions predate the freeze. My claim 3 held for books only | Terms: evidence = Book 1 positions whose decision commit has the gate's freeze as a strict ancestor; pilot and shadow positions shown, never counted; Known limit added. I chose "Book 1 only" over extending the order check: simpler, and promoted shadow ideas reach paper anyway |
| SF2 slippage has no reference price | Agreed (strong evidence): `fno/desk/execution.py:52` keeps price and pad apart; "paper fill" with the pad would allow about 2 × pad + Rs 0.50 | New term "paper price before pad"; `real_test_pass` 2 and `real_test_stops` (b) measure from it, worse positive, as `fill_honesty` does |
| SF3 fixed 20 replaced 8.4's registered number | Agreed (strong evidence): 8.4 and decision 8 say "its registered number of trades or 6 months, whichever is later" | max(20, registered number) or 6 months, the later; Q3 now asks only the floor and states 8.4's rule |
| Note: status and evidence fields with extra text; no version line | Agreed: the draft now parses with today's `parse_protocol` and all 12 items carry the exact status and bare labels (checked by script); the version line is exempted by a `require_version` parameter in the code round | Question references moved to Reason lines |
| Note: A16 covers only nearest weekly and monthly expiries | Agreed | Stated in `fill_honesty` and Known limits; the owner sees it with the questions |
| Note: `real_cap_fit` source | Agreed | Names the 3 pm recorder (A4, `research/data/quotes/`) at S1's timetable capture time |

## 6. ChatGPT review 118 (PARTIAL): changes made at the commit after f8cbbc6c

The orchestrator answers review 118 in response 171; these are the builder's checks and edits.

| Point | Builder's check | Edit |
|---|---|---|
| Slippage mixes market timing with execution | Agreed (strong evidence): E8's 60-minute fill lands about 10:15 next session (`docs/stories/G-forecasts.md:541`) | New terms "valid quote" and "execution slippage" (owner's order time); real-minus-paper reported as the timing gap |
| Paired test must bind | Agreed (strong evidence): 8.4 says "paired"; the draft judged only the unpaired bound | `real_test_pass` 1 binding paired bound with margin Q11; the prediction bound kept as floor 2 |
| Cap fit on arbitrary days | Agreed (strong evidence) | Last 20 eligible opportunities with their own contracts; plus the next proposed trade |
| Fill honesty against a later snapshot | Partly agreed: a later move is no proof, but the fill's own snapshot is circular. And an independent quote at fill time rarely exists (E8 at ~10:15 from A16; 3 pm recorder near 14:30-14:55) | Split into (a) validity and (b) independent check; the shortfall goes to the owner as Q13 rather than a gate that can never pass |
| Wording (model-based bound, Bonferroni, settlement proxy) | Agreed | Done; the replay adds C1 charges and the pad. Also corrected 76.9 points as "before charges" |

## 7. The owner's answers (15 Oct 2026, relayed by the orchestrator) and what is still open

Written into the gate: Q1 Rs 2 lakh; Q2 Rs 5,000; Q3 max(30, registered) trades and 6 months; Q4 route (a) second
untouched period; Q5 one-sided 95%; Q6 bootstrap and t bounds both binding; Q7 replay cap Rs 5,000 at 1 lot; Q8 90%
of eligible cards, every skip with its paper net; Q9 both stops (−Rs 20,000 cumulative and Rs 20,000 peak to
trough); Q10 one S1 freeze; Q11 paired bound at or above −Rs 500 per trade; Q12 quote age at most 5 minutes, none
means unknown.

Not yet answered, so every item's status stays "proposal, owner decides" until they are:
1. **Q12, source.** With recorders only, A16's snapshots are 15 minutes apart, so about two in three real orders
   have no recorder quote within 5 minutes and their slippage is unknown; under the 10% unknown-leg limit the test
   would fail on missing data, not on execution (some evidence: arithmetic on the 15-minute grid). The owner noting
   Groww's bid and ask at each order (screenshot to Drive) avoids that. Which source?
2. **Q12, unknown-leg limit:** 10% as proposed?
3. **Q13:** fill honesty's independent check when fewer than 20 paper legs have a second recorder's quote.
4. **Q4 scope:** is route (a) the only route, or the default with route (b) still allowed when a registration names
   it before its first counted entry?
5. **The unnumbered parts** (scope, the evidence-record definition, `index_benchmark`, the replay windows, the cap-fit
   rule, `owner_approval`): does the owner accept them as a set?

Answered later on 15 Oct (relayed): Q12 source (the owner's Groww screenshot at each real order, saved to Drive,
A16 as fallback; 5 minutes for real orders, 15 for recorder-only uses; more than 10% unknown legs is not met) and
Q13 (a) (validity binding, independent check reported). Depth was added to a valid quote at the owner's word
("fresh, two-sided, depth"); A16 keeps Groww's bid and offer quantities in its raw answer (`fno/providers/groww.py:83`).
Still open: point 4 (Q4 scope) and point 5 (the unnumbered parts as a set).

**All answered (15 Oct 2026):** Q4 the second untouched period is the only route (route (b) removed), and the
unnumbered parts accepted as a set (row 793aeb54). Every gate item's status is now "decided by the owner on
2026-10-15", citing rows 946bb8e7, f0f6d2d8 and 793aeb54.

## 8. Judge 171 addendum 2 (FAIL, 2 should-fix): both fixed; one new question

- SF1: `real_test_pass` 3 now says unknown legs (10% or fewer) are left out of the mean and listed; more than 10% is
  not met.
- SF2: Q13 was re-asked with the missing option; the owner kept 8.3 condition 4 as written (row 22df15bf). `fill_honesty`
  (b) is now the binding mean gap to the next A16 snapshot within the paper pad, its noise stated; the validity check
  stays; the "reported only" independent check is removed.
- Note: the prediction floor is Rs 2,734 (1.7291 × 5,000 × √0.1); my Rs 2,160 was wrong.
- **New, open (Q14), strong evidence from the code:** `FILL_PAD_RS = 0.0` (`fno/desk/pricing.py:17`): the desk fills
  at the touch and research uses a Rs 1 per unit pad (`fno/research_engine/cycle_costs.py:24`). The gate's "paper
  pad" is therefore Rs 0 today, which makes `real_test_pass` 3 allow Rs 0.50, makes stop (b) fire on any adverse
  5-trade average, and makes `fill_honesty` (b) a "mean gap at most Rs 0" test that 15 minutes of noise fails about
  half the time. Options to the owner: (a) the research pad, Rs 1 per unit; (b) the desk pad in force (Rs 0 today);
  (c) a figure the owner names. Recommendation (a), reasoning only.

**Q13 and Q14 answered (15 Oct 2026, row 162d8fbf):** Q13 re-asked neutrally with option (d), 8.3 as written, and its
noise-aware form; the owner kept 8.3 (row 22df15bf) made noise-aware: not met only when the one-sided 95% lower bound
of the mean gap to the next A16 snapshot exceeds the pad. Q14: the gate's paper pad is research's Rs 1 per unit, so
execution slippage may average up to Rs 1.50 per unit and stop (b) fires above Rs 2 per unit over 5 trades. Every
item is decided.

## 9. Code round (orchestrator's go after judge 171 addendum 4 PASS)

**What changed:** `fno/evaluation/gate.py` (new, 36 lines: `GATE_FILE`, the 12 `GATE_ITEMS`, `gate_problems`);
`completeness.py` (`completeness_problems` takes `required` and `versioned`, defaults unchanged for S1); `freeze.py`
(`_require_gate`: the freeze refuses unless `frozen_files` lists the gate and the gate is complete and decided);
`cli.py` (`check` prints the gate's line and fails on it); `tests/evaluation/builders.py` (the temporary repository
holds and lists the committed gate); `tests/evaluation/test_freeze.py` (the exact hash set now includes the gate);
`tests/evaluation/test_real_money_gate.py` (new, 16 tests). Judge A's note 1 is in the gate text: fill honesty's
bound uses one gap per position; note 2 is in the story as a note for RM2.

| # | Claim | Evidence |
|---|---|---|
| C1 | The committed gate is complete and decided; `python -m fno evaluation check` prints both documents and exits 0; `check --decided` fails only on S1's 13 undecided items | strong evidence (run output) |
| C2 | The freeze refuses an undecided gate (no record, ledger unchanged), an unlisted gate, a missing gate and an uncommitted gate edit; a decided gate is hashed in `FREEZE_v1.md` and a later edit shows in `verify` | strong evidence (tests) |
| C3 | Broken-code proofs (each mutation run against `tests/evaluation`, then restored): no gate check in the freeze, 2 fail; undecided ignored, 3 fail; version line always required, 27 fail; `check` ignoring the gate, 1 fails; no required gate items, 29 fail. Restored: 60 pass | strong evidence |
| C4 | `fno/evaluation/` imports no provider, desk, book, broker, Groww or order module (AST test) | strong evidence |
| C5 | The real repository's S1 freeze now refuses until S1's text owner adds the gate to `frozen_files` (owner Q10 = yes); that is the intended link, not a failure | strong evidence (run: the freeze names the 13 undecided protocol items first; the gate check runs after) |
| C6 | No file over 350 lines: `freeze.py` 189, `cli.py` 111, `gate.py` 36, the new test 137 | strong evidence |

Open for S1's text owner (session 0185gR5D): the `frozen_files` line (`research/evaluation/REAL_MONEY_GATE.md`,
`fno/evaluation/gate.py`), now allowed by the owner's Q10.

**`frozen_files` line, in this branch (S1 text owner, session 0185gR5D, approved the wording):** the Files list adds
`research/evaluation/REAL_MONEY_GATE.md` and `fno/evaluation/gate.py`, and the Reason gains the RM1 bullet. One part of
the proposed wording was not taken, with the reason: appending "(gate files added on 2026-10-15, RM1 Q10)" to the
Status line would fail S1's own check, which accepts only "decided by the owner on YYYY-MM-DD" exactly
(`fno/evaluation/protocol.py`, `DECIDED`); the date is in the Reason instead. A test guards that the real protocol
lists both gate files.
