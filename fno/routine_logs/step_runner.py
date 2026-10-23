"""Runs one routine command, passing its output through live (the routine session still reads it) and keeping a copy
for the log: at most the last `KEEP_BYTES`, as a 35-minute daily run can print a lot and the tail holds the cause."""

from __future__ import annotations

import subprocess
from collections import deque
from collections.abc import Callable, Sequence

KEEP_BYTES = 2_000_000
CUT = "[... earlier output cut: the log keeps the last {kept} bytes ...]\n"
NOT_STARTED = 127


def run_command(command: Sequence[str], echo: Callable[[str], None] = print) -> tuple[int, str]:
    """(exit code, kept output). A command that cannot start returns 127 with the reason as its output."""
    try:
        process = subprocess.Popen(list(command), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                   bufsize=1, errors="replace")  # fmt: skip
    except OSError as error:
        line = f"could not start {command[0]!r}: {type(error).__name__}: {error.strerror or error}\n"
        echo(line.rstrip("\n"))
        return NOT_STARTED, line
    kept: deque[str] = deque()
    size, cut = 0, False
    assert process.stdout is not None
    for line in process.stdout:
        echo(line.rstrip("\n"))
        kept.append(line)
        size += len(line)
        while size > KEEP_BYTES and kept:
            size -= len(kept.popleft())
            cut = True
    code = process.wait()
    text = "".join(kept)
    return code, (CUT.format(kept=KEEP_BYTES) + text) if cut else text


def last_lines(text: str, count: int) -> list[str]:
    return [line for line in text.splitlines() if line.strip()][-count:]
