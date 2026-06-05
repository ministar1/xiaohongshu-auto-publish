from __future__ import annotations

from pathlib import Path

import pytest

from tests.factories import task
from xiaohongshu_auto_publish.errors import StateError
from xiaohongshu_auto_publish.models import TaskStatus
from xiaohongshu_auto_publish.state.store import StateStore, generate_task_id


def test_create_update_and_audit(app_config: object) -> None:
    store = StateStore(app_config)
    store.create_task(task("task-1"))
    store.update_status("task-1", TaskStatus.CONTENT_REVIEWING)
    assert store.get_task("task-1").status == TaskStatus.CONTENT_REVIEWING
    assert (store.task_dir("task-1") / "audit_log.jsonl").read_text(encoding="utf-8").count("\n") >= 2


def test_record_failure_and_retry(app_config: object) -> None:
    store = StateStore(app_config)
    store.create_task(task("task-1"))
    store.record_failure("task-1", "package", StateError("失败", "detail", retryable=True))
    assert store.get_task("task-1").last_failed_stage == "package"
    assert store.increment_retry("task-1", "package") == 1


def test_corrupt_task_json_raises(app_config: object) -> None:
    store = StateStore(app_config)
    store.create_task(task("task-1"))
    (store.task_dir("task-1") / "task.json").write_text("{bad", encoding="utf-8")
    with pytest.raises(StateError):
        store.get_task("task-1")


def test_task_id_generation_returns_unique_candidate(tmp_path: Path) -> None:
    task_id, attempted = generate_task_id(tmp_path, "中文")
    assert task_id.startswith("20")
    assert "-topic-" in task_id
    assert attempted
