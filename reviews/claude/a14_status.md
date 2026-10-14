# A14 status (builder session 01FVYzWZtDAZrZLDZ6DtmSYL)

Updated: 14 Oct 2026, about 16:39 IST. Branch `story/A14-nse-margins`, draft PR #90, issue #89.

**Ready for judge** at code tip `cc3a393` (main merged at 31fd08e; this status file is the only later commit). Full suite
with `env -u FNO_SLACK_BOT_TOKEN`: 3,092 passed; ruff, format and `tools/check_imports.py` clean.

Groww broker check (claims response 77, "Broker check 2"):
- SPAN: Groww 6,893 = my `i1` row's max(0, scan - NOV) 6,893.25 (rounded). Groww uses the beginning-of-day file.
- Exposure: Groww 58,819.02 = NSE's 2% rule on 22,622.70, the index in NSE's 15:32 file, equal to the paisa. My row
  uses the previous close (22,721.95): 59,077.07, Rs 258 above Groww today. On an up day the row is below Groww's by
  Rs 2.60 per index point (about Rs 590 a lot per 1% rise): the one way it can be looser. Proposal for the judge:
  rescale exposure by decision-time index / file index in C2 (not changed).
- Switch set: `risk.margins.nse_span_check` = "Groww margin API (read-only), orchestrator run", 2026-10-14. Judge decides
  whether criterion 1 is met.
- Funding at entry (orchestrator's note): Groww's total 113,312.64 asks for the bought premium up front and does not
  count the sold premium; C2's MarginRoom credits the net premium. C2 is looser than Groww's funds check at entry.
  Outside A14; flagged, not changed.

Not merged into main.
