"""The book side of an AI book's forecast (stories F1 and G5), what its routine runs:

- `brief`: checks the fired text (`parse_pointer`) and the versioned prompt's hash, builds the export from the
  committed files and prints the prompt, then `INPUT` and the export. Nothing is shown unless every check passes.
- `seal`: completes and checks the answer (refusals name what to fix, so the model can fix it before 15:15), then
  publishes only the commitment. The salt and answer stay in the routine's private working folder.
- `reveal`: waits until 15:15:10 IST, then publishes the answer and the salt, then the run's own timing (story F8c;
  `brief` noted its start), in a publish of its own, so a timing failure can never cost the reveal.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .answer import check_answer, complete_answer
from .envelope import Envelope
from .export import build_export, export_sha256
from .paths import WORK_FOLDER, commitment_path, reveal_path
from .pointer import BookPointer, parse_pointer
from .run_timing import RunTiming
from .seal import Commitment, new_salt, reveal_text
from .timing import receipt_deadline, reveal_from
from .transport import PublishFailed, SubmissionTransport
from .versions import version_by_label

POINTER_FILE, EXPORT_FILE, SEALED_FILE = "pointer.txt", "export.json", "sealed.json"


class BookStepRefused(RuntimeError):
    """A step cannot run (wrong order, already sealed); the message says what to do."""


def answer_labels(pointer: BookPointer, export: dict) -> dict:
    """What the pointer and the export fix in every answer: the book cannot mislabel them."""
    return {"book": pointer.book, "day": pointer.day.isoformat(), "export_sha256": export_sha256(export),
            "pack_sha256": pointer.pack_sha256, "version": pointer.version}  # fmt: skip


def envelope_of(pointer: BookPointer) -> Envelope | None:
    width = version_by_label(pointer.version).envelope_width
    return Envelope.from_rules(pointer.rules, width) if pointer.rules is not None else None


@dataclass
class BookSession:
    root: Path
    transport: SubmissionTransport
    clock: Callable[[], datetime]
    sleep: Callable[[float], None]
    timing: RunTiming
    out: Callable[[str], None] = print

    def brief(self, text: str) -> None:
        pointer = parse_pointer(text)
        self.timing.start(pointer)
        version = version_by_label(pointer.version)
        prompt = version.prompt_text(self.root)
        export = build_export(self.root, pointer, version)
        self._save(POINTER_FILE, text)
        self._save(EXPORT_FILE, json.dumps(export, sort_keys=True))
        late = self.clock() > receipt_deadline(pointer.day)
        self.out(prompt)
        self.out(
            f"INPUT (export_sha256 {export_sha256(export)}){'; WARNING: already past 15:15:00 IST' if late else ''}"
        )
        self.out(json.dumps(export, sort_keys=True, indent=1))

    def seal(self, answer_file: Path) -> None:
        pointer, export = parse_pointer(self._load(POINTER_FILE)), json.loads(self._load(EXPORT_FILE))
        labels = answer_labels(pointer, export)
        answer = complete_answer(json.loads(Path(answer_file).read_text(encoding="utf-8")), labels)
        checked = check_answer(answer, labels, envelope_of(pointer))
        wrong = [f"{q}: {why}" for q, why in checked.problems.items() if why]
        if wrong:
            raise BookStepRefused("not sealed; fix and run seal again: " + "; ".join(wrong))
        path = commitment_path(pointer.day, pointer.book)
        if self.transport.existing(path) is not None:
            raise BookStepRefused(f"{path} already exists: this book is sealed for {pointer.day} (written once)")
        salt = new_salt()
        self._save(SEALED_FILE, json.dumps({"answer": answer, "salt": salt}))  # kept before publishing: reveal needs it
        commitment = Commitment.of(answer, salt)
        commit = self.transport.publish(path, commitment.to_text(), _message(pointer, "commitment (sealed answer)"))
        when = "before" if self.clock() <= receipt_deadline(pointer.day) else "AFTER"
        self.out(f"sealed: {pointer.book} {pointer.day} commitment {commitment.commitment_sha256[:12]} in commit "
                 f"{commit[:10]}, pushed {when} 15:15:00 IST by this clock (GitHub's push time decides)")  # fmt: skip

    def reveal(self) -> None:
        pointer = parse_pointer(self._load(POINTER_FILE))
        sealed = json.loads(self._load(SEALED_FILE))
        wait = (reveal_from(pointer.day) - self.clock()).total_seconds()
        if wait > 0:
            self.out(f"waiting {wait:.0f} s until {reveal_from(pointer.day):%H:%M:%S} IST before revealing")
            self.sleep(wait)
        path, text = reveal_path(pointer.day, pointer.book), reveal_text(sealed["answer"], sealed["salt"])
        existing = self.transport.existing(path)
        if existing is not None:
            if existing != text:
                raise BookStepRefused(f"{path} already holds a different reveal (written once)")
            self.out(f"already revealed: {path}")
        else:
            commit = self.transport.publish(path, text, _message(pointer, "reveal (answer and salt)"))
            self.out(f"revealed: {pointer.book} {pointer.day} in commit {commit[:10]}")
        self._time_run(pointer)

    def _time_run(self, pointer: BookPointer) -> None:
        """The run's timing for BG1's ledger; a failure is said and never raised (the reveal is already out)."""
        try:
            self.out(self.timing.publish(pointer, _message(pointer, "run timing")))
        except (PublishFailed, ValueError, OSError) as failed:
            self.out(f"timing NOT published ({failed}): the run's AI minutes will show as not captured")

    def _save(self, name: str, text: str) -> None:
        folder = self.root / WORK_FOLDER
        folder.mkdir(exist_ok=True)
        (folder / name).write_text(text, encoding="utf-8")

    def _load(self, name: str) -> str:
        path = self.root / WORK_FOLDER / name
        if not path.is_file():
            raise BookStepRefused(f"{name} missing: run the steps in order (brief, seal, reveal)")
        return path.read_text(encoding="utf-8")


def _message(pointer: BookPointer, what: str) -> str:
    return f"F1/G5 {pointer.book} {pointer.day}: forecast {what}"
