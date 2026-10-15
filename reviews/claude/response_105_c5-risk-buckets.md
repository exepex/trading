# Response 105: story C5, risk buckets and the Rs 20 lakh paper account (claims for the judge)

Builder: Claude, 15 Oct 2026. Branch `story/c5-risk-buckets` (lane 1: money and risk). Story text:
`docs/stories/C-code-roles.md` section C5. Not merged; G6 not used.

## What changed, in one paragraph

C2 gains four rules (`paper_account`, `bucket_cap`, `open_risk_cap`, `new_risk_per_day`) behind the existing
`RiskRule` interface, all wired in `fno/risk/wiring.py`. The owner's numbers live in `config.yaml` `risk`
(`paper_account_rs` 20,00,000; `caps`: 30,000 / 1,50,000 / 50,000; `drawdown_brake_rs` 1,20,000). Each cap sums B2's
maximum losses (the open trades' from their ledger cash, the proposal's by B2's own model) and only refuses. E1 opens
new accounts with `risk.paper_account_rs` (the hard-coded Rs 5 lakh constant is gone). The daily stress line of 6.2 is
a computed record (`build_stress_line`), not a limit. Open trades now carry the day they opened (`OpenTrade.opened_on`).

## Claims (acceptance criteria)

| # | Criterion | Code | Test | Evidence |
|---|---|---|---|---|
| 1 | Bucket cap passes at exactly Rs 30,000, refuses at Rs 30,000.01, other buckets not counted | `fno/risk/caps.py:22` (`MaxLossCap.check` :35), `:69` | `tests/risk/test_caps.py:46`, `:53`, `:99` (real wiring, at and Rs 0.01 under the total) | strong evidence |
| 2 | Open-risk cap at Rs 1,50,000 across all buckets | `fno/risk/caps.py:75` | `tests/risk/test_caps.py:60` | strong evidence |
| 3 | New risk per day at Rs 50,000; earlier sessions not counted; unknown first-fill day refused | `fno/risk/caps.py:63`, `:81`; `fno/risk/book_view.py:36`; `fno/playbook/book_effects.py` (decision day); `fno/playbook/decision_codec.py:62`, `:79` | `tests/risk/test_caps.py:68`, `:75`; `tests/risk/test_c5_account.py:172` | strong evidence |
| 4 | A cap only refuses; the decision judges the same proposal, lots unchanged | `fno/risk/caps.py:35` (returns a verdict only) | `tests/risk/test_caps.py:90` | strong evidence |
| 5 | Buckets as 6.2: SF/SC NIFTY short volatility, BF NIFTY long volatility, BANKNIFTY its own group; unlisted structure, stock, other index, mixed underlyings refused as "unmapped bucket" | `fno/risk/buckets.py:37`, `:45`; `config.yaml:54` | `tests/risk/test_buckets.py:33`, `:45`, `:49`, `:62`, `:68` | strong evidence (code); reasoning only for the SF/SC/BF sides (see question 2) |
| 6 | A held trade's maximum loss equals B2's for the same entry; not-defined-risk held positions refused; locked-in counts 0 | `fno/risk/open_risk.py:36` (`max_loss` :60) | `tests/risk/test_buckets.py:83` (SF 1 and 3 lots, SC 2 lots, real charges, to 1e-6), `:92`, `:99` | strong evidence |
| 7 | New accounts open with Rs 20,00,000; any book opened otherwise refused (`paper_account`) | `fno/books/account.py:115`, `:129`; `fno/composition.py:113`, `:116`; `fno/risk/caps.py:87` | `tests/books/test_paper_account.py` (`test_a_new_account_opens_with_the_owners_paper_account_of_rs_20_lakh`); `tests/risk/test_caps.py:82`; `tests/risk/test_c5_account.py:106` | strong evidence |
| 8 | Brake at Rs 1,20,000 (Rs 0.01 less passes, at and beyond refuses); only a signed `restart_brake` row lifts it; an unsigned row makes the book unreadable | `config.yaml:46`; C2's `fno/risk/drawdown.py` and `fno/risk/overrides.py` unchanged | `tests/risk/test_c5_account.py:118`, `:146`; C2's `tests/risk/test_drawdown.py`, `tests/risk/test_books.py` (now at 1.2 lakh) | strong evidence |
| 9 | Daily stress line: the five 6.2 scenarios, loss from entry and from marks, below the sum of maximum losses, zero for an empty book | `fno/risk/stress_line.py:51`; `config.yaml:78` | `tests/risk/test_c5_account.py:156` | some evidence (one structure checked against the bound; the bound holds by no-arbitrage for balanced structures, reasoning only beyond that) |
| 10 | Every C5 number from `config.yaml` `risk`, no defaults, malformed is an error, repository holds the owner's numbers | `fno/risk/cap_settings.py:41` | `tests/risk/test_c5_account.py:39`, `:57`, `:75`; `tests/risk/test_caps.py:41` | strong evidence |
| 11 | No Rs 5 lakh size or Rs 30,000 brake left in `fno/`; E1's writer has no default cash; not-rescaled limits marked in `config.yaml` | `config.yaml:55`, `:85` | `tests/risk/test_c5_account.py:82`, `:97` | strong evidence (for `fno/`; the scan does not read docs or research folders) |

Gates on the pushed tree: see the orchestrator message (full suite, `ruff check fno tests tools`, `ruff format`,
`python tools/check_imports.py`).

## Tests changed, and why (not weakened)

- `tests/books/test_paper_account.py`: the committed books really were opened at Rs 5 lakh on 13 Oct; the test now says
  so and asserts that this differs from the configured account (so it is refused). Other E1 tests use the new size.
- `tests/risk/test_books.py`, `tests/checks/test_validity_limits.py`: the brake cases moved from Rs 30,000 to Rs 1,20,000
  (C4 reads the brake from `config.yaml` too, so C4 follows automatically).
- `tests/risk/test_manager.py`, `tests/playbook/test_evaluation_wiring.py`: the four new rule names; verdicts found by
  name, not by position.
- E4, E6 and P10 tests: Rs 5 lakh cash literals replaced by Rs 20 lakh; `BooksReader` now takes the account size.

## Known limits (said plainly)

1. **Every trade is refused today**, by design: the three books in `journal/` opened at Rs 5 lakh on 13 Oct, and the
   paper-account rule refuses them until the owner decides how to reopen them (question 4). No strategy is approved
   to paper yet, so nothing is lost now.
2. **C2's Rs 5 lakh-era limits still run unchanged** (question 1): `max_open_trades` 3, `max_stress_loss_rs` 30,000,
   exposure Rs 15,000 each. They are stricter than the new caps, so they can only refuse more; but while
   `max_open_trades` is 3, at most Rs 30,000 can ever be at risk and the Rs 1.5 lakh cap never binds. Home's
   "limit used / max" (P10) still shows `max_stress_loss_rs`.
3. **New risk per day counts only trades still open.** A trade opened and closed in the same session is not in the
   book's open trades, so it does not count. In the daily desk (one entry run at about 15:15) this should not happen;
   reasoning only.
4. **Open trades' maximum loss is recomputed from the ledger**, not read from the decision record. It equals B2's
   number at entry (tested); after a partial exit it is the remaining position's, which can be larger than at entry
   (hand check, no charges or pads: a 200-wide short fly with Rs 160 credit, short call bought back at 150, holds a put
   credit spread whose maximum loss is Rs 13,000 - Rs 650 = Rs 12,350, against Rs 2,600 at entry; the code gives
   Rs 12,350). The caps count that real, larger number. It needs quotes for every held
   contract: a missing quote refuses the trade (fail closed), as C2's other rules do.
5. **Records written before C5** have no `opened_on`; a replay of such a decision through the new-risk cap is refused
   (fail closed, never guessed). I found no committed decision records with open trades.
6. **Underlying group is read from the symbol** (letters before the first digit). Correct for NIFTY and BANKNIFTY
   symbols in this repository; a stock with a digit in its name would parse wrongly, but every stock is refused today.
7. **C4 does not recompute the new caps** (it does follow the new brake). C4 independently re-checks C2; adding the
   caps there is a follow-up story.
8. **VIX +50% is modelled as each leg's implied volatility x 1.5** (no smile change); "+5%" keeps volatility unchanged.
   Reasoning only (question 3).
9. **S1's protocol text** (`catastrophic_loss_book`: "Rs 30,000") is not edited, as instructed; REPLAN section 4 says it
   becomes the account brake and bucket caps.

## Questions for the owner (never decided by me)

1. **C2's Rs 5 lakh-era limits on the Rs 20 lakh account.** Options: (a) keep `max_open_trades` 3, stress Rs 30,000 and
   exposure Rs 15,000 (today; the Rs 1.5 lakh cap can never bind); (b) retire `max_open_trades` (design 03 item 1 says
   the open-trade limit is "rescaled by risk bucket") and give new numbers for the stress and exposure limits; (c)
   retire the stress-loss limit too, relying on the Rs 1.5 lakh open-risk cap plus the daily stress line. My view
   (reasoning only): (b) for `max_open_trades`, because 6.2's own reason column says the bucket cap is "the owner's
   original 3-trade limit, applied to each correlated group"; the stress and exposure numbers are yours.
2. **Bucket side of directional structures (STR1).** 6.2 gives one side per position. A put credit spread is both
   bullish and short volatility; a bull call debit spread is bullish and long volatility. Options: (a) direction wins
   for verticals (bullish/bearish), volatility for flies and condors; (b) a position sits in two buckets and counts
   against both caps. Until you choose, those codes are unmapped and refused. The SF/SC/BF mapping (short, short, long
   volatility) is my reading of 6.2: say if you disagree.
3. **Stress line details.** "+5%": volatility unchanged (my reading) or with a VIX change? VIX change as a factor on
   every leg (built) is an approximation; acceptable?
4. **The three books opened at Rs 5 lakh.** Options: (a) reopen them at Rs 20 lakh by replacing the 13 Oct opening rows
   (no trade has ever been filled in them); (b) keep the 13 Oct rows and add a dated Rs 15 lakh top-up entry (E1 has no
   such entry kind today: a new story); (c) start new book folders. Until then nothing trades.
5. **Stock buckets.** "One stock" and "stock results this week" need the events calendar (A6/A12) and stock options
   (A18). Today any stock is refused. Confirm that this waits for A18.

## What the judge should test hardest

- The cap boundary: each cap at its number and Rs 0.01 over, with real B2 maximum losses (not only the fixed-number
  tests): `tests/risk/test_caps.py:99` does it for the bucket cap; try the open-risk and new-risk caps the same way.
- `HeldMaxLoss` against B2 by hand for one condor and after a partial close (a leg bought back): is the remaining
  maximum loss right, and is the "net short tail" refusal right for every legal partial state?
- That nothing in `fno/` still opens or sizes on Rs 5 lakh (the regex scan in `tests/risk/test_c5_account.py:82`), and
  that the books' committed Rs 5 lakh rows are refused, not silently used.
- That `opened_on` survives every path a book is rebuilt by (ledger, D2's same-session entries, D3's codec, replay).
