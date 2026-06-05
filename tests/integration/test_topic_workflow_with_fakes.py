from __future__ import annotations

from tests.factories import report
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.input.normalizer import InputNormalizer, TopicInputRequest
from xiaohongshu_auto_publish.models import ReviewReport, TaskMetadata, TaskStatus
from xiaohongshu_auto_publish.orchestration.orchestrator import WorkflowOrchestrator
from xiaohongshu_auto_publish.state.store import StateStore


class FakeContent:
    def __init__(self, content_report: ReviewReport) -> None:
        self.content_report = content_report

    def review(self, _task: TaskMetadata) -> ReviewReport:
        return self.content_report


def test_topic_workflow_with_fake_content_blocks(app_config: object) -> None:
    state = StateStore(app_config)
    artifacts = ArtifactStore(app_config)
    orchestrator = WorkflowOrchestrator(
        state,
        artifacts,
        InputNormalizer(app_config, state, artifacts),
        content_review_service=FakeContent(report(blocking=True)),
    )
    created = orchestrator.create_from_topic(TopicInputRequest("高血压药物"))
    result = orchestrator.continue_task(created.task_id or "")
    assert result.status == TaskStatus.CONTENT_BLOCKED
