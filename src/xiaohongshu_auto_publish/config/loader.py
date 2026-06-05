from __future__ import annotations

import os
import re
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, get_args, get_origin

from xiaohongshu_auto_publish.config.schema import (
    AccountConfig,
    AppConfig,
    LLMConfig,
    PathConfig,
    PublishConfig,
    RetentionConfig,
    SearchConfig,
    StorageConfig,
    WritingConfig,
)
from xiaohongshu_auto_publish.errors import ConfigError

ENV_KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

CONFIG_TEMPLATE = """[llm]
provider = "openai-compatible"
base_url = "https://api.openai.com/v1"
model = ""
api_key_env = "XHS_AGENT_LLM_API_KEY"
timeout_seconds = 60
max_retries = 2

[search]
provider = "tavily"
api_key_env = "XHS_AGENT_TAVILY_API_KEY"
max_results = 8
timeout_seconds = 30

[storage]
workspace_dir = "workspace"
artifact_version_digits = 3

[retention]
keep_recent_versions = 5
keep_task_days = 180
archive_dir = "workspace/archive"
cleanup_dry_run_default = true

[writing]
default_style = "popular"
title_candidates = 5
enable_series_suggestions = true

[source_policy]
config_path = "rules/source_policy.toml"

[format_rules]
config_path = "rules/xhs_format_rules.toml"

[account]
profiles_dir = "accounts"
default_account = "default"

[publish]
enabled = false
default_channel = "manual"
require_confirm_before_publish = true
"""

ENV_EXAMPLE_TEMPLATE = """XHS_AGENT_LLM_API_KEY=
XHS_AGENT_TAVILY_API_KEY=
"""

SOURCE_POLICY_TEMPLATE = """[trusted_sources]
"who.int" = { category = "public_health", priority = 1 }
"cdc.gov" = { category = "public_health", priority = 1 }
"nih.gov" = { category = "medical_institution", priority = 2 }
"nhc.gov.cn" = { category = "health_authority", priority = 1 }

[risk_sources]
example-spam.test = "low credibility"
"""

FORMAT_RULES_TEMPLATE = """[title]
max_length = 40
severity = "confirm"

[body]
max_length = 1200
max_paragraph_length = 120
severity = "warn"

[hashtags]
min_count = 2
max_count = 8
severity = "confirm"

[emoji]
max_count = 20
severity = "warn"

[media]
min_items = 0
max_items = 9
require_cover = false

[[sensitive_words]]
word = "根治"
severity = "block"
reason = "医学健康内容不得承诺根治"
"""

DEFAULT_ACCOUNT_TEMPLATE = """account_id = "default"
positioning = "医学与养生科普账号"
audience = "关注健康生活方式的普通读者"
tone = "通俗、谨慎、不过度承诺"
forbidden_phrases = ["根治", "保证有效", "替代治疗"]
style_examples = ["先给结论，再解释原因，最后给可执行建议"]
conversion_strategy = "用收藏价值和系列化选题引导关注"
"""


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise ConfigError("无法读取 .env 文件", str(path), related_artifacts=[path]) from exc
    for index, line in enumerate(lines, start=1):
        if not line:
            continue
        if "=" not in line:
            raise ConfigError(
                ".env 格式错误",
                f"{path}:{index} 不是 KEY=VALUE 格式",
                related_artifacts=[path],
            )
        key, value = line.split("=", 1)
        if not key or not ENV_KEY_RE.fullmatch(key):
            raise ConfigError(
                ".env 变量名非法",
                f"{path}:{index} 的变量名必须匹配 [A-Za-z_][A-Za-z0-9_]*",
                related_artifacts=[path],
            )
        values[key] = value
    return values


def load_config(
    config_path: str | Path = "config.toml",
    overrides: Sequence[str] | None = None,
    env: Mapping[str, str] | None = None,
) -> AppConfig:
    root = Path.cwd()
    path = Path(config_path)
    if not path.is_absolute():
        path = root / path
    raw = _default_raw()
    if path.exists():
        try:
            loaded = tomllib.loads(path.read_text(encoding="utf-8"))
        except tomllib.TOMLDecodeError as exc:
            raise ConfigError(
                "配置文件 TOML 格式错误",
                f"{path}: {exc}",
                related_artifacts=[path],
            ) from exc
        except OSError as exc:
            raise ConfigError("无法读取配置文件", str(path), related_artifacts=[path]) from exc
        _deep_merge(raw, loaded)

    env_file_values = parse_env_file(root / ".env")
    merged_env: dict[str, str] = dict(env_file_values)
    merged_env.update(dict(os.environ if env is None else env))
    _apply_environment(raw, merged_env)

    config = _config_from_raw(raw)
    config.project_root = root
    config.runtime_secrets = {key: value for key, value in merged_env.items() if key in {config.llm.api_key_env, config.search.api_key_env}}
    for override in overrides or []:
        _apply_override(config, override)
    validate_config(config)
    return config


