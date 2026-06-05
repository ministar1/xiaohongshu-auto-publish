from __future__ import annotations

from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class TaskStatus(StrEnum):
    CREATED = "created"
    RESEARCHING = "researching"
    RESEARCH_FAILED = "research_failed"
    WAITING_RESEARCH_EDIT = "waiting_research_edit"
    CONTENT_REVIEWING = "content_reviewing"
    CONTENT_BLOCKED = "content_blocked"
    CONTENT_PASSED_WITH_WARNINGS = "content_passed_with_warnings"
    WRITING_REVIEWING = "writing_reviewing"
    WRITING_FAILED = "writing_failed"
    WAITING_DRAFT_EDIT = "waiting_draft_edit"
    FORMAT_REVIEWING = "format_reviewing"
    FORMAT_BLOCKED = "format_blocked"
    WAITING_FORMAT_CONFIRM = "waiting_format_confirm"
    PACKAGE_READY = "package_ready"
    WAITING_PUBLISH_CONFIRM = "waiting_publish_confirm"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    PUBLISH_FAILED = "publish_failed"
    FAILED = "failed"


class Severity(StrEnum):
    S0 = "S0"
    S1 = "S1"
    S2 = "S2"
    S3 = "S3"


class WritingStyle(StrEnum):
    POPULAR = "popular"
    PROFESSIONAL = "professional"
    BALANCED = "balanced"


class ParseStatus(StrEnum):
    OK = "ok"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(slots=True)
class LastError:
    summary: str
    detail: str = ""
    retryable: bool = False
    stage: str | None = None
    next_action: str | None = None
    related_artifacts: list[str] = field(default_factory=list)


@dataclass(slots=True)
class PromptVersionRecord:
    prompt_id: str
    version: str
    schema_id: str
    schema_version: int
    template_hash: str
    model: str
    locked_at: str


@dataclass(slots=True)
class TaskMetadata:
    task_id: str
    input_type: str
    topic: str
    account_id: str = "default"
    style: WritingStyle = WritingStyle.POPULAR
    audience: str | None = None
    status: TaskStatus = TaskStatus.CREATED
    created_at: str = ""
    updated_at: str = ""
    retry_counts: dict[str, int] = field(default_factory=dict)
    last_failed_stage: str | None = None
    last_error: LastError | None = None
    prompt_versions: dict[str, PromptVersionRecord] = field(default_factory=dict)
    manual_overrides: list[dict[str, str]] = field(default_factory=list)
    current_artifacts: dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ArtifactRef:
    artifact_id: str
    task_id: str
    stage: str
    kind: str
    version: int
    path: str
    created_at: str
    source_artifacts: list[str] = field(default_factory=list)
    user_editable: bool = True
    complete: bool = True
    error_type: str | None = None
    retryable: bool | None = None


@dataclass(slots=True)
class SourceRecord:
    url: str
    title: str
    organization: str
    published_at: str | None
    retrieved_at: str
    credibility: str
    relevance: str
    notes: str = ""


@dataclass(slots=True)
class ReviewIssue:
    location: str
    quote: str
    issue_type: str
    severity: Severity
    risk: str
    suggestion: str
    blocking: bool


@dataclass(slots=True)
class ReviewReport:
    task_id: str
    stage: str
    issues: list[ReviewIssue]
    blocking: bool
    summary: str
    model: str
    created_at: str
    source_artifacts: list[str] = field(default_factory=list)
    raw_output_excerpt: str = ""
    manual_override: bool = False
    parse_status: ParseStatus = ParseStatus.OK
    parse_warnings: list[str] = field(default_factory=list)


@dataclass(slots=True)
class MediaItem:
    path: str
    role: str
    width: int
    height: int
    ratio: str
    description: str
    is_cover_candidate: bool = False


@dataclass(slots=True)
class PublishPackage:
    title: str
    body: str
    hashtags: list[str]
    media_items: list[MediaItem]
    cover_title: str
    source_records: list[SourceRecord]
    review_summary: str
    media_validation_passed: bool
    user_confirmed: bool
    can_publish: bool


