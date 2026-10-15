# Response 105: story C5, risk buckets and the Rs 20 lakh paper account (claims for the judge)

Builder: Claude, 15 Oct 2026. Branch `story/c5-risk-buckets` (lane 1: money and risk). Story text:
`docs/stories/C-code-roles.md` section C5. Not merged; G6 not used. Owner decisions used: 14 Oct (Rs 20 lakh, Rs 10,000
a trade), 15 Oct (caps and brake; "1 A" and "2 A"), 13 Oct (Manual account), all quoted in the story text.

## What changed

- **Risk profiles** (`config.yaml` `risk.profiles`): `books` and `manual`. Each lists the rules it runs and holds
  exactly their settings; any problem in any profile stops start-up (`fno/risk/profile_settings.py`).
  - Books: paper account Rs 20,00,000, Rs 10,000 a trade, bucket Rs 30,000, open risk Rs 1,50,000, new risk Rs 50,000 a
    session, brake Rs 1,20,000, margins at most one session old. No flat 3-trade, stress or exposure limit.
  - Manual: its 13 Oct limits unchanged (Rs 5 lakh, Rs 10,000, 3 open, Rs 30,000 brake, C2's stress and exposure, 7-day
    margins).
- **C2:** four new rules behind `RiskRule` (`paper_account`, `bucket_cap`, `open_risk_cap`, `new_risk_per_day`),
  each summing B2 maximum losses and only refusing. The composition root builds a profile's rules from a `RULES` table.
- **C4:** recomputes the same profile's rules with its own arithmetic (`fno/checks/validity_caps.py`); the 3-open,
  stress and exposure checks run for the Manual profile only.
- **E1** opens new accounts with the books' `paper_account_rs` (the Rs 5 lakh constant is gone).
- **Margin age:** a strategy, calendar days (Manual) or NSE sessions (books, design 6.1a), in C2 and C4.
- **Open trades carry their first-fill day** (`opened_on`) through the ledger, D2's same-session entries and D3's codec.
- **The daily stress line** is a computed record, not a limit (`build_stress_line`).

## Gap list: design 6.1-6.3 and the C5 paragraph, each mapped

| Requirement (source) | Where | Criterion or reason out |
|---|---|---|
| Paper account Rs 20 lakh (6.1) | `config.yaml:49` books; `fno/risk/caps.py:87`; `fno/composition.py` | 7 |
| Rs 10,000 max loss per trade, charges included (6.1) | C2's `MaxLossPerTrade`, books profile | 10 (unchanged rule, new profile) |
| Worst loss fixed at entry; never unprotected selling (6.1) | `fno/risk/open_risk.py:36` refuses a net short tail | 6 (C4 shape checks already refuse naked shorts) |
| Stressed margin multiplier 1.45, funds at entry (6.1) | C2's `MarginRoom`, unchanged | out: unchanged by C5 |
| Strategy pauses Rs 30,000 cumulative (6.1) | E6 | out: E6's rule, not an account cap |
| Four kinds of loss; caps count kind 1 (6.1a) | `HeldMaxLoss` = B2's terminal loss plus charges | 6; kinds 2-4 out (8.4, E7) |
| Fail closed: margin older than one session (6.1a) | `fno/risk/margin_age.py:38`; `fno/checks/validity_settings.py:35` | 12 |
| Fail closed: unmapped bucket (6.1a) | `fno/risk/buckets.py:45`; `fno/checks/validity_caps.py:45` | 5 |
| Fail closed: missing margin row (6.1a) | C2 `MarginTable`, C4 `stressed_per_lot`, unchanged | existing C2/C4 tests |
| Bucket mapping frozen with C5 (6.1a) | `config.yaml` `risk` is in S1's `frozen_files` settings | reasoning: S1 hashes `config.yaml:risk` |
| Bucket = underlying group and side (6.2) | `fno/risk/buckets.py` | 5; stocks and results week out (A6/A12, A18) |
| Bucket cap Rs 30,000 (6.2) | `fno/risk/caps.py:69` | 1 |
| Account cap Rs 1.5 lakh, a cap on entries, not a stop (6.2) | `fno/risk/caps.py:75` | 2, 4 |
| New risk Rs 50,000 a session (6.2) | `fno/risk/caps.py:81` | 3 |
| Drawdown brake Rs 1.2 lakh, owner restart in writing (6.2) | `config.yaml` books; C2 `drawdown.py`, `overrides.py` | 8 |
| Weather RED: no new trades (6.2) | weather layer | out: M1/T1, not a C5 cap |
| Daily stress line on every card (6.2) | `fno/risk/stress_line.py:51` | 9; showing it on the card is T1 |
| Effective sample: distinct buckets-and-weeks (6.2) | scoreboard | out: S2/S3 reporting; `Bucket` gives them the key |
| Overnight holding allowed; events calendar (6.3) | strategy and E7 rules | out: not account caps |
| Physical settlement of stock options (6.3) | C4 | out: no stock options yet (A18) |
| "Config through fno/config.py" (C5 paragraph) | `risk` is an allowed key; profiles checked at start-up | 10 |
| Books drop 3-open, stress, exposure; Manual unchanged ("1 A", "2 A") | profiles | 10, 11, 13 |
| C4 in step (judge C) | `fno/checks/validity_caps.py`, `validity_limits.py` | 13 |

