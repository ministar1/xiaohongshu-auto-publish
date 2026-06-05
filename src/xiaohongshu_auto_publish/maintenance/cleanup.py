from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import ConfigError
from xiaohongshu_auto_publish.models import TaskStatus, now_iso

RUNNING_STATUSES = {
    TaskStatus.RESEARCHING,
    TaskStatus.CONTENT_REVIEWING,
    TaskStatus.WRITING_REVIEWING,
    TaskStatus.FORMAT_REVIEWING,
    TaskStatus.PUBLISHING,
}


@dataclass(frozen=True, slots=True)
class CleanupCandidate:
    path: Path
    reason: str
    bytes_to_free: int


def cleanup_workspace(config: AppConfig, apply: bool = False) -> list[CleanupCandidate]:
    _validate_archive_dir(config)
    workspace = _workspace(config)
    candidates: list[CleanupCandidate] = []
    for task_dir in workspace.iterdir() if workspace.exists() else []:
        if not task_dir.is_dir() or task_dir.name == "archive":
            continue
        for stage_dir in task_dir.iterdir():
            if not stage_dir.is_dir() or stage_dir.name == "media":
                continue
            files = sorted(stage_dir.glob("*.v*.*"))
            old_files = files[: max(0, len(files) - config.retention.keep_recent_versions)]
            for path in old_files:
                if path.name in {"task.json", "artifacts.jsonl", "audit_log.jsonl"}:
                    continue
                candidates.append(CleanupCandidate(path, "超过保留版本数", path.stat().st_size))
    if apply:
        for candidate in candidates:
            candidate.path.unlink(missing_ok=True)
        _append_maintenance_log(workspace, "cleanup_apply", [str(item.path) for item in candidates])
    return candidates


def _validate_archive_dir(config: AppConfig) -> None:
    workspace = _workspace(config)
    archive = _archive(config)
    try:
        archive.relative_to(workspace)
    except ValueError as exc:
        raise ConfigError("归档目录越界", "archive_dir 必须位于 workspace_dir 内") from exc


def _workspace(config: AppConfig) -> Path:
    path = Path(config.storage.workspace_dir)
    if not path.is_absolute():
        path = config.project_root / path
    return path.resolve()


def _archive(config: AppConfig) -> Path:
    path = Path(config.retention.archive_dir)
    if not path.is_absolute():
        path = config.project_root / path
    return path.resolve()


def _append_maintenance_log(workspace: Path, event_type: str, paths: list[str]) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    log = workspace / "maintenance_log.jsonl"
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event_type": event_type, "paths": paths, "created_at": now_iso()}, ensure_ascii=False) + "\n")
