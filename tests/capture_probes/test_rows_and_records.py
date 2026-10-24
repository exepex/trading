"""Criteria 8-11 (story MS-P0b): row quality, write-once files, nothing secret or priced in the repository or Slack,
and a commit that stages only the probe's own paths."""

import gzip
import json
import subprocess
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pytest

from fno.capture_probes.archive import SlotArchive, slot_bytes
from fno.capture_probes.command import cmd_capture_probe
from fno.capture_probes.dry_run import MADE_UP_LEVEL
from fno.capture_probes.publish import GitPublisher, RepoPathsCommitter
from fno.capture_probes.rows import quality_of
from fno.capture_probes.wiring import RECEIPTS_AREA
from fno.storage.raw_store import LocalFolderStore, RawFileConflict

from .fakes import SESSION, GrowwError, Rig, status

SEEN = datetime(2026, 10, 29, 4, 37, tzinfo=UTC)


@pytest.mark.parametrize(
    ("bid", "ask", "lot", "age", "quality"),
    [
        (99.0, 101.0, 75, 0, "ok"),
        (None, None, 75, 0, "empty_bid_ask"),
        (0.0, 0.0, 75, 0, "empty_bid_ask"),
        (99.0, None, 75, 0, "one_sided"),
        (None, 101.0, None, 0, "one_sided+lot_unknown"),
        (99.0, 101.0, 75, 15, "ok"),  # exactly 15 minutes old: not yet stale
        (99.0, 101.0, 75, 16, "stale"),
        (None, None, None, 30, "empty_bid_ask+stale+lot_unknown"),
    ],
)
def test_a_row_carries_every_flag_that_applies(bid, ask, lot, age, quality):
    assert quality_of(bid, ask, lot, SEEN - timedelta(minutes=age), SEEN) == quality


def test_a_row_with_no_source_time_is_never_stale():
    assert quality_of(1.0, 2.0, 1, None, SEEN) == "ok"


def test_a_slot_file_is_written_once(tmp_path):
    archive = SlotArchive(LocalFolderStore(tmp_path), "school/p0b")
    lines = [{"row": {"a": 1}}]
    assert archive.save("nse", "2026-10-29", "10:07", lines) == "ok"
    assert archive.save("nse", "2026-10-29", "10:07", lines) == "ok"  # same bytes: a no-op
    assert archive.save("nse", "2026-10-29", "10:07", [{"row": {"a": 2}}]) == "conflict"
    assert archive.save("nse", "2026-10-29", "10:37", []) == "none"
    assert gzip.decompress(slot_bytes(lines)).decode() == '{"row": {"a": 1}}\n'
    with pytest.raises(RawFileConflict):
        LocalFolderStore(tmp_path).put("school/p0b/nse/2026-10-29/1007.jsonl.gz", b"other")


def _prices() -> list[str]:
    figures = []
    for level in MADE_UP_LEVEL.values():
        figures += [f"{level:g}", f"{level * 0.999:g}", f"{level * 1.001:g}", f"{level - 1:g}", f"{level + 1:g}"]
    return figures


def test_nothing_printed_posted_or_committed_holds_a_price_or_secret(tmp_path):
    rig = Rig(tmp_path, groww_faults={30: GrowwError("401")}, nse_faults={5: status(403)})
    code, lines = rig.run()
    committed = rig.counts().to_json() + (tmp_path / "capture_errors.csv").read_text()
    public = "\n".join(lines + rig.alerts.sent) + committed
    assert rig.alerts.sent  # the stops were posted
    for figure in _prices():
        assert f" {figure} " not in f" {public} " and f'": {figure},' not in committed, figure
    for secret in ("SECRET-IN-MESSAGE", "Cookie", "Bearer", "token", "User-Agent"):
        assert secret not in public


def test_the_dry_run_command_writes_only_under_its_folder(tmp_path, capsys):
    class Args:
        dry_run, session = tmp_path, SESSION

    assert cmd_capture_probe(Args()) == 0
    out = capsys.readouterr().out
    assert "done, 206 Groww and 44 NSE requests" in out
    written = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob("*") if p.is_file())
    assert written[0] == "counts/2026-10-29.json" and len([p for p in written if p.endswith(".gz")]) == 8
    assert json.loads((tmp_path / "counts" / "2026-10-29.json").read_text())["session"] == "2026-10-29"


def test_the_live_command_refuses_a_session_date():
    class Args:
        dry_run, session = None, date(2026, 10, 29)

    lines = []
    assert cmd_capture_probe(Args(), lines.append) == 2


def test_a_commit_stages_only_the_probe_s_own_paths(tmp_path):
    git = []

    def run(args, **kw):
        git.append(args)
        out = ""
        if args[1] == "ls-files":
            out = "\0".join(["receipts/data/school/p0b/nse/2026-10-29/1007.jsonl.gz.sha256",
                             "research/school/probes/p0b/2026-10-29.json", "research/ops/capture_errors.csv",
                             "research/other/file.csv", "receipts/data/other/x.sha256"])  # fmt: skip
        elif args[1] == "status":
            out = " M research/school/probes/p0b/2026-10-29.json\n"
        elif args[1:3] == ["config", "core.hooksPath"]:
            out = ".githooks"
        return subprocess.CompletedProcess(args, 0, stdout=out, stderr="")

    owned = (RECEIPTS_AREA, "research/school/probes/p0b/", "research/ops/capture_errors.csv")
    committer = RepoPathsCommitter(Path(tmp_path), owned, run=run)
    assert GitPublisher(committer).publish("slot 10:07 counts") is None
    adds = [args for args in git if args[1] in ("add", "commit")]
    for args in adds:
        paths = args[args.index("--") + 1 :]
        assert paths == list(owned), args
    assert not any("--no-verify" in args for args in git)
