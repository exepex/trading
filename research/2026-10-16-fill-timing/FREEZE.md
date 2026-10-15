# Freeze record: FT1, the fill-timing study (story E8a)

Frozen at commit `47d15989a4045a1804b235fcb5fad13ec7e2a7ea` (15 Oct 2026 IST), before any option or future price of this study was read. Only the
coverage probe ran before it, and it recorded symbols and candle counts, never a price (`probe.csv`). Ledger trial
54 names this commit.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `0dea9e11a01066ac811eba944ffb64973574a75de0c26b4640bf19399fe1e238` |
| `probe.csv` | `6cefa0cac8b585c2e220129f32e33bef19ec191954bb370b12a27ae91a167d58` |

The analysis code's hashes are added here in their own commit before the full fetch (`PROTOCOL.md` section 19).
Merging this branch into `main` must keep the freeze commit in history (a merge, never a squash or rebase), or B4's
ledger guard refuses the trial.

Check before reading results: `sha256sum -c` on the files above at the run commit.

## Analysis code, frozen before the full fetch (PROTOCOL.md section 19)

Tested on synthetic data only (`tests/research_ft1/`, 67 tests; `mutation_proof.py`: 18 of 18 planted bugs caught,
among them a sign error, a stale-leg substitution, an expiry-week entry and a wrong R mapping). The dry run ran before
this freeze, as the protocol orders (section 17): 5 decision days, 111 contract windows archived to Drive, 0 failed,
2.41 s a call (Drive upload included); the full plan is 2,548 windows. It read candle counts and the row layout only
(one window, `NSE-NIFTY-30Mar26-22450-PE` 13-17 Mar 2026, came back empty: its legs will count as missing), never a
price. `study.py --run` refuses to run unless each file below hashes to its row here and the folder has no uncommitted
change.

| File | SHA-256 |
|---|---|
| `study.py` | `9a90629dd8e94cc82a1068144e6e9792f6bbdddd8b08b6e7423e0066985b123d` |
| `ft1study/__init__.py` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `ft1study/analysis.py` | `82906a10e0a5299c3c0fa5e25f00b9fa8da04f73dc519c4176ec74151b673bb8` |
| `ft1study/archive.py` | `74f0045b2053ba7cad7e1ca1c2db09850a2995532a9e6466dfa9490cf65c076d` |
| `ft1study/bars.py` | `c9d12e3545ccc87d88651fe1ed83db42bcdfc1a7e3106cf4303e8f92a6e6dfd0` |
| `ft1study/bootstrap.py` | `815623e69e12af0529248c13280ab6ff80b3b9b7a839ae41592e6daa1d7239a9` |
| `ft1study/candles.py` | `3efaf7e4b7acc361b8942924e454c464abe208ffb67c262b5f1a8c277c35da42` |
| `ft1study/cells.py` | `f554659321576bf30ae41a7b18cfb3b5ef1bd043d92050f7ffc782b295df9d95` |
| `ft1study/contracts.py` | `7f027e299be4bd8d02a12b60f2257c2e28ff122b91b6ba7d9d235b4ad9018ce4` |
| `ft1study/days.py` | `91cc1a579e6f5c2267ef153db827088416a9f2f71f5026788e033228cb668dd0` |
| `ft1study/entries.py` | `7c4a7861fef45c333534c38e353eb4bb6001ab4af35ec641ee7b7346a76b1784` |
| `ft1study/fetch.py` | `7778fb7138a662130476506e8b068931b9b3a2feb8c520bd37b2c2d6302446a5` |
| `ft1study/figures.py` | `9b378f339510fc50256eabaa38ec083c83e1ae08993a85d288dd8c68a7db8339` |
| `ft1study/flips.py` | `a3018f631dbc487c571de2ca6c1e9a9045fd49dc115306aa16fc362a03957cb8` |
| `ft1study/freeze.py` | `317ac89dee2d254c087c55bda36a1d524479934840c0348b7dac2ab0462ae8e5` |
| `ft1study/handcheck.py` | `f8fbba9b385a7e63ee47467e7519af1a3180232891d323193a285f7ff9b4eb0b` |
| `ft1study/observe.py` | `b20984bbb7a1bb80dcf38cd309b6bfa9cc92e427146976244c7f6e655af78ace` |
| `ft1study/plan.py` | `08a3df6928a569db43190c17026254fbc3cada9a5dff8bbf56210412a66794c3` |
| `ft1study/probe.py` | `ccb2df35378928f0166b924d6488a4f160039622d45cc840e8348aed72985976` |
| `ft1study/report.py` | `8674fac185df6d582fc1a27d4acbd87ddb81dc298c9b0e9ca197ab2952a35721` |
| `ft1study/spreads.py` | `81e7c60172df9994d3f8e1c81f1f49634c57e6f5ee0b1aae0229cb5a12782c8c` |
| `ft1study/steps.py` | `ed7b0a17b8aebed15e934b209b514e6c51417393fed5691ee92eea3445d8abff` |
| `ft1study/timepart.py` | `38c85c07f907999ddf906f35e37e6bf88da7a947901951195fd4f8dcdb7d5db3` |
| `ft1study/times.py` | `47b410b8d1bad3504f1f85a6c0b97e3515b9e2c22c6318ac3b407e3f9197b0da` |
| `ft1study/wiring.py` | `a88361b546428f9bf5ef7e98cd5aaa8e1e9b2b07f36542ce3e9fff375bab56d5` |
