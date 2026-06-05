from __future__ import annotations

from pathlib import Path

from tests.factories import report
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.input.normalizer import ArticleInputRequest, InputNormalizer
from xiaohongshu_auto_publish.models import ReviewReport, TaskMetadata, TaskStatus
from xiaohongshu_auto_publish.orchestration.orchestrator import WorkflowOrchestrator
from xiaohongshu_auto_publish.state.store import StateStore


class FakeContent:
    def __init__(self, content_report: ReviewReport) -> None:
        self.content_report = content_report

    def review(self, _task: TaskMetadata) -> ReviewReport:
        return self.content_report


def test_article_workflow_with_fake_content_warns(app_config: object, tmp_path: Path) -> None:
    article = tmp_path / "article.md"
    article.write_text("# 标题\n正文", encoding="utf-8")
    state = StateStore(app_config)
    artifacts = ArtifactStore(app_config)
    orchestrator = WorkflowOrchestrator(
        state,
        artifacts,
        InputNormalizer(app_config, state, artifacts),
        content_review_service=FakeContent(report(blocking=False)),
    )
    created = orchestrator.create_from_article(ArticleInputRequest(article_path=article, slug="article"))
    result = orchestrator.continue_task(created.task_id or "")
    assert result.status == TaskStatus.CONTENT_PASSED_WITH_WARNINGS
