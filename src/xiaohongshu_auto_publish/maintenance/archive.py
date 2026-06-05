from __future__ import annotations

import json
import shutil
from pathlib import Path

from xiaohongshu_auto_publish.config.schema import AppConfig
from xiaohongshu_auto_publish.errors import StateError
from xiaohongshu_auto_publish.maintenance.cleanup import RUNNING_STATUSES, _append_maintenance_log, _archive, _workspace
from xiaohongshu_auto_publish.models import now_iso
from xiaohongshu_auto_publish.state.store import StateStore


def archive_task(config: AppConfig, state_store: StateStore, task_id: str) -> Path:
    task = state_store.get_task(task_id)
    if task.status in RUNNING_STATUSES:
        raise StateError("执行中任务不能归档", task.status.value)
    workspace = _workspace(config)
    archive_root = _archive(config)
    source = workspace / task_id
    target = archive_root / task_id
    if target.exists():
        raise StateError("归档目标已存在", str(target), related_artifacts=[target])
    archive_root.mkdir(parents=True, exist_ok=True)
    state_store.append_audit_event(task_id, "task_archived", summary="任务归档")
    shutil.move(str(source), str(target))
    _append_maintenance_log(workspace, "archive", [str(target)])
    _write_archive_marker(target)
    return target


def _write_archive_marker(target: Path) -> None:
    marker = target / "archived.json"
    marker.write_text(json.dumps({"archived_at": now_iso()}, ensure_ascii=False), encoding="utf-8")
