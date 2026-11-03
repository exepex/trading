"""Evidence citations in an AI book's decision (story F4 design 1; built with F5's code, which calls it): a top-level
`evidence` list of 0 to 20 items `{"pack": "common" | "private", "pointer": "<RFC 6901 JSON pointer>"}`, with no value
copied into the answer, so no private pack value becomes public through the reveal. `evidence_problems` checks the
shape (F5's and F6's `check_decision` call it, so `seal` refuses a malformed list before the deadline); `resolve`
follows a pointer in a pack body. Standard library only: it runs in the routine's `seal`."""

from __future__ import annotations

PACKS, ITEM_KEYS = ("common", "private"), ("pack", "pointer")
MAX_ITEMS, MAX_POINTER_CHARS = 20, 300


class Unresolved(LookupError):
    """The pointer does not reach a value in that body."""


def evidence_problems(evidence) -> list[str]:
    """Shape problems of an evidence list; empty means acceptable."""
    if not isinstance(evidence, list):
        return ["evidence must be a list"]
    if len(evidence) > MAX_ITEMS:
        return [f"evidence holds {len(evidence)} items, at most {MAX_ITEMS}"]
    problems, seen = [], set()
    for n, item in enumerate(evidence):
        if not isinstance(item, dict) or sorted(item) != sorted(ITEM_KEYS):
            problems.append(f"evidence[{n}] must have exactly the keys pack and pointer")
            continue
        pack, pointer = item["pack"], item["pointer"]
        if pack not in PACKS:
            problems.append(f"evidence[{n}].pack must be one of {', '.join(PACKS)}")
        if not _is_pointer(pointer):
            problems.append(f"evidence[{n}].pointer must be a JSON pointer of at most {MAX_POINTER_CHARS} characters")
        if (repr(pack), repr(pointer)) in seen:  # repr: an unhashable value is a shape problem, never a crash
            problems.append(f"evidence[{n}] repeats an earlier item")
        seen.add((repr(pack), repr(pointer)))
    return problems


def resolve(body, pointer: str):
    """The value at `pointer` in `body` (RFC 6901: `~1` is "/", `~0` is "~", list indices are numbers)."""
    if not _is_pointer(pointer):
        raise Unresolved(f"{pointer!r} is not a JSON pointer")
    value = body
    for token in pointer.split("/")[1:] if pointer else ():
        key = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict) and key in value:
            value = value[key]
        elif isinstance(value, list) and key.isdigit() and int(key) < len(value) and str(int(key)) == key:
            value = value[int(key)]
        else:
            raise Unresolved(f"{pointer} does not reach a value")
    return value


def _is_pointer(pointer) -> bool:
    return isinstance(pointer, str) and len(pointer) <= MAX_POINTER_CHARS and (pointer == "" or pointer[0] == "/")
