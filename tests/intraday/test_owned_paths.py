"""Story A16e: the live committer commits only A16's own paths (`slots/`, `rv/`, `heartbeat.json`), passes only those
that exist or are tracked, and refuses to pull or commit while anything else is staged in the checkout, with one
alert per run. Real Git: a bare origin and a clone, as in the two-clone test."""

from datetime import time

from fno.alerts.sender import SENT
from fno.storage.raw_store import LocalFolderStore
from tests.intraday.fakes import DAY, FakeAlerts, FakeClock, ist
from tests.intraday.test_two_clones import FOLDER, clone, git, recorder

STRAY_RV_CANDLE = f"{FOLDER}/rv-candle/2026/nifty_rv_candle_20261015.csv"
STRAY_TMP = f"{FOLDER}/heartbeat.json.tmp"
MANIFEST_ROW = "research/data/manifests/groww-candles/nifty-15m.csv"
REFUSED = "intraday files NOT pulled or committed: 1 file(s) staged that are not the recorder's"


def checkout_with_origin(tmp_path):
    origin = tmp_path / "origin.git"
    git(tmp_path, "init", "-q", "--bare", "-b", "main", str(origin))
    seed = clone(tmp_path, origin, "seed")
    (seed / "README.md").write_text("x\n")
    git(seed, "add", "README.md")
    git(seed, "commit", "-q", "-m", "start")
    git(seed, "push", "-q", "origin", "HEAD:main")
    return seed, clone(tmp_path, origin, "run")


def write(checkout, path, text="stray\n"):
    target = checkout / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def build(tmp_path, checkout, hour, minute, second=0, alerts=None):
    return recorder(checkout, LocalFolderStore(tmp_path / "drive"), FakeClock(ist(DAY, hour, minute, second)),
                    alerts=alerts)  # fmt: skip


def pushed_files(seed) -> set[str]:
    git(seed, "pull", "-q", "origin", "main")
    return set(git(seed, "ls-files").split()) - {"README.md"}


def staged(checkout) -> list[str]:
    return git(checkout, "diff", "--cached", "--name-only").split()


def test_only_the_recorders_paths_are_committed_and_strays_beside_them_stay_untracked(tmp_path):
    seed, checkout = checkout_with_origin(tmp_path)
    for path in (STRAY_RV_CANDLE, STRAY_TMP):
        write(checkout, path)
    outcome = build(tmp_path, checkout, 15, 29, 30).snapshot()  # the 15:30 mark: the session's RV is written too
    assert outcome.lines[-1].startswith("intraday files committed and pushed")
    files = pushed_files(seed)
    assert f"{FOLDER}/heartbeat.json" in files and f"{FOLDER}/rv/2026/nifty_rv_20261015.csv" in files
    assert {f.split("/")[3] for f in files} == {"slots", "rv", "heartbeat.json"}  # nothing else reached GitHub
    untracked = git(checkout, "ls-files", "--others", "--exclude-standard").split()
    assert sorted(untracked) == sorted([STRAY_RV_CANDLE, STRAY_TMP])  # left exactly as they were


def test_a_fresh_folder_without_rv_commits_its_first_slot_row_and_heartbeat(tmp_path):
    seed, checkout = checkout_with_origin(tmp_path)
    outcome = build(tmp_path, checkout, 9, 14).snapshot()  # the first mark of the first session: no rv/ yet
    assert not (checkout / FOLDER / "rv").exists()
    assert outcome.lines[-1].startswith("intraday files committed and pushed")
    assert pushed_files(seed) == {f"{FOLDER}/heartbeat.json", f"{FOLDER}/slots/2026/10/15/nifty_20261015_0915.csv"}


def test_no_owned_path_at_all_and_a_stray_file_give_nothing_to_commit_and_no_refusal(tmp_path):
    _, checkout = checkout_with_origin(tmp_path)
    write(checkout, STRAY_RV_CANDLE)
    alerts = FakeAlerts()
    sync = build(tmp_path, checkout, 9, 14, alerts=alerts).sync
    assert sync.commit("empty") == "intraday files: nothing new to commit"
    assert sync.pull() == "pulled main" and alerts.sent == []


def test_a_file_staged_in_the_folder_by_another_writer_stops_pull_and_commit_with_one_alert(tmp_path):
    seed, checkout = checkout_with_origin(tmp_path)
    write(checkout, STRAY_RV_CANDLE)
    git(checkout, "add", STRAY_RV_CANDLE)
    head = git(checkout, "rev-parse", "HEAD")
    alerts = FakeAlerts()
    run = build(tmp_path, checkout, 9, 14, alerts=alerts)
    outcome = run.snapshot()
    assert outcome.lines[0] == f"{REFUSED}: {STRAY_RV_CANDLE}; {SENT}"  # the pull line
    assert outcome.lines[-1] == f"{REFUSED}: {STRAY_RV_CANDLE}"  # the commit line: refused, alert already sent
    assert alerts.sent == [f"{REFUSED}: {STRAY_RV_CANDLE}"]
    assert git(checkout, "rev-parse", "HEAD") == head and staged(checkout) == [STRAY_RV_CANDLE]
    assert (checkout / FOLDER / "slots/2026/10/15/nifty_20261015_0915.csv").exists()  # kept on disk, not lost
    git(checkout, "reset", "-q", "--", STRAY_RV_CANDLE)  # the other writer clears its staging
    assert run.sync.commit("after").startswith("intraday files committed and pushed (2 file(s))")
    assert pushed_files(seed) == {f"{FOLDER}/heartbeat.json", f"{FOLDER}/slots/2026/10/15/nifty_20261015_0915.csv"}


def test_a_manifest_row_staged_outside_the_folder_is_refused_too(tmp_path):
    _, checkout = checkout_with_origin(tmp_path)
    write(checkout, MANIFEST_ROW, "path,sha256\n")
    git(checkout, "add", MANIFEST_ROW)
    head = git(checkout, "rev-parse", "HEAD")
    alerts = FakeAlerts()
    outcome = build(tmp_path, checkout, 9, 14, alerts=alerts).snapshot()
    assert outcome.lines[-1] == f"{REFUSED}: {MANIFEST_ROW}"
    assert alerts.sent == [f"{REFUSED}: {MANIFEST_ROW}"]
    assert git(checkout, "rev-parse", "HEAD") == head and staged(checkout) == [MANIFEST_ROW]


def test_a_run_of_three_marks_with_a_foreign_file_staged_sends_one_alert(tmp_path):
    _, checkout = checkout_with_origin(tmp_path)
    write(checkout, MANIFEST_ROW)
    git(checkout, "add", MANIFEST_ROW)
    alerts = FakeAlerts()
    outcomes = build(tmp_path, checkout, 9, 14, alerts=alerts).run(until=time(9, 45))
    assert [o.mark for o in outcomes] == ["09:15", "09:30", "09:45"]
    assert all(o.lines[-1] == f"{REFUSED}: {MANIFEST_ROW}" for o in outcomes)  # three refusal lines
    assert len(alerts.sent) == 1  # one alert per run, never one per mark


def test_more_than_five_staged_paths_are_shown_as_five_and_a_count(tmp_path):
    _, checkout = checkout_with_origin(tmp_path)
    names = [f"other/file_{n}.txt" for n in range(7)]
    for name in names:
        write(checkout, name)
    git(checkout, "add", "other")
    line = build(tmp_path, checkout, 9, 14).sync.pull()
    assert line.startswith("intraday files NOT pulled or committed: 7 file(s)")
    assert ", ".join(names[:5]) + f" and 2 more; {SENT}" in line
