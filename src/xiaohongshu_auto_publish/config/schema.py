from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class LLMConfig:
    provider: str = "openai-compatible"
    base_url: str = "https://api.openai.com/v1"
    model: str = ""
    api_key_env: str = "XHS_AGENT_LLM_API_KEY"
    timeout_seconds: int = 60
    max_retries: int = 2


@dataclass(slots=True)
class SearchConfig:
    provider: str = "tavily"
    api_key_env: str = "XHS_AGENT_TAVILY_API_KEY"
    max_results: int = 8
    timeout_seconds: int = 30


@dataclass(slots=True)
class StorageConfig:
    workspace_dir: str = "workspace"
    artifact_version_digits: int = 3


@dataclass(slots=True)
class RetentionConfig:
    keep_recent_versions: int = 5
    keep_task_days: int = 180
    archive_dir: str = "workspace/archive"
    cleanup_dry_run_default: bool = True


@dataclass(slots=True)
class WritingConfig:
    default_style: str = "popular"
    title_candidates: int = 5
    enable_series_suggestions: bool = True


@dataclass(slots=True)
class PathConfig:
    config_path: str


@dataclass(slots=True)
class AccountConfig:
    profiles_dir: str = "accounts"
    default_account: str = "default"


@dataclass(slots=True)
class PublishConfig:
    enabled: bool = False
    default_channel: str = "manual"
    require_confirm_before_publish: bool = True


@dataclass(slots=True)
class AppConfig:
    llm: LLMConfig = field(default_factory=LLMConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    retention: RetentionConfig = field(default_factory=RetentionConfig)
    writing: WritingConfig = field(default_factory=WritingConfig)
    source_policy: PathConfig = field(default_factory=lambda: PathConfig("rules/source_policy.toml"))
    format_rules: PathConfig = field(default_factory=lambda: PathConfig("rules/xhs_format_rules.toml"))
    account: AccountConfig = field(default_factory=AccountConfig)
    publish: PublishConfig = field(default_factory=PublishConfig)
    project_root: Path = Path(".")
    runtime_secrets: dict[str, str] = field(default_factory=dict, repr=False)
