from __future__ import annotations

import pytest

from tests.factories import task
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.errors import StateError
from xiaohongshu_auto_publish.maintenance.archive import archive_task
from xiaohongshu_auto_publish.maintenance.cleanup import cleanup_workspace
from xiaohongshu_auto_publish.models import TaskStatus
from xiaohongshu_auto_publish.state.store import StateStore


def test_cleanup_dry_run_does_not_modify_files(app_config: object) -> None:
    state = StateStore(app_config)
    state.create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    for index in range(7):
        artifacts.save_markdown("task-1", "drafts", "draft", f"v{index}")
    candidates = cleanup_workspace(app_config, apply=False)
    assert candidates
    assert all(item.path.exists() for item in candidates)


def test_archive_rejects_running_task_and_moves_completed(app_config: object) -> None:
    state = StateStore(app_config)
    state.create_task(task("task-1", TaskStatus.RESEARCHING))
    with pytest.raises(StateError):
        archive_task(app_config, state, "task-1")
    state.update_status("task-1", TaskStatus.FAILED)
    target = archive_task(app_config, state, "task-1")
    assert target.exists()
