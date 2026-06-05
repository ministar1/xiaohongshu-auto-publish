from __future__ import annotations

from tests.factories import report, task
from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.input.normalizer import InputNormalizer, TopicInputRequest
from xiaohongshu_auto_publish.models import ArtifactRef, PublishPackage, ReviewReport, TaskMetadata, TaskStatus
from xiaohongshu_auto_publish.orchestration.orchestrator import FormatReviewResult, WorkflowOrchestrator, _has_current_publish_manifest
from xiaohongshu_auto_publish.publish.manual import ManualPublisher
from xiaohongshu_auto_publish.state.store import StateStore


class FakeContent:
    def __init__(self, content_report: ReviewReport) -> None:
        self.content_report = content_report

    def review(self, _task: object) -> ReviewReport:
        return self.content_report


class FakeFormat:
    def review(self, _task: object) -> FormatReviewResult:
        return FormatReviewResult(blocked=False, requires_confirmation=False, warnings=[], artifacts=[])


class FakePackage:
    def __init__(self) -> None:
        self.called = False

    def build(self, _task: TaskMetadata, user_confirmed: bool = False) -> tuple[PublishPackage, list[ArtifactRef]]:
        self.called = True
        return (
            PublishPackage(
                title="标题",
                body="正文",
                hashtags=[],
                media_items=[],
                cover_title="标题",
                source_records=[],
                review_summary="通过",
                media_validation_passed=True,
                user_confirmed=user_confirmed,
                can_publish=user_confirmed,
            ),
            [],
        )


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


def test_continue_after_draft_builds_package_when_format_passes(app_config: object) -> None:
    state = StateStore(app_config)
    artifacts = ArtifactStore(app_config)
    metadata = state.create_task(task("task-1", TaskStatus.WAITING_DRAFT_EDIT))
    package = FakePackage()
    orch = WorkflowOrchestrator(
        state,
        artifacts,
        InputNormalizer(app_config, state, artifacts),
        format_review_service=FakeFormat(),
        package_builder=package,
    )
    result = orch.continue_task(metadata.task_id, yes=True)
    assert result.status == TaskStatus.PACKAGE_READY
    assert package.called


def test_publish_manual_updates_status(app_config: object) -> None:
    state = StateStore(app_config)
    artifacts = ArtifactStore(app_config)
    metadata = state.create_task(task("task-1", TaskStatus.PACKAGE_READY))
    artifacts.save_json(
        metadata.task_id,
        "package",
        "publish_manifest",
        {
            "title": "标题",
            "body": "正文",
            "hashtags": [],
            "media_validation_passed": True,
            "user_confirmed": True,
            "can_publish": True,
        },
    )
    orch = WorkflowOrchestrator(
        state,
        artifacts,
        InputNormalizer(app_config, state, artifacts),
        publisher=ManualPublisher(),
    )
    result = orch.publish(metadata.task_id, confirmed=True)
    assert result.status == TaskStatus.PUBLISHED
    assert result.warnings


def test_stale_publish_manifest_is_not_current() -> None:
    manifest = ArtifactRef(
        artifact_id="publish_manifest-001",
        task_id="task-1",
        stage="package",
        kind="publish_manifest",
        version=1,
        path="package/publish_manifest.v001.json",
        created_at="2026-06-06T00:00:00+08:00",
    )
    format_review = ArtifactRef(
        artifact_id="format_review-002",
        task_id="task-1",
        stage="reviews",
        kind="format_review",
        version=2,
        path="reviews/format_review.v002.md",
        created_at="2026-06-06T00:01:00+08:00",
    )
    assert not _has_current_publish_manifest([manifest, format_review])
