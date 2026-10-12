# Wave 0 judgment, round 1 (2026-10-12)

Scope: 4eaf7f3..3f012cd (W0.1-W0.6). Verdict: **FAIL** (2 blocking, 8 should fix, 10 minor).
Commands: pytest 101 passed; ruff clean; only exempt html_report.py over 350 lines; news-once: 9 feeds and NSE
answered, BSE 403 from the cloud; no order calls anywhere; no secrets in the diff.

| Claim | Result |
|---|---|
| W0.1 safeguards | FAIL (findings 1, 2, 8, 18) |
| W0.2 profiles and shadow book | FAIL (findings 9, 10, 16) |
| W0.3 polite fetching | PASS |
| W0.4 Groww data | PASS with minor findings (11) |
| W0.5 news watcher | FAIL (findings 3, 4, 5, 12, 13) |
| W0.6 news weighting | FAIL (findings 2, 6, 7) |

Blocking
1. One failed chain at square-off (overnight trim, no try) aborts the review before the journal is saved: every
   exit of that review is lost, repeatedly, until the close. Fix: per-trade try in the trim; always save; test.
2. A failed adverse-news close raises out of the review: closed trades get no record or alert and the automatic
   kill switch is skipped. Fix: per-trade try in `_exit_on_adverse_news`; record/alert/kill always run; test.

Should fix
3. Marketaux token leaks in connection-error text (query parameter in the URL) into logs and `news-once`.
4. The watcher thread dies silently on an unexpected exception (e.g. a Finnhub row with a string datetime).
5. Aggregators (Marketaux/Finnhub/AskNews re-serving one ET article) inflate credibility to "widely reported".
6. Classifier keywords match inside words ("turmoil", "software", "award") and the cost flip inverts headlines
   ("Sensex falls amid global turmoil" +1.0; "Oil India shares jump on record profit" -1.0).
7. `news_shock` can never fire for world news on indices: max weight 0.7 x 1.0 x 0.6 = 0.42 < 0.5.
8. The performance kill switch uses the all-time worst drawdown, so it never clears after recovery.
9. The shadow book is trimmed by the overnight cap and skips the adverse-news exit.
10. Synthetic open trades committed in journal/shadow_trades.json.

Minor
11. `auto` provider crashes with a key but no TOTP/secret, or without the SDK; should fall back to NSE.
12. Daily API allowances reset on every restart (in memory only).
13. `news-once` does not wait between sources (docstring says it does).
14. The 5 s gap is measured from request start; NSE retries can send up to 4 requests in about 5 s.
15. The watcher can poll on an NSE holiday before the first tick loads holidays.
16. Docs: README "slows down 5x"; DATA_SOURCES "not BSE"; SAFEGUARDS "only money limits" (trades per day/week
    differ too) and "judged as % of capital" (readiness uses a fixed Rs 20,000 drawdown).
17. Dead code: ExitReason.PERFORMANCE_STOP unused; NewsWatcher.errors never surfaced.
18. Test gaps: weekly trade cap not asserted; no trim test; Groww re-sign-in untested; no watcher thread/restart test.
19. CLAUDE.md design: new behaviour added inside existing classes; `api_sources_from_environment` builds concrete
    classes outside services.py; inline regex in classifier.
20. One requests.Session shared by the desk thread and the watcher thread.
