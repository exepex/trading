# Judge 167: story LR1 text, the weekly post-mortem v1 (quality rule 1; judge C)

Date: 15 Oct 2026 (UTC). Branch `story/lr1-weekly-postmortem` at **cb632340b67d33c0f88c44e42f4d93e91ffa2102**
(`docs/stories/LR-learning.md`). Builder session_0145TfSwzmpk6MBrH92f5h4G; claims response 162.
- Judged under the owner's "keep the design simple" rule and the coordination rule.
- Judged with the builder's recommended options: retire G4's Monday post, the AI writer later, Saturday 10:41 IST.

## Verdict: PASS (text); 3 notes

| Check | Status | Evidence |
|---|---|---|
| No second scoring path | MET | The story reads G4's report through the existing `weekly_summary` (`fno/forecast_scoring/score_report.py:99`), G8's committed `research/forecasts/v4_scores/<d>.json` with its `EXPLORATORY` line (`fno/forecast_scoring/v4/records.py:16`), M1's `WeatherRecords` (`fno/weather/records.py:21`) and G7's `big_move_outcomes` (`fno/forecast_v4_rules/series.py:67`). All exist on `main`. "New this week" is a subtraction of two committed counts. Test 7 fails if `fno/learning/` imports G4's or G8's scoring modules: a sound guard |
| Three sections | MET | Forecasts (G8, then G4 unchanged), weather (colours, label, status, GREEN-day misses, counts per colour, M1's own RED share) and data health (3 pm marker and lateness, card delivery, A16 session count, one completeness line). Each has an empty-state line, and V1, V4 and V5 show G8's status, never an error |
| Never decides a trade | MET | Criterion 12's AST test forbids imports from `fno/desk/`, `fno/books/`, `fno/risk/` and `fno/checks/`. The text says "reports and never decides a trade" |
| 13 criteria | MET | Each is testable and tied to a test in the plan: dry run, write-once, Slack failure, equality with the named report, exploratory line, holiday week, `test: true` cards, the workflow's schedule, secret and commit scan |
| Coordination | no duplicate | No other row of `docs/WORK_REGISTER.md` builds a weekly report. S4 (the monthly report) is slice C, by design apart |

### The pending owner choices

- **Retire G4's Monday post (recommended): the verdict holds.** If the owner keeps it, the same `weekly_summary` text
  goes to #fno-desk on Monday (`forecast-scores.yml`, cron `41 3 * * 1`) and again on Saturday: one function posting
  twice. Under the coordination rule that is a duplicate. With that option LR1 must show the G4 part as one line
  naming the Monday post, not the text again. Either way, the workflow change to G4's cron is lane 1 and belongs in
  this story's code.
- **AI writer later: the verdict holds.** The text is code-built lines, so there is no AI cost and nothing for an
  advocate yet.
- **Saturday 10:41 IST: the verdict holds.** G4 scores daily at 22:41 IST, so Friday's report is the latest. LR1 runs
  G8's own `report --as-of <Saturday>` first. The owner's routine-timing rule (setup well before any market time) is
  not touched on a Saturday.

## Notes (none changes a trade)

1. **One writer of `research/forecasts/v4_scores/`.** Today no workflow writes it, and LR1's job would be the first.
   If G8 later gets its own schedule, only one job may write that folder. Record it in the register now: the LR1 row
   says "writes v4_scores on Saturdays until G8 has its own job", so the G8 builder sees it.
2. **Reuse readers that exist (DRY).** A16's session rows already have a reader, `RvTable`, used by G8
   (`fno/forecast_scoring/v4/wiring.py:36`, `INTRADAY_FOLDER`). The 3 pm canonical marker is already read by the
   quote recorder (`QuoteSnapshotRecorder.canonical`). Use them behind the new interfaces rather than new parsers of
   the same files.
3. **Today's data.** `research/forecasts/v4_scores/` and M1's weather folder do not exist on `main` yet. The first
   Saturday's report will print mostly "no v4 score report yet" and "missing" lines. That is correct by the story's
   empty states; the owner should expect it.

**Verdict: PASS for cb632340b67d33c0f88c44e42f4d93e91ffa2102** (story text), with the builder's recommended options.
Code may start. It posts to Slack and adds a schedule (lane 1), but decides no trade, so rule 9 applies only if the
orchestrator says so.

## Note (15 Oct 2026): on hold for a revised text

The owner chose the AI writer and the devil's advocate **in v1**, not later. So the PASS above, which assumed "AI
writer later", does not cover the coming revision. The other two answers match the assumptions: retire G4's Monday
post, Saturday 10:41. I will judge the revised SHA as an addendum here. Points I will check there:
- BG1's budget meter counts the AI cost;
- the AI text never changes a committed number (it may only reword or comment on code-built lines);
- the advocate's checks;
- the week's post still goes out when the AI part fails.

## Addendum 1 (15 Oct 2026): revision 1 at 86f46232b28b8e583b64706d273143ccc0b49007

Owner answers (relayed by the orchestrator): one weekly report, so G4's Monday post is retired in LR1's change; the AI
writer and the devil's advocate are both in v1, the simple way; Saturday 10:41 IST. The forecasts, weather and data
health sections are unchanged and stay MET as above.

## Verdict: PASS (text); 1 note

| My hold-note point | Status | Evidence |
|---|---|---|
| The AI cost is counted | MET | The writer routine records its run with F8's `budget record-usage --self-timed --purpose books_and_roles` (`fno/budget/cli.py`). It is not fired when BG1's month signal (`accounting/budget/<YYYY-MM>_signal.json`, `fno/budget/signal.py`) is `stop` |
| The AI never changes a number | MET | The code-built lines stay the source of truth and are posted every time. The prose is shown only if the code advocate passes four rules: the SHA line ties it to the committed lines; at most 150 words with no link, mention or code block; every number in the prose copied from the lines; no number written in words |
| The post goes out if the AI part fails | MET | A `stop` signal, missing secrets (`UnconfiguredTrigger`), a failed fire (`FireFailed`), no prose by 11:41, or any failed advocate rule each give the lines alone plus one line naming why (criteria 15-17) |
| No second AI caller | MET | The writer is fired through the existing `RoutineTrigger`/`RoutineFireTrigger` (`fno/pipeline/trigger.py`), as the AI books do (`fno/ai/fire.py`), with a pointer holding only the Saturday and the lines' SHA-256. All named classes exist on `main` |
| Only the publisher reads the prose | MET | Criterion 18's AST test |
| Merge-tree with `origin/main` | MET | No conflict |

**Choosing a code check, not a second AI call, for the advocate is right.** It is cheaper and certain for "numbers
copied exactly". An advocate that argues in words is T3 (slice B), as stated.

## Note (does not change a trade)

**Rule 3 must compare whole number tokens, not substrings.** As written ("appears as the same text in the lines"), a
substring match would let a prose "4" pass because "40%" or "2026-10-14" contains it. Extract each number token from
both texts with the same pattern (digits with their decimal point, sign and `%`, dates as one token) and check the
prose's tokens are a subset of the lines' tokens. Add one test: prose "4 sessions" against lines holding only "40%"
fails. Test 11's 41% vs 40% case does not cover this.

**On coordination:** the builder sent me this SHA directly, as the orchestrator said it would. I told the orchestrator.

**Verdict: PASS for 86f46232b28b8e583b64706d273143ccc0b49007** (story text). Code may start.
