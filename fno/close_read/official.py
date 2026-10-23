"""NSE's official closes for a day, from the index-close file: the copy archived in Drive (the version first archived,
which G13b scores), else NSE's own archive, as every reader of these files gets it (`fno/storage/wiring.py`
`build_index_close_files`, never writing to Drive). Behind an interface so a test or another archive swaps in one
class."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from ..fo_bhavcopy import read_index_closes
from ..research_data.nifty_panel import DailyFiles


class OfficialCloses(ABC):
    @abstractmethod
    def closes(self, day: date) -> tuple[str, dict[str, float]] | None:
        """The file's name and its closes by official index name; None while no file exists yet. A damaged file
        raises `BadFile`."""


class ArchivedIndexCloses(OfficialCloses):
    def __init__(self, files: DailyFiles):
        self.files = files

    def closes(self, day: date) -> tuple[str, dict[str, float]] | None:
        filename, data = self.files.get(day)
        if data is None:
            return None
        return filename, read_index_closes(data, filename)
