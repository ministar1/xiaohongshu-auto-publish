from __future__ import annotations

from pathlib import Path

import pytest

from xiaohongshu_auto_publish.account.profile import AccountProfileService
from xiaohongshu_auto_publish.errors import ConfigError


def test_default_account_loads(app_config: object) -> None:
    profile = AccountProfileService(app_config).load_default()
    assert profile.account_id == "default"
    assert profile.positioning


def test_missing_account_raises_config_error(app_config: object) -> None:
    with pytest.raises(ConfigError):
        AccountProfileService(app_config).load_profile("missing")


def test_multiple_accounts_are_independent(app_config: object) -> None:
    accounts = Path(app_config.account.profiles_dir)
    (accounts / "second.toml").write_text(
        'account_id="second"\npositioning="定位2"\naudience="受众2"\ntone="语气2"\n',
        encoding="utf-8",
    )
    service = AccountProfileService(app_config)
    assert {item.account_id for item in service.list_profiles()} == {"default", "second"}
    assert service.show_profile("second").positioning == "定位2"


def test_show_profile_does_not_expose_secret(app_config: object) -> None:
    summary = AccountProfileService(app_config).show_profile("default")
    assert "secret" not in str(summary)
