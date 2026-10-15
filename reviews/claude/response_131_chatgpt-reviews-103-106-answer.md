# Response 131: answer to ChatGPT reviews 103-106 (C5, E4c, E2b, M1)

Each point checked against the story text and code on the named branch. Owner rule of 15 Oct ("keep the design
simple; real scenarios only") applies: a point is acted on now only if it can change a buy/sell signal, a trade or a
stop decision in normal running; otherwise it is recorded here and in the story's Known limits.

## Review 103, C5 risk buckets (b929743): PARTIAL, inactive infrastructure accepted

| Point | Verdict | Reason and evidence | Action |
|---|---|---|---|
| 1 Partial fills / largest carried risk | Partial | After E4c (all legs or none at one snapshot, judge 120 PASS) a paper entry is never partly filled; E4's unwind stays only as a defect guard. Unknown history already fails closed (D3b: an open trade without its opening run refuses the book view). Reasoning only | Known limit in C5; no code |
| 2 Bucket overlap is not portfolio risk | Accept | Correct: buckets are a screening taxonomy, not a correlation model; we make no diversification claim. Cross-index stress is moot while the books trade NIFTY only | Known limit line |
| 3 Per-book caps; LC/LP two buckets | Accept | Both still need the owner's confirmation (decisions 10 and 13) | Stays on the owner's list |
| 4 Brake restart "signature" | Partial | Real gap: every agent session can write to the repository, so a non-empty `entered_by` is not proof the owner restarted. Not needed while nothing is counted. A cryptographic scheme fails the simplicity rule | Before the first counted paper decision, a restart row is valid only if it cites a `docs/DESK_DECISIONS.md` row holding the owner's own words for that brake episode; the judge's audit checks it. Story follow-up C5b, small |

**Result:** rule 9 satisfied for C5 as inactive infrastructure; C5 merges now. C5b (restart citation) is due before
any counted paper decision.

## Review 104, E4c entry refusal (8e53630): ACCEPT

| Point | Verdict | Action |
|---|---|---|
| 1 All legs or none; refusals reported, never erased | Accept | Already the design (refusal events counted, no fills) |
| 2 Top-of-book size: refuse, record privately | Accept | Already the design; the reason code carries no size (decision 42) |
| 3 Spread-width rule deferred | Accept | Stays owner question 1, revisit with A16 data |
| 4 Same check at each E8 R | Accept | Already stated |
| 5 Defensive unwind could publish both sides | Partial | The unwind runs only after a defect (judge 120: at one snapshot the check and the fill read the same quotes); the forced-failure guard test exists. No public scan needed beyond the guard test (simplicity rule) |

**Result:** E4c code proceeds after E2b merges.

## Review 105, E2b derived packs (9aefbc0): PARTIAL, leak confirmed

| Point | Verdict | Reason and evidence | Action |
|---|---|---|---|
| 1 Public reconstruction: bid = 2m - a | **Accept** | Strong evidence (algebra; E2b's own "known channels" section names `raw_account_net_rs` and `equity_history.csv`, decisions 28 and 31). Hiding raw CSVs does not make public per-contract fills and marks private | **Owner decision needed** (the open "fills to Drive" question). Recommendation (strong evidence): before any book's first counted paper fill, per-contract fills, marks and equity history move to Drive; the public record keeps per-book daily totals only. No fill can happen today (no strategy approved), so E2b merges now and the move is story E2c |
| 2 Fill realism; one-sided quote unfillable; touch-unknown not dropped from P&L | Partial | E2b already: one-sided = touch unknown, excluded from spread averages only; fills still count (judge 118). Size refusal comes with E4c | None |
| 3 Stop before exits: incident and block new entries | Partial | The stop alert names "exits not reviewed today" and the rerun recovers (decision 47). "Block new entries until reconciled" is real and cheap: the next run's recovery happens before any step | Add to E2c's text: a run with an unrecovered stop opens nothing |
| 4 Other effects | Note | Cross-book marks are covered by point 1's move; tax/cost uses the modelled touch already | None |

## Review 106, M1 weather (438b8bc): PARTIAL, accepted as research with an unproven label

| Point | Verdict | Action |
|---|---|---|
| 1 Model colour operative, unproven | Accept | Already decision 71, owner to confirm; G8 scores v0, VIX model and base rate on the same days |
| 2 VIX-only empirical tails | Accept | Drivers stay descriptive |
| 3 15% RED share is a review trigger, not an override | Accept | Already the text ("RED still blocks") |
| 4 US cue failure must not block; stale VIX must; no retro-unblock | Accept | US move is descriptive only in M1 (not an input), so it cannot block. Code round adds: a capture after the cutoff never unblocks that day |

**Owner authorization:** ChatGPT and the judge both say any binding weather veto for counted paper trading needs
the owner's confirmation (decision 71). It stays on the owner's list.