@dataclass(slots=True)
class AccountProfile:
    account_id: str
    positioning: str
    audience: str
    tone: str
    forbidden_phrases: list[str] = field(default_factory=list)
    style_examples: list[str] = field(default_factory=list)
    conversion_strategy: str = ""


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def to_jsonable(value: object) -> object:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, Path):
        return str(value)
    if is_dataclass(value) and not isinstance(value, type):
        return {key: to_jsonable(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): to_jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(item) for item in value]
    return value


def _str_dict(data: object) -> dict[str, Any]:
    if isinstance(data, dict):
        return data
    return {}


def last_error_from_dict(data: object) -> LastError | None:
    raw = _str_dict(data)
    if not raw:
        return None
    return LastError(
        summary=str(raw.get("summary", "")),
        detail=str(raw.get("detail", "")),
        retryable=bool(raw.get("retryable", False)),
        stage=str(raw["stage"]) if raw.get("stage") is not None else None,
        next_action=str(raw["next_action"]) if raw.get("next_action") is not None else None,
        related_artifacts=[str(item) for item in raw.get("related_artifacts", [])],
    )


def prompt_record_from_dict(data: object) -> PromptVersionRecord:
    raw = _str_dict(data)
    return PromptVersionRecord(
        prompt_id=str(raw.get("prompt_id", "")),
        version=str(raw.get("version", "")),
        schema_id=str(raw.get("schema_id", "")),
        schema_version=int(raw.get("schema_version", 1)),
        template_hash=str(raw.get("template_hash", "")),
        model=str(raw.get("model", "")),
        locked_at=str(raw.get("locked_at", "")),
    )


def task_from_dict(data: object) -> TaskMetadata:
    raw = _str_dict(data)
    prompt_versions = {str(key): prompt_record_from_dict(value) for key, value in _str_dict(raw.get("prompt_versions")).items()}
    style_raw = str(raw.get("style", WritingStyle.POPULAR.value))
    status_raw = str(raw.get("status", TaskStatus.CREATED.value))
    return TaskMetadata(
        task_id=str(raw["task_id"]),
        input_type=str(raw.get("input_type", "")),
        topic=str(raw.get("topic", "")),
        account_id=str(raw.get("account_id", "default")),
        style=WritingStyle(style_raw),
        audience=str(raw["audience"]) if raw.get("audience") is not None else None,
        status=TaskStatus(status_raw),
        created_at=str(raw.get("created_at", "")),
        updated_at=str(raw.get("updated_at", "")),
        retry_counts={str(key): int(value) for key, value in _str_dict(raw.get("retry_counts")).items()},
        last_failed_stage=str(raw["last_failed_stage"]) if raw.get("last_failed_stage") is not None else None,
        last_error=last_error_from_dict(raw.get("last_error")),
        prompt_versions=prompt_versions,
        manual_overrides=[{str(key): str(value) for key, value in _str_dict(item).items()} for item in raw.get("manual_overrides", [])],
        current_artifacts={str(key): str(value) for key, value in _str_dict(raw.get("current_artifacts")).items()},
    )


def artifact_from_dict(data: object) -> ArtifactRef:
    raw = _str_dict(data)
    return ArtifactRef(
        artifact_id=str(raw["artifact_id"]),
        task_id=str(raw["task_id"]),
        stage=str(raw["stage"]),
        kind=str(raw["kind"]),
        version=int(raw["version"]),
        path=str(raw["path"]),
        created_at=str(raw.get("created_at", "")),
        source_artifacts=[str(item) for item in raw.get("source_artifacts", [])],
        user_editable=bool(raw.get("user_editable", True)),
        complete=bool(raw.get("complete", True)),
        error_type=str(raw["error_type"]) if raw.get("error_type") is not None else None,
        retryable=bool(raw["retryable"]) if raw.get("retryable") is not None else None,
    )
