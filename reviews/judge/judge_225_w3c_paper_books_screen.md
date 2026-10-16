# Judge 225: W3c, the paper books screen (exepex/omenix-dashboard story/w3c-paper-books at 5e648af, from main 1972241)

**Verdict: PASS.** `npm test` gives **511 passed, 0 failed, 0 skipped** in a read-only clone (the claimed figure).

| Check | Result | Evidence |
|---|---|---|
| One card per book, never summed | MET | `view.ts` maps each account alone ("the screen sums nothing"). There is no `reduce` or total in the screen's views or components, and a test checks that no three-book total appears |
| Shadows apart; B0 is "Measurement" | MET | A separate shadows section from `shadows[]` (2.8.0), using its `label` (`measurement` for B0) |
| Legs and alerts owner-only; gateway test | MET | Legs and today's alerts are shown only on the dashboard, which is behind Vercel Authentication. The contract marks them `x-visibility: owner`, enforced by `OWNER_PATHS` on the contract side. The gateway import test covers every `lib/fno-*`, `components/fno-*` and W3 page by pattern, so it covers this screen, and it passes |
| Costs before and after; no made-up fills | MET | Closed trades show gross, costs, net, result and how each closed, plus the 5/30/60-minute fills. A missed fill says why, and a trade from before E8 says "Before owner-timing fills", never a number |
| Judge 222's tightening | MET | `screens-import-graph.test.ts` now requires every reader of a screen's wiring to be a loader of that screen's own routes, matched by endpoint `fno/<screen>` or `fno/<screen>-<part>` in that loader's own folder, and each screen to have such a route. New planted cases: another screen's loader reading the weather wiring is caught; the weather history's loader passes |
| No cap bar (deviation) | Accepted | The contract does not send the Rs 1,50,000 open-risk cap. Writing it into the screen would be a second copy of a C5 config value, which silently goes stale when the cap changes. Showing open risk alone, with a request for an `open_max_loss_cap` contract field, is the right call |
| India only | MET (code) | The same static-params, `dynamicParams = false` and `notFound` pattern; the nav item sits in India's Portfolio group only |

**Notes (not should-fix):**
- **`fno-screen.css` gets a third edit** (the bar track moved from the weather). W3d also edits this file. Whichever of
  W3c and W3d merges second gets its resolution re-checked, as for W3a part 2.
- **The tightened import test matches by endpoint,** so W3d's route must carry `endpoint: fno/strategy-lab` for
  `fno-strategy-lab`, or this test fails when both are on main. The failure would be loud, not silent: it is a check,
  not a risk.
