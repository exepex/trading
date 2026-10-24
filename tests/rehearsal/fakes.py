"""Fakes for REH1's tests: a Drive that records every write and refuses a second write of a name, as Drive's
write-once store does."""

from __future__ import annotations

import hashlib


class RecordingDrive:
    def __init__(self, files: dict[str, bytes] | None = None):
        self.files = dict(files or {})
        self.writes: list[str] = []

    def get(self, path):
        return self.files.get(path)

    def put(self, path, data):
        if path in self.files:
            raise FileExistsError(path)
        self.writes.append(path)
        self.files[path] = data

    def file_id(self, path):
        return f"id:{path}" if path in self.files else None

    def replace_contents(self, file_id, data):
        path = file_id.removeprefix("id:")
        self.writes.append(path)
        self.files[path] = data

    def _in(self, folder):
        prefix = folder.rstrip("/") + "/"
        return {p[len(prefix) :]: d for p, d in self.files.items() if p.startswith(prefix)}

    def checksums(self, folder):
        return {n: hashlib.md5(d).hexdigest() for n, d in self._in(folder).items() if "/" not in n}

    def folders(self, folder):
        return sorted({n.split("/")[0] for n in self._in(folder) if "/" in n})

    def metadata(self, path, fields):
        return {"id": f"id:{path}"} if path in self.files else None

    def root_listing(self):
        return "fno", sorted({p.split("/")[0] for p in self.files})
