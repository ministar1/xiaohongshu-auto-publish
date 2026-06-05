from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from xiaohongshu_auto_publish.artifacts.front_matter import parse_markdown
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.errors import ArtifactError


def test_save_read_and_latest_versions(app_config: object) -> None:
    store = ArtifactStore(app_config)
    first = store.save_markdown("task-1", "drafts", "draft", "body")
    second = store.save_markdown("task-1", "drafts", "draft", "body2")
    assert first.version == 1
    assert second.version == 2
    assert store.latest("task-1", "drafts", "draft") == second
    assert store.read_markdown(second).body == "body2"


def test_latest_ignores_partial_by_default(app_config: object) -> None:
    store = ArtifactStore(app_config)
    complete = store.save_markdown("task-1", "reviews", "content_review", "ok")
    partial = store.save_partial("task-1", "reviews", "content_review", "bad", "parse", True)
    assert store.latest("task-1", "reviews", "content_review") == complete
    assert store.latest("task-1", "reviews", "content_review", include_partial=True) == partial


def test_front_matter_rejects_unsafe_inputs() -> None:
    with pytest.raises(ArtifactError):
        parse_markdown("---\nvalue: !!python/object/apply:os.system\n---\nbody")
    with pytest.raises(ArtifactError):
        parse_markdown("---\n" + "\n".join(f"k{index}: 1" for index in range(101)) + "\n---\nbody")


def test_concurrent_writes_do_not_duplicate_versions(app_config: object) -> None:
    store = ArtifactStore(app_config)
    with ThreadPoolExecutor(max_workers=4) as pool:
        refs = list(pool.map(lambda _: store.save_markdown("task-1", "drafts", "draft", "x"), range(8)))
    assert sorted(ref.version for ref in refs) == list(range(1, 9))


def test_path_escape_is_rejected(app_config: object) -> None:
    store = ArtifactStore(app_config)
    with pytest.raises(ArtifactError):
        store.read_markdown(store.workspace_dir.parent / "outside.md")
