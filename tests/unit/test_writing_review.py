from __future__ import annotations

from tests.factories import task
from xiaohongshu_auto_publish.account.profile import AccountProfileService
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.llm.gateway import FakeLLMGateway
from xiaohongshu_auto_publish.review.writing import WritingReviewService
from xiaohongshu_auto_publish.state.store import StateStore


def test_writing_review_outputs_revised_and_report(app_config: object) -> None:
    metadata = StateStore(app_config).create_task(task("task-1"))
    artifacts = ArtifactStore(app_config)
    artifacts.save_markdown("task-1", "drafts", "draft", "# 标题\n正文")
    service = WritingReviewService(
        app_config,
        FakeLLMGateway(
            ['{"title_candidates":["标题1"],"body":"正文 #健康","hashtags":["健康"],"opening_notes":"开头","account_fit":"一致"}']
        ),
        artifacts,
        AccountProfileService(app_config),
    )
    refs = service.review(metadata)
    assert [ref.kind for ref in refs] == ["revised", "writing_review"]