def check_required_secrets(config: AppConfig) -> list[str]:
    missing: list[str] = []
    if not config.runtime_secrets.get(config.llm.api_key_env):
        missing.append(config.llm.api_key_env)
    if config.search.provider == "tavily" and not config.runtime_secrets.get(config.search.api_key_env):
        missing.append(config.search.api_key_env)
    return missing


def validate_config(config: AppConfig) -> None:
    if config.llm.timeout_seconds <= 0 or config.search.timeout_seconds <= 0:
        raise ConfigError("配置值非法", "timeout_seconds 必须为正数")
    if config.llm.max_retries < 0:
        raise ConfigError("配置值非法", "llm.max_retries 必须大于等于 0")
    if config.retention.keep_recent_versions < 1:
        raise ConfigError("配置值非法", "retention.keep_recent_versions 必须大于等于 1")
    if config.retention.keep_task_days < 0:
        raise ConfigError("配置值非法", "retention.keep_task_days 必须大于等于 0")
    workspace = _resolve_under_root(config.project_root, config.storage.workspace_dir)
    archive = _resolve_under_root(config.project_root, config.retention.archive_dir)
    if not _is_within(archive, workspace):
        raise ConfigError(
            "归档目录越界",
            "retention.archive_dir 必须位于 storage.workspace_dir 内",
            related_artifacts=[archive],
        )


def init_project(root: Path, overwrite: bool = False) -> list[Path]:
    created: list[Path] = []
    files = {
        root / "config.toml": CONFIG_TEMPLATE,
        root / ".env.example": ENV_EXAMPLE_TEMPLATE,
        root / "rules" / "source_policy.toml": SOURCE_POLICY_TEMPLATE,
        root / "rules" / "xhs_format_rules.toml": FORMAT_RULES_TEMPLATE,
        root / "accounts" / "default.toml": DEFAULT_ACCOUNT_TEMPLATE,
    }
    for file_path, content in files.items():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        if file_path.exists() and not overwrite:
            continue
        file_path.write_text(content, encoding="utf-8")
        created.append(file_path)
    for directory in (root / "workspace", root / "workspace" / "archive"):
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)
    return created


def _default_raw() -> dict[str, object]:
    return {
        "llm": {
            "provider": "openai-compatible",
            "base_url": "https://api.openai.com/v1",
            "model": "",
            "api_key_env": "XHS_AGENT_LLM_API_KEY",
            "timeout_seconds": 60,
            "max_retries": 2,
        },
        "search": {
            "provider": "tavily",
            "api_key_env": "XHS_AGENT_TAVILY_API_KEY",
            "max_results": 8,
            "timeout_seconds": 30,
        },
        "storage": {"workspace_dir": "workspace", "artifact_version_digits": 3},
        "retention": {
            "keep_recent_versions": 5,
            "keep_task_days": 180,
            "archive_dir": "workspace/archive",
            "cleanup_dry_run_default": True,
        },
        "writing": {
            "default_style": "popular",
            "title_candidates": 5,
            "enable_series_suggestions": True,
        },
        "source_policy": {"config_path": "rules/source_policy.toml"},
        "format_rules": {"config_path": "rules/xhs_format_rules.toml"},
        "account": {"profiles_dir": "accounts", "default_account": "default"},
        "publish": {
            "enabled": False,
            "default_channel": "manual",
            "require_confirm_before_publish": True,
        },
    }


def _deep_merge(target: dict[str, object], update: Mapping[str, object]) -> None:
    for key, value in update.items():
        if key not in target:
            raise ConfigError("未知配置字段", f"不支持配置项 {key}")
        current = target[key]
        if isinstance(current, dict) and isinstance(value, Mapping):
            _deep_merge(current, value)
        elif isinstance(current, dict):
            raise ConfigError("配置类型错误", f"{key} 必须是 TOML table")
        else:
            target[key] = value


