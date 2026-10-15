# Response 190: answer to ChatGPT review 122 (E8 owner-timing fills, story text)

Reviewed: `story/e8-owner-timing-fills` at `df7a1d65` (judge 193 addendum 3 PASS). ChatGPT: CHANGE one entry-funds
point before code; accept the rest. Each point checked against the story text and the repository.

1. **Price cap and its denominator: ACCEPT.** A fill-only average hides the misses; with a cap, bought options fill
   mostly on mornings that moved against them (E8a: price moves above 10% of trade risk on 23-28% of mornings, some
   evidence). The report shows net P&L per executed fill AND per eligible opportunity (a miss is 0 in the denominator),
   with miss reasons and the NIFTY-move split over the whole opportunity set. Reporting only, no new engine.
2. **Availability calendar: CHANGED by the owner (16 Oct row), not as ChatGPT proposed.** ChatGPT judged dates-only in
   the repository acceptable; it did not weigh that `exepex/trading` is **public** (checked: visibility public), so
   future away dates would show anyone when the owner is away. The owner chose: dates in a private Drive file, its
   SHA-256 committed to the repository before T. That keeps rule 8's proof (no "away" added after seeing a result).
   One addition of ours (strong reasoning): a file of a few dates is guessable, so a bare hash could be reversed by
   trying calendars; the Drive file carries a random salt line, never committed, so the committed hash reveals nothing.
3. **One available session for entries, exits never expire: ACCEPT** (already rule 8). Missed-away entries and exit
   delay are reported apart; a pending exit is never counted as risk reduced.
4. **Four views are one decision's counterfactuals: ACCEPT.** `e4_1515` is labelled an unexecutable timing yardstick
   (it fills before the card exists). AC9's isolation fixture is extended both ways to the S1 stop path and the drawdown
   brake: identical verdict-account cash, caps, brake and S1 stop with the diagnostic views on or off.
5. **Funds and margin at the fill: ACCEPT, and wider than AnyPrice (checked).** Rule 6 and AC6 re-check only C2's
   per-trade cap and buckets on the fill's prices. But approved cash, available cash and margin are separate, and even
   under `ApprovedLimit` cash can move between decision and fill (other fills that morning) and the margin row can
   change overnight. So every entry-range option re-runs the existing C2/C4 entry checks (cash, stressed margin, caps,
   buckets) on the due-mark prices, the current verdict account and pending fills: "missed, insufficient funds" or
   "missed, over risk cap". Two AC6 fixtures: a bought option whose new debit is under the loss cap but above available
   cash; a credit vertical with loss headroom but too little margin. These are the paper desk's own checks, not Groww's
   funds or margin API, so AC12's read-only rule (no broker order, position, margin or funds call) is unchanged.

Owner's entry rule: still open (recommended `ApprovedLimit`; ChatGPT agrees, reasoning only); needed before S1's freeze.

Next: the E8 builder writes points 1, 2, 4 and 5 into the text; judge C re-checks only those; then the code.
