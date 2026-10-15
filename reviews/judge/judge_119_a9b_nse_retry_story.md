# Judge 119: A9b story text, NSE downloads: one retry policy and a named failure everywhere: `story/a9b-nse-retry` ad0c9aee768b29ebc210fd24365ca1ec6a9ccd56 (quality rule 1, text only)

**Number note.** A9b has no response file yet, so I used 119, the next free judge number. The orchestrator may
renumber it if 119 is reserved.

**What I checked:**
- the A9b section, the only change;
- the inventory against the code on `main` today: every `NseArchiveSource` subclass, every NSE fetcher outside it,
  every place that catches `HTTPError`;
- the pacer (`fno/http_pacing.py`), `PublicData` (`fno/providers/public.py`) and its callers, and the filings
  librarian;
- the five questions the orchestrator asked.

## The orchestrator's questions

**(a) Is the 22-class inventory complete? Yes.**
- **Subclasses.** An AST walk over `fno/`, `research/` and `tools/` finds exactly **22 transitive subclasses** of
  `NseArchiveSource`, in four files: `fno/filings/sources.py` 4, `fno/storage/raw_source.py` 7,
  `fno/storage/snapshot_source.py` 10, and `fno/vix_history/source.py` 1. NSDL's `NsdlFpiDailySource` and
  `NsdlFpiDailyBySessionSource` are among the 10.
- **NSE fetchers outside the class.** Only `fno/providers/public.py` (PublicData, out of scope) and
  `tools/nse_raw_download` (out). `fno/http_pacing.py` holds only host names.
- **A14** reads its SPAN files from Drive (`nse_margins/wiring.py:33`), so its NSE path is `data-librarian`, which the
  table already covers.
- **`HTTPError` catches** around an NSE fetch exist only at `fno/filings/librarian.py:128` and `:151`. The table's
  `filings archive` row covers both. The other catches (`drive_check.py`, `drive_session.py`) are Drive's.

**(b) The `check-once` alert: proof that it fires, and no live post in tests?**
- **That it fires: yes.** Criterion 3 requires "`participant-oi check-once` sends its UNREACHABLE alert on a 503", and
  rule 4 (in criterion 6) requires a broken-code proof per criterion. So a test must fail when the alert is not sent.
- **No live post: not stated.** In practice it cannot happen. The suite-wide fixture of judge 86 deletes
  `FNO_SLACK_BOT_TOKEN` and the other credentials for every test, with a guard against a silent sender.
- Minor 1 asks for the guarantee to be written into the criterion.

**(c) A reason for the 120 s Retry-After cap? Partly.**
- The text gives the purpose: "rather than block a run; the next scheduled run tries again".
- It gives no reason for the number 120 and no evidence label.
- Minor 2.

**(d) Does excluding PublicData leave a traceback? None that I found today.**
- **What `PublicData.nse_json` can raise:** `requests.RequestException`, including `SourceCoolingOff` (`session.get`
  is outside any try); `HTTPError` (`raise_for_status`); or `RuntimeError` (an empty answer).
- **Its two callers both catch these:**
  - The quotes recorder's `NseLevelSource` catches `Exception` per field and records it (`fno/quotes/market_levels.py`
    lines 82 and 86).
  - The A12 filing indexes are caught by the librarian's `LIST_ERRORS` (`requests.RequestException`, `RuntimeError`,
    `ValueError`, `KeyError`, `TypeError`, `librarian.py:38`).
- So the exclusion is safe today, but only because those callers catch broadly. Minor 3 asks the story to say so,
  naming the two callers, so a later caller of `PublicData` is not assumed covered by A9b.

**(e) The README correction as a criterion? Yes.**
- Criterion 5: "the participant-OI README line corrected".
- Scope 4 names the file and line (`research/data/participant_oi/README.md:54`).

## The policy itself (checked against the pacer)

- **403 and 429 together.** The pacer counts both as refusals (`REFUSAL_STATUS_CODES = (403, 429)`) and pauses a host
  after 2 in a row for 15 minutes. So the story's "a 429 gets one retry in practice" is right: the second 429 pauses
  the host, and the next try meets `SourceCoolingOff`.
- **403 raised at once as `RawFileRefused`** is right. The pacer's comment says NSE "can refuse once until its cookies
  are set", so a single 403 on one file must not stop a whole archive run. A12 goes on to the next company, and a
  second 403 pauses the host and stops the run politely.
- **`SourceCoolingOff`.** Not retrying it is right: today `_response` retries it, which sleeps 65 s into a paused host
  for nothing.
- **Successful paths unchanged** (criterion 4: one request, same bytes and `Last-Modified`, plus one real download
  against its manifest SHA-256).
- **No partial raw file:** kept and stated.

## Minor (text, non-blocking)

1. **Criterion 3, `check-once`:** add "with a fake alert sender; no test posts to Slack (judge 86's fixture)". Then the
   alert proof and the no-live-post guarantee are both in the criterion.
2. **The 120 s cap:** add a reason and label. For example: "reasoning only: a wait longer than 2 minutes is a block,
   not a hiccup. The pacer's own pause is 15 minutes, and the next scheduled run is the right retry". Also say that the
   worst case, 3 x 120 s per file, matters for long runs (A12's deadline-bound backfill).
3. **The `PublicData` out-of-scope line:** say why it is safe today. Its two callers, the quotes recorder's
   `NseLevelSource` and the A12 filing indexes, catch every exception it can raise. Say also that any new `PublicData`
   caller must do the same until `PublicData` is brought under this policy.
4. **A8's measured release time** (owner decision: "the time our 5-minute check first sees the file"). With retries, a
   check that sees a 503 and then a 200 sees the file up to 65 s after it started. Say which time `check-once` records:
   the start of the check, or the time of the successful answer. That keeps the measured release times consistent
   before and after A9b.

## Verdict: PASS for ad0c9aee768b29ebc210fd24365ca1ec6a9ccd56 (story text)

- The inventory is complete by my own search.
- The policy is consistent with the pacer and the owner's politeness rule.
- The caller table covers every NSE path I could find.
- The criteria carry the cases rule 5 asks for: `Retry-After` 120/121, the fourth try, the second 429, the empty 200.

Code may start. Fold the four minors into the code round; I check them there.
