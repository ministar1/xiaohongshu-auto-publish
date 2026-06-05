from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import ConfigError
from xiaohongshu_auto_publish.models import AccountProfile


@dataclass(frozen=True, slots=True)
class ProfileSummary:
    account_id: str
    is_default: bool
    path: Path
    positioning: str
    audience: str
    tone: str


class AccountProfileService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._profiles_dir = self._resolve_profiles_dir()

    def load_default(self) -> AccountProfile:
        return self.load_profile(self._config.account.default_account)

    def load_profile(self, account_id: str) -> AccountProfile:
        path = self._profile_path(account_id)
        if not path.exists():
            raise ConfigError(
                "账号画像不存在",
                f"未找到账号画像 {account_id}: {path}",
                next_action="运行 xhs-agent init 创建默认账号，或检查 account.profiles_dir",
                related_artifacts=[path],
            )
        try:
            raw = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError("账号画像 TOML 格式错误", f"{path}: {exc}", related_artifacts=[path]) from exc
        except OSError as exc:
            raise ConfigError("无法读取账号画像", str(path), related_artifacts=[path]) from exc
        profile = _profile_from_raw(raw, path)
        if profile.account_id != account_id:
            raise ConfigError(
                "账号画像 ID 不一致",
                f"{path.name} 中 account_id={profile.account_id!r}，应为 {account_id!r}",
                related_artifacts=[path],
            )
        return profile

    def list_profiles(self) -> list[ProfileSummary]:
        if not self._profiles_dir.exists():
            return []
        summaries: list[ProfileSummary] = []
        for path in sorted(self._profiles_dir.glob("*.toml")):
            account_id = path.stem
            try:
                profile = self.load_profile(account_id)
            except ConfigError:
                continue
            summaries.append(
                ProfileSummary(
                    account_id=profile.account_id,
                    is_default=profile.account_id == self._config.account.default_account,
                    path=path,
                    positioning=profile.positioning,
                    audience=profile.audience,
                    tone=profile.tone,
                )
            )
        return summaries

    def show_profile(self, account_id: str) -> ProfileSummary:
        profile = self.load_profile(account_id)
        return ProfileSummary(
            account_id=profile.account_id,
            is_default=profile.account_id == self._config.account.default_account,
            path=self._profile_path(account_id),
            positioning=profile.positioning,
            audience=profile.audience,
            tone=profile.tone,
        )

    def _resolve_profiles_dir(self) -> Path:
        path = Path(self._config.account.profiles_dir)
        if not path.is_absolute():
            path = self._config.project_root / path
        return path.resolve()

    def _profile_path(self, account_id: str) -> Path:
        if not account_id or any(char in account_id for char in "\\/"):
            raise ConfigError("账号 ID 非法", "账号 ID 不能包含路径分隔符")
        path = (self._profiles_dir / f"{account_id}.toml").resolve()
        try:
            path.relative_to(self._profiles_dir)
        except ValueError as exc:
            raise ConfigError("账号画像路径越界", str(path), related_artifacts=[path]) from exc
        return path


def _profile_from_raw(raw: dict[str, Any], path: Path) -> AccountProfile:
    missing = [field for field in ("account_id", "positioning", "audience", "tone") if not raw.get(field)]
    if missing:
        raise ConfigError(
            "账号画像缺少必填字段",
            f"{path} 缺少: {', '.join(missing)}",
            related_artifacts=[path],
        )
    return AccountProfile(
        account_id=str(raw["account_id"]),
        positioning=str(raw["positioning"]),
        audience=str(raw["audience"]),
        tone=str(raw["tone"]),
        forbidden_phrases=[str(item) for item in raw.get("forbidden_phrases", [])],
        style_examples=[str(item) for item in raw.get("style_examples", [])],
        conversion_strategy=str(raw.get("conversion_strategy", "")),
    )
