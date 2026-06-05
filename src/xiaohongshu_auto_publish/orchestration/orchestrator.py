from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from xiaohongshu_auto_publish.artifacts.store import ArtifactStore
from xiaohongshu_auto_publish.errors import ReviewBlockedError, StateError, XHSError
from xiaohongshu_auto_publish.input.normalizer import (
    ArticleInputRequest,
    InputNormalizer,
    TopicInputRequest,
)
from xiaohongshu_auto_publish.models import (
    ArtifactRef,
    PublishPackage,
    ReviewIssue,
    ReviewReport,
    TaskMetadata,
    TaskStatus,
)
from xiaohongshu_auto_publish.orchestration.states import phase_to_status, retry_target
from xiaohongshu_auto_publish.state.store import StateStore


class ResearchServiceProtocol(Protocol):
    def run(self, task: TaskMetadata) -> list[ArtifactRef]: ...


class ContentReviewServiceProtocol(Protocol):
    def review(self, task: TaskMetadata) -> ReviewReport: ...


class WritingReviewServiceProtocol(Protocol):
    def review(self, task: TaskMetadata, content_report: ReviewReport | None = None) -> list[ArtifactRef]: ...


class FormatReviewServiceProtocol(Protocol):
    def review(self, task: TaskMetadata) -> FormatReviewResult: ...


class PackageBuilderProtocol(Protocol):
    def build(self, task: TaskMetadata, user_confirmed: bool = False) -> tuple[PublishPackage, list[ArtifactRef]]: ...


class PublisherProtocol(Protocol):
    def publish(self, package: PublishPackage, confirmed: bool) -> PublishResult: ...


@dataclass(frozen=True, slots=True)
class FormatReviewResult:
    blocked: bool
    requires_confirmation: bool
    warnings: list[str]
    artifacts: list[ArtifactRef]


@dataclass(frozen=True, slots=True)
class PublishResult:
    success: bool
    channel: str
    message: str
    retryable: bool = False
    published_url: str | None = None
    raw_artifact_path: Path | None = None


@dataclass(slots=True)
class WorkflowResult:
    status: TaskStatus
    artifact_paths: list[Path] = field(default_factory=list)
    blocking_issues: list[ReviewIssue] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    next_command: str | None = None
    failure_summary: str | None = None
    task_id: str | None = None


