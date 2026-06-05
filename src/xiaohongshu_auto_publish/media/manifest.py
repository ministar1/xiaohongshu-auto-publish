from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlparse

from xiaohongshu_auto_publish.errors import MediaValidationError
from xiaohongshu_auto_publish.models import MediaItem

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
MAX_IMAGE_BYTES = 15 * 1024 * 1024


class MediaValidationStage(StrEnum):
    FORMAT = "format"
    PACKAGE = "package"


@dataclass(frozen=True, slots=True)
class MediaValidationIssue:
    path: str
    severity: str
    message: str


@dataclass(frozen=True, slots=True)
class ImageValidationResult:
    passed: bool
    issues: list[MediaValidationIssue]


@dataclass(slots=True)
class MediaManifest:
    task_dir: Path
    items: list[MediaItem] = field(default_factory=list)

    @classmethod
    def load(cls, task_dir: Path) -> MediaManifest:
        path = task_dir / "media" / "media_manifest.json"
        if not path.exists():
            return cls(task_dir=task_dir, items=[])
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise MediaValidationError("素材 manifest 读取失败", str(path), related_artifacts=[path]) from exc
        if not isinstance(raw, dict) or not isinstance(raw.get("items", []), list):
            raise MediaValidationError("素材 manifest 根结构错误", "必须包含 items 列表", related_artifacts=[path])
        items = [_media_item(item, task_dir, path) for item in raw.get("items", [])]
        return cls(task_dir=task_dir, items=items)

    def validate(self, stage: MediaValidationStage, require_cover: bool = False) -> ImageValidationResult:
        issues: list[MediaValidationIssue] = []
        if require_cover and not any(item.role == "cover" or item.is_cover_candidate for item in self.items):
            issues.append(MediaValidationIssue("", "block", "缺少封面候选素材"))
        for item in self.items:
            path = resolve_media_path(self.task_dir, item.path)
            image = validate_image_file(path, item.path, missing_severity="warn" if stage == MediaValidationStage.FORMAT else "block")
            issues.extend(image.issues)
        passed = not any(issue.severity == "block" for issue in issues)
        return ImageValidationResult(passed=passed, issues=issues)


def resolve_media_path(task_dir: Path, value: str) -> Path:
    if urlparse(value).scheme:
        raise MediaValidationError("不支持远程素材 URL", value)
    path = Path(value)
    if path.is_absolute():
        raise MediaValidationError("素材路径必须是任务目录内相对路径", value)
    resolved = (task_dir / path).resolve()
    try:
        resolved.relative_to(task_dir.resolve())
    except ValueError as exc:
        raise MediaValidationError("素材路径越界", value, related_artifacts=[resolved]) from exc
    return resolved


def validate_image_file(path: Path, display_path: str | None = None, missing_severity: str = "block") -> ImageValidationResult:
    label = display_path or str(path)
    issues: list[MediaValidationIssue] = []
    if path.suffix.lower() not in ALLOWED_EXTENSIONS:
        issues.append(MediaValidationIssue(label, "block", "图片扩展名不支持"))
    if not path.exists():
        issues.append(MediaValidationIssue(label, missing_severity, "图片文件不存在"))
        return ImageValidationResult(passed=not any(issue.severity == "block" for issue in issues), issues=issues)
    size = path.stat().st_size
    if size <= 0:
        issues.append(MediaValidationIssue(label, "block", "图片文件为空"))
    if size > MAX_IMAGE_BYTES:
        issues.append(MediaValidationIssue(label, "block", "图片文件过大"))
    try:
        head = path.read_bytes()[:16]
    except OSError as exc:
        raise MediaValidationError("图片文件无法读取", str(path), related_artifacts=[path]) from exc
    if not _magic_matches(path.suffix.lower(), head):
        issues.append(MediaValidationIssue(label, "block", "图片 magic bytes 不匹配"))
    return ImageValidationResult(passed=not any(issue.severity == "block" for issue in issues), issues=issues)


def _magic_matches(extension: str, head: bytes) -> bool:
    if extension == ".png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if extension in {".jpg", ".jpeg"}:
        return head.startswith(b"\xff\xd8\xff")
    if extension == ".webp":
        return head.startswith(b"RIFF") and b"WEBP" in head[:12]
    return False


def _media_item(raw: object, task_dir: Path, manifest_path: Path) -> MediaItem:
    if not isinstance(raw, dict):
        raise MediaValidationError("素材条目结构错误", "items[] 必须是 object", related_artifacts=[manifest_path])
    required = ("path", "role", "width", "height", "ratio", "description", "is_cover_candidate")
    missing = [field for field in required if field not in raw]
    if missing:
        raise MediaValidationError(
            "素材条目缺少字段",
            ", ".join(missing),
            related_artifacts=[manifest_path],
        )
    resolve_media_path(task_dir, str(raw["path"]))
    return MediaItem(
        path=str(raw["path"]),
        role=str(raw["role"]),
        width=int(raw["width"]),
        height=int(raw["height"]),
        ratio=str(raw["ratio"]),
        description=str(raw["description"]),
        is_cover_candidate=bool(raw["is_cover_candidate"]),
    )
