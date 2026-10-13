"""The weekly audit draw's seed (judge 62 addenda 1 and 2): NSE's NIFTY 50 close of the week's last session, read from
the index-close file archived in Drive, never from the repository's closes file. A planted edit of that file (its close
or its SHA-256) refuses the draw rather than steering it; a week is a candidate only once a later close is in; each draw
is recorded once with its seed inputs."""

import hashlib
import json
from datetime import date, timedelta

import pytest

from fno.ai.audit_plan import FiredSession, audits_due, record_draws, weeks_to_draw
from fno.ai.close_archive import DriveIndexCloseArchive, NoCloseArchive
from fno.ai.draw_seed import final_last_closes, verified_seeds
from fno.ai.paths import CLOSES_FILE, fired_path
from fno.constants import BOOK3_AI
from fno.storage.raw_source import NseIndexCloseSource
from fno.storage.raw_store import LocalFolderStore

WEEKDAYS = [d for d in (date(2026, 10, 14) + timedelta(days=n) for n in range(30)) if d.weekday() < 5]
HEADER = "date,session,underlying,vix,index_file,index_sha256\n"


def index_file(close: float) -> bytes:
    return f"Index Name,Index Date,Closing Index Value\nNifty 50,x,{close}\nIndia VIX,x,14.1\n".encode()


class Market:
    """The Drive archive (raw area) and the repository's closes file, both written as O6 would."""

    def __init__(self, root, days):
        self.root, self.raw = root, LocalFolderStore(root / "drive" / "raw")
        rows = []
        for i, day in enumerate(days):
            data = index_file(22000.5 + i)
            self.raw.put(NseIndexCloseSource.path_for(day), data)
            sha = hashlib.sha256(data).hexdigest()
            rows.append(f"{day},regular,{22000.5 + i},14.1,{NseIndexCloseSource.filename_for(day)},{sha}\n")
        self.closes = root / CLOSES_FILE
        self.closes.parent.mkdir(parents=True, exist_ok=True)
        self.closes.write_text(HEADER + "".join(rows))

    def seeds(self, weeks=None):
        weeks = weeks or {d.isocalendar()[:2] for d in WEEKDAYS}
        return verified_seeds(self.closes, DriveIndexCloseArchive(self.raw), weeks)

    def edit_row(self, day, old, new):
        text = self.closes.read_text()
        line = next(row for row in text.splitlines() if row.startswith(day.isoformat()))
        self.closes.write_text(text.replace(line, line.replace(old, new)))


def last_of_first_week():
    return [d for d in WEEKDAYS if d.isocalendar()[:2] == WEEKDAYS[0].isocalendar()[:2]][-1]


def test_the_seed_is_the_archived_close_and_a_week_waits_for_a_later_close(tmp_path):
    week_one = [d for d in WEEKDAYS if d <= last_of_first_week()]
    market = Market(tmp_path, week_one)
    assert market.seeds() == ({}, [])  # the week's last close may not be final yet
    market = Market(tmp_path, WEEKDAYS)
    seeds, refused = market.seeds()
    first = WEEKDAYS[0].isocalendar()[:2]
    assert refused == [] and seeds[first].close_date == last_of_first_week().isoformat()
    assert seeds[first].nifty_close == repr(22000.5 + len(week_one) - 1)
    assert seeds == market.seeds()[0]  # the same inputs give the same seed
    assert WEEKDAYS[-1].isocalendar()[:2] not in seeds  # the newest week is never final


def test_a_planted_close_in_the_repository_refuses_the_draw_instead_of_steering_it(tmp_path):
    market = Market(tmp_path, WEEKDAYS)
    day = last_of_first_week()
    close = final_last_closes(market.closes)[day.isocalendar()[:2]].underlying
    market.edit_row(day, f",{close},", ",23999.0,")
    seeds, refused = market.seeds()
    assert day.isocalendar()[:2] not in seeds
    assert refused and "refused" in refused[0] and "23999.0" in refused[0]


def test_a_planted_file_hash_or_a_missing_archive_refuses_the_draw(tmp_path):
    market = Market(tmp_path, WEEKDAYS)
    day = last_of_first_week()
    sha = final_last_closes(market.closes)[day.isocalendar()[:2]].index_sha256
    market.edit_row(day, sha, "f" * 64)
    seeds, refused = market.seeds()
    assert day.isocalendar()[:2] not in seeds and "is not the one" in refused[0]
    week = {day.isocalendar()[:2]}
    assert verified_seeds(market.closes, NoCloseArchive(), week)[0] == {}
    empty = DriveIndexCloseArchive(LocalFolderStore(tmp_path / "nothing"))
    assert "no index-close file archived" in verified_seeds(market.closes, empty, week)[1][0]


def test_only_weeks_with_sessions_to_draw_are_checked(tmp_path):
    market = Market(tmp_path, WEEKDAYS)
    assert market.seeds(weeks={(2020, 1)}) == ({}, [])
    sessions = [FiredSession(d, BOOK3_AI, {}) for d in WEEKDAYS]
    assert weeks_to_draw(sessions) == {d.isocalendar()[:2] for d in WEEKDAYS[10:]}


def test_each_draw_is_recorded_once_with_its_seed_inputs(tmp_path):
    for day in WEEKDAYS:
        (tmp_path / fired_path(day)).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / fired_path(day)).write_text(json.dumps({BOOK3_AI: {"fired": True, "version": "v", "session": "s"}}))
    seeds, refused = Market(tmp_path, WEEKDAYS).seeds()
    written = record_draws(tmp_path, seeds)
    assert refused == [] and written and record_draws(tmp_path, seeds) == []
    record = json.loads((tmp_path / written[0]).read_text())
    assert set(record["seed"]) == {"week", "close_date", "nifty_close", "index_sha256"} and len(record["drawn"]) == 2
    due = {(s.day.isoformat(), s.book) for s in audits_due(tmp_path, seeds)}
    assert {tuple(d) for d in record["drawn"]} <= due and len(due) == 10 + 2 * len(written)


@pytest.mark.parametrize("bad", ["", "abc"])
def test_an_unreadable_close_refuses_the_week(tmp_path, bad):
    market = Market(tmp_path, WEEKDAYS)
    day = last_of_first_week()
    close = final_last_closes(market.closes)[day.isocalendar()[:2]].underlying
    market.edit_row(day, f",{close},", f",{bad},")
    assert day.isocalendar()[:2] not in market.seeds()[0]


def test_a_deleted_last_session_row_refuses_the_draw_instead_of_moving_it(tmp_path):
    market = Market(tmp_path, WEEKDAYS)
    day = last_of_first_week()
    text = market.closes.read_text()
    market.closes.write_text("".join(r for r in text.splitlines(keepends=True) if not r.startswith(day.isoformat())))
    seeds, refused = market.seeds()
    assert day.isocalendar()[:2] not in seeds and "missing from the closes file" in refused[0]
