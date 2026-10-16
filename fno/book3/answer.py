"""Book 3's `decision` object (story F6 expected design 3, F7): its exact shape, checked by `check_decision` when the
routine seals (F1t's `seal`, so the model can fix a refused answer before the deadline) and again by the decider. The
standard library only, because the routine side imports nothing else. The checks are on shape alone: whether a pick
is a built candidate, a proposal fits the constitution or a card was given is decided by the decider on the day."""

from __future__ import annotations

ACTIONS = ("trade", "no_trade")
SHADOW_ACTIONS = ("take", "no_trade")
KEYS = ("action", "cards_used", "proposals", "reason", "shadow", "trades")
TRADE_KEYS = ("opportunity_id", "reason")
PROPOSAL_KEYS = ("reason", "spec", "supersedes")
SHADOW_KEYS = ("action", "opportunity_id", "reason", "width")
MAX_REASON_CHARS = 600
MAX_SPEC_CHARS = 20_000  # a D1 playbook file is about 3,000 characters


def check_decision(decision) -> list[str]:
    """Every shape problem, each naming what to fix; empty when the shape is right."""
    if not isinstance(decision, dict) or sorted(decision) != list(KEYS):
        return [f"decision must have exactly the keys {', '.join(KEYS)}"]
    problems = []
    if decision["action"] not in ACTIONS:
        problems.append(f"action must be one of {', '.join(ACTIONS)}")
    problems += _reason("reason", decision["reason"])
    problems += _trades(decision["trades"], decision["action"])
    problems += _items("proposals", decision["proposals"], PROPOSAL_KEYS, _proposal)
    problems += _items("shadow", decision["shadow"], SHADOW_KEYS, _shadow)
    problems += _unique_texts("shadow opportunity_id", [s.get("opportunity_id") for s in _dicts(decision["shadow"])])
    problems += _cards(decision["cards_used"])
    return problems


def _reason(where: str, value) -> list[str]:
    if not isinstance(value, str) or not value.strip() or "\n" in value or len(value) > MAX_REASON_CHARS:
        return [f"{where} must be one line of 1 to {MAX_REASON_CHARS} characters"]
    return []


def _text(where: str, value, empty_ok: bool = False) -> list[str]:
    if not isinstance(value, str) or (not empty_ok and not value.strip()):
        return [f"{where} must be text" + ("" if empty_ok else ", not empty")]
    return []


def _dicts(value) -> list[dict]:
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _items(name: str, value, keys: tuple[str, ...], check) -> list[str]:
    if not isinstance(value, list):
        return [f"{name} must be a list"]
    problems = []
    for n, item in enumerate(value):
        where = f"{name}[{n}]"
        if not isinstance(item, dict) or sorted(item) != list(keys):
            problems.append(f"{where} must have exactly the keys {', '.join(keys)}")
            continue
        problems += check(where, item)
    return problems


def _trades(value, action) -> list[str]:
    problems = _items("trades", value, TRADE_KEYS, _trade)
    if problems:
        return problems
    if (action == "trade") != bool(value):
        problems.append("trades must be non-empty exactly when action is trade")
    return problems + _unique_texts("trades opportunity_id", [t["opportunity_id"] for t in value])


def _trade(where: str, item: dict) -> list[str]:
    return _text(f"{where}.opportunity_id", item["opportunity_id"]) + _reason(f"{where}.reason", item["reason"])


def _proposal(where: str, item: dict) -> list[str]:
    problems = _text(f"{where}.spec", item["spec"]) + _text(f"{where}.supersedes", item["supersedes"], empty_ok=True)
    if isinstance(item["spec"], str) and len(item["spec"]) > MAX_SPEC_CHARS:
        problems.append(f"{where}.spec must be at most {MAX_SPEC_CHARS} characters")
    return problems + _reason(f"{where}.reason", item["reason"])


def _shadow(where: str, item: dict) -> list[str]:
    problems = _text(f"{where}.opportunity_id", item["opportunity_id"]) + _reason(f"{where}.reason", item["reason"])
    action, width = item["action"], item["width"]
    if action not in SHADOW_ACTIONS:
        problems.append(f"{where}.action must be one of {', '.join(SHADOW_ACTIONS)}")
    is_number = isinstance(width, (int, float)) and not isinstance(width, bool)
    if action == "take" and not (is_number and width > 0):
        problems.append(f"{where}.width must be a positive number for a take")
    if action == "no_trade" and width is not None:
        problems.append(f"{where}.width must be null for no_trade")
    return problems


def _unique_texts(where: str, values: list) -> list[str]:
    texts = [v for v in values if isinstance(v, str)]
    return [f"{where} must not repeat"] if len(texts) != len(set(texts)) else []


def _cards(value) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(c, str) and c for c in value):
        return ["cards_used must be a list of card IDs (text)"]
    return _unique_texts("cards_used", value)
