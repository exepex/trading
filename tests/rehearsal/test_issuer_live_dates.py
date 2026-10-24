"""REH1o: G13's three issuers check their own `daily.live_from` date, so in a rehearsal each is given the date the
daily run's root made live (O1), as G10 did for the v4 pack: on a replayed day before its date it issues, and its
posts carry the step's not-live note (set by REH1j's `NotLiveInRealRuns` for the step's children). A real run, a day
on or after the date, and the backfills keep the real date."""

from datetime import date

import pytest

from fno.constants import ENV_FNO_REHEARSAL
from fno.premium_ranges import wiring as premium
from fno.price_distribution import wiring as distribution
from fno.price_ranges import wiring as ranges
from fno.rehearsal.live_wiring import rehearsed_date
from fno.rehearsal.mode import Rehearsal

D19, D22, D23 = date(2026, 10, 19), date(2026, 10, 22), date(2026, 10, 23)
CFG = {"daily": {"live_from": {"price_distribution": "2026-10-22", "price_ranges": "2026-10-22",
                               "premium_ranges": "2026-10-23"}}}  # fmt: skip


def mode(monkeypatch, tmp_path, day):
    monkeypatch.setenv(ENV_FNO_REHEARSAL, Rehearsal.new(day, tmp_path, tmp_path).to_env())


def stub(monkeypatch, module, *names):
    for name in names:
        monkeypatch.setattr(module, name, lambda *a, **k: None)


def distribution_live(monkeypatch):
    seen = []
    stub(monkeypatch, distribution, "build_chains", "build_day_builder", "build_store", "build_session_calendar")
    monkeypatch.setattr(distribution, "LiveRecorder", lambda *a: seen.append(a[5]))
    distribution.build_live_recorder(CFG)
    return seen[0]


def ranges_live(monkeypatch):
    seen = []
    stub(monkeypatch, ranges, "build_store", "build_session_calendar", "build_tables", "build_seals", "IndexFileCloses",
         "build_stored_index_close_files", "SnapshotChains", "build_quote_store", "build_builder")  # fmt: skip
    monkeypatch.setattr(ranges, "build_closes", lambda tables: type("C", (), {"closes": None})())
    monkeypatch.setattr(ranges, "RangeIssuer", lambda *a: seen.append(a[6]))
    ranges.build_issuer(CFG)
    return seen[0]


def premium_live(monkeypatch):
    seen = []
    stub(monkeypatch, premium, "build_session_calendar", "method_sha256")
    monkeypatch.setattr(premium, "PremiumIssuer", lambda *a: seen.append(a[3]))
    premium.build_issuer(CFG, store=object())
    return seen[0]


ISSUERS = {"price_distribution": (distribution_live, D22), "price_ranges": (ranges_live, D22),
           "premium_ranges": (premium_live, D23)}  # fmt: skip


@pytest.mark.parametrize("step", ISSUERS)
def test_before_its_date_a_rehearsal_s_issuer_issues_on_the_replayed_day(monkeypatch, tmp_path, step):
    live, _ = ISSUERS[step]
    mode(monkeypatch, tmp_path, D19)
    assert live(monkeypatch) == D19


@pytest.mark.parametrize("step", ISSUERS)
def test_on_its_date_and_with_no_mode_the_real_date_stands(monkeypatch, tmp_path, step):
    live, real = ISSUERS[step]
    mode(monkeypatch, tmp_path, real)
    assert live(monkeypatch) == real  # the boundary: the live day itself
    mode(monkeypatch, tmp_path, date(2026, 10, 26))
    assert live(monkeypatch) == real  # a day after it: the real date, never the replayed day
    monkeypatch.delenv(ENV_FNO_REHEARSAL)
    assert live(monkeypatch) == real  # a real run, whatever today is


def test_an_unset_date_is_the_replayed_day_in_a_rehearsal_and_none_in_a_real_run(monkeypatch, tmp_path):
    mode(monkeypatch, tmp_path, D19)
    assert rehearsed_date("price_ranges", None) == D19
    monkeypatch.delenv(ENV_FNO_REHEARSAL)
    assert rehearsed_date("price_ranges", None) is None


def test_the_backfills_keep_the_real_date(monkeypatch, tmp_path):
    """A rehearsal never runs a backfill, and a backfill stops before the real live date: never moved."""
    mode(monkeypatch, tmp_path, D19)
    seen = []
    stub(monkeypatch, ranges, "build_store", "build_session_calendar", "build_builder", "SnapshotChains",
         "build_quote_store", "build_tables")  # fmt: skip
    monkeypatch.setattr(ranges, "build_closes", lambda tables: type("C", (), {"closes": None})())
    monkeypatch.setattr(ranges, "RangeBackfill", lambda *a: seen.append(a[-1]))
    ranges.build_backfill(CFG, eod=False)
    assert seen == [D22]
