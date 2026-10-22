"""Tickets and the three counts (story MS-P1f, 327 item 1).

A ticket is a 1-lot virtual trade where a driver's rule fired but its account did not trade: beyond the slot's trade
limit, or while the daily stop or the brake holds the account. It obeys the same quotes and laws as a trade, with
only the account limits relaxed, lives in its own ledger (never a driver's account) and is never summed into rupees
shown to the owner. Every scheduled decision is counted: eligible, fillable, executed."""
