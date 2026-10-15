# Protocol v4: V7's own null (`tools/v4_vix_null.py`)

200,000 series per null; worst held-out conditional rate over the full period and the calmest and most volatile 125/250-session stretches, both orientations. Claim nominal 0.133% (L1), 0.200% (L2); futility target 2.5%. Exposed 2019-26 data; held-out seeds measure Monte Carlo error only.

| n | rule | share of windows | claim L1 | claim L2 | false futility | within |
|---|---|---|---|---|---|---|
| 125 | R0 borrowed V6b, NIFTY band 5-7 | 6% | 0.549% | 1.099% | 13.26% | **no** |
| 125 | R0 borrowed V6b, NIFTY band 8-12 | 7% | 2.316% | 3.505% | 31.19% | **no** |
| 125 | R0 borrowed V6b, NIFTY band 13+ | 37% | 1.271% | 2.042% | 15.61% | **no** |
| 125 | R1 own, no gate | 100% | 5.808% | 7.317% | 29.87% | **no** |
| 125 | R2 own, mean VIX 0-13 | 37% | 1.564% | 1.564% | 24.27% | **no** |
| 125 | R2 own, mean VIX 13-17 | 14% | 1.281% | 1.813% | 13.36% | **no** |
| 125 | R2 own, mean VIX 17-inf | 49% | 1.241% | 1.774% | 24.00% | **no** |
| 250 | R0 borrowed V6b, NIFTY band 5-7 | 4% | 3.891% | 4.658% | 50.00% | **no** |
| 250 | R0 borrowed V6b, NIFTY band 8-12 | 7% | 13.793% | 13.793% | 55.56% | **no** |
| 250 | R0 borrowed V6b, NIFTY band 13+ | 48% | 11.154% | 15.234% | 79.48% | **no** |
| 250 | R1 own, no gate | 100% | 16.760% | 19.791% | 64.66% | **no** |
| 250 | R2 own, mean VIX 0-13 | 39% | 20.610% | 24.628% | 18.94% | **no** |
| 250 | R2 own, mean VIX 13-17 | 12% | 4.481% | 6.133% | 31.17% | **no** |
| 250 | R2 own, mean VIX 17-inf | 49% | 10.761% | 15.053% | 75.04% | **no** |
