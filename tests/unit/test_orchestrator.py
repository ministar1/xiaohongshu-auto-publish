from __future__ import annotations

from tests.factories import report
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.input.normalizer import InputNormalizer, TopicInputRequest
from xiaohongshu_auto_publish.models import ReviewReport, TaskStatus
from xiaohongshu_auto_publish.orchestration.orchestrator import WorkflowOrchestrator
from xiaohongshu_auto_publish.state.store import StateStore


class FakeContent:
    def __init__(self, content_report: ReviewReport) -> None:
        self.content_report = content_report

    def review(self, _task: object) -> ReviewReport:
        return self.content_report


def _orchestrator(app_config: object, content: FakeContent | None = None) -> WorkflowOrchestrator:
    state = StateStore(app_config)
    artifacts = ArtifactStore(app_config)
    return WorkflowOrchestrator(state, artifacts, InputNormalizer(app_config, state, artifacts), content_review_service=content)


def test_create_from_topic_stops_at_waiting_research_edit(app_config: object) -> None:
    result = _orchestrator(app_config).create_from_topic(TopicInputRequest("睡眠"))
    assert result.status == TaskStatus.WAITING_RESEARCH_EDIT


def test_content_review_s0_blocks(app_config: object) -> None:
    orch = _orchestrator(app_config, FakeContent(report(blocking=True)))
    created = orch.create_from_topic(TopicInputRequest("睡眠"))
    result = orch.continue_task(created.task_id or "")
    assert result.status == TaskStatus.CONTENT_BLOCKED


def test_content_review_s2_requires_confirmation(app_config: object) -> None:
    orch = _orchestrator(app_config, FakeContent(report(blocking=False)))
    created = orch.create_from_topic(TopicInputRequest("睡眠"))
    result = orch.continue_task(created.task_id or "")
    assert result.status == TaskStatus.CONTENT_PASSED_WITH_WARNINGS


def test_rollback_updates_pointer(app_config: object) -> None:
    orch = _orchestrator(app_config)
    created = orch.create_from_topic(TopicInputRequest("睡眠"))
    result = orch.rollback_task(created.task_id or "", "research")
    assert result.status == TaskStatus.WAITING_RESEARCH_EDIT
