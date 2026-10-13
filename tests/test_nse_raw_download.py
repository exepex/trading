"""The standalone NSE download tool (tools/nse_raw_download) keeps the archive layout and never overwrites."""

import hashlib
import importlib.util
import sys
from datetime import date
from pathlib import Path

from fno.storage.raw_source import NseDailyFoSource, NseIndexCloseSource, NseLegacyFoSource, ParticipantOiSource
from fno.storage.wiring import RAW_AREA

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "nse_raw_download" / "nse_raw_download.py"
spec = importlib.util.spec_from_file_location("nse_raw_download", SCRIPT)
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)


def test_the_tool_uses_exactly_the_archive_layout_and_addresses_of_fno_storage():
    pairs = (
        (tool.CURRENT_FO, NseDailyFoSource),
        (tool.OLD_FO, NseLegacyFoSource),
        (tool.INDEX_CLOSE, NseIndexCloseSource),
        (tool.PARTICIPANT_OI, ParticipantOiSource),
    )
    for dataset, source in pairs:
        for day in (date(2019, 1, 2), date(2024, 7, 5), date(2026, 10, 9)):
            assert dataset.path_for(day) == f"{RAW_AREA}/{source.path_for(day)}"
            assert dataset.url_for(day) == source.url_for(source.path_for(day))
    assert tool.relative_path(date(2024, 1, 2)) == tool.CURRENT_FO.path_for(date(2024, 1, 2))
    assert tool.OLD_FO.covers(date(2024, 7, 5)) and not tool.OLD_FO.covers(date(2024, 7, 8))
    assert tool.CURRENT_FO.covers(date(2024, 1, 1)) and not tool.CURRENT_FO.covers(date(2023, 12, 29))


def run(tmp_path, monkeypatch, manifest_rows, answers, start, end, oi_manifest_rows=()):
    manifests = {}
    for dataset, rows in ((tool.CURRENT_FO, manifest_rows), (tool.PARTICIPANT_OI, oi_manifest_rows)):
        manifests[dataset] = tmp_path / f"{dataset.folder.rsplit('/', 1)[-1]}.csv"
        manifests[dataset].write_text("date,url,status,sha256,rows_kept\n" + "".join(f"{r}\n" for r in rows))
    asked = []

    def fake_download(url):
        asked.append(url)
        return answers.pop(0)

    monkeypatch.setattr(tool, "download", fake_download)
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    return tool.run(tmp_path / "fno-research", start, end, manifests), asked


def test_the_folder_comes_from_the_command_line_or_one_question(monkeypatch, tmp_path):
    assert tool.choose_folder(['"G:/My Drive/fno-research"']) == Path("G:/My Drive/fno-research")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert tool.choose_folder([]) == tmp_path  # Enter = the current folder
    monkeypatch.setattr("builtins.input", lambda prompt: "  D:/fno-research  ")
    assert tool.choose_folder([]) == Path("D:/fno-research")


def test_verified_files_are_saved_holidays_are_not_asked_and_a_mismatch_is_never_saved(tmp_path, monkeypatch):
    day, holiday = date(2025, 1, 27), date(2025, 1, 28)
    good = hashlib.sha256(b"zip").hexdigest()
    rows = [f"{day},u,200,{good},1", f"{holiday},u,404,,0"]
    answers = [(200, b"zip"), (200, b"oi csv"), (200, b"index csv"), (404, b"")]
    code, asked = run(tmp_path, monkeypatch, rows, answers, day, holiday)
    root = tmp_path / "fno-research"
    saved = root / tool.CURRENT_FO.path_for(day)
    assert code == 0 and saved.read_bytes() == b"zip" and len(asked) == 4  # the holiday's F&O file was not requested
    assert asked[-1] == tool.PARTICIPANT_OI.url_for(holiday)  # participant OI is asked on its own
    assert (root / tool.INDEX_CLOSE.path_for(day)).read_bytes() == b"index csv"
    saved.write_bytes(b"changed")
    code, asked = run(tmp_path, monkeypatch, rows, [], day, holiday)
    assert code == 1 and asked == [] and saved.read_bytes() == b"changed"  # reported, untouched
    saved.unlink()
    code, _ = run(tmp_path, monkeypatch, rows, [(200, b"tampered")], day, holiday)
    assert code == 1 and not saved.exists()