def _apply_environment(raw: dict[str, object], values: Mapping[str, str]) -> None:
    mapping = {
        "XHS_AGENT_LLM_PROVIDER": "llm.provider",
        "XHS_AGENT_LLM_BASE_URL": "llm.base_url",
        "XHS_AGENT_LLM_MODEL": "llm.model",
        "XHS_AGENT_LLM_TIMEOUT_SECONDS": "llm.timeout_seconds",
        "XHS_AGENT_LLM_MAX_RETRIES": "llm.max_retries",
        "XHS_AGENT_SEARCH_PROVIDER": "search.provider",
        "XHS_AGENT_SEARCH_MAX_RESULTS": "search.max_results",
        "XHS_AGENT_WORKSPACE_DIR": "storage.workspace_dir",
    }
    for env_key, path in mapping.items():
        if env_key in values:
            _set_raw_path(raw, path, values[env_key])


def _set_raw_path(raw: dict[str, object], path: str, value: str) -> None:
    section_name, field_name = path.split(".", 1)
    section = raw.get(section_name)
    if not isinstance(section, dict) or field_name not in section:
        raise ConfigError("未知配置字段", path)
    current = section[field_name]
    if isinstance(current, bool):
        section[field_name] = value.lower() in {"1", "true", "yes", "on"}
    elif isinstance(current, int):
        section[field_name] = int(value)
    else:
        section[field_name] = value


def _config_from_raw(raw: Mapping[str, object]) -> AppConfig:
    return AppConfig(
        llm=_dataclass_from_raw(LLMConfig, raw["llm"]),
        search=_dataclass_from_raw(SearchConfig, raw["search"]),
        storage=_dataclass_from_raw(StorageConfig, raw["storage"]),
        retention=_dataclass_from_raw(RetentionConfig, raw["retention"]),
        writing=_dataclass_from_raw(WritingConfig, raw["writing"]),
        source_policy=_dataclass_from_raw(PathConfig, raw["source_policy"]),
        format_rules=_dataclass_from_raw(PathConfig, raw["format_rules"]),
        account=_dataclass_from_raw(AccountConfig, raw["account"]),
        publish=_dataclass_from_raw(PublishConfig, raw["publish"]),
    )


def _dataclass_from_raw(cls: type[Any], raw: object) -> Any:
    if not isinstance(raw, Mapping):
        raise ConfigError("配置类型错误", f"{cls.__name__} 必须是 table")
    names = {field.name for field in fields(cls)}
    extra = set(raw) - names
    if extra:
        raise ConfigError("未知配置字段", ", ".join(sorted(str(item) for item in extra)))
    return cls(**raw)


def _apply_override(config: AppConfig, override: str) -> None:
    if "=" not in override:
        raise ConfigError("CLI 覆盖格式错误", f"{override} 不是 key=value")
    path, value = override.split("=", 1)
    parts = path.split(".")
    if len(parts) != 2:
        raise ConfigError("CLI 覆盖路径错误", "只支持 section.field 形式")
    section = getattr(config, parts[0], None)
    if section is None or not is_dataclass(section):
        raise ConfigError("未知 CLI 覆盖字段", path)
    if not hasattr(section, parts[1]):
        raise ConfigError("未知 CLI 覆盖字段", path)
    current = getattr(section, parts[1])
    converted = _convert_override(value, current)
    object.__setattr__(section, parts[1], converted)


def _convert_override(value: str, current: object) -> object:
    if isinstance(current, bool):
        lowered = value.lower()
        if lowered not in {"true", "false", "1", "0", "yes", "no"}:
            raise ConfigError("CLI 覆盖类型错误", f"{value} 不能转换为 bool")
        return lowered in {"true", "1", "yes"}
    if isinstance(current, int):
        try:
            return int(value)
        except ValueError as exc:
            raise ConfigError("CLI 覆盖类型错误", f"{value} 不能转换为 int") from exc
    if isinstance(current, float):
        try:
            return float(value)
        except ValueError as exc:
            raise ConfigError("CLI 覆盖类型错误", f"{value} 不能转换为 float") from exc
    origin = get_origin(type(current))
    if origin is not None or get_args(type(current)):
        raise ConfigError("CLI 覆盖类型错误", "不支持替换复杂字段")
    return value


def _resolve_under_root(root: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def _is_within(child: Path, parent: Path) -> bool:
    try:
        child.relative_to(parent)
    except ValueError:
        return False
    return True
