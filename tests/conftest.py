from __future__ import annotations

from pathlib import Path

import pytest

from xiaohongshu_auto_publish.config.loader import init_project
from xiaohongshu_auto_publish.config.schema import AppConfig


@pytest.fixture
def app_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppConfig:
    monkeypatch.chdir(tmp_path)
    init_project(tmp_path)
    config = AppConfig(project_root=tmp_path)
    config.storage.workspace_dir = str(tmp_path / "workspace")
    config.retention.archive_dir = str(tmp_path / "workspace" / "archive")
    config.account.profiles_dir = str(tmp_path / "accounts")
    config.source_policy.config_path = str(tmp_path / "rules" / "source_policy.toml")
    config.format_rules.config_path = str(tmp_path / "rules" / "xhs_format_rules.toml")
    config.runtime_secrets = {
        config.llm.api_key_env: "secret-llm",
        config.search.api_key_env: "secret-search",
    }
    return config