## Claims (acceptance criteria)

| # | Criterion | Code | Test | Evidence |
|---|---|---|---|---|
| 1 | Bucket cap at Rs 30,000 passes, Rs 0.01 over refused, other buckets not counted | `fno/risk/caps.py:22`, `:35`, `:69` | `tests/risk/test_caps.py:46`, `:53`, `:99` (real wiring) | strong evidence |
| 2 | Open-risk cap at Rs 1,50,000 across buckets | `fno/risk/caps.py:75` | `tests/risk/test_caps.py:60` | strong evidence |
| 3 | New risk per day at Rs 50,000; earliest fill day; same-session choices count; unknown day refused | `fno/risk/caps.py:63`, `:81`; `fno/risk/book_view.py:36`; `fno/playbook/book_effects.py`; `fno/playbook/decision_codec.py` | `tests/risk/test_caps.py:68`, `:75`; `tests/risk/test_c5_account.py:210` | strong evidence |
| 4 | A cap only refuses; same proposal, lots unchanged | `fno/risk/caps.py:35` | `tests/risk/test_caps.py:90` | strong evidence |
| 5 | Buckets as 6.2; unmapped refused | `fno/risk/buckets.py:37`, `:45`; `config.yaml` `bucket_sides` | `tests/risk/test_buckets.py:40`, `:52`, `:56`, `:69`, `:75` | strong evidence (code); reasoning only for the SF/SC/BF sides (question 1) |
| 6 | Held maximum loss = B2's; net short tail refused; locked-in counts 0 | `fno/risk/open_risk.py:36`, `:60` | `tests/risk/test_buckets.py:90`, `:99`, `:106`; reviewer's 3,000 random positions agree exactly | strong evidence |
| 7 | New accounts open with Rs 20 lakh; any other opening refused | `fno/books/account.py`, `fno/composition.py`, `fno/risk/caps.py:87` | `tests/books/test_paper_account.py`; `tests/risk/test_caps.py:82`; `tests/risk/test_c5_account.py:144` | strong evidence |
| 8 | Brake at Rs 1,20,000; only a signed restart row lifts it | `config.yaml` books; C2's `drawdown.py`, `overrides.py` | `tests/risk/test_c5_account.py:156`, `:184` | strong evidence |
| 9 | Daily stress line, five scenarios, below the sum of maximum losses | `fno/risk/stress_line.py:51`; `config.yaml:97` | `tests/risk/test_c5_account.py:194` | some evidence (one structure checked; the bound holds by no-arbitrage for balanced structures, reasoning only beyond) |
| 10 | Books run exactly their rules; any setting problem in any profile stops start-up | `fno/risk/profile_settings.py:60`, `:71`, `:108`; `fno/risk/wiring.py:90` | `tests/risk/test_c5_account.py:44`, `:93`, `:98`, `:118`, `:125`, `:225` | strong evidence |
| 11 | Manual keeps its 13 Oct limits, runs exactly those rules | `config.yaml:64` | `tests/risk/test_c5_account.py:60`; `tests/risk/test_settings.py` | strong evidence |
| 12 | Books' margin older than one session refused; weekends and holidays never age a row | `fno/risk/margin_age.py:38`; `fno/checks/validity_settings.py:35` | `tests/risk/test_margin_age.py:28`, `:37`; `tests/checks/test_validity_caps.py:107` | strong evidence |
| 13 | C4 in step: own caps, books without old checks, breach C2 allowed refused, 4 open pass books and fail Manual, C4 max loss = C2's, C4 refuses to start on a missing setting | `fno/checks/validity_caps.py`, `validity_limits.py:58`, `validity_settings.py:129` | `tests/checks/test_validity_caps.py:50`, `:57`, `:66`, `:78`, `:85`, `:92`, `:102`, `:117`, `:132`, `:139` | strong evidence |