class WorkflowOrchestrator:
    def __init__(
        self,
        state_store: StateStore,
        artifact_store: ArtifactStore,
        normalizer: InputNormalizer,
        research_service: ResearchServiceProtocol | None = None,
        content_review_service: ContentReviewServiceProtocol | None = None,
        writing_review_service: WritingReviewServiceProtocol | None = None,
        format_review_service: FormatReviewServiceProtocol | None = None,
        package_builder: PackageBuilderProtocol | None = None,
        publisher: PublisherProtocol | None = None,
    ) -> None:
        self._state = state_store
        self._artifacts = artifact_store
        self._normalizer = normalizer
        self._research = research_service
        self._content = content_review_service
        self._writing = writing_review_service
        self._format = format_review_service
        self._package = package_builder
        self._publisher = publisher

    def create_from_topic(self, request: TopicInputRequest) -> WorkflowResult:
        normalized = self._normalizer.create_topic(request)
        task = normalized.task
        if self._research is None:
            self._state.update_status(
                task.task_id,
                TaskStatus.WAITING_RESEARCH_EDIT,
                stage="research",
                artifact_ids=[normalized.artifact.artifact_id],
                summary="已创建选题，等待补充调研服务或手动编辑",
            )
            return self.get_status(task.task_id)
        self._state.update_status(task.task_id, TaskStatus.RESEARCHING, stage="research")
        try:
            artifacts = self._research.run(task)
        except XHSError as exc:
            self._state.record_failure(task.task_id, "research", exc, TaskStatus.RESEARCH_FAILED)
            return self.get_status(task.task_id)
        self._state.update_status(
            task.task_id,
            TaskStatus.WAITING_RESEARCH_EDIT,
            stage="research",
            artifact_ids=[item.artifact_id for item in artifacts],
            summary="调研完成，等待用户编辑或确认",
        )
        return self.get_status(task.task_id)

    def create_from_article(self, request: ArticleInputRequest) -> WorkflowResult:
        normalized = self._normalizer.create_article(request)
        self._state.update_status(
            normalized.task.task_id,
            TaskStatus.CONTENT_REVIEWING,
            stage="content",
            artifact_ids=[normalized.artifact.artifact_id],
            summary="文章已导入，进入内容审核入口",
        )
        return self.get_status(normalized.task.task_id)

    def continue_task(
        self,
        task_id: str,
        yes: bool = False,
        force_parse: bool = False,
        prompt_policy: str = "locked",
        manual_review_note: str | None = None,
    ) -> WorkflowResult:
        task = self._state.get_task(task_id)
        if prompt_policy == "latest":
            self._state.append_audit_event(
                task_id,
                "prompt_policy_latest",
                summary="用户显式选择 latest 提示词策略",
                user_confirmed=True,
            )
        if task.status in {TaskStatus.WAITING_RESEARCH_EDIT, TaskStatus.CONTENT_REVIEWING, TaskStatus.CREATED}:
            return self.review_content(task_id, force_parse=force_parse, manual_review_note=manual_review_note)
        if task.status == TaskStatus.CONTENT_PASSED_WITH_WARNINGS:
            if not yes:
                return self.get_status(task_id)
            self._state.append_audit_event(
                task_id,
                "user_confirmed_warnings",
                stage="content",
                summary="用户确认 S2/S3 警告后继续",
                user_confirmed=True,
            )
            self._state.update_status(task_id, TaskStatus.WRITING_REVIEWING, stage="writing", user_confirmed=True)
            return self.review_writing(task_id)
        if task.status == TaskStatus.WAITING_DRAFT_EDIT:
            if not yes:
                return self.get_status(task_id)
            self._state.update_status(task_id, TaskStatus.FORMAT_REVIEWING, stage="format", user_confirmed=True)
            return self.review_format(task_id)
        if task.status == TaskStatus.WAITING_FORMAT_CONFIRM:
            if not yes:
                return self.get_status(task_id)
            self._state.append_audit_event(
                task_id,
                "user_confirmed_format",
                stage="format",
                summary="用户确认格式 confirm 问题后继续",
                user_confirmed=True,
            )
            self._state.update_status(task_id, TaskStatus.PACKAGE_READY, stage="package", user_confirmed=True)
            return self.build_package(task_id, user_confirmed=yes)
        if task.status == TaskStatus.PACKAGE_READY:
            return self.build_package(task_id, user_confirmed=yes)
        raise StateError("当前状态不能 continue", task.status.value)

    def review_content(
        self,
        task_id: str,
        force_parse: bool = False,
        manual_review_note: str | None = None,
    ) -> WorkflowResult:
        task = self._state.get_task(task_id)
        if force_parse:
            self._state.append_audit_event(
                task_id,
                "force_parse_requested",
                stage="content",
                summary="用户请求生成诊断型解析报告；该选项不允许绕过阻断",
            )
        if manual_review_note:
            self._state.append_audit_event(
                task_id,
                "manual_override_requested",
                stage="content",
                summary=manual_review_note,
                user_confirmed=True,
            )
        if self._content is None:
            return self.get_status(task_id)
        self._state.update_status(task_id, TaskStatus.CONTENT_REVIEWING, stage="content")
        report = self._content.review(task)
        blocking = [issue for issue in report.issues if issue.blocking]
        if report.blocking or blocking or report.parse_status.value != "ok":
            self._state.update_status(
                task_id,
                TaskStatus.CONTENT_BLOCKED,
                stage="content",
                summary="内容审核阻断",
                artifact_ids=report.source_artifacts,
            )
            return WorkflowResult(
                status=TaskStatus.CONTENT_BLOCKED,
                blocking_issues=blocking,
                warnings=report.parse_warnings,
                next_command=f"xhs-agent review-content {task_id}",
                task_id=task_id,
            )
        warnings = [issue for issue in report.issues if not issue.blocking]
        if warnings:
            self._state.update_status(
                task_id,
                TaskStatus.CONTENT_PASSED_WITH_WARNINGS,
                stage="content",
                summary="内容审核通过但有提示",
            )
            return WorkflowResult(
                status=TaskStatus.CONTENT_PASSED_WITH_WARNINGS,
                warnings=[issue.risk for issue in warnings],
                next_command=f"xhs-agent continue {task_id} --yes",
                task_id=task_id,
            )
        self._state.update_status(task_id, TaskStatus.WRITING_REVIEWING, stage="writing")
        return self.review_writing(task_id)

    def review_writing(self, task_id: str) -> WorkflowResult:
        task = self._state.get_task(task_id)
        if task.status not in {TaskStatus.WRITING_REVIEWING, TaskStatus.CONTENT_PASSED_WITH_WARNINGS}:
            raise StateError("写作审核前置状态不满足", task.status.value)
        if self._writing is None:
            return self.get_status(task_id)
        try:
            artifacts = self._writing.review(task)
        except XHSError as exc:
            self._state.record_failure(task_id, "writing", exc, TaskStatus.WRITING_FAILED)
            return self.get_status(task_id)
        self._state.update_status(
            task_id,
            TaskStatus.WAITING_DRAFT_EDIT,
            stage="writing",
            artifact_ids=[item.artifact_id for item in artifacts],
            summary="写作审核完成，等待用户确认或编辑",
        )
        return self.get_status(task_id)

    def review_format(self, task_id: str) -> WorkflowResult:
        task = self._state.get_task(task_id)
        if self._format is None:
            return self.get_status(task_id)
        result = self._format.review(task)
        if result.blocked:
            self._state.update_status(
                task_id,
                TaskStatus.FORMAT_BLOCKED,
                stage="format",
                artifact_ids=[item.artifact_id for item in result.artifacts],
                summary="格式审核阻断",
            )
        elif result.requires_confirmation:
            self._state.update_status(
                task_id,
                TaskStatus.WAITING_FORMAT_CONFIRM,
                stage="format",
                artifact_ids=[item.artifact_id for item in result.artifacts],
                summary="格式审核需要用户确认",
            )
        else:
            self._state.update_status(
                task_id,
                TaskStatus.PACKAGE_READY,
                stage="package",
                artifact_ids=[item.artifact_id for item in result.artifacts],
                summary="格式审核通过",
            )
        return self.get_status(task_id)

    def build_package(self, task_id: str, user_confirmed: bool = False) -> WorkflowResult:
        task = self._state.get_task(task_id)
        if self._package is None:
            return self.get_status(task_id)
        try:
            package, artifacts = self._package.build(task, user_confirmed=user_confirmed)
        except XHSError as exc:
            self._state.record_failure(task_id, "package", exc, TaskStatus.FAILED)
            return self.get_status(task_id)
        if not package.can_publish:
            self._state.record_failure(
                task_id,
                "package",
                ReviewBlockedError("发布包不可发布", "请检查审核、确认和素材复验", retryable=True),
                TaskStatus.FAILED,
                [item.artifact_id for item in artifacts],
            )
        else:
            self._state.update_status(
                task_id,
                TaskStatus.PACKAGE_READY,
                stage="package",
                artifact_ids=[item.artifact_id for item in artifacts],
                summary="发布包已生成",
                user_confirmed=user_confirmed,
            )
        return self.get_status(task_id)

    def publish(self, task_id: str, confirmed: bool = False) -> WorkflowResult:
        task = self._state.get_task(task_id)
        if task.status != TaskStatus.PACKAGE_READY:
            raise StateError("发布前置状态不满足", task.status.value)
        if not confirmed:
            raise StateError("发布前必须确认", "--yes 不能替代发布确认参数")
        if self._publisher is None:
            return self.get_status(task_id)
        self._state.update_status(task_id, TaskStatus.PUBLISHING, stage="publish", user_confirmed=True)
        raise StateError("缺少发布包读取实现", "请先生成发布包并使用 ManualPublisher")

    def retry_task(self, task_id: str, prompt_policy: str = "locked") -> WorkflowResult:
        task = self._state.get_task(task_id)
        if task.last_failed_stage is None:
            raise StateError("当前任务没有可恢复失败阶段", task.status.value)
        if prompt_policy == "latest":
            self._state.append_audit_event(
                task_id,
                "prompt_policy_latest",
                stage=task.last_failed_stage,
                summary="用户显式迁移到最新提示词版本",
                user_confirmed=True,
            )
        self._state.increment_retry(task_id, task.last_failed_stage)
        target = retry_target(task.last_failed_stage)
        self._state.update_status(task_id, target, stage=task.last_failed_stage, summary="任务重试")
        return self.get_status(task_id)

    def rollback_task(self, task_id: str, to_phase: str) -> WorkflowResult:
        task = self._state.get_task(task_id)
        target = phase_to_status(to_phase)
        self._state.update_status(task_id, target, stage=to_phase, summary="非破坏性回滚")
        self._state.append_audit_event(
            task_id,
            "rollback",
            stage=to_phase,
            from_status=task.status,
            to_status=target,
            summary=f"回滚到 {to_phase}",
        )
        return self.get_status(task_id)

    def get_status(self, task_id: str) -> WorkflowResult:
        task = self._state.get_task(task_id)
        refs = self._artifacts.list_artifacts(task_id, include_partial=True)
        paths = [self._artifacts.task_dir(task_id) / ref.path for ref in refs[-5:]]
        return WorkflowResult(
            status=task.status,
            artifact_paths=paths,
            next_command=_next_command(task),
            failure_summary=task.last_error.summary if task.last_error else None,
            task_id=task_id,
        )

    def list_tasks(self) -> list[TaskMetadata]:
        return self._state.list_tasks()


def _next_command(task: TaskMetadata) -> str | None:
    mapping = {
        TaskStatus.WAITING_RESEARCH_EDIT: f"xhs-agent continue {task.task_id}",
        TaskStatus.CONTENT_BLOCKED: f"xhs-agent review-content {task.task_id}",
        TaskStatus.CONTENT_PASSED_WITH_WARNINGS: f"xhs-agent continue {task.task_id} --yes",
        TaskStatus.WAITING_DRAFT_EDIT: f"xhs-agent continue {task.task_id} --yes",
        TaskStatus.WAITING_FORMAT_CONFIRM: f"xhs-agent continue {task.task_id} --yes",
        TaskStatus.PACKAGE_READY: f"xhs-agent publish {task.task_id}",
        TaskStatus.RESEARCH_FAILED: f"xhs-agent retry {task.task_id}",
        TaskStatus.WRITING_FAILED: f"xhs-agent retry {task.task_id}",
        TaskStatus.FORMAT_BLOCKED: f"xhs-agent review-format {task.task_id}",
        TaskStatus.FAILED: f"xhs-agent retry {task.task_id}",
    }
    return mapping.get(task.status)
