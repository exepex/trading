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

## Revision 2, before review (judge 428), frozen at `a7a1b28a9730c14a47710e70090ddbc963a7fe48`

Nothing had been fitted or scored. The ledger rows 56-70 now name this commit.

| File | SHA-256 |
|---|---|
| `PROTOCOL.md` | `ec02703d245a7d97e3ab4f8020279e896ee2b00cf6ca020e5839cb59837553f0` |
