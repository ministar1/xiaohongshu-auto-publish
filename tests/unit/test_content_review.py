from __future__ import annotations

from tests.factories import task
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.llm.gateway import FakeLLMGateway
from xiaohongshu_auto_publish.models import ParseStatus
from xiaohongshu_auto_publish.review.content import ContentReviewService
from xiaohongshu_auto_publish.state.store import StateStore


def test_content_review_s0_blocks_and_writes_report(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "draft", "危险说法")
    service = ContentReviewService(
        FakeLLMGateway(
            [
                '{"summary":"bad","blocking":true,"issues":[{"issue_type":"risk","severity":"S0","risk":"危险","blocking":true,"suggestion":"删除"}]}'
            ]
        ),
        artifacts,
    )
    report = service.review(metadata)
    assert report.blocking
    assert report.issues[0].severity == "S0"


def test_content_review_partial_blocks(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "draft", "内容")
    service = ContentReviewService(FakeLLMGateway(['{"summary":"partial","blocking":false,"partial":true,"issues":[]}']), artifacts)
    assert service.review(metadata).parse_status == ParseStatus.PARTIAL
