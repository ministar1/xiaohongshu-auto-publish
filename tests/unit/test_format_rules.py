from __future__ import annotations

import pytest

from xiaohongshu_auto_publish.errors import ConfigError
from xiaohongshu_auto_publish.rules.format_rules import FormatRules, RuleSeverity


def test_format_rules_defaults_and_sensitive_word(app_config: object) -> None:
    app_config.format_rules.config_path = "missing.toml"
    rules = FormatRules.load(app_config)
    issues = rules.check_text("能根治吗", "正文", ["健康", "科普"])
    assert issues[0].severity == RuleSeverity.BLOCK


def test_format_rules_invalid_toml_rejected(app_config: object) -> None:
    path = app_config.project_root / "bad_rules.toml"
    path.write_text("[title\n", encoding="utf-8")
    app_config.format_rules.config_path = str(path)
    with pytest.raises(ConfigError):
        FormatRules.load(app_config)
