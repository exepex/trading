"""Book 3 has no research candidates to forward-test in shadow (its playbook's `shadow_on` is always empty), so D2
never asks it for a shadow account; asking is a wiring error, refused loudly."""

from __future__ import annotations

from ..playbook.schema import Strategy
from ..playbook.shadow import ShadowAccount, ShadowBooks


class NoShadowBooks(ShadowBooks):
    def account(self, strategy: Strategy) -> ShadowAccount:
        raise RuntimeError(f"Book 3 has no shadow candidates, yet {strategy.name} v{strategy.version} asked for one")
