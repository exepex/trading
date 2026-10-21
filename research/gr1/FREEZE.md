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
