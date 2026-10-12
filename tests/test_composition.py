"""Clean-slate criterion 9: the quote recorder and the `chain` command each use their own provider setting."""

import pytest

from fno import cli, composition
from fno.config import load_app_config
from fno.providers import groww


class Picked(Exception):
    """Stops the command right after the provider is chosen; carries the name that was asked for."""


@pytest.fixture
def chosen(monkeypatch):
    """Records the provider name each code path asks `get_provider` for, without building a provider or the network."""
    names = []

    def fake_get_provider(name, cfg):
        names.append(name)
        raise Picked(name)

    monkeypatch.setattr(composition, "get_provider", fake_get_provider)
    monkeypatch.setattr(cli, "get_provider", fake_get_provider)
    return names


def _config(tmp_path, provider="nse", quotes_provider="auto"):
    path = tmp_path / "config.yaml"
    path.write_text(f"provider: {provider}\nquotes:\n  provider: {quotes_provider}\nlot_sizes: {{NIFTY: 65}}\n")
    return str(path)


def test_the_repository_settings_keep_both_sources_as_before():
    cfg = load_app_config()
    assert cfg["provider"] == "nse" and cfg["quotes"]["provider"] == "auto"


def test_chain_uses_the_root_provider_and_the_recorder_its_own(tmp_path, chosen):
    config = _config(tmp_path)
    with pytest.raises(Picked):
        cli.main(["--config", config, "chain", "NIFTY"])
    with pytest.raises(Picked):
        composition.build_quote_recorder(load_app_config(config))
    assert chosen == ["nse", "auto"]


def test_changing_one_setting_never_changes_the_other(tmp_path, chosen):
    for provider, quotes_provider in (("groww", "auto"), ("nse", "nse")):
        config = _config(tmp_path, provider, quotes_provider)
        with pytest.raises(Picked):
            cli.main(["--config", config, "chain", "NIFTY"])
        with pytest.raises(Picked):
            composition.build_quote_recorder(load_app_config(config))
    assert chosen == ["groww", "auto", "nse", "nse"]


def test_the_command_line_override_changes_chain_only(tmp_path, chosen):
    config = _config(tmp_path)
    with pytest.raises(Picked):
        cli.main(["--config", config, "--provider", "sample", "chain", "NIFTY"])
    with pytest.raises(Picked):
        cli.main(["--config", config, "--provider", "sample", "quotes", "record", "--outside-window"])
    assert chosen == ["sample", "auto"]


def test_auto_picks_groww_with_credentials_and_nse_without(monkeypatch):
    from fno.providers import get_provider

    class FakeGroww:
        name = "groww"

        def __init__(self, config):
            pass

    monkeypatch.setattr(groww, "GrowwProvider", FakeGroww)
    monkeypatch.setattr(groww, "has_groww_credentials", lambda: True)
    assert get_provider("auto", {}).name == "groww"
    monkeypatch.setattr(groww, "has_groww_credentials", lambda: False)
    assert get_provider("auto", {}).name == "nse"
