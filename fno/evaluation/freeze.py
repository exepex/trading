"""The protocol's freeze (story S1, criteria 1 and 3). `research/evaluation/FREEZE_v<n>.md` records:
- the protocol version and the commit that last changed the protocol;
- the SHA-256 of every file and every config section the protocol's `frozen_files` item lists.

The freezer refuses unless the protocol is committed unchanged, complete, and decided item by item by the owner. It
also refuses when a listed file is missing, or when this version is already frozen. It then registers the protocol in
the research ledger (B4). A later change to any hashed target is a new protocol version, never an edit of a frozen
one."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

from ..research_engine.ledger import Ledger, read_ledger, write_ledger
from .completeness import completeness_problems, undecided_items
from .protocol import PROTOCOL_FILE, parse_protocol

FREEZE_TEMPLATE = "research/evaluation/FREEZE_v{version}.md"
CONFIG_PREFIX = "config.yaml:"
TARGET = re.compile(r"`([^`\s]+)`")
COMMIT_LINE = re.compile(r"^Protocol commit: `([0-9a-f]{40})`$", re.MULTILINE)
VERSION_LINE = re.compile(r"^Protocol version: ([1-9][0-9]*)$", re.MULTILINE)
HASH_ROW = re.compile(r"^\| `([^`]+)` \| `([0-9a-f]{64})` \|$", re.MULTILINE)


class FreezeRefused(RuntimeError):
    """The protocol cannot be frozen as it stands; the message says why."""


@dataclass(frozen=True)
class FreezeRecord:
    version: int
    protocol_commit: str
    hashes: dict[str, str]  # target (a repository path, or config.yaml:<section>) -> SHA-256


def freeze_path(version: int) -> str:
    return FREEZE_TEMPLATE.format(version=version)


def frozen_targets(text: str) -> list[str]:
    """The targets the `frozen_files` item lists; the protocol itself is always one."""
    item = parse_protocol(text).items.get("frozen_files")
    listed = TARGET.findall(item.value) if item else []
    return sorted({PROTOCOL_FILE, *(t for t in listed if "/" in t or t.startswith(CONFIG_PREFIX))})


def _config_section(root: Path, dotted: str):
    node = yaml.safe_load((root / "config.yaml").read_text(encoding="utf-8"))
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            raise FreezeRefused(f"config.yaml has no section {dotted!r}")
        node = node[part]
    return node


def target_hash(root: Path, target: str) -> str:
    """A file's SHA-256, or a config section's: the SHA-256 of its canonical JSON (sorted keys, dates as text)."""
    if target.startswith(CONFIG_PREFIX):
        section = _config_section(root, target.removeprefix(CONFIG_PREFIX))
        data = json.dumps(section, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return hashlib.sha256(data).hexdigest()
    path = root / target
    if not path.is_file():
        raise FreezeRefused(f"{target} is listed in frozen_files but does not exist")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def render(record: FreezeRecord) -> str:
    rows = "\n".join(f"| `{target}` | `{sha}` |" for target, sha in sorted(record.hashes.items()))
    return (
        f"# Evaluation protocol freeze record\n\nProtocol version: {record.version}\n"
        f"Protocol commit: `{record.protocol_commit}`\n\n"
        "Every target's SHA-256 at the freeze (a config section: the SHA-256 of its canonical JSON). A change to any "
        "of them is a new protocol version with its own freeze (story S1, criterion 3).\n\n"
        f"| Target | SHA-256 |\n|---|---|\n{rows}\n"
    )


def read_record(text: str) -> FreezeRecord:
    version, commit = VERSION_LINE.search(text), COMMIT_LINE.search(text)
    hashes = dict(HASH_ROW.findall(text))
    if version is None or commit is None or PROTOCOL_FILE not in hashes:
        raise FreezeRefused("a freeze record names its version, the protocol commit and the protocol's hash")
    return FreezeRecord(int(version.group(1)), commit.group(1), hashes)


def changed_targets(root: Path, record: FreezeRecord) -> list[str]:
    """Targets whose bytes (or config section) differ from the freeze, or that are gone."""
    changed = []
    for target, sha in sorted(record.hashes.items()):
        try:
            if target_hash(root, target) != sha:
                changed.append(target)
        except FreezeRefused:
            changed.append(target)
    return changed


class ProtocolFreezer:
    def __init__(self, root: Path, git, ledger: Ledger | None = None):
        self.root, self.git = Path(root), git
        self.ledger = ledger or Ledger(self.root, git)

    def _checked_text(self) -> tuple[int, str]:
        if not self.git.unchanged_since("HEAD", PROTOCOL_FILE) or self.git.committed_text(PROTOCOL_FILE) is None:
            raise FreezeRefused(f"commit {PROTOCOL_FILE} first: the freeze names the commit that holds it")
        text = (self.root / PROTOCOL_FILE).read_text(encoding="utf-8")
        protocol = parse_protocol(text)
        problems = completeness_problems(text, protocol)
        undecided = undecided_items(protocol)
        if problems or undecided:
            why = problems + ([f"not decided by the owner: {', '.join(undecided)}"] if undecided else [])
            raise FreezeRefused("the protocol is not ready to freeze: " + "; ".join(why))
        return protocol.version, text

    def freeze(self, today: date) -> FreezeRecord:
        version, text = self._checked_text()
        path = self.root / freeze_path(version)
        if path.exists():
            raise FreezeRefused(f"{freeze_path(version)} exists: a change is a new protocol version")
        commit = self.git.commits_touching(PROTOCOL_FILE)[-1]
        record = FreezeRecord(version, commit, {t: target_hash(self.root, t) for t in frozen_targets(text)})
        path.write_text(render(record), encoding="utf-8")
        self._register(record, today)
        return record

    def _register(self, record: FreezeRecord, today: date) -> None:
        """A ledger row for the protocol (B4): prospective, no hypothesis, naming the protocol and its commit."""
        rows = self.ledger.rows()
        trial = str(max((int(r["trial_id"]) for r in rows if r["trial_id"].isdigit()), default=0) + 1)
        description = f"Evaluation protocol v{record.version}: the three books' comparison rules (story S1)"
        experiment = f"evaluation-protocol-v{record.version}"
        self.ledger.register(trial, experiment, description, "prospective", False, PROTOCOL_FILE, today)
        rows = [
            r | {"protocol_commit": record.protocol_commit} if r["trial_id"] == trial else r for r in self.ledger.rows()
        ]
        self.ledger.file.write_text(write_ledger(read_ledger(write_ledger(rows))))
