"""Story G10 completion, criteria 4, 7 and 9: the daily run's two v4 steps as built. `v4_release` runs `v4-pack release`
after the `v4` part has ended (at most 14:45), `v4_deadline` runs `v4-pack deadline` from 15:12; both live from
`daily.live_from.v4_pack`, each committing only its own receipts; the step order is fixed in `DAILY_RUN_STEPS`."""

from datetime import date, time

from fno.constants import DAILY_RUN_STEPS
from fno.daily.quote_steps import AfterPart
from fno.daily.steps import Alerted, CommandStep, LiveFrom, NotBefore
from fno.daily.v4_wiring import DEADLINE, RELEASE
from fno.v4_pack import wiring as pack_wiring

from .test_candle_step import _built_steps


def test_the_order_puts_the_release_after_the_forecasts_and_before_the_desk_and_the_deadline_last():
    order = list(DAILY_RUN_STEPS)
    assert order.index("forecasts_v4") + 1 == order.index("v4_release") == order.index("versions") - 1
    assert order.index("v4_deadline") == order.index("candles") - 1  # from 15:12, before 15:33's candles


def test_the_built_steps_wait_for_their_times_and_commit_only_their_receipts(monkeypatch):
    steps = _built_steps(monkeypatch)
    release, deadline = steps["v4_release"], steps["v4_deadline"]
    assert isinstance(release, Alerted) and isinstance(release.step, LiveFrom) and release.step.live_from is None
    after = release.step.step
    assert isinstance(after, AfterPart) and (after.name, after.by) == ("v4", time(14, 45))
    assert isinstance(after.step, CommandStep) and after.step.arguments(date(2026, 10, 26)) == RELEASE
    assert after.step.pathspecs == ("receipts/data/v4/days/", "receipts/data/v4/packs/")
    waiting = deadline.step.step
    assert isinstance(waiting, NotBefore) and waiting.at == time(15, 12)
    assert waiting.step.arguments(date(2026, 10, 26)) == DEADLINE
    assert waiting.step.pathspecs == ("receipts/data/v4/deadlines/",)


def test_a_record_with_a_v4_sidecar_counts_as_recorded(tmp_path):
    recorded = pack_wiring._recorded_v4("groww/derivatives/quote-snapshots-v4")
    day = date(2026, 10, 26)
    assert not recorded(tmp_path, day)
    folder = tmp_path / "research/data/quotes/groww/derivatives/quote-snapshots-v4/2026/10"
    folder.mkdir(parents=True)
    (folder / "nifty_20261026_143000.meta.json").write_text("{}")
    assert recorded(tmp_path, day) and not recorded(tmp_path, date(2026, 10, 27))


def test_claude_md_gives_the_steps_in_the_code_s_order():
    """Judge 584 SF3: the routine reads CLAUDE.md; the deadline check runs before the candles, A4h's reads last."""
    from fno.config import ROOT

    text = " ".join((ROOT / "CLAUDE.md").read_text(encoding="utf-8").split())
    section = text.split("## Daily desk routine", 1)[1].split("## ", 1)[0]
    order = [section.index(words) for words in ("protocol v4's release", "E3's desk", "v4's 15:10 deadline check",
                                                  "candle catch-up", "last, A4h's close reads")]  # fmt: skip
    assert order == sorted(order) and "last, v4's 15:10 deadline check" not in section


def test_nifty_s_14_55_files_and_the_v4_files_are_apart_by_git_itself(tmp_path):
    """The NIFTY-glob plant without the constant: git stages NIFTY's part's own spec on a real tree, never a v4 file."""
    import shutil
    import subprocess

    from fno.config import ROOT
    from fno.daily.quote_parts import QUOTE_PARTS

    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")
    folders = ("quote-snapshots", "quote-snapshots-v4")
    for folder in folders:
        sidecar = tmp_path / f"research/data/quotes/groww/derivatives/{folder}/2026/10/nifty_20261026_143000.meta.json"
        sidecar.parent.mkdir(parents=True)
        sidecar.write_text("{}")
    nifty = next(part for part in QUOTE_PARTS if part.name == "nifty")
    staged = subprocess.run(["git", "add", "--dry-run", *nifty.pathspecs], cwd=tmp_path, capture_output=True,
                            text=True, check=True).stdout  # fmt: skip
    assert "quote-snapshots/2026" in staged and "quote-snapshots-v4" not in staged
