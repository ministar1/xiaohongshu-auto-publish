from __future__ import annotations

from tests.factories import task
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.review.format import FormatReviewService
from xiaohongshu_auto_publish.rules.format_rules import FormatRules
from xiaohongshu_auto_publish.state.store import StateStore


def test_format_review_blocks_sensitive_word(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "revised", "# 根治高血压\n正文 #健康 #科普")
    result = FormatReviewService(artifacts, FormatRules.load(app_config)).review(metadata)
    assert result.blocked


def test_format_review_warns_missing_image(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "revised", "# 标题\n正文 #健康 #科普")
    result = FormatReviewService(artifacts, FormatRules.load(app_config)).review(metadata)
    assert not result.blocked
