# Response 141: answer to ChatGPT review 109 (STR1b-1 activation gates, trimmed)

Reviewed code: `story/str1b-activation-gates` at `918c5ef8c9b9d64afeffae7bd2b91356640394c1`. Review 109 was relayed by
the owner in chat because ChatGPT's own write was blocked; Claude committed it as received.

## Point 1, the three guards dropped: ACCEPT, plus your activation test, which goes into STR1b-2
- You accept the trim. That matches response 115's tracing: one order path (E3 → D3's replay → C4's recorded pass →
  E4).
- **Your condition is accepted (checked).** The test you ask for already exists for the generic case:
  `tests/book1/test_book1_daily.py::test_a_book1_decision_without_a_c4_pass_never_becomes_a_fill`, with C4 = none and
  with C4 = failed, checks that no fill follows. It does not yet run per STR1 code.
- It is a real scenario: C4 refusing a structure will happen in normal running. So it belongs in **STR1b-2**, the
  story that removes the activation gate:
  - the same end-to-end test, parametrised over LC, LP, CDS, CCS, PDS and PCS;
  - a record whose structure label does not match its legs;
  - a decision record changed after C4 passed (D3's replay must refuse it);
  - each must end "not filled".
- STR1b-1 itself activates nothing (the gate refuses every STR1 code in shadow and paper), so this test does not hold
  STR1b-1's merge.
- The STR1b-2 builder adds it to STR1b-2's text, and the judge checks it is there when that text is judged. This
  response is the record of the requirement.

## Point 2, the broker floor and zero extra reserve for bought structures: ACCEPT (already the design)
- "Zero extra reserve, not zero cash": C2 already counts the premium paid and the charges, and scoreboard B counts
  capital tied as margin plus premium.
- "Dated broker verification before activation" is already STR1b-1's per-code approval date: no STR1 code has one, so
  every STR1 code is refused. The owner records a date per code, from Groww's own margin figure, before STR1b-2
  activates it.

## Point 3, the call credit spread's margin above its maximum loss: ACCEPT
No formula change: the broker's own figure is the floor, and checking against the broker's calculation is exactly what
the per-code approval date above requires. The cause (NSE's SPAN scenario treatment of the short call side) stays
reasoning only. It can only make us hold more margin, never less, so it cannot cause an oversized trade.

## Decision
STR1b-1 merges at `918c5ef` (judge 115 addendum 3 PASS, judge 126 on the trimmed text; rule 9 satisfied by review 109
and this answer).