def test_old_years_get_old_format_and_index_files_and_days_without_files_are_asked_once(tmp_path, monkeypatch):
    friday, saturday = date(2019, 1, 4), date(2019, 1, 5)
    answers = [(200, b"old zip"), (200, b"oi"), (200, b"index"), (404, b""), (404, b"")]
    code, asked = run(tmp_path, monkeypatch, [], answers, friday, saturday)
    root = tmp_path / "fno-research"
    assert code == 0 and len(asked) == 5 and "historical/DERIVATIVES/2019/JAN/fo04JAN2019bhav.csv.zip" in asked[0]
    assert (root / "raw/nse/derivatives/fo-bhavcopy-legacy/2019/01/fo04JAN2019bhav.csv.zip").read_bytes() == b"old zip"
    assert (root / "raw/nse/indices/index-close/2019/01/ind_close_all_04012019.csv").read_bytes() == b"index"
    assert (root / "raw/nse/derivatives/participant-oi/2019/01/fao_participant_oi_04012019.csv").read_bytes() == b"oi"
    code, asked = run(tmp_path, monkeypatch, [], [], friday, saturday)
    assert asked == []  # the Saturday without a file is remembered; the Friday's files are already there


def test_both_formats_are_fetched_where_nse_has_both_and_a_refusal_stops_at_once(tmp_path, monkeypatch):
    day = date(2024, 7, 5)
    code, asked = run(tmp_path, monkeypatch, [], [(200, b"new"), (200, b"old"), (200, b"oi"), (200, b"idx")], day, day)
    assert code == 0 and len(asked) == 4 and "/content/fo/" in asked[0] and "historical" in asked[1]
    code, asked = run(tmp_path, monkeypatch, [], [(429, b"")], date(2024, 7, 8), date(2024, 7, 12))
    assert asked == [tool.CURRENT_FO.url_for(date(2024, 7, 8))]  # nothing more after the refusal


def test_a_certificate_failure_stops_at_once_with_plain_advice(monkeypatch):
    import ssl
    from urllib.error import URLError

    waits = []

    def refuse(request, timeout=None, context=None):
        raise URLError(ssl.SSLCertVerificationError("unable to get local issuer certificate"))

    monkeypatch.setattr(tool, "urlopen", refuse)
    monkeypatch.setattr(tool.time, "sleep", waits.append)
    try:
        tool.download("https://example.invalid/f.zip")
    except tool.CertificateProblem as exc:
        assert "Install Certificates.command" in str(exc) and waits == []  # no pointless retries
    else:
        raise AssertionError("expected CertificateProblem")


def test_verification_is_never_switched_off():
    assert tool.CONTEXT.verify_mode == __import__("ssl").CERT_REQUIRED and tool.CONTEXT.check_hostname


def test_participant_oi_is_checked_against_its_own_manifest_and_its_known_gaps_are_not_asked(tmp_path, monkeypatch):
    day, gap = date(2026, 10, 9), date(2026, 10, 10)
    oi_rows = [f"{day},u,200,{hashlib.sha256(b'oi').hexdigest()},5", f"{gap},u,404,,0"]
    answers = [(200, b"zip"), (200, b"tampered oi"), (200, b"idx"), (404, b"")]
    code, asked = run(tmp_path, monkeypatch, [], answers, day, gap, oi_manifest_rows=oi_rows)
    assert code == 1 and not (tmp_path / "fno-research" / tool.PARTICIPANT_OI.path_for(day)).exists()
    assert tool.PARTICIPANT_OI.url_for(gap) not in asked  # the manifest says NSE has no file that day
    code, asked = run(tmp_path, monkeypatch, [], [(200, b"oi")], day, day, oi_manifest_rows=oi_rows)
    assert code == 0 and asked == [tool.PARTICIPANT_OI.url_for(day)]


def test_the_shipped_participant_oi_manifest_is_read():
    expected, no_file = tool.load_manifests(
        {tool.PARTICIPANT_OI: SCRIPT.with_name(tool.MANIFESTS[tool.PARTICIPANT_OI])}
    )
    assert tool.file_tag(tool.PARTICIPANT_OI, "2019-06-03") in expected
    assert tool.file_tag(tool.PARTICIPANT_OI, "2019-01-05") in no_file  # a Saturday


def test_index_closes_are_fetched_on_a_trading_day_without_an_fo_file(tmp_path, monkeypatch):
    """30 Mar 2021: NSE has no old-format F&O file, but publishes participant OI and the index closes."""
    day = date(2021, 3, 30)
    code, asked = run(tmp_path, monkeypatch, [], [(404, b""), (200, b"oi"), (200, b"index")], day, day)
    root = tmp_path / "fno-research"
    assert code == 0 and asked[-1] == tool.INDEX_CLOSE.url_for(day)
    assert (root / tool.INDEX_CLOSE.path_for(day)).read_bytes() == b"index"
    assert not (root / tool.OLD_FO.path_for(day)).exists()


def test_index_closes_are_not_asked_on_a_day_without_any_derivatives_file(tmp_path, monkeypatch):
    sunday = date(2021, 3, 28)
    code, asked = run(tmp_path, monkeypatch, [], [(404, b""), (404, b"")], sunday, sunday)
    assert code == 0 and tool.INDEX_CLOSE.url_for(sunday) not in asked and len(asked) == 2