## Margin freshness: how C5 differs from C4's 7-day lookback (judge C, point a)

- **Books (C5, design 6.1a):** a margin row is usable only if dated on or after the previous NSE session (the day's
  own row or the previous session's), counted on A7's session calendar. A row from two sessions back is refused even
  if it is two calendar days old; Friday's row is fine on Monday; 20 Oct 2026 (holiday) is skipped. A day the calendar
  cannot answer refuses (C2: `CalendarError` is a `ValueError`, refused by the manager; C4: `fresh` returns False).
- **Manual (C2/C4 as before):** at most 7 calendar days.
- **Fit with A14:** A14 writes each session's rows from NSE's first file of the day (before 09:00 IST), so at 15:00 the
  day's own row normally exists. Today `research/data/margins/margins.csv` has no data rows at all, so every trade is
  refused for this reason too until A14 writes rows.

## Self-review by two independent review agents (owner's step 2)

Both read the diff only, verified claims with snippets, made no edits.

| Finding | Verdict | Action |
|---|---|---|
| Held maximum loss C2 vs C4 vs B2 | No bug: 3,000 random 2-4 leg positions, plus unequal units, agree exactly | none |
| Cap boundaries, brake, opened_on paths, margin session counting | No bug found | none |
| C4 crashes (TypeError) instead of refusing when a profile setting is missing | Accepted: verified | fixed: C4 checks its own settings at start-up (`fno/checks/validity_settings.py:129`); test `tests/checks/test_validity_caps.py:132` |
| C4 margin check lets a `CalendarError` through | Accepted (reasoning only, unreachable today) | fixed: `fresh` fails closed; test `:139` |
| Manual profile never read at runtime, so a wrong value passes silently | Accepted: verified | fixed: `all_profiles` checks every profile when any risk manager is built; test `tests/risk/test_c5_account.py:225` |
| Refusal text named `risk.caps.bucket_sides` | Accepted | fixed |
| C4 took the first ledger row as first-fill day, C2 the minimum | Accepted (reasoning only; the ledger is append-only) | fixed: C4 takes the minimum too |
| C4 needs a two-sided quote for a held leg's strike; C2 accepts a stale mark | Partly accepted: true; C4's existing `margin_room` already needs the same mid, so C4 already refuses such a book. Kept: C4 is the stricter check and fails closed | known limit 6 |
| Stress line not shown anywhere | True; showing it is T1's scope (6.2 "every card shows") | out of scope, stated |
| Same-session exits make room for more new risk | True, C2 and C4 agree | known limit 3, question 3 |
| All three books refused (opened at Rs 5 lakh) | True, intended | question 2 |

## Each criterion broken on purpose (owner's step 3)

Each line is one deliberate change, the test run, and its result; every file was restored after its run. Script:
`/tmp/.../scratchpad/mutate.py` (outside the repository), run with `PYTHONDONTWRITEBYTECODE=1`. **Found while doing
this:** without that flag, a mutation restored within the same second, at the same file size, left a stale `.pyc`, so
the restored code ran the mutated bytecode. The first run's results were thrown away and all were re-run with bytecode
writing off. One mutation was missed in the first run (first-fill day max instead of min); the test now has a second,
later fill and catches it.

| Criterion broken | File | Test run | Result |
|---|---|---|---|
| 1 bucket cap boundary | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 2 passed in 0.14s |
| 1 bucket selector | `fno/risk/caps.py` | `test_caps.py::test_another_bucket_does_not_count_against_this_one` | caught: 1 failed in 0.12s |
| 2 open-risk counts all | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 5 passed in 0.12s |
| 3 new risk counts only today | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 8 passed in 0.13s |
| 3 unknown first-fill day | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 11 passed in 0.12s |
| 3 ledger first-fill day | `fno/risk/book_view.py` | `test_c5_account.py` | caught: 1 failed, 25 passed in 0.60s |
| 3 same-session entry day | `fno/playbook/book_effects.py` | `test_c5_account.py` | caught: 1 failed, 25 passed in 0.61s |
| 4 cap never resizes (proposal kept) | `fno/risk/manager.py` | `test_caps.py` | caught: 1 failed, 15 passed in 0.12s |
| 5 index groups only | `fno/risk/buckets.py` | `test_buckets.py` | caught: 1 failed, 8 passed in 0.14s |
| 5 unlisted structure refused | `fno/risk/buckets.py` | `test_buckets.py` | caught: 1 failed, 7 passed in 0.12s |
| 6 held max loss exit pads | `fno/risk/open_risk.py` | `test_buckets.py` | caught: 1 failed, 12 passed in 0.29s |
| 6 net short tail refused | `fno/risk/open_risk.py` | `test_buckets.py` | caught: 1 failed, 15 passed in 0.22s |
| 7 paper account exact | `fno/risk/caps.py` | `test_caps.py` | caught: 1 failed, 13 passed in 0.15s |
| 7 E1 opens at books size | `fno/composition.py` | `test_paper_account.py` | caught: 1 failed in 0.35s |
| 8 brake amount | `config.yaml` | `test_c5_account.py` | caught: 1 failed in 0.35s |
| 8 restart needs signature | `fno/risk/overrides.py` | `test_c5_account.py` | caught: 1 failed, 23 passed in 0.54s |
| 9 stress line max-loss sum | `fno/risk/stress_line.py` | `test_c5_account.py` | caught: 1 failed, 24 passed in 0.59s |
| 10 unused setting refused | `fno/risk/profile_settings.py` | `test_c5_account.py` | caught: 1 failed, 14 passed in 0.34s |
| 10 every profile checked | `fno/risk/wiring.py` | `test_c5_account.py` | caught: 1 failed, 26 passed in 0.69s |
| 11 Manual unchanged | `config.yaml` | `test_c5_account.py` | caught: 1 failed, 1 passed in 0.33s |
| 12 margin one session (C2) | `fno/risk/margin_age.py` | `test_margin_age.py` | caught: 1 failed, 2 passed in 0.15s |
| 13 C4 bucket breach | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 2 passed in 0.37s |
| 13 C4 new risk today | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 4 passed in 0.37s |
| 13 C4 old 3-trade check off for books | `fno/checks/validity_limits.py` | `test_validity_caps.py` | caught: 1 failed in 0.17s |
| 13 C4 paper account | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 7 passed in 0.55s |
| 13 C4 held max loss | `fno/checks/validity_caps.py` | `test_validity_caps.py` | caught: 1 failed, 2 passed in 0.27s |
| 13 C4 margin one session | `fno/checks/validity_settings.py` | `test_validity_caps.py` | caught: 1 failed, 9 passed in 0.66s |
| 13 C4 checks its own settings | `fno/checks/validity_settings.py` | `test_validity_caps.py` | caught: 1 failed, 12 passed in 0.62s |

## Sample of real output (owner's step 4)

The app's wired books risk manager (`build_risk_manager(config.yaml)`) on a temporary account, synthetic prices (not a
live chain), margin rows dated the previous session. Each refusal names its rule; the brake engages after a closed loss
of about Rs 1.24 lakh and lifts after a signed `restart_brake` row.

