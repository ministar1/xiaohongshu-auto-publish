from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from xiaohongshu_auto_publish.errors import StateError
from xiaohongshu_auto_publish.models import TaskStatus


class Trigger(StrEnum):
    START_RESEARCH = "start_research"
    RESEARCH_DONE = "research_done"
    RESEARCH_FAILED = "research_failed"
    START_CONTENT_REVIEW = "start_content_review"
    CONTENT_BLOCK = "content_block"
    CONTENT_WARN = "content_warn"
    CONTENT_PASS = "content_pass"
    CONFIRM_WARNINGS = "confirm_warnings"
    START_WRITING = "start_writing"
    WRITING_DONE = "writing_done"
    WRITING_FAILED = "writing_failed"
    START_FORMAT = "start_format"
    FORMAT_BLOCK = "format_block"
    FORMAT_CONFIRM = "format_confirm"
    FORMAT_PASS = "format_pass"
    CONFIRM_FORMAT = "confirm_format"
    PACKAGE_DONE = "package_done"
    PACKAGE_FAILED = "package_failed"
    START_PUBLISH = "start_publish"
    PUBLISH_DONE = "publish_done"
    PUBLISH_FAILED = "publish_failed"
    RETRY = "retry"
    ROLLBACK = "rollback"


@dataclass(frozen=True, slots=True)
class Transition:
    current: TaskStatus
    trigger: Trigger
    target: TaskStatus
    requires_confirmation: bool = False
    allows_retry: bool = False
    failure_stage: str | None = None


TRANSITIONS: tuple[Transition, ...] = (
    Transition(TaskStatus.CREATED, Trigger.START_RESEARCH, TaskStatus.RESEARCHING),
    Transition(TaskStatus.RESEARCHING, Trigger.RESEARCH_DONE, TaskStatus.WAITING_RESEARCH_EDIT),
    Transition(TaskStatus.RESEARCHING, Trigger.RESEARCH_FAILED, TaskStatus.RESEARCH_FAILED, True, True, "research"),
    Transition(TaskStatus.CREATED, Trigger.START_CONTENT_REVIEW, TaskStatus.CONTENT_REVIEWING),
    Transition(TaskStatus.WAITING_RESEARCH_EDIT, Trigger.START_CONTENT_REVIEW, TaskStatus.CONTENT_REVIEWING, True),
    Transition(TaskStatus.CONTENT_REVIEWING, Trigger.CONTENT_BLOCK, TaskStatus.CONTENT_BLOCKED, False, True, "content"),
    Transition(
        TaskStatus.CONTENT_REVIEWING,
        Trigger.CONTENT_WARN,
        TaskStatus.CONTENT_PASSED_WITH_WARNINGS,
        True,
    ),
    Transition(TaskStatus.CONTENT_REVIEWING, Trigger.CONTENT_PASS, TaskStatus.WRITING_REVIEWING),
    Transition(
        TaskStatus.CONTENT_PASSED_WITH_WARNINGS,
        Trigger.CONFIRM_WARNINGS,
        TaskStatus.WRITING_REVIEWING,
        True,
    ),
    Transition(TaskStatus.WRITING_REVIEWING, Trigger.WRITING_DONE, TaskStatus.WAITING_DRAFT_EDIT, True),
    Transition(TaskStatus.WRITING_REVIEWING, Trigger.WRITING_FAILED, TaskStatus.WRITING_FAILED, False, True, "writing"),
    Transition(TaskStatus.WAITING_DRAFT_EDIT, Trigger.START_FORMAT, TaskStatus.FORMAT_REVIEWING, True),
    Transition(TaskStatus.FORMAT_REVIEWING, Trigger.FORMAT_BLOCK, TaskStatus.FORMAT_BLOCKED, False, True, "format"),
    Transition(TaskStatus.FORMAT_REVIEWING, Trigger.FORMAT_CONFIRM, TaskStatus.WAITING_FORMAT_CONFIRM, True),
    Transition(TaskStatus.FORMAT_REVIEWING, Trigger.FORMAT_PASS, TaskStatus.PACKAGE_READY),
    Transition(TaskStatus.WAITING_FORMAT_CONFIRM, Trigger.CONFIRM_FORMAT, TaskStatus.PACKAGE_READY, True),
    Transition(TaskStatus.PACKAGE_READY, Trigger.PACKAGE_DONE, TaskStatus.PACKAGE_READY),
    Transition(TaskStatus.PACKAGE_READY, Trigger.PACKAGE_FAILED, TaskStatus.FAILED, False, True, "package"),
    Transition(TaskStatus.PACKAGE_READY, Trigger.START_PUBLISH, TaskStatus.PUBLISHING, True),
    Transition(TaskStatus.PUBLISHING, Trigger.PUBLISH_DONE, TaskStatus.PUBLISHED),
    Transition(TaskStatus.PUBLISHING, Trigger.PUBLISH_FAILED, TaskStatus.PUBLISH_FAILED, False, True, "publish"),
)


def validate_transition(current: TaskStatus, trigger: Trigger) -> Transition:
    for transition in TRANSITIONS:
        if transition.current == current and transition.trigger == trigger:
            return transition
    raise StateError("非法状态迁移", f"{current.value} 不能执行 {trigger.value}")


def retry_target(stage: str | None) -> TaskStatus:
    mapping = {
        "research": TaskStatus.RESEARCHING,
        "content": TaskStatus.CONTENT_REVIEWING,
        "writing": TaskStatus.WRITING_REVIEWING,
        "format": TaskStatus.FORMAT_REVIEWING,
        "package": TaskStatus.PACKAGE_READY,
        "publish": TaskStatus.PUBLISHING,
        "prompt_version_missing": TaskStatus.FAILED,
    }
    if stage not in mapping:
        raise StateError("不可重试状态", f"last_failed_stage={stage!r}")
    return mapping[stage]


def phase_to_status(phase: str) -> TaskStatus:
    mapping = {
        "research": TaskStatus.WAITING_RESEARCH_EDIT,
        "content": TaskStatus.CONTENT_REVIEWING,
        "draft": TaskStatus.WAITING_DRAFT_EDIT,
        "format": TaskStatus.FORMAT_REVIEWING,
        "package": TaskStatus.PACKAGE_READY,
    }
    if phase not in mapping:
        raise StateError("未知回滚阶段", f"--to-phase {phase} 不受支持")
    return mapping[phase]
