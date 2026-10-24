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

- Orchestrator, 25 Oct: "plan accepted"; "Q3: F4 is yours"; "Q4: ... one trading runner (F1t); any later
  market-school AI driver reuses it, never a second one". Second message, "Owner update 25 Oct: every earlier pause and
  condition from older decisions is lifted; so build on Q1 = yes ... and Q2 = draft the envelope and constitution v1
  exactly as decided 16 Oct".
  - F1t text 470cbdc5: the strategy label (criterion 17b), and the paper-strategy go-live check removed.
  - F4 text fe5721d3: the port is F1t's, and NoJudge applies until F4 lands.
  - F6: main merged at 50b479e1 (full gates 16,720 passed).
  - Drafts at 7d44b51e: Book 2's envelope v1 and Book 3's constitution v1 (inert until registered in D6).
- Found: Book 2 cannot trade even with Q1 lifted. D2 trades only `paper` rules, the only rule is `research`, and D4
  refuses a trade the rules did not offer. Book 3 trades its own research specs. Owner question Q5 was sent.

## Decisions so far

- F1t's code is re-ported onto main after the text PASS, never merged blind; F6 is re-judged after F1t's port; F5's
  code follows F1t and F6.
- Until F4's code lands, Book 2 is "judge failed" every day (fail closed).

## Open questions

- Owner Q5: may Book 2 (only) take registered research candidates as its rule defaults, labelled "strategy not yet
  passed", under D2's 1-open-trade unproven limit? Recommended: (A) yes; (B) is to wait for a paper rule.
- Owner: approve the envelope v1 and constitution v1 drafts (register their hashes in D6) before go-live.
