from __future__ import annotations

import json
import os
import secrets
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from filelock import FileLock, Timeout

from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import LockError, StateError, XHSError
from xiaohongshu_auto_publish.models import LastError, TaskMetadata, TaskStatus, now_iso, task_from_dict, to_jsonable

FAILURE_STATUSES = {TaskStatus.FAILED, TaskStatus.RESEARCH_FAILED, TaskStatus.WRITING_FAILED, TaskStatus.PUBLISH_FAILED}


@dataclass(slots=True)
class AuditEvent:
    event_id: str
    task_id: str
    event_type: str
    stage: str | None = None
    from_status: TaskStatus | None = None
    to_status: TaskStatus | None = None
    artifact_ids: list[str] = field(default_factory=list)
    summary: str = ""
    created_at: str = field(default_factory=now_iso)
    user_confirmed: bool = False
    metadata: dict[str, object] = field(default_factory=dict)


class StateStore:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self.workspace_dir = self._resolve_workspace()
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def create_task(self, metadata: TaskMetadata) -> TaskMetadata:
        task_dir = self.task_dir(metadata.task_id)
        try:
            task_dir.mkdir(parents=True, exist_ok=False)
        except FileExistsError as exc:
            raise StateError(
                "任务已存在",
                metadata.task_id,
                next_action="请使用更明确的 --slug 或重新执行创建命令",
            ) from exc
        metadata.created_at = metadata.created_at or now_iso()
        metadata.updated_at = metadata.updated_at or metadata.created_at
        self._write_task_atomic(task_dir, metadata)
        self.append_audit_event(
            metadata.task_id,
            "task_created",
            to_status=metadata.status,
            summary="任务已创建",
        )
        return metadata

    def get_task(self, task_id: str) -> TaskMetadata:
        path = self.task_dir(task_id) / "task.json"
        if not path.exists():
            raise StateError("任务不存在", task_id, related_artifacts=[path])
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            return task_from_dict(raw)
        except (OSError, json.JSONDecodeError, KeyError, ValueError) as exc:
            raise StateError("任务状态损坏", f"{path}: {exc}", related_artifacts=[path]) from exc

    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        stage: str | None = None,
        summary: str = "状态更新",
        artifact_ids: Iterable[str] = (),
        user_confirmed: bool = False,
    ) -> TaskMetadata:
        task_dir = self.task_dir(task_id)
        lock = FileLock(str(task_dir / "state.lock"))
        try:
            with lock.acquire(timeout=10):
                task = self.get_task(task_id)
                previous = task.status
                task.status = status
                if status not in FAILURE_STATUSES:
                    task.last_failed_stage = None
                    task.last_error = None
                task.updated_at = now_iso()
                self._write_task_atomic(task_dir, task)
                self.append_audit_event(
                    task_id,
                    "status_updated",
                    stage=stage,
                    from_status=previous,
                    to_status=status,
                    artifact_ids=list(artifact_ids),
                    summary=summary,
                    user_confirmed=user_confirmed,
                )
                return task
        except Timeout as exc:
            raise LockError("状态锁获取失败", str(task_dir / "state.lock"), retryable=True) from exc

    def record_failure(
        self,
        task_id: str,
        stage: str,
        error: XHSError | LastError,
        status: TaskStatus = TaskStatus.FAILED,
        related_artifacts: Iterable[str] = (),
    ) -> TaskMetadata:
        task_dir = self.task_dir(task_id)
        lock = FileLock(str(task_dir / "state.lock"))
        try:
            with lock.acquire(timeout=10):
                task = self.get_task(task_id)
                previous = task.status
                related = [str(item) for item in related_artifacts]
                if isinstance(error, XHSError):
                    last_error = LastError(
                        summary=error.summary,
                        detail=error.detail,
                        retryable=error.retryable,
                        stage=stage,
                        next_action=error.next_action,
                        related_artifacts=related,
                    )
                else:
                    last_error = error
                    last_error.stage = stage
                    last_error.related_artifacts = related
                task.status = status
                task.last_failed_stage = stage
                task.last_error = last_error
                task.updated_at = now_iso()
                self._write_task_atomic(task_dir, task)
                self.append_audit_event(
                    task_id,
                    "failure_recorded",
                    stage=stage,
                    from_status=previous,
                    to_status=status,
                    artifact_ids=related,
                    summary=last_error.summary,
                    metadata={"retryable": last_error.retryable, "next_action": last_error.next_action},
                )
                return task
        except Timeout as exc:
            raise LockError("状态锁获取失败", str(task_dir / "state.lock"), retryable=True) from exc

    def increment_retry(self, task_id: str, stage: str) -> int:
        task_dir = self.task_dir(task_id)
        lock = FileLock(str(task_dir / "state.lock"))
        try:
            with lock.acquire(timeout=10):
                task = self.get_task(task_id)
                count = task.retry_counts.get(stage, 0) + 1
                task.retry_counts[stage] = count
                task.updated_at = now_iso()
                self._write_task_atomic(task_dir, task)
                self.append_audit_event(
                    task_id,
                    "retry_incremented",
                    stage=stage,
                    summary=f"{stage} 重试次数更新为 {count}",
                    metadata={"retry_count": count},
                )
                return count
        except Timeout as exc:
            raise LockError("状态锁获取失败", str(task_dir / "state.lock"), retryable=True) from exc

    def append_audit_event(
        self,
        task_id: str,
        event_type: str,
        stage: str | None = None,
        from_status: TaskStatus | None = None,
        to_status: TaskStatus | None = None,
        artifact_ids: Iterable[str] = (),
        summary: str = "",
        user_confirmed: bool = False,
        metadata: dict[str, object] | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            event_id=secrets.token_hex(8),
            task_id=task_id,
            event_type=event_type,
            stage=stage,
            from_status=from_status,
            to_status=to_status,
            artifact_ids=list(artifact_ids),
            summary=summary,
            user_confirmed=user_confirmed,
            metadata=dict(metadata or {}),
        )
        path = self.task_dir(task_id) / "audit_log.jsonl"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(to_jsonable(event), ensure_ascii=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def list_tasks(self) -> list[TaskMetadata]:
        tasks: list[TaskMetadata] = []
        for path in sorted(self.workspace_dir.iterdir()):
            if not path.is_dir() or path.name == "archive":
                continue
            task_json = path / "task.json"
            if task_json.exists():
                tasks.append(self.get_task(path.name))
        return tasks

    def task_dir(self, task_id: str) -> Path:
        path = (self.workspace_dir / task_id).resolve()
        try:
            path.relative_to(self.workspace_dir)
        except ValueError as exc:
            raise StateError("任务路径越界", task_id, related_artifacts=[path]) from exc
        return path

    def _write_task_atomic(self, task_dir: Path, task: TaskMetadata) -> None:
        task_dir.mkdir(parents=True, exist_ok=True)
        target = task_dir / "task.json"
        temp = task_dir / "task.json.tmp"
        try:
            with temp.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(to_jsonable(task), ensure_ascii=False, indent=2))
                handle.flush()
                os.fsync(handle.fileno())
            temp.replace(target)
        except OSError as exc:
            temp.unlink(missing_ok=True)
            raise StateError("任务状态写入失败", str(target), related_artifacts=[target]) from exc

    def _resolve_workspace(self) -> Path:
        path = Path(self._config.storage.workspace_dir)
        if not path.is_absolute():
            path = self._config.project_root / path
        return path.resolve()


def slugify(value: str) -> str:
    lowered = value.lower()
    chars: list[str] = []
    previous_dash = False
    for char in lowered:
        if char.isascii() and char.isalnum():
            chars.append(char)
            previous_dash = False
        elif char in {" ", "_", "-"} and not previous_dash:
            chars.append("-")
            previous_dash = True
    slug = "".join(chars).strip("-")
    return slug or "topic"


def generate_task_id(workspace_dir: Path, slug: str, now: datetime | None = None) -> tuple[str, list[str]]:
    date = (now or datetime.now()).strftime("%Y%m%d")
    normalized = slugify(slug)
    attempted: list[str] = []
    suffix = 1
    while len(attempted) < 30:
        active_slug = normalized if suffix == 1 else f"{normalized}-{suffix}"
        for _ in range(5):
            candidate = f"{date}-{active_slug}-{secrets.token_hex(2)}"
            attempted.append(candidate)
            if not (workspace_dir / candidate).exists():
                return candidate, attempted
            if len(attempted) >= 30:
                break
        suffix += 1
    raise StateError(
        "任务 ID 冲突过多",
        f"已尝试: {attempted}",
        next_action="请使用 --slug 指定更明确的英文短名",
    )
