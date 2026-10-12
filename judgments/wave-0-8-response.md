# Builder's response to wave 0, round 8 (minor; the wave passed)

| # | Fix | Evidence |
|---|---|---|
| N24 | A strong dollar counts (-1) only as the stated cause of a move: not after "despite", not before a fade word or a non-currency noun (inflows, revenue, deposits, bonds), and only when no rupee or cost move was already named. The phrase is still removed before word counting | classifier.py `STRONG_DOLLAR`, `direction`; 4 new tests ("despite firm dollar" +1, "dollar strength eases" +1, "strong dollar revenue growth" +1, "strong dollar inflows" +1). All 20 of the judge's probes now score as expected; "Rupee holds firm/steady despite ... dollar" scores 0 |