```text

== empty Rs 20 lakh book, one 1-lot short fly: OPEN
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00
  (this trade's B2 maximum loss: Rs 3,354.54)

== 8 flies already open (opened 9 Oct) in NIFTY/short_volatility, one more: REFUSED
  bucket_cap: REFUSED - bucket NIFTY/short_volatility: maximum losses Rs 30,190.88 with this trade's Rs 3,354.54 are above the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 30,190.88 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00
  (a 1-lot long fly: Rs 11,133.40)

== 5 long-vol trades opened TODAY, one more short fly: REFUSED
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 59,021.53 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: REFUSED - trades opened this session: maximum losses Rs 59,021.53 with this trade's Rs 3,354.54 are above the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00

== 14 long-vol trades open since 9 Oct, one more short fly: REFUSED
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: REFUSED - all open positions: maximum losses Rs 159,222.12 with this trade's Rs 3,354.54 are above the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00

== closed loss of about Rs 1.24 lakh on 6 Oct (drawdown brake): REFUSED
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: REFUSED - closed equity Rs 1,876,381.76 is Rs 123,618.24 below its high Rs 2,000,000.00; new trades wait for the owner's restart

== after the owner's written restart row of 7 Oct: OPEN
  bucket_cap: ok - bucket NIFTY/short_volatility: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 30,000.00
  open_risk_cap: ok - all open positions: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 150,000.00
  new_risk_per_day: ok - trades opened this session: maximum losses Rs 3,354.54 with this trade's Rs 3,354.54 are within the cap Rs 50,000.00
  drawdown_brake: ok - drawdown Rs 0.00 is below the brake Rs 120,000.00
```

