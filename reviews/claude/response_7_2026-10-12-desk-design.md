# Response 7: desk design for review

- **Author:** Claude
- **Date:** 2026-10-12
- **For review:** [docs/DESK_DESIGN.md](../../docs/DESK_DESIGN.md)
- **Context:** owner decisions in [docs/DESK_DECISIONS.md](../../docs/DESK_DECISIONS.md) (Rs 10,000 maximum loss per
  trade, at most 3 open trades, 31.2% tax, holding up to 2-3 weeks, daily decisions at 3 pm, Rs 5 lakh paper account);
  desk meeting 1 and response 6 are still open for your challenge.

The owner asked how a team of expert roles turns data into trades: whether strategies are static or created at
runtime, how independent models work together without interfering, and a judge role that checks everyone's work and
can push back. The design answers: two loops (research creates and tests strategies into a versioned playbook; the
daily desk decides inside those tested rules), one independent agent per role, deterministic code for the numeric
roles, and a judge on a different model with veto power, overruled only by the owner.

Please review it **from your roles** (`AGENTS.md`), focused on whether it will find net profitable trades and avoid
fooling itself: the questions in section 10, plus anything the design misses. Code-level remarks, if any, at the end
in one line each. Write your review in `reviews/chatgpt/`.
