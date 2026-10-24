# 25 Oct 2026 (IST): AI books' trading builder (F1t, F5, F6), session_01B3RARTgoiGJwBKXRCgGRe8

## Messages and the decisions they lead to

- Orchestrator (session_01Mt6dcBU5kp2htdPN2KmiZH), relaying the owner's decision of 25 Oct: "the AI books (Book 2
  Hybrid, Book 3 AI team) must be able to decide and book PAPER trades; the 22 Oct cut-list's pause on them is
  lifted." Scope given to this session: F1t (the runner), then F5 (Book 2's decider), then F6 (Book 3). No live switch
  is touched.
  - Found: the register was out of date. F1t has about 5,170 lines of 16 Oct code, never judged, 4,810 commits behind
    main with 19 conflicts. F6/F7 has code (judge 400 FAIL, answered at d46379c7, not re-judged) that merges cleanly
    with main. F5's text passed, but its last docs commits were not on main. F4 (Book 2's daily judge) has no owner.
  - Done: the register rows went to this session, and F5's passed docs tail was merged to main (3e125f5d). The plan
    went to the orchestrator.
  - F1t text revision 2 on story/f1t-runner-v2 (PR #149, tip edbc939a), for the code judge:
    - facts re-read on main;
    - F4's judge step folded in;
    - status-only reason codes;
    - a rehearsal never fires a routine;
    - decisions reuse G11's RunTerms chain;
    - updated go-live checks.
- Evidence from the AI forecast audits of 15-23 Oct:
  - 7 of 12 fired book-days on time;
  - answers came 36 s to 5 min 9 s after the fire;
  - the model was reported "unknown" on 10 of 11 answered book-days.
  Under the 16 Oct no-trade rule for an unknown model, the books would trade about 1 day in 11 unless the decision
  prompt fixes model reporting.

## Decisions so far

- F1t's code is re-ported onto main after the text PASS, never merged blind; F6 is re-judged after F1t's port; F5's
  code follows F1t and F6.
- Until F4's code lands, Book 2 is "judge failed" every day (fail closed).

## Open questions

- Owner: does the 25 Oct decision lift the 15 Oct rule "AI books trade on paper only after a strategy has passed"? Recommended:
  yes for paper, every AI trade labelled "strategy not yet passed" and reported apart.
- Owner: approve drafts of Book 2's envelope v1 and Book 3's constitution v1 (as decided on 16 Oct)? Recommended: yes.
- Orchestrator: assign F4 to this session? Recommended: yes. Also confirm with the MS owner that the later AI drivers
  reuse F1t's runner.
