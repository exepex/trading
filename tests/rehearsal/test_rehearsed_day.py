"""REH1, acceptance 1 over O2's fixture day through the real wiring: with the mode set, every Drive write of the whole
run lands under `dryrun/<run_id>/` and the real record keeps every file it had. The harness's Drive seam is wrapped by
the rehearsal's own function, exactly as the real builder wraps it (the guard's test shows the real builder does). The
fixture's clock is the harness's, so the rehearsal's skipped waits fall back to the run's own waits."""

from fno.constants import ENV_FNO_REHEARSAL
from fno.rehearsal.clock import ReplayClock
from fno.rehearsal.drive_wiring import rehearsed_drive
from fno.rehearsal.mode import Rehearsal
from tests.e2e.harness import fixture_day


def test_a_rehearsed_day_writes_only_under_dryrun_and_never_the_real_record(tmp_path, monkeypatch):
    day = fixture_day(tmp_path, monkeypatch)
    mode = Rehearsal.new(day.day, tmp_path / "home", day.root)
    monkeypatch.setenv(ENV_FNO_REHEARSAL, mode.to_env())
    for seam in ("fno.storage.wiring.build_owner_drive", "fno.storage.quote_wiring.build_owner_drive"):
        monkeypatch.setattr(seam, lambda *a, **k: rehearsed_drive(day.drive))
    ReplayClock(mode.state).start(day.clock())
    before = dict(day.drive.files)
    assert day.run() == (0, "day done")
    written = {path for path in day.drive.files if path not in before}
    assert written and all(path.startswith(f"{mode.drive_root}/") for path in written)
    assert {path: day.drive.files[path] for path in before} == before  # the real record: every file as it was
