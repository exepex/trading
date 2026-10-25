"""A stand-in `growwapi` package for tests of story GW1 (the SDK is an optional install): it records every sign-in
and every call by name, answers from `answers`, and has the order calls a read-only guard must never reach."""

from __future__ import annotations

import sys
import types


class FakeSdk:
    def __init__(self):
        self.tokens: list[str] = []
        self.calls: list[str] = []
        self.answers: dict = {}
        self.sign_in_error: Exception | None = None

    def client_class(self):
        sdk = self

        class GrowwAPI:
            EXCHANGE_NSE, SEGMENT_FNO, SEGMENT_CASH = "NSE", "FNO", "CASH"

            def __init__(self, token):
                if sdk.sign_in_error is not None:
                    raise sdk.sign_in_error
                sdk.tokens.append(token)

            def __getattr__(self, name):
                def call(*args, **kwargs):
                    sdk.calls.append(name)
                    answer = sdk.answers.get(name, {})
                    return answer(*args, **kwargs) if callable(answer) else answer

                return call

        return GrowwAPI


def fake_sdk(monkeypatch) -> FakeSdk:
    sdk = FakeSdk()
    module = types.ModuleType("growwapi")
    module.GrowwAPI = sdk.client_class()
    monkeypatch.setitem(sys.modules, "growwapi", module)
    return sdk
