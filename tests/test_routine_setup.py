"""Story O7: every routine sets up through tools/routine_setup.sh, which installs with the interpreter it checks."""

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SETUP = ROOT / "tools" / "routine_setup.sh"
ROUTINE_DOCS = ("CLAUDE.md", "AGENTS.md", "README.md")
BARE_PIP = re.compile(r"(?<!-m )\bpip3? install\b")


def _code_lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines() if not line.lstrip().startswith("#")]


def test_setup_installs_only_through_the_interpreter_it_checks():
    lines = _code_lines(SETUP)
    assert not [line for line in lines if BARE_PIP.search(line)]
    assert any("-m pip install" in line and "--use-pep517" in line for line in lines)
    assert any('"$name" -c "import $modules"' in line for line in lines)


def test_setup_covers_both_names_and_turns_hooks_on():
    text = SETUP.read_text(encoding="utf-8")
    assert text.count("for name in python3 python") == 2
    assert "git config core.hooksPath .githooks" in text
    assert "set -eu" in text


def test_routine_docs_never_name_a_bare_pip_install():
    offenders = [
        f"{name}:{number}"
        for name in ROUTINE_DOCS
        for number, line in enumerate((ROOT / name).read_text(encoding="utf-8").splitlines(), 1)
        if BARE_PIP.search(line)
    ]
    assert offenders == []


def test_the_3pm_routine_and_readme_name_the_script():
    claude = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    recorder = claude.split("## Daily desk routine", 1)[1].split("\n## ", 1)[0]
    assert "sh tools/routine_setup.sh --groww" in recorder
    assert "sh tools/routine_setup.sh --groww" in (ROOT / "README.md").read_text(encoding="utf-8")


def _run_setup_with_fake_python(tmp_path: Path, plain_install_works: bool, repeat_works: bool):
    """Runs the real script with a stand-in `python3` that logs its pip calls and answers the probe and the import."""
    fake = tmp_path / "python3"
    log = tmp_path / "calls.log"
    fake.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  *"-m pip install"*)\n'
        '    echo "$*" >> "$LOG"\n'
        '    case "$*" in *--ignore-installed*) exit $REPEAT_EXIT ;; *) exit $PLAIN_EXIT ;; esac ;;\n'
        '  *sys.executable*) echo "$0 $0" ;;\n'
        "  *) exit 0 ;;\n"
        "esac\n",
        encoding="utf-8",
    )
    fake.chmod(0o755)
    env = {
        "PATH": f"{tmp_path}:/usr/bin:/bin",
        "HOME": str(tmp_path),
        "LOG": str(log),
        "PLAIN_EXIT": "0" if plain_install_works else "1",
        "REPEAT_EXIT": "0" if repeat_works else "1",
    }
    result = subprocess.run(["sh", str(SETUP)], capture_output=True, text=True, env=env, cwd=ROOT, check=False)
    calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
    return result, calls


def test_setup_repeats_over_system_packages_when_the_plain_install_fails(tmp_path):
    result, calls = _run_setup_with_fake_python(tmp_path, plain_install_works=False, repeat_works=True)
    assert result.returncode == 0, result.stderr
    assert "routine setup ok" in result.stdout
    assert [("--ignore-installed" in call) for call in calls] == [False, True]


def test_setup_does_not_repeat_when_the_plain_install_works(tmp_path):
    result, calls = _run_setup_with_fake_python(tmp_path, plain_install_works=True, repeat_works=False)
    assert result.returncode == 0, result.stderr
    assert len(calls) == 1 and "--ignore-installed" not in calls[0]


def test_setup_stops_loudly_when_both_installs_fail(tmp_path):
    result, _ = _run_setup_with_fake_python(tmp_path, plain_install_works=False, repeat_works=False)
    assert result.returncode == 1
    assert "routine setup FAILED: installing into" in result.stderr