<details><summary>The script that produced it</summary>

```python
"""C5 sample output: the app's wired books manager (config.yaml) on a temporary account, synthetic prices."""
import sys, tempfile
from dataclasses import replace
from datetime import date, datetime, timedelta
from pathlib import Path
sys.path.insert(0, "/home/user/trading")
from fno.accounting.ledgers import Order
from fno.books.fills import Fill
from fno.composition import open_account_writer
from fno.config import load_app_config
from fno.constants import BOOK1_RULES, BOOKS, SIDE_BUY, SIDE_SELL
from fno.models import IST
from fno.risk.book_view import load_risk_book
from fno.risk.inputs import TradeTerms
from fno.risk.margins import MARGIN_COLUMNS
from fno.risk.overrides import OVERRIDE_COLUMNS, overrides_file
from fno.risk.wiring import build_risk_manager
from tests.risk.builders import CHARGES, FLY, LOT, contract, market, open_trade, proposal, short_fly

DAY = date(2026, 10, 14); EXPIRY = date(2026, 10, 27)
PRICES = {(25000, "CE"): 150.0, (25000, "PE"): 140.0, (25200, "CE"): 70.0, (24800, "PE"): 60.0}
root = Path(tempfile.mkdtemp())
(root / "margins.csv").write_text(",".join(MARGIN_COLUMNS) + "\nSF,200,9000,-10270,65000,sample,2026-10-13\nBF,200,3000,10270,65000,sample,2026-10-13\n")
cfg = load_app_config(overrides={"risk": {"margins": {"file": str(root / "margins.csv")},
                                           "stressed_margin": {"as_of": "2026-10-14"}}})
manager = build_risk_manager(cfg, root)
m = market(25000, PRICES, EXPIRY, day=DAY)
for b in BOOKS:
    with open_account_writer(b, root) as w:
        w.start(date(2026, 9, 1))
book = load_risk_book(root, BOOK1_RULES, m, {})

def show(title, decision):
    print(f"\n== {title}: {'OPEN' if decision.ok else 'REFUSED'}")
    for v in decision.verdicts:
        if not v.ok or v.rule in ("bucket_cap", "open_risk_cap", "new_risk_per_day", "drawdown_brake"):
            print(f"  {v.rule}: {'ok' if v.ok else 'REFUSED'} - {v.reason}")

new = lambda lots=1, tid="new": proposal(tid, FLY, 200, short_fly(25000, 200), EXPIRY, lots=lots)
one = manager.evaluate(new(), book, m)
show("empty Rs 20 lakh book, one 1-lot short fly", one)
loss = next(v for v in one.verdicts if v.rule == "max_loss_per_trade").numbers["max_loss_rs"]
print(f"  (this trade's B2 maximum loss: Rs {loss:,.2f})")
cash = one.entry_cash_rs
from fno.constants import STRUCTURE_LONG_IRON_FLY as LONG
long_fly = [(k, kind, -side) for k, kind, side in short_fly(25000, 200)]
long_cash = manager.costs.entry_cash_flow(proposal("l", LONG, 200, long_fly, EXPIRY), m)
def held(n, opened, structure=FLY):
    legs, flow = (long_fly, long_cash) if structure == LONG else (short_fly(25000, 200), cash)
    return tuple(replace(open_trade(f"h{i}", structure, 200, legs, EXPIRY, flow), opened_on=opened) for i in range(n))
older = DAY - timedelta(days=5)
n_bucket = int(30000 // loss)
show(f"{n_bucket} flies already open (opened 9 Oct) in NIFTY/short_volatility, one more", manager.evaluate(new(), replace(book, open_trades=held(n_bucket, older)), m))
long_loss = manager.evaluate(proposal("l", LONG, 200, long_fly, EXPIRY), book, m).verdicts[2].numbers["max_loss_rs"]
print(f"  (a 1-lot long fly: Rs {long_loss:,.2f})")
n_day = int((50000 - loss) // long_loss) + 1
mixed = held(n_day, DAY, LONG)
show(f"{n_day} long-vol trades opened TODAY, one more short fly", manager.evaluate(new(), replace(book, open_trades=mixed), m))
many = tuple(replace(t, trade_id=f"x{t.trade_id}") for t in held(int((150000 - loss) // long_loss) + 1, older, LONG))
show(f"{len(many)} long-vol trades open since 9 Oct, one more short fly", manager.evaluate(new(), replace(book, open_trades=many), m))

with open_account_writer(BOOK1_RULES, root) as w:
    when = lambda d: datetime(d.year, d.month, d.day, 15, 15, tzinfo=IST)
    c = contract(25000, "CE", EXPIRY)
    w.apply_fill(Fill.priced("f1", "loser", when(date(2026, 10, 5)), c, Order(SIDE_SELL, 100.0, LOT, 0.0), CHARGES))
    w.apply_fill(Fill.priced("f2", "loser", when(date(2026, 10, 6)), c, Order(SIDE_BUY, 2000.0, LOT, 0.0), CHARGES))
braked = load_risk_book(root, BOOK1_RULES, m, {})
show("closed loss of about Rs 1.24 lakh on 6 Oct (drawdown brake)", manager.evaluate(new(), braked, m))
overrides_file(root, BOOK1_RULES).write_text(",".join(OVERRIDE_COLUMNS) + "\n2026-10-07,restart_brake,reviewed the 6 Oct loss,owner\n")
show("after the owner's written restart row of 7 Oct", manager.evaluate(new(), load_risk_book(root, BOOK1_RULES, m, {}), m))
```
</details>

