"""The standalone NSE download tool (tools/nse_raw_download) keeps the archive layout and never overwrites."""

import hashlib
import importlib.util
import sys
from datetime import date
from pathlib import Path

from fno.storage.raw_source import NseDailyFoSource
from fno.storage.wiring import RAW_AREA

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "nse_raw_download" / "nse_raw_download.py"
spec = importlib.util.spec_from_file_location("nse_raw_download", SCRIPT)
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)


def test_the_tool_uses_exactly_the_archive_layout_of_fno_storage():
    for day in (date(2024, 1, 2), date(2026, 10, 9)):
        assert tool.relative_path(day) == f"{RAW_AREA}/{NseDailyFoSource.path_for(day)}"
        assert tool.BASE_URL + tool.FILENAME.format(day=day) == NseDailyFoSource.url_for(NseDailyFoSource.path_for(day))


def run(tmp_path, monkeypatch, manifest_rows, answers, start=date(2024, 1, 25), end=date(2024, 1, 26)):
    manifest = tmp_path / "manifest.csv"
    manifest.write_text("date,url,status,sha256,rows_kept\n" + "".join(f"{r}\n" for r in manifest_rows))
    asked = []

    def fake_download(url):
        asked.append(url)
        return answers.pop(0)

    monkeypatch.setattr(tool, "download", fake_download)
    monkeypatch.setattr(tool.time, "sleep", lambda s: None)
    return tool.run(tmp_path / "fno-research", start, end, manifest), asked


def test_the_folder_comes_from_the_command_line_or_one_question(monkeypatch, tmp_path):
    assert tool.choose_folder(['"G:/My Drive/fno-research"']) == Path("G:/My Drive/fno-research")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("builtins.input", lambda prompt: "")
    assert tool.choose_folder([]) == tmp_path  # Enter = the current folder
    monkeypatch.setattr("builtins.input", lambda prompt: "  D:/fno-research  ")
    assert tool.choose_folder([]) == Path("D:/fno-research")


def test_verified_files_are_saved_holidays_are_not_asked_and_a_mismatch_is_never_saved(tmp_path, monkeypatch):
    good = hashlib.sha256(b"zip").hexdigest()
    rows = [f"2024-01-25,u,200,{good},1", "2024-01-26,u,404,,0"]
    code, asked = run(tmp_path, monkeypatch, rows, [(200, b"zip")])
    saved = tmp_path / "fno-research" / tool.relative_path(date(2024, 1, 25))
    assert code == 0 and saved.read_bytes() == b"zip" and len(asked) == 1  # the holiday was not requested
    saved.write_bytes(b"changed")
    code, asked = run(tmp_path, monkeypatch, rows, [])
    assert code == 1 and asked == [] and saved.read_bytes() == b"changed"  # reported, untouched
    saved.unlink()
    code, _ = run(tmp_path, monkeypatch, rows, [(200, b"tampered")])
    assert code == 1 and not saved.exists()


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
