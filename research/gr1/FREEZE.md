# Freeze record: GR1, sharper price ranges

Protocol frozen at commit `54bb5a4268c7c7da6af67350439a70231be0548b` (22 Oct 2026, about 02:20 IST). At that point no GR1 candidate had been
fitted or scored, and no conditioner had been read against an outcome. Ledger trials 56-70 named this commit until revision 2.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `ab67f3b67d2698d1635924fcb54e45745f2b3aee25743a13e99260d73387580e` |

The study code's hashes are added here in their own commit, after its tests on synthetic data and before run 1
(protocol section 12). Merging this branch into `main` must keep the freeze commit in history (a merge, never a
squash or rebase), or B4's ledger guard refuses the trials.

Check before reading results: `sha256sum -c` on the files above, at the run commit.

## Revision 2, before review (judge 428 and judge B's note on section 12), frozen at `eb8d061a6847ef6dd69263880af03b9c5a87f4a6`

Nothing had been fitted or scored. The ledger rows 56-70 now name this commit. (An intermediate revision-2 freeze at
`a7a1b28a`, hash `ec02703d...53f0`, was superseded before review by this one, which adds section 12's (a)-(d) word for
word at judge B's request.)

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `8ed575b36e322d73a350550e5e642a878e814677f2a92c4671cac96a40ef2eaa` |

## Judge 428.1's notes applied (after its PASS of a7a1b28a, before any code), frozen at `9c67a3c7d7c80c201fc28db907a3e635042f2e87`

Nothing had been fitted, scored or coded. The ledger rows 56-70 now name this commit. Delta from a7a1b28a is wording
only, plus C2's crossing check on every scored day: section 2's honest limit, section 12's (a)-(d), C2's guard and
section 14.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `89de9cf4d43fdf9c1a9c6a5a017356f05edd3cec26627e6537e54ab52f70dfaa` |

## Deviation 3 (input probe, before the code freeze), protocol frozen at `23c9ce504996e43525e4f74a66a1691717b6202e`

Nothing had been fitted or scored. The probe counted inputs only (`probe.py`, its close a constant, so no outcome
read). Ledger rows 56-70 now name this commit.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `3293c2bf6a484e8d52af1c8e89eb8d5faaedf4a6ff050027c4afd34c2e5ccf42` |
| `probe.csv` | `abeae36d55349aa9b5b1c0dd36f183d63d1e04da9fed0ac1e780c1d0e1f4b599` |

## Analysis code

Frozen before run 1 (protocol section 12, step 2). It was tested on synthetic data only: `tests/research_gr1/`, 34 tests.
`mutation_proof.py` catches 23 of 23 planted bugs, among them a broken seal, a moved centre, no Holm, a raw-date cue
look-ahead, USD/INR of the day, no train gap rule and a worse candidate winning. `study.py` refuses to run unless each
file below hashes to its row here and the folder has no uncommitted change (`gr1study/guard.py`).

| File | SHA-256 |
|---|---|
| `gr1study/candidates.py` | `f2d790561620cc1cebcc278b4733b9a8aef7124f474b0c45c1b380dc5ff2e8fe` |
| `gr1study/cues.py` | `b4b292e1163b98cc252b4772e67a3ef31f80196c806cc1c807a5b694f98461aa` |
| `gr1study/evaluate.py` | `55aee813d5a5ad970e8a666484cd9303c0a5de281207ce2e7c310d4334e5fd3e` |
| `gr1study/final.py` | `804d8d619f9d89b454f7ec617a67f0d6bdbd4401273f4c9e43f7aeee1a07db60` |
| `gr1study/fit.py` | `64591c2864592fa372f8be8497effcf79cae8a5c081fc34af0434ef043308517` |
| `gr1study/guard.py` | `229a2c0b5c92d89859a53a3a09d00d6acf3513171079feccf162bc8a93ff039e` |
| `gr1study/inputs.py` | `bcb863ed9d2d7ed8eca27903679bc2fa3585f88c89451312afc7fd8fa33141cd` |
| `gr1study/n0.py` | `db50b2f409187442395853feebc39456ba281d39cf0ce23ab92fb8aa760b6c30` |
| `gr1study/periods.py` | `a431fabe9303ce5d0f92a61b80be556432e467b52e7dcdaf23b050450609940e` |
| `gr1study/rows.py` | `37cf0e48406ae454523ed0b051e35442ba2838045b758ef78c5b91cebb74b149` |
| `gr1study/scaling.py` | `d33a070d9536e27466e0c0086bfe93263d79517c46a71bff6fe673f2e18130e6` |
| `gr1study/selection.py` | `3f9b5767e9dd5ad77bc02bf73b80dfff78e0c7a2717963d809c54167c0d53819` |
| `mutation_proof.py` | `97cf1ea1222f170e6dc5a66be4e2af80d90621d428748d6c638382c8666ca531` |
| `probe.py` | `193c08ef94939c4690da743c1157b645c49c68419bd03a68bc02e2ddb3b63b37` |
| `study.py` | `25cabe14e0670bbac4b3f5a1231ced5cac06363aabb65c020f658690c8c8acc7` |
