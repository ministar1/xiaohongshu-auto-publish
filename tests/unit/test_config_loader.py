from __future__ import annotations

from pathlib import Path

import pytest

from xiaohongshu_auto_publish.config.loader import check_required_secrets, load_config, parse_env_file
from xiaohongshu_auto_publish.errors import ConfigError


def test_config_load_priority_env_and_cli(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "config.toml").write_text("[llm]\nmodel='from-file'\ntimeout_seconds=20\n", encoding="utf-8")
    (tmp_path / ".env").write_text("XHS_AGENT_LLM_MODEL=from-env\n", encoding="utf-8")
    config = load_config(
        tmp_path / "config.toml",
        ["llm.model=from-cli", "llm.timeout_seconds=30"],
        env={"XHS_AGENT_LLM_API_KEY": "secret", "XHS_AGENT_TAVILY_API_KEY": "search"},
    )
    assert config.llm.model == "from-cli"
    assert config.llm.timeout_seconds == 30


def test_env_parser_rejects_invalid_key(tmp_path: Path) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("1BAD=value\n", encoding="utf-8")
    with pytest.raises(ConfigError):
        parse_env_file(env_path)


def test_config_check_only_returns_missing_names(app_config: object) -> None:
    config = app_config
    assert check_required_secrets(config) == []
    config.runtime_secrets = {}
    assert check_required_secrets(config) == ["XHS_AGENT_LLM_API_KEY", "XHS_AGENT_TAVILY_API_KEY"]


def test_invalid_override_key_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ConfigError):
        load_config(overrides=["llm.unknown=value"])