## Tests changed, and why (not weakened)

- C2's old limit tests (`tests/risk/test_settings.py`, `test_manager.py`) now test the Manual profile, which keeps
  them; the books' rule list is asserted exactly.
- C4's existing tests run on the Manual profile (its old checks, Rs 5 lakh fixtures); the books are in the new
  `tests/checks/test_validity_caps.py`.
- `tests/books/test_paper_account.py`: the committed books really were opened at Rs 5 lakh on 13 Oct; the test says so
  and asserts it differs from the books' account.
- `tests/risk/test_books.py`, `tests/checks/test_validity_limits.py`: brake cases at Rs 1,20,000.
- E4, E6, P10 tests: Rs 20 lakh cash; Home's `limit_max` is now the books' open-risk cap (Rs 1,50,000) instead of C2's
  stress limit, which the books no longer have.

## Known limits (said plainly)

1. **Every book trade is refused today**, by design: the books opened at Rs 5 lakh (question 2) and the margins file
   has no rows.
2. **Bucket side comes from the recorded structure code**, not from the legs; a wrong code in a decision record would
   put a position in the wrong bucket. C4 shape checks tie the code to the legs at entry.
3. **New risk per day counts only trades still open**: a trade opened and closed in the same session drops out.
4. **Open trades' maximum loss is recomputed from the ledger** and can rise after a partial exit (hand check: a short
   fly with its short call bought back holds a put spread with Rs 12,350 maximum loss against Rs 2,600 at entry). The
   caps count that real number. It needs a quote for every held contract (C2 accepts a stale mark).
5. **Records written before C5** have no `opened_on` and are refused by the new-risk cap on replay.
6. **C4 needs a two-sided quote** for every held leg (caps and margin room); C2 does not. C4 is the stricter, so a
   thinly quoted wing refuses the whole book's entries that day.
7. **VIX +50% is each leg's implied volatility x 1.5** (no smile change); "+5%" keeps volatility unchanged.
8. **S1's protocol text** (`catastrophic_loss_book`: "Rs 30,000") is not edited, as instructed.

## Questions for the owner (never decided by me)

1. **Bucket side of directional structures (STR1).** A put credit spread is both bullish and short volatility. (a)
   direction wins for verticals, volatility for flies and condors; (b) a position counts in two buckets. Until you
   choose, those codes are refused. SF/SC short volatility and BF long volatility is my reading of 6.2: say if not.
2. **The three books opened at Rs 5 lakh.** (a) reopen at Rs 20 lakh by replacing the 13 Oct opening rows (no fill has
   ever been made); (b) keep them and add a dated Rs 15 lakh top-up entry (a new E1 entry kind); (c) new book folders.
3. **Same-session exits and the Rs 50,000 a session**: should a trade opened and closed the same session still count?
   (Today it does not; reasoning only that it is rare in a once-a-day desk.)
4. **Stress line details:** "+5%" with volatility unchanged, and VIX moves as a factor on every leg: acceptable?
5. **Stocks:** confirm stock buckets wait for A18.

## What the judge should test hardest

- Each cap at its number and Rs 0.01 over with real B2 maximum losses, in C2 and in C4.
- `HeldMaxLoss` and C4's `held_max_loss` after partial exits and with unequal units.
- That a broken Manual profile, a missing books setting, or an unused setting stops start-up in both C2 and C4.
- That nothing in `fno/` sizes the books on Rs 5 lakh, and the committed Rs 5 lakh books are refused.
